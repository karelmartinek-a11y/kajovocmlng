"""Executable DESIGN reference, not production acceptance or a database emulator.

All inputs/state are plain dictionaries; transitions return copies. The caller's
replacement of the durable dictionary is the modeled COMMIT linearization point.
Prepared dictionaries are private and cannot authorize dispatch. Synthetic IDs,
JSON hashing and auth/precheck facts are test abstractions, not wire contracts.
Main integration must validate masks and transport separately.
Receipts and IDs remain ABSTRACT_MODEL data. Event identity/payload follow the
native SSE shape, but UUID, timestamp and wire-schema validation are not modeled.

Physical SQL plan (NOT runtime proof): BEGIN; B authority/credential heads;
C stable locator then domain idempotency record (unique insert/read/compare);
E generation job FOR UPDATE; recheck current guards; H children, queue/outbox;
I audit_head last; COMMIT. Applicable A/D/F/G locks retain 51.6 order.
Production must prove constraints, isolation, fresh auth, audit chain, crash
durability, lock ordering and fresh worker dispatch guards against real SQL.
51.21's generic run approval/resume is supporting atomicity precedent, not a
replacement of 12.21's generation-specific six-write set.
"""

from copy import deepcopy
import hashlib
import hmac
import json
import re


RULE_SOURCES = {
    'sixWrites': '12.21 numbered items 1-6; 51.30 final paragraph forbids split T1',
    'eligibility': '12.21 first three paragraphs: exact revision/turn/capability, no blocking questions',
    'commit': '51.5 steps 8-15 and final paragraph; 12.21 crash paragraph',
    'lockPlan': '51.6 SSOT-DECL-198 classes A-I; 51.12 locator subordinal 0 then record 1',
    'replay': '49.4 stable locator/clientRequestDigest paragraphs; 51.12 claim steps 4-6 and terminal replay paragraph',
    'auth': '51.12 terminal replay paragraph: authentication and result access remain mandatory',
    'sequence': '49.5 first paragraph; 51.13 locked root allocation and rollback paragraph',
    'audit': '49.5 audit_head paragraph; 51.5 steps 13-14',
    'delivery': '49.5 outbox, post-commit publication and transactional inbox paragraphs',
    'resume': '51.21 decision steps 1-7, replay and resume paragraphs; 51.30 Approval decision row',
    'unknown': '49.4 unknown outcome/exactly-once limitations; 51.12 lost-response replay; conservative model lookup-only policy',
    'cancellation': '49.4 immutable terminal outcomes and cancellation closure; 51.5 fresh cancellation guards; post-approval cancellation is separate work',
    'precheck': '12.21 eligibility; 51.5 preflight is not authoritative: precheckAccepted is a trusted model fact, never caller authority',
    'fieldNames': '12.21 and 12.44.3 ApprovalReceipt technical serialization; abstract receipt wrapper is not a public mask',
    'phaseClosure': '12.3-12.5; 49.15 phase-success steps 1-7; 49.25 phase-terminal crash row; 51.16; 51.31 active-phase index',
    'serverGuards': '12.5; 25.11 generation_job; 51.5/51.9; operation-contracts record 354 fencingPolicy; 26.1 server-derived authority',
    'checkpoint': '49.15 complete output checkpoint; 51.21 immutable checkpoint/pointer paragraph',
    'nativeEvent': '12.44.1: aggregate Counter eventId and two-field payload; receipt is separate',
}
WRITES = ('idempotency', 'authority', 'approvedPointer', 'phaseClosure',
          'terminalEvidence', 'checkpointPointer', 'successorReservation',
          'eventAudit', 'jobTransition', 'planningQueueOutbox')
ACTIVE_PHASE_STATES = frozenset(('QUEUED', 'RUNNING', 'WAITING_FOR_DEPENDENCY',
                               'WAITING_FOR_OWNER', 'REPAIRING', 'CANCEL_REQUESTED'))
COMPLETION_EDGES = frozenset((('WAITING_FOR_OWNER', 'RUNNING'),
                            ('RUNNING', 'SUCCEEDED'), ('REPAIRING', 'SUCCEEDED')))
