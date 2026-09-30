"""Test real DESIGN model transitions; never issue a production/package PASS."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile

import generation_atomic_model as model
from ssot_sources import ROOT, SSOT


def fixture():
    snapshot = {
        'jobId': 'job-1', 'jobState': 'DISCUSSING', 'stateVersion': '7', 'eventSequence': '0',
        'currentTurnId': 'turn-2', 'currentTurnStatus': 'COMPLETED',
        'specificationRevisionId': 'spec-3', 'specificationDigest': model.digest({'spec': 3}),
        'capabilitySnapshotId': 'cap-4', 'capabilitySnapshotDigest': model.digest({'cap': 4}),
        'precheckAccepted': True, 'approvable': True, 'blockingQuestions': [],
        'currentPhase': 'DISCUSSING', 'currentPhaseRunId': 'discussion-1',
        'latestCheckpointId': 'checkpoint-1', 'cancellationVersion': '0',
    }
    request = {key: snapshot[key] for key in model.CURRENT}
    request.update(jobId='job-1', expectedStateVersion='7', idempotencyKey='approval-1')
    auth = {'authenticated': True, 'resultAccess': True, 'callerAuthorityKind': 'OWNER_FULL',
            'stableCallerObjectId': 'owner-1', 'jobIds': ['job-1']}
    phase = {'id': 'discussion-1', 'jobId': 'job-1', 'phase': 'DISCUSSING',
             'state': 'WAITING_FOR_OWNER', 'stateVersion': '4', 'fence': '11',
             'outputCheckpointId': 'checkpoint-1'}
    checkpoint = {'id': 'checkpoint-1', 'jobId': 'job-1', 'phaseRunId': 'discussion-1',
                  'sequence': '2', 'complete': True,
                  'snapshot': {k: snapshot[k] for k in model.CURRENT}}
    heads = {'platformIncarnation': 'incarnation-1', 'deploymentEpoch': '2',
             'recoveryEpoch': '3', 'coordinatorFence': '8'}
    return model.initial(snapshot, phase, checkpoint, heads), request, auth


def run_checks():
    checks = []

    def check(name, condition):
        checks.append({'case': name, 'passed': bool(condition)})

    def rejected(name, reason, function):
        try:
            function()
        except model.Rejected as exc:
            check(name, str(exc) == reason)
        else:
            check(name, False)

    state, request, auth = fixture()
    context = model.execution_context(state)

    # Separate trusted server input, never added to request/auth or re-resolved
    # from a stale command. Individual tests override it for guard failures.
    def prepare(s, r, a, **kwargs):
        return model.prepare(s, r, a, server_context=context, **kwargs)

    def commit(s, t, a, **kwargs):
        return model.commit(s, t, a, server_context=context, **kwargs)

    def approve(s, r, a, **kwargs):
        return model.approve(s, r, a, server_context=context, **kwargs)

    original = deepcopy(state)
    transaction = prepare(state, request, auth)
    check('prepare/no-authority-planning-event-outbox-or-other-write', state == original)
    rejected('prepare/cannot-deliver', 'NO_COMMITTED_OUTBOX',
             lambda: model.deliver(state, model.consumer('job-1'), 'uncommitted'))
    for write in model.WRITES + ('queue', 'outbox'):
        rejected('split-commit/' + write, 'INCOMPLETE_ATOMIC_SET',
                 lambda write=write: commit(state, transaction, auth, omit=(write,)))
        check('split-rollback/' + write, state == original)
    for fault, reason in [('audit_failure', 'AUDIT_FAILURE'), ('crash_before', 'CRASH_BEFORE_COMMIT')]:
        rejected(fault, reason, lambda fault=fault: commit(state, transaction, auth, **{fault: True}))
        check(fault + '/rollback-including-counters', state == original)

    committed, receipt = approve(state, request, auth)
    event_id = receipt['eventId']
    check('commit/exact-payload-fields', set(receipt['payload']) == {
        'jobId', 'specificationRevisionId', 'specificationDigest', 'executionAuthorityId', 'planningPhaseRunId', 'jobState'})
    check('commit/six-write-effects', len(committed['idempotency']) == len(committed['authorities']) ==
          len(committed['events']) == len(committed['audit']) == len(committed['planning']) ==
          len(committed['queue']) == len(committed['outbox']) == 1
          and committed['approvedPointer']['specificationDigest'] == request['specificationDigest']
          and committed['job']['jobState'] == 'ANALYZING')
    check('commit/contiguous-counters-after-rollback', receipt['snapshot']['stateVersion'] == '8'
          and receipt['snapshot']['eventSequence'] == '1' and committed['auditSequence'] == '1')
    check('commit/snapshot-current-identities-and-precheck', all(receipt['snapshot'][k] == request[k]
          for k in model.CURRENT) and receipt['snapshot']['precheckAccepted'] is True)
    check('commit/input-not-mutated', state == original)
    again, replay = approve(committed, request, auth)
    check('replay/no-new-writes-frozen-receipt', again == committed and replay == receipt)
    receipt_copy = deepcopy(receipt)
    replay['payload']['jobState'] = 'CORRUPTED_BY_CALLER'
    check('replay/caller-cannot-mutate-stored-receipt', model.lookup(committed, request, auth) == receipt_copy)
    advanced = deepcopy(committed)
    advanced['job'].update(stateVersion='19', jobState='IMPLEMENTING', currentTurnId='later-turn',
                           capabilitySnapshotId='later-capability', precheckAccepted=False)
    after, frozen = approve(advanced, request, auth)
    check('replay/state-advance-keeps-original-result', after == advanced and frozen == receipt_copy)
    changed = {**request, 'specificationDigest': model.digest('different')}
    rejected('same-key/altered-digest-before-cas', 'IDEMPOTENCY_CONFLICT',
             lambda: approve(advanced, changed, auth))
    rejected('new-key/stale-cas', 'STALE_CAS',
             lambda: approve(committed, {**request, 'idempotencyKey': 'second'}, auth))
    second = prepare(state, {**request, 'idempotencyKey': 'second'}, auth)
    rejected('race/second-prepared-command-loses-cas', 'STALE_CAS',
             lambda: commit(committed, second, auth))
    same_race, race_receipt = commit(committed, transaction, auth)
    check('race/same-key-one-result', same_race == committed and race_receipt == receipt_copy)
    for field in ('authenticated', 'resultAccess'):
        rejected('replay/current-auth/' + field, 'AUTH_REQUIRED',
                 lambda field=field: approve(advanced, request, {**auth, field: False}))
    rejected('commit/revoked-auth', 'AUTH_REQUIRED',
             lambda: commit(state, transaction, {**auth, 'authenticated': False}))
    for field in model.CURRENT:
        stale = {**request, field: 'stale'}
        rejected('fresh/snapshot/' + field, 'STALE_SNAPSHOT',
                 lambda stale=stale: approve(state, stale, auth))
    for field, value in [('precheckAccepted', False), ('approvable', False), ('blockingQuestions', ['q']),
                         ('currentTurnStatus', 'RUNNING'), ('cancellationRequested', True)]:
        ineligible = deepcopy(state)
        ineligible['job'][field] = value
        rejected('fresh/eligibility/' + field, 'NOT_APPROVABLE',
                 lambda ineligible=ineligible: approve(ineligible, request, auth))
    for value in [0, True, '01', '-1', '1.0', '9223372036854775808']:
        rejected('counter/' + repr(value), 'COUNTER_OVERFLOW' if value == '9223372036854775808' else 'DECIMAL_COUNTER_REQUIRED',
                 lambda value=value: model.counter(value))
    unknown, pending = approve(state, request, auth, commit_unknown=True)
    check('unknown/uncommitted-lookup-never-creates-effect', unknown == state and pending == {'disposition': 'LOOKUP_ONLY', 'receipt': None})
    known, resolved = approve(committed, request, auth, commit_unknown=True)
    check('unknown/committed-lookup-recovers-receipt', known == committed and resolved['receipt'] == receipt_copy)
    cancelled = model.request_cancellation(committed)
    check('cancellation/after-commit-does-not-reverse-approval',
          all(cancelled[k] == committed[k] for k in committed if k != 'job')
          and cancelled['job']['jobState'] == 'ANALYZING'
          and model.lookup(cancelled, request, auth) == receipt_copy)

    inbox = model.consumer('job-1')
    before, untouched, outcome = model.deliver(committed, inbox, event_id, crash='before_delivery')
    check('crash/before-delivery-keeps-durable-outbox', before == committed and untouched == inbox)
    sent, consumed, outcome = model.deliver(before, untouched, event_id, crash='after_delivery')
    check('crash/after-delivery-before-marker', outcome == 'APPLIED' and not sent['outbox'][event_id]['delivered']
          and len(consumed['applied']) == 1)
    recovered, deduped, outcome = model.deliver(sent, consumed, event_id)
    check('recovery/poll-redelivers-and-deduplicates', outcome == 'DUPLICATE' and deduped == consumed
          and recovered['outbox'][event_id]['delivered'])
    event = deepcopy(committed['events'][0])
    corrupt = deepcopy(event)
    corrupt['payload']['specificationDigest'] = model.digest('corrupt')
    rejected('inbox/same-id-altered-digest', 'EVENT_DIGEST_CONFLICT', lambda: model.consume(consumed, corrupt))
    rejected('inbox/wrong-job-same-sequence', 'WRONG_JOB', lambda: model.consume(model.consumer('job-2'), event))
    corrupt = deepcopy(event)
    corrupt['payload']['jobId'] = 'job-2'
    rejected('inbox/extra-payload-job', 'EVENT_SHAPE_INVALID', lambda: model.consume(inbox, corrupt))
    gap_event = {**event, 'eventId': '3'}
    gap, outcome = model.consume(inbox, gap_event)
    check('inbox/gap-no-silent-apply', outcome == 'SNAPSHOT_REQUIRED' and gap['eventSequence'] == '0'
          and gap['applied'] == [] and gap['inbox'] == {})
    snapshot = {**receipt_copy['snapshot'], 'eventSequence': '2', 'stateVersion': '9'}
    synced = model.resnapshot(gap, snapshot)
    final, outcome = model.consume(synced, gap_event)
    check('inbox/snapshot-then-next-sequence', outcome == 'APPLIED' and final['eventSequence'] == '3'
          and len(final['applied']) == 1 and not final['snapshotRequired'])
    rejected('snapshot/wrong-job', 'WRONG_JOB', lambda: model.resnapshot(gap, {**snapshot, 'jobId': 'job-2'}))
    rejected('snapshot/regression', 'STALE_SNAPSHOT', lambda: model.resnapshot(final, snapshot))
    missing_history = model.consumer('job-1', '1')
    _, outcome = model.consume(missing_history, event)
    check('inbox/old-sequence-without-history-requires-snapshot', outcome == 'SNAPSHOT_REQUIRED')

    predecessor = committed['phases']['discussion-1']
    successor_id = receipt_copy['payload']['planningPhaseRunId']
    checkpoint = committed['checkpoints'][committed['job']['latestCheckpointId']]
    check('phase/waiting-owner-uses-running-edge', checkpoint['phasePath'] ==
          ['WAITING_FOR_OWNER', 'RUNNING', 'SUCCEEDED'] and predecessor['stateVersion'] == '6')
    check('phase/one-active-queued-successor', predecessor['state'] == 'SUCCEEDED'
          and sum(p['state'] in model.ACTIVE_PHASE_STATES for p in committed['phases'].values()) == 1
          and committed['phases'][successor_id]['state'] == 'QUEUED'
          and committed['successors'] == {'discussion-1': successor_id})
    check('checkpoint/immutable-chain-and-successor-input',
          committed['checkpoints']['checkpoint-1'] == original['checkpoints']['checkpoint-1']
          and checkpoint['sequence'] == '3' and checkpoint['previousId'] == 'checkpoint-1'
          and committed['phases'][successor_id]['inputCheckpointId'] == checkpoint['id'])
    check('event/native-shape-separate-from-abstract-receipt', receipt_copy['modelFormat'] == 'ABSTRACT_APPROVAL_RECEIPT'
          and set(event) == {'type', 'objectId', 'eventId', 'emittedAt', 'payload'}
          and event['eventId'] == receipt_copy['snapshot']['eventSequence']
          and set(event['payload']) == {'specificationRevisionId', 'specificationDigest'})
    rejected('phase/no-direct-waiting-success-edge', 'ILLEGAL_PHASE_EDGE',
             lambda: model.phase_transition(deepcopy(state['phases']['discussion-1']), 'SUCCEEDED'))
    rejected('server/required-on-fresh-command', 'SERVER_CONTEXT_REQUIRED',
             lambda: model.approve(state, request, auth))
    for field in (*model.HEAD_FIELDS, 'phaseRunId', 'phaseState', 'phaseStateVersion',
                  'phaseFence', 'cancellationVersion', 'checkpointId'):
        bad = {**context, field: 'stale'}
        rejected('server/stale/' + field, 'STALE_SERVER_CONTEXT',
                 lambda bad=bad: model.approve(state, request, auth, server_context=bad))
        rejected('server/recheck-at-commit/' + field, 'STALE_SERVER_CONTEXT',
                 lambda bad=bad: model.commit(state, transaction, auth, server_context=bad))
    for field, value, reason in [('checkpointDigest', model.digest('wrong'), 'CHECKPOINT_STALE'),
                                  ('leaseValidAtLock', False, 'SERVER_LEASE_INVALID'),
                                  ('dependenciesCurrent', False, 'DEPENDENCIES_STALE')]:
        rejected('server/' + field, reason,
                 lambda field=field, value=value: model.approve(state, request, auth,
                                                               server_context={**context, field: value}))
    for field in ('phaseFence', 'recoveryEpoch', 'checkpointId', 'serverContext'):
        rejected('request/cannot-supply-server/' + field, 'CALLER_SERVER_FIELDS_FORBIDDEN',
                 lambda field=field: approve(state, {**request, field: context.get(field)}, auth))
    for phase_state in ('RUNNING', 'REPAIRING'):
        ready = deepcopy(state)
        ready['phases']['discussion-1']['state'] = phase_state
        closed, _ = model.approve(ready, request, auth, server_context=model.execution_context(ready))
        check('phase/legal-completion/' + phase_state,
              closed['phases']['discussion-1']['state'] == 'SUCCEEDED'
              and closed['phases']['discussion-1']['stateVersion'] == '5')
    for phase_state in ('QUEUED', 'CANCEL_REQUESTED', 'FAILED', 'SUCCEEDED', 'WAITING_FOR_DEPENDENCY'):
        invalid = deepcopy(state)
        invalid['phases']['discussion-1']['state'] = phase_state
        rejected('phase/deny-completion/' + phase_state, 'PHASE_NOT_COMPLETABLE',
                 lambda invalid=invalid: approve(invalid, request, auth))
    missing = deepcopy(state)
    missing['phases'].clear()
    rejected('phase/completed-turn-does-not-replace-phase', 'DISCUSSION_PHASE_REQUIRED',
             lambda: approve(missing, request, auth))
    duplicate = deepcopy(state)
    duplicate['phases']['other'] = {**duplicate['phases']['discussion-1'], 'id': 'other'}
    rejected('phase/active-uniqueness-precondition', 'MULTIPLE_ACTIVE_PHASES',
             lambda: approve(duplicate, request, auth))
    for field, value in [('complete', False), ('phaseRunId', 'other'), ('jobId', 'other')]:
        invalid = deepcopy(state)
        invalid['checkpoints']['checkpoint-1'][field] = value
        rejected('checkpoint/reject/' + field, 'CHECKPOINT_INCOMPLETE',
                 lambda invalid=invalid: approve(invalid, request, auth))
    missing = deepcopy(state)
    missing['checkpoints'].clear()
    rejected('checkpoint/missing', 'CHECKPOINT_INCOMPLETE', lambda: approve(missing, request, auth))
    stale = deepcopy(state)
    stale['checkpoints']['checkpoint-1']['snapshot']['specificationDigest'] = model.digest('stale')
    rejected('checkpoint/fresh-digest-cannot-hide-stale-content', 'CHECKPOINT_STALE',
             lambda: model.approve(stale, request, auth, server_context=model.execution_context(stale)))
    for field in model.HEAD_FIELDS:
        changed_state = deepcopy(state)
        changed_state['heads'][field] = 'new-authority'
        rejected('race/server-authority-change/' + field, 'STALE_CAS',
                 lambda changed_state=changed_state: model.commit(changed_state, transaction, auth,
                     server_context=model.execution_context(changed_state)))
    rejected('race/cancellation-before-commit', 'STALE_CAS',
             lambda: commit(model.request_cancellation(state), transaction, auth))
    reserved = deepcopy(state)
    reserved['successors']['discussion-1'] = 'other-successor'
    rejected('phase/duplicate-successor-reservation', 'SUCCESSOR_ALREADY_RESERVED',
             lambda: approve(reserved, request, auth))
    replay_state = deepcopy(committed)
    replay_state['heads']['recoveryEpoch'] = '99'
    replay_state['phases']['discussion-1']['fence'] = '99'
    replay_state['checkpoints'].clear()
    replay_state, replay_result = model.approve(replay_state, request, auth)
    check('replay/bypasses-fresh-phase-fence-checkpoint-guards', replay_result == receipt_copy
          and len(replay_state['successors']) == len(replay_state['planning']) == 1)

    # Corrupt committed copies to exercise invariants independently of WRITES.
    invalid = deepcopy(committed)
    invalid['phases']['discussion-1']['state'] = 'RUNNING'
    rejected('invariant/predecessor-left-active', 'MULTIPLE_ACTIVE_PHASES',
             lambda: model.validate_handoff(state, invalid, receipt_copy))
    invalid = deepcopy(committed)
    invalid['terminalEvidence'].clear()
    rejected('invariant/terminal-evidence-missing', 'TERMINAL_EVIDENCE_INVALID',
             lambda: model.validate_handoff(state, invalid, receipt_copy))
    invalid = deepcopy(committed)
    invalid['successors'].clear()
    rejected('invariant/successor-reservation-missing', 'SUCCESSOR_INVALID',
             lambda: model.validate_handoff(state, invalid, receipt_copy))
    invalid = deepcopy(committed)
    invalid['checkpoints']['checkpoint-1']['complete'] = False
    rejected('invariant/immutable-checkpoint-overwrite', 'CHECKPOINT_CHAIN_INVALID',
             lambda: model.validate_handoff(state, invalid, receipt_copy))
    check('failures/input-and-server-context-unchanged', state == original and context == model.execution_context(original))
    return checks


def main():
    # Resolve the live source through ssot_sources; do not use a pinned stale hash.
    source_hash = hashlib.sha256(SSOT.read_bytes()).hexdigest()
    checks = run_checks()
    from ssot_sources import resource_index,resources
    rs=resource_index(resources(SSOT.read_text(encoding='utf8')))
    report = {'evidenceLevel': 'DESIGN', 'evidenceGate':'SSOT_CONTRACT_READY',
              'resourceVersions':{p:r['sha256'] for p,r in rs.items() if p in (
                  'contracts/payload-contracts.json','contracts/generation/http-design.schema.json',
                  'contracts/generation/generation-contracts.schema.json','scripts/ssot/ssot_control.py')},
              'modelSha256':hashlib.sha256(Path(model.__file__).read_bytes()).hexdigest(),
              'sourceSha256': source_hash, 'currentSSOThash': source_hash,
              'source': str(SSOT.relative_to(ROOT)), 'ruleSources': model.RULE_SOURCES,
              'checked': len(checks), 'failed': sum(not c['passed'] for c in checks), 'checks': checks,
              'limitations': model.LIMITATIONS, 'productionAcceptance': False,
              'integration': 'Main integrates masks and transport separately; this verifier does neither.'}
    destination = os.environ.get('KCML_AUDIT_OUTPUT')
    # Default outside shared repo so running this task changes only its two scripts.
    out = ROOT / destination if destination else Path(tempfile.mkdtemp(prefix='kcml-atomic-design-'))
    out.mkdir(parents=True, exist_ok=True)
    path = out / 'generation-atomic-model-tests.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('evidenceLevel', 'currentSSOThash', 'checked', 'failed', 'productionAcceptance')}))
    print(str(path))
    return int(report['failed'] != 0)


if __name__ == '__main__':
    raise SystemExit(main())