HEAD_FIELDS = ('platformIncarnation', 'deploymentEpoch', 'recoveryEpoch', 'coordinatorFence')
CURRENT = ('currentTurnId', 'currentTurnStatus', 'specificationRevisionId',
           'specificationDigest', 'capabilitySnapshotId', 'capabilitySnapshotDigest')
LIMITATIONS = [
    'DESIGN only: deterministic in-memory transitions, no SQL or external services.',
    'Physical SQL plan is not runtime proof of locks, constraints, isolation or durability.',
    'Auth/precheck/snapshot provenance and JSON canonicalization are trusted model inputs.',
    'No worker execution authority: full dispatch/lease/cancellation design is outside this scoped model; real execution tests are separately production work.',
    'Main integrates operation masks and transport separately; no package acceptance claim.',
    'Server context is trusted test input; acquisition, DB-time lease validity and full guard applicability are not proven.',
    'Only discussion-to-planning closure is modeled; no full lifecycle, wire or design coverage claim.',
]


class Rejected(ValueError):
    """Model reason codes are not public error-mask definitions."""


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


def digest(value):
    return 'sha256:' + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                               ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def counter(value):
    require(type(value) is str and re.fullmatch(r'0|[1-9][0-9]*', value) is not None,
            'DECIMAL_COUNTER_REQUIRED')
    require(int(value) <= 9223372036854775807, 'COUNTER_OVERFLOW')
    return int(value)


def increment(value):
    result = str(counter(value) + 1)
    counter(result)
    return result


def initial(snapshot, phase, checkpoint, heads):
    counter(snapshot['stateVersion'])
    counter(snapshot['eventSequence'])
    return {'job': deepcopy(snapshot), 'idempotency': {}, 'authorities': {},
            'approvedPointer': None, 'events': [], 'audit': [], 'planning': {},
            'queue': {}, 'outbox': {}, 'auditSequence': '0',
            'phases': {phase['id']: deepcopy(phase)},
            'checkpoints': {checkpoint['id']: deepcopy(checkpoint)},
            'heads': deepcopy(heads), 'successors': {}, 'terminalEvidence': {}}


def execution_context(state):
    """Abstract trusted server resolution; NEVER taken from the public request.

    Lease validity at the modeled lock boundary is a supplied fact, not an
    implementation of DB-time expiry, lease acquisition or takeover.
    """
    job = state['job']
    phase = state['phases'][job['currentPhaseRunId']]
    checkpoint = state['checkpoints'][job['latestCheckpointId']]
    return {**deepcopy(state['heads']), 'phaseRunId': phase['id'],
            'phaseState': phase['state'], 'phaseStateVersion': phase['stateVersion'],
            'phaseFence': phase['fence'], 'cancellationVersion': job['cancellationVersion'],
            'checkpointId': checkpoint['id'], 'checkpointDigest': digest(checkpoint),
            'leaseValidAtLock': True, 'dependenciesCurrent': True,
            'emittedAt': '2000-01-01T00:00:00Z'}


def active_phase_invariant(state):
    phases = list(state['phases'].values())
    require(all(p['jobId'] == state['job']['jobId'] for p in phases), 'WRONG_PHASE_JOB')
    require(sum(p['state'] in ACTIVE_PHASE_STATES for p in phases) <= 1,
            'MULTIPLE_ACTIVE_PHASES')


def phase_transition(phase, target):
    """Only the edges needed by this derivation; not the full phase machine."""
    require((phase['state'], target) in COMPLETION_EDGES, 'ILLEGAL_PHASE_EDGE')
    phase['state'] = target
    phase['stateVersion'] = increment(phase['stateVersion'])


def validate_server_context(state, context):
    require(isinstance(context, dict), 'SERVER_CONTEXT_REQUIRED')
    active_phase_invariant(state)
    job = state['job']
    phase = state['phases'].get(job.get('currentPhaseRunId'))
    require(phase is not None and phase['phase'] == 'DISCUSSING'
            and job['currentPhase'] == 'DISCUSSING', 'DISCUSSION_PHASE_REQUIRED')
    require(phase['state'] in ('RUNNING', 'WAITING_FOR_OWNER', 'REPAIRING'), 'PHASE_NOT_COMPLETABLE')
    expected = {**state['heads'], 'phaseRunId': phase['id'], 'phaseState': phase['state'],
                'phaseStateVersion': phase['stateVersion'], 'phaseFence': phase['fence'],
                'cancellationVersion': job['cancellationVersion'],
                'checkpointId': job['latestCheckpointId']}
    require(all(context.get(k) == v for k, v in expected.items()), 'STALE_SERVER_CONTEXT')
    require(context.get('leaseValidAtLock') is True, 'SERVER_LEASE_INVALID')
    require(context.get('dependenciesCurrent') is True, 'DEPENDENCIES_STALE')
    checkpoint = state['checkpoints'].get(job['latestCheckpointId'])
    require(checkpoint is not None and checkpoint.get('complete') is True
            and checkpoint.get('phaseRunId') == phase['id']
            and checkpoint.get('jobId') == job['jobId']
            and phase.get('outputCheckpointId') == checkpoint['id'], 'CHECKPOINT_INCOMPLETE')
    require(context.get('checkpointDigest') == digest(checkpoint)
            and checkpoint.get('snapshot') == {k: job[k] for k in CURRENT}, 'CHECKPOINT_STALE')
    # No pre-existing execution authority or plan is fabricated as an input guard.
    # Authority is created by approval; the plan is produced by its queued successor.
    require(isinstance(context.get('emittedAt'), str) and bool(context['emittedAt']), 'SERVER_TIME_REQUIRED')


def authenticate(auth, request):
    require(auth.get('authenticated') is True and auth.get('resultAccess') is True
            and auth.get('callerAuthorityKind') == 'OWNER_FULL'
            and request['jobId'] in auth.get('jobIds', []), 'AUTH_REQUIRED')


def locator(request, auth):
    # Stable family/caller/target/key, never session, current revision or attempt.
    return digest(['generation.approve', auth['callerAuthorityKind'],
                   auth['stableCallerObjectId'], request['jobId'], request['idempotencyKey']])


def request_digest(request):
    return digest({key: value for key, value in request.items() if key != 'idempotencyKey'})


def lookup(state, request, auth):
    authenticate(auth, request)
    record = state['idempotency'].get(locator(request, auth))
    if record is None:
        return None
    require(hmac.compare_digest(record['requestDigest'], request_digest(request)), 'IDEMPOTENCY_CONFLICT')
    return deepcopy(record['receipt'])


def prepare(state, request, auth, *, server_context=None):
    """Replay precedes ALL fresh CAS/eligibility tests. No durable mutation."""
    receipt = lookup(state, request, auth)
    if receipt is not None:
        return {'kind': 'REPLAY', 'receipt': receipt}
    job = state['job']
    require(request['jobId'] == job['jobId'], 'WRONG_JOB')
    counter(request['expectedStateVersion'])
    require(request['expectedStateVersion'] == job['stateVersion'], 'STALE_CAS')
    require(job['jobState'] == 'DISCUSSING' and not job.get('cancellationRequested', False), 'NOT_APPROVABLE')
    require(job['currentTurnStatus'] == 'COMPLETED' and job['precheckAccepted'] is True
            and job['approvable'] is True and job['blockingQuestions'] == [], 'NOT_APPROVABLE')
    require(all(request[key] == job[key] for key in CURRENT), 'STALE_SNAPSHOT')
    require(set(request) == set(CURRENT) | {'jobId', 'expectedStateVersion', 'idempotencyKey'},
            'CALLER_SERVER_FIELDS_FORBIDDEN')
    validate_server_context(state, server_context)
    return {'kind': 'PREPARED', 'baseDigest': digest(state), 'request': deepcopy(request),
            'serverContext': deepcopy(server_context),
            'auth': deepcopy(auth), 'locator': locator(request, auth), 'writes': list(WRITES)}


def commit(state, transaction, auth, *, server_context=None, omit=(), audit_failure=False, crash_before=False):
    """Fault injection omits real staged writes; invariant validation rejects them.

    Audit failure/crash discards every staged write, including counter allocation.
    Current auth is checked even when committing a previously prepared request.
    """
    require(transaction['kind'] == 'PREPARED', 'NOT_PREPARED')
    request = transaction['request']
    authenticate(auth, request)
    require(locator(request, auth) == transaction['locator'], 'AUTH_REQUIRED')
    replay = lookup(state, request, auth)
    if replay is not None:
        return deepcopy(state), replay
    require(digest(state) == transaction['baseDigest'], 'STALE_CAS')
    prepare(state, request, auth, server_context=server_context)
    require(all(server_context[k] == transaction['serverContext'][k]
                for k in (*HEAD_FIELDS, 'phaseRunId', 'phaseState', 'phaseStateVersion',
                          'phaseFence', 'cancellationVersion', 'checkpointId', 'checkpointDigest')),
            'STALE_SERVER_CONTEXT')
    require(not set(omit) - set(WRITES) - {'queue', 'outbox'}, 'UNKNOWN_FAULT')
    staged = deepcopy(state)
    key = transaction['locator']
    authority_id, planning_id = ('authority:' + key, 'planning:' + key)
    predecessor_id = state['job']['currentPhaseRunId']
    checkpoint_id = 'checkpoint:' + key
    predecessor = deepcopy(state['phases'][predecessor_id])
    path = [predecessor['state']]
    if predecessor['state'] == 'WAITING_FOR_OWNER':
        phase_transition(predecessor, 'RUNNING')
        path.append('RUNNING')
    phase_transition(predecessor, 'SUCCEEDED')
    path.append('SUCCEEDED')
    predecessor.update(outputCheckpointId=checkpoint_id, successorId=planning_id)
    payload = {name: request[name] for name in ('jobId', 'specificationRevisionId', 'specificationDigest')}
    payload.update(executionAuthorityId=authority_id, planningPhaseRunId=planning_id, jobState='ANALYZING')
    snapshot = deepcopy(state['job'])
    snapshot.update(jobState='ANALYZING', stateVersion=increment(snapshot['stateVersion']),
                    eventSequence=increment(snapshot['eventSequence']), currentPhase='ANALYZING',
                    currentPhaseRunId=planning_id, latestCheckpointId=checkpoint_id)
    event_id = snapshot['eventSequence']
    receipt = {'modelFormat': 'ABSTRACT_APPROVAL_RECEIPT', 'payload': payload,
               'snapshot': snapshot, 'eventId': event_id, 'committed': True}
    receipt['resultDigest'] = digest(receipt)
    event = {'type': 'generation.spec.approved', 'objectId': request['jobId'],
             'eventId': event_id, 'emittedAt': server_context['emittedAt'],
             'payload': {k: request[k] for k in ('specificationRevisionId', 'specificationDigest')}}
    checkpoint = {'id': checkpoint_id, 'jobId': request['jobId'], 'phaseRunId': predecessor_id,
                  'complete': True, 'previousId': state['job']['latestCheckpointId'],
                  'previousDigest': server_context['checkpointDigest'],
                  'sequence': increment(state['checkpoints'][state['job']['latestCheckpointId']]['sequence']),
                  'phaseVersionBefore': state['phases'][predecessor_id]['stateVersion'],
                  'phaseVersionAfter': predecessor['stateVersion'],
                  'jobVersionBefore': state['job']['stateVersion'], 'jobVersionAfter': snapshot['stateVersion'],
                  'serverGuards': deepcopy(server_context), 'result': deepcopy(payload), 'phasePath': path}
    written = []
    for write in WRITES:
        if write in omit:
            continue
        written.append(write)
        if write == 'idempotency':
            staged['idempotency'][key] = {'requestDigest': request_digest(request), 'receipt': deepcopy(receipt)}
        elif write == 'authority':
            staged['authorities'][authority_id] = deepcopy(payload)
        elif write == 'approvedPointer':
            staged['approvedPointer'] = {k: request[k] for k in ('specificationRevisionId', 'specificationDigest')}
        elif write == 'phaseClosure':
            staged['phases'][predecessor_id] = deepcopy(predecessor)
        elif write == 'terminalEvidence':
            staged['terminalEvidence'][predecessor_id] = {
                'resultDigest': digest(payload), 'checkpointDigest': digest(checkpoint), 'phasePath': path}
        elif write == 'checkpointPointer':
            staged['checkpoints'][checkpoint_id] = deepcopy(checkpoint)
        elif write == 'successorReservation':
            require(predecessor_id not in staged['successors'], 'SUCCESSOR_ALREADY_RESERVED')
            staged['successors'][predecessor_id] = planning_id
        elif write == 'eventAudit':
            staged['events'].append(event)
            staged['auditSequence'] = increment(staged['auditSequence'])
            staged['audit'].append({'chainSequence': staged['auditSequence'], 'eventDigest': digest(event)})
            require(not audit_failure, 'AUDIT_FAILURE')
        elif write == 'jobTransition':
            staged['job'] = snapshot
        elif write == 'planningQueueOutbox':
            active_phase_invariant(staged)
            staged['phases'][planning_id] = {'id': planning_id, 'jobId': request['jobId'],
                'phase': 'ANALYZING', 'state': 'QUEUED', 'stateVersion': '0',
                'predecessorId': predecessor_id, 'inputCheckpointId': checkpoint_id}
            staged['planning'][planning_id] = deepcopy(payload)
            if 'queue' not in omit:
                staged['queue'][planning_id] = {'planningPhaseRunId': planning_id, 'jobId': request['jobId']}
            if 'outbox' not in omit:
                staged['outbox'][event_id] = {'event': deepcopy(event), 'delivered': False}
    require(tuple(written) == WRITES and planning_id in staged['queue'] and event_id in staged['outbox'],
            'INCOMPLETE_ATOMIC_SET')
    validate_handoff(state, staged, receipt)
    require(not crash_before, 'CRASH_BEFORE_COMMIT')
    return staged, deepcopy(receipt)


def approve(state, request, auth, *, server_context=None, commit_unknown=False, **faults):
    if commit_unknown:
        result = lookup(state, request, auth)
        return deepcopy(state), {'disposition': 'LOOKUP_ONLY', 'receipt': result}
    transaction = prepare(state, request, auth, server_context=server_context)
    if transaction['kind'] == 'REPLAY':
        return deepcopy(state), transaction['receipt']
    return commit(state, transaction, auth, server_context=server_context, **faults)


def validate_handoff(before, after, receipt):
    """Structural successor obligations, independent of the staged-write labels."""
    active_phase_invariant(after)
    predecessor_id = before['job']['currentPhaseRunId']
    successor_id = receipt['payload']['planningPhaseRunId']
    predecessor = after['phases'][predecessor_id]
    successor = after['phases'].get(successor_id, {})
    checkpoint = after['checkpoints'].get(after['job']['latestCheckpointId'], {})
    evidence = after['terminalEvidence'].get(predecessor_id, {})
    path = checkpoint.get('phasePath', [])
    require(predecessor['state'] == 'SUCCEEDED' and path
            and path[0] == before['phases'][predecessor_id]['state'] and path[-1] == 'SUCCEEDED'
            and all(edge in COMPLETION_EDGES for edge in zip(path, path[1:])), 'PHASE_CLOSURE_INVALID')
    require(evidence.get('resultDigest') == digest(receipt['payload'])
            and evidence.get('checkpointDigest') == digest(checkpoint)
            and evidence.get('phasePath') == path and checkpoint.get('complete') is True
            and predecessor.get('outputCheckpointId') == checkpoint.get('id'), 'TERMINAL_EVIDENCE_INVALID')
    require(after['successors'].get(predecessor_id) == successor_id
            and predecessor.get('successorId') == successor_id
            and successor.get('predecessorId') == predecessor_id
            and successor.get('phase') == 'ANALYZING' and successor.get('state') == 'QUEUED'
            and successor.get('inputCheckpointId') == checkpoint.get('id')
            and after['job']['currentPhaseRunId'] == successor_id
            and after['job']['currentPhase'] == after['job']['jobState'] == 'ANALYZING'
            and successor_id in after['queue'] and successor_id in after['planning'], 'SUCCESSOR_INVALID')
    require(all(after['checkpoints'].get(k) == v for k, v in before['checkpoints'].items())
            and checkpoint.get('previousId') == before['job']['latestCheckpointId']
            and checkpoint.get('previousDigest') == digest(before['checkpoints'][checkpoint['previousId']]),
            'CHECKPOINT_CHAIN_INVALID')


def consumer(job_id, sequence='0'):
    counter(sequence)
    return {'jobId': job_id, 'eventSequence': sequence, 'inbox': {}, 'applied': [], 'snapshotRequired': False}


def consume(current, event):
    require(event['objectId'] == current['jobId'], 'WRONG_JOB')
    require(set(event) == {'type', 'objectId', 'eventId', 'emittedAt', 'payload'}
            and event['type'] == 'generation.spec.approved'
            and set(event['payload']) == {'specificationRevisionId', 'specificationDigest'}, 'EVENT_SHAPE_INVALID')
    sequence = counter(event['eventId'])
    previous = current['inbox'].get(event['eventId'])
    if previous is not None:
        require(hmac.compare_digest(previous, digest(event)), 'EVENT_DIGEST_CONFLICT')
        return deepcopy(current), 'DUPLICATE'
    result = deepcopy(current)
    if sequence != counter(current['eventSequence']) + 1:
        result['snapshotRequired'] = True
        return result, 'SNAPSHOT_REQUIRED'
    result['inbox'][event['eventId']] = digest(event)
    result['eventSequence'] = event['eventId']
    result['applied'].append(deepcopy(event['payload']))
    return result, 'APPLIED'


def resnapshot(current, committed_snapshot):
    """Input must be a trusted committed server snapshot, never an SSE claim."""
    require(committed_snapshot['jobId'] == current['jobId'], 'WRONG_JOB')
    require(counter(committed_snapshot['eventSequence']) >= counter(current['eventSequence']), 'STALE_SNAPSHOT')
    counter(committed_snapshot['stateVersion'])
    result = deepcopy(current)
    result.update(eventSequence=committed_snapshot['eventSequence'], snapshotRequired=False,
                  snapshot=deepcopy(committed_snapshot))
    return result


def deliver(state, current, event_id, *, crash=None):
    """Polling works without notifications. Crash after delivery leaves outbox pending."""
    require(crash in (None, 'before_delivery', 'after_delivery'), 'UNKNOWN_FAULT')
    require(event_id in state['outbox'], 'NO_COMMITTED_OUTBOX')
    row = state['outbox'][event_id]
    if crash == 'before_delivery':
        return deepcopy(state), deepcopy(current), 'CRASH_BEFORE_DELIVERY'
    updated, outcome = consume(current, row['event'])
    durable = deepcopy(state)
    if crash != 'after_delivery' and outcome in ('APPLIED', 'DUPLICATE'):
        durable['outbox'][event_id]['delivered'] = True
    return durable, updated, outcome


def request_cancellation(state):
    """Only models a control request; does not assert cancellation terminal closure.

    Approval authority/pointer/receipt survive. Production cancellation event,
    audit/outbox, queue claims and cleanup are outside this approval model.
    """
    result = deepcopy(state)
    result['job']['cancellationRequested'] = True
    result['job']['stateVersion'] = increment(result['job']['stateVersion'])
    result['job']['cancellationVersion'] = increment(result['job']['cancellationVersion'])
    return result


if __name__ == '__main__':
    print(json.dumps({'evidenceLevel': 'DESIGN', 'rules': RULE_SOURCES, 'limitations': LIMITATIONS}, indent=2))
