"""DESIGN reference model for exact immutable generation reads, not DB execution.

The in-memory snapshot models CONSISTENT_READ. It does not implement PostgreSQL
isolation, triggers, credentials, session reset, retention or audit persistence.
HTTP masks remain the companion HTTP verifier's responsibility; these checks
compose its existing validators with repository and native event/read predicates.
"""
from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import types

import generation_http_contract as http
from ssot_sources import ROOT, SSOT, resource_index, resources
from verify_phase2_handoffs import witness

CONTROL = 'scripts/ssot/ssot_control.py'
EVENTS = 'contracts/generation/document-events.schema.json'
SECTIONS = ('12.19', '12.23', '12.44.1', '12.44.2', '12.44.3', '26.1', '51.2', '51.10')
BINDINGS = {
    'route.0232': ('GenerationSpecification', 'revisionId', 'generation.spec.proposed',
                   'specificationRevisionId', 'specificationDigest'),
    'route.0237': ('GenerationPlan', 'planId', 'generation.plan.created', 'planId', 'planDigest'),
}
JOB = '00000000-0000-4000-8000-000000000001'
DOCUMENT = '00000000-0000-4000-8000-000000000002'
OTHER = '00000000-0000-4000-8000-000000000003'
LATER = '00000000-0000-4000-8000-000000000004'
TIME = '2026-09-25T00:00:00.000Z'


class Rejected(ValueError):
    """An explicit reference-model predicate rejected the operation."""


@dataclass(frozen=True)
class ImmutableRow:
    route: str
    parent: str
    identity: str
    revision: str
    canonical_bytes: bytes
    canonical_digest: str


class Repository:
    """Fixture writer plus read-only snapshots; no deployed repository claim.

    Records model UNIQUE(parent, revision), UNIQUE(parent, digest), and
    UNIQUE(parent, id) per document collection. No latest-pointer fallback.
    """

    def __init__(self, document, contract_failure):
        self.document = document
        self.contract_failure = contract_failure
        self.state = {'rows': {}, 'jobs': {}, 'activationEpoch': '1', 'latest': {},
                      'domainCommands': [], 'idempotency': [], 'events': [], 'outbox': [],
                      'authorities': [], 'planning': []}

    def append_fixture(self, rid, parent, identity, revision, value, claimed_digest):
        """Model immutable insertion constraints, not a public write endpoint."""
        definition = BINDINGS[rid][0]
        for identifier in (parent, identity):
            self.document.validate('Uuid', identifier)
        self.document.validate('Counter', revision)
        self.document.validate(definition, value)
        if value['jobId'] != parent:
            raise Rejected('PARENT_OWNERSHIP')
        if definition == 'GenerationPlan' and value['planId'] != identity:
            raise Rejected('PLAN_IDENTITY')
        if http.digest(value) != claimed_digest:
            raise Rejected('CANONICAL_DIGEST')
        for row in self.state['rows'].values():
            if row.route != rid:
                continue
            if row.identity == identity and row.parent != parent:
                raise Rejected('PARENT_OWNERSHIP')
            if row.parent != parent:
                continue
            if row.identity == identity:
                raise Rejected('IMMUTABLE_ID')
            if row.revision == revision:
                raise Rejected('UNIQUE_PARENT_REVISION')
            if row.canonical_digest == claimed_digest:
                raise Rejected('UNIQUE_PARENT_DIGEST')
        row = ImmutableRow(rid, parent, identity, revision, http.canonical(value), claimed_digest)
        self.state['rows'][(rid, parent, identity)] = row
        return row

    def mutate_fixture(self, rid, parent, identity, action):
        if (rid, parent, identity) not in self.state['rows']:
            raise Rejected('API_OBJECT_NOT_FOUND')
        if action not in ('UPDATE', 'DELETE', 'REPARENT'):
            raise Rejected('UNKNOWN_MUTATION')
        raise Rejected('IMMUTABLE_MUTATION')

    def snapshot(self):
        # One copy is the model's linearization point. Subsequent lookups never
        # consult live rows, metadata, activation epoch or current pointers.
        return ReadSnapshot(deepcopy(self.state), self.document, self.contract_failure)


class ReadSnapshot:
    def __init__(self, state, document, contract_failure):
        self.state = state
        self.document = document
        self.contract_failure = contract_failure

    def lookup(self, rid, paths):
        if rid not in BINDINGS:
            raise Rejected('API_REQUEST_INVALID')
        definition, path_key, *_ = BINDINGS[rid]
        if set(paths) != {'id', path_key}:
            raise Rejected('API_REQUEST_INVALID')
        for value in paths.values():
            self.document.validate('Uuid', value)
        row = self.state['rows'].get((rid, paths['id'], paths[path_key]))
        if row is None:
            raise Rejected('API_OBJECT_NOT_FOUND')
        if (row.route, row.parent, row.identity) != (rid, paths['id'], paths[path_key]):
            raise Rejected('API_IMMUTABLE_DOCUMENT_INVALID')
        try:
            value = json.loads(row.canonical_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise Rejected('API_IMMUTABLE_DOCUMENT_INVALID') from exc
        if (http.canonical(value) != row.canonical_bytes or http.digest(value) != row.canonical_digest
                or not isinstance(value, dict) or value.get('jobId') != row.parent
                or (rid == 'route.0237' and value.get('planId') != row.identity)):
            raise Rejected('API_IMMUTABLE_DOCUMENT_INVALID')
        try:
            self.document.validate(definition, value)
        except self.contract_failure as exc:
            raise Rejected('API_IMMUTABLE_DOCUMENT_INVALID') from exc
        return row, value

    def response(self, rid, paths, trace, *, fault=None):
        """Fault is a test observation, never a caller-selected error or permission."""
        if fault not in (None, 'API_READ_TIMEOUT', 'API_READ_CANCELLED', 'API_STORAGE_ROLLBACK'):
            raise Rejected('UNKNOWN_READ_FAULT')
        try:
            if fault:
                raise Rejected(fault)
            row, value = self.lookup(rid, paths)
        except Rejected as exc:
            code = str(exc)
            if code not in http.CASES or not http.applicable(code, rid):
                raise
            classification, _, retry, action, _, _ = http.CASES[code]
            details = {'fieldPaths': [], 'reason': code}
            error = {'stableCode': code, 'classification': classification, 'retryDirective': retry,
                     'message': code, 'details': details, 'detailsDigest': http.digest(details),
                     'currentSnapshot': None, 'nextAction': action}
            response = {'status': 'CANCELLED' if code == 'API_READ_CANCELLED' else 'FAILED',
                        'output': None, 'error': error, 'meta': None}
            row = None
        else:
            job = self.state['jobs'][row.parent]
            response = {'status': 'SUCCEEDED', 'output': value, 'error': None,
                        'meta': {**trace, 'stateVersion': job['stateVersion'],
                                 'eventSequence': job['eventSequence'],
                                 'activationEpoch': self.state['activationEpoch'],
                                 'idempotencyReplay': False}}
        response.update(routeId=rid, operationId=http.ROUTES[rid][0], terminal=True,
                        correlationId=trace['correlationId'], logicalOperationId=trace['logicalOperationId'])
        response['resultDigest'] = http.digest({k: response[k] for k in ('status', 'output', 'error')})
        if response['meta'] is not None:
            response['meta']['resultDigest'] = response['resultDigest']
        return response, row


def run_checks(raw, rs):
    checks = []

    def check(name, condition):
        checks.append({'case': name, 'passed': bool(condition)})

    def rejected(name, exception, reason, fn):
        try:
            fn()
        except exception as exc:
            check(name, reason is None or reason in str(exc))
        else:
            check(name, False)

    bundle = json.loads(rs[http.GEN]['raw'])
    payload = json.loads(rs[http.PAYLOAD]['raw'])
    contract = json.loads(rs[http.PATH]['raw'])
    validate = http.validators(bundle, contract, payload)
    native = types.ModuleType('read_design_native')
    sys.modules[native.__name__] = native
    exec(compile(rs[CONTROL]['raw'], 'SSOT:ssot_control.py', 'exec'), native.__dict__)
    defs = deepcopy(bundle['$defs'])
    for key, value in {'Counter': '0', 'PositiveCounter': '1', 'Timestamp': TIME,
                       'RelPath': 'fixture.json', 'JsonPointer': '', 'NonemptyJsonPointer': '/fixture'}.items():
        defs[key] = {'const': value}
    trace = {'logicalOperationId': OTHER, 'correlationId': LATER, 'commandId': DOCUMENT, 'serverTime': TIME}

    with tempfile.TemporaryDirectory(prefix='kcml-read-design-') as directory:
        source = Path(directory) / 'SSOT.md'
        source.write_bytes(raw)
        document = native.Document(source)
        for rid, (definition, path_key, kind, event_id_key, event_digest_key) in BINDINGS.items():
            start = len(checks)
            value = witness(defs[definition], defs)
            value['jobId'] = JOB
            if rid == 'route.0237':
                value['planId'] = DOCUMENT
                value['specificationDigest'] = value['scopeLock']['approvedSpecificationDigest']
            else:
                value['objective']['statement'] = 'Přesný immutable dokument'
                question = witness(defs['Question'], defs)
                question['blocking'] = True
                value['openQuestions'] = [question]
            repo = Repository(document, native.ContractFailure)
            repo.state['jobs'][JOB] = {'stateVersion': '7', 'eventSequence': '5'}
            row = repo.append_fixture(rid, JOB, DOCUMENT, '1', value, native.semantic_digest(value))
            paths = {'id': JOB, path_key: DOCUMENT}
            check('canonical/native-agreement', row.canonical_digest == http.digest(value))
            check('canonical/utf8-sorted-compact', row.canonical_bytes == json.dumps(
                value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf8'))
            check('canonical/key-order-independent', http.digest(dict(reversed(list(value.items())))) == row.canonical_digest)
            if rid == 'route.0232':
                check('proposal/blocking-questions-allowed', value['openQuestions'][0]['blocking'])

            event_payload = {event_id_key: DOCUMENT, event_digest_key: row.canonical_digest}
            commit = {'jobId': JOB, 'documentId': DOCUMENT, 'documentDigest': row.canonical_digest, 'eventSequence': '5'}
            if rid == 'route.0237':
                event_payload['specificationDigest'] = value['specificationDigest']
                commit['approvedSpecificationDigest'] = value['specificationDigest']
            event = {'type': kind, 'eventId': '5', 'objectId': JOB, 'emittedAt': TIME, 'payload': event_payload}
            event_schema = json.loads(rs[EVENTS]['raw'])
            validate(event_schema).validate(event)
            selector = native.validate_generation_document_event(document, event, value,
                persisted_event=deepcopy(event), commit_snapshot=commit, committed=True)
            check('event/exact-selector', selector == {'operationId': http.ROUTES[rid][0],
                'pathParameters': paths, 'persisted_job_id': JOB, 'persisted_document_id': DOCUMENT,
                'persisted_document_digest': row.canonical_digest})
            # Existing committed publication is fixture state, not created by read.
            repo.state['events'].append(deepcopy(event))
            repo.state['outbox'].append(deepcopy(event))
            repo.state['latest'][(rid, JOB)] = DOCUMENT
            frozen = deepcopy(repo.state)
            snapshot = repo.snapshot()
            response, stored = snapshot.response(rid, selector['pathParameters'], trace)

            def consume(result=response, pointer=stored, meta=response['meta'], selected=paths):
                return http.check_read_response(rid, result, validator=validate, native=native,
                    document=document, path_parameters=selected,
                    persisted_job_id=pointer.parent if pointer else None,
                    persisted_document_id=pointer.identity if pointer else None,
                    persisted_document_digest=pointer.canonical_digest if pointer else None,
                    snapshot_meta=meta)

            check('composition/event-repository-http-native-read', consume() == 200)
            check('snapshot/exact-document', response['output'] == value)
            check('snapshot/job-and-activation-metadata', all(response['meta'][k] == v for k, v in
                {'stateVersion': '7', 'eventSequence': '5', 'activationEpoch': '1', 'idempotencyReplay': False}.items()))
            check('read/no-business-writes-or-event', repo.state == frozen)
            check('read/snapshot-not-mutated', snapshot.state == frozen)

            for action in ('UPDATE', 'DELETE', 'REPARENT'):
                rejected('immutable/' + action, Rejected, 'IMMUTABLE_MUTATION',
                         lambda: repo.mutate_fixture(rid, JOB, DOCUMENT, action))
            rejected('immutable/no-overwrite', Rejected, 'IMMUTABLE_ID', lambda:
                repo.append_fixture(rid, JOB, DOCUMENT, '2', value, row.canonical_digest))
            rejected('immutable/wrong-parent', Rejected, 'PARENT_OWNERSHIP', lambda:
                repo.append_fixture(rid, OTHER, DOCUMENT, '1', value, row.canonical_digest))
            reparented = deepcopy(value)
            reparented['jobId'] = OTHER
            rejected('immutable/no-identity-reparent', Rejected, 'PARENT_OWNERSHIP', lambda:
                repo.append_fixture(rid, OTHER, DOCUMENT, '1', reparented, http.digest(reparented)))
            rejected('immutable/forged-digest', Rejected, 'CANONICAL_DIGEST', lambda:
                repo.append_fixture(rid, JOB, DOCUMENT, '2', value, 'sha256:' + 'f' * 64))
            later_value = deepcopy(value)
            if rid == 'route.0237':
                later_value['planId'] = LATER
            else:
                later_value['objective']['statement'] = 'A different revision'
                rejected('immutable/unique-parent-digest', Rejected, 'UNIQUE_PARENT_DIGEST', lambda:
                    repo.append_fixture(rid, JOB, LATER, '2', value, row.canonical_digest))
            overwritten = deepcopy(value)
            if rid == 'route.0237':
                overwritten['specificationDigest'] = 'sha256:' + 'f' * 64
                overwritten['scopeLock']['approvedSpecificationDigest'] = overwritten['specificationDigest']
            else:
                overwritten['objective']['statement'] = 'Attempted overwrite'
            rejected('immutable/no-changed-content-overwrite', Rejected, 'IMMUTABLE_ID', lambda:
                repo.append_fixture(rid, JOB, DOCUMENT, '2', overwritten, http.digest(overwritten)))
            rejected('immutable/unique-parent-revision', Rejected, 'UNIQUE_PARENT_REVISION', lambda:
                repo.append_fixture(rid, JOB, LATER, '1', later_value, http.digest(later_value)))
            check('immutable/rejections-preserve-state', repo.state == frozen)

            # Controlled interleaving: another writer commits after snapshot start.
            repo.append_fixture(rid, JOB, LATER, '2', later_value, http.digest(later_value))
            repo.state['latest'][(rid, JOB)] = LATER
            repo.state['jobs'][JOB] = {'stateVersion': '8', 'eventSequence': '9'}
            repo.state['activationEpoch'] = '2'
            live_after_writer = deepcopy(repo.state)
            old_response, _ = snapshot.response(rid, paths, trace)
            check('snapshot/repeatable-across-writer', old_response == response)
            fresh = repo.snapshot()
            invisible, missing = snapshot.response(rid, {'id': JOB, path_key: LATER}, trace)
            check('snapshot/new-row-not-visible', consume(invisible, missing, None,
                  {'id': JOB, path_key: LATER}) == 404)
            fresh_response, fresh_row = fresh.response(rid, paths, trace)
            check('retry/original-document-not-current-pointer', fresh_response['output'] == value)
            check('retry/fresh-consistent-metadata', fresh_response['meta']['eventSequence'] == '9'
                  and fresh_response['meta']['stateVersion'] == '8' and fresh_response['meta']['activationEpoch'] == '2')
            check('retry/composed-exact-selector', consume(fresh_response, fresh_row, fresh_response['meta']) == 200)
            for field in ('stateVersion', 'eventSequence', 'activationEpoch'):
                torn = deepcopy(response)
                torn['meta'][field] = fresh_response['meta'][field]
                rejected('snapshot/reject-torn-' + field, ValueError, 'READ_SNAPSHOT_META_MISMATCH', lambda:
                    consume(torn))
            torn = deepcopy(response)
            torn['meta']['idempotencyReplay'] = True
            rejected('read/no-idempotency-replay', ValueError, 'READ_HAS_NO_IDEMPOTENCY_REPLAY', lambda:
                consume(torn, stored, torn['meta']))
            later_response, later_row = fresh.response(rid, {'id': JOB, path_key: LATER}, trace)
            check('snapshot/new-row-visible-in-fresh-snapshot', consume(later_response, later_row,
                  later_response['meta'], {'id': JOB, path_key: LATER}) == 200)
            rejected('retry/reject-latest-document-substitution', native.ContractFailure, None, lambda:
                consume(later_response, later_row, later_response['meta']))
            rejected('read/reject-foreign-parent-pointer', native.ContractFailure, None, lambda:
                consume(pointer=replace(stored, parent=OTHER)))
            rejected('read/reject-wrong-canonical-pointer', native.ContractFailure, None, lambda:
                consume(pointer=replace(stored, canonical_digest='sha256:' + 'f' * 64)))
            wrong_digest = deepcopy(response)
            wrong_digest['resultDigest'] = row.canonical_digest
            rejected('read/document-digest-is-not-result-digest', ValueError, 'RESULT_DIGEST_MISMATCH', lambda:
                consume(wrong_digest))

            for label, selected in [('missing', {'id': JOB, path_key: OTHER}),
                                     ('wrong-parent', {'id': OTHER, path_key: DOCUMENT})]:
                result, missing = fresh.response(rid, selected, trace)
                check('lookup/' + label + '-exact-404', consume(result, missing, None, selected) == 404
                      and result['output'] is None)
            rejected('lookup/no-latest-alias', native.ContractFailure, None, lambda:
                fresh.lookup(rid, {'id': JOB, path_key: 'latest'}))
            rejected('lookup/no-omitted-id-fallback', Rejected, 'API_REQUEST_INVALID', lambda:
                fresh.lookup(rid, {'id': JOB}))
            rejected('lookup/no-extra-selector', Rejected, 'API_REQUEST_INVALID', lambda:
                fresh.lookup(rid, {**paths, 'current': True}))

            # Inject corrupt storage into isolated snapshots to exercise fail-closed
            # reads. These bypass fixture insertion intentionally.
            invalid_native = deepcopy(value)
            del invalid_native['schemaVersion']
            for label, damaged in [
                ('digest', replace(row, canonical_digest='sha256:' + 'f' * 64)),
                ('content', replace(row, canonical_bytes=http.canonical(later_value))),
                ('parent', replace(row, parent=OTHER)),
                ('identity', replace(row, identity=OTHER)),
                ('noncanonical', replace(row, canonical_bytes=json.dumps(value).encode('utf8'))),
                ('invalid-json', replace(row, canonical_bytes=b'{broken')),
                ('invalid-native-schema', replace(row, canonical_bytes=http.canonical(invalid_native),
                                                 canonical_digest=http.digest(invalid_native))),
            ]:
                corrupt = repo.snapshot()
                corrupt.state['rows'][(rid, JOB, DOCUMENT)] = damaged
                result, missing = corrupt.response(rid, paths, trace)
                check('corrupt/' + label + '-no-document', consume(result, missing, None) == 500
                      and result['output'] is None and result['error']['retryDirective'] == 'DO_NOT_RETRY')
            for fault, status in [('API_READ_TIMEOUT', 504), ('API_READ_CANCELLED', 409),
                                  ('API_STORAGE_ROLLBACK', 503)]:
                result, missing = fresh.response(rid, paths, trace, fault=fault)
                check('failure/' + fault, consume(result, missing, None) == status and result['output'] is None)
                check('failure/read-only-context-' + fault, http.check_error_context(rid, result,
                      validator=validate, effect='READ_ONLY', dispatched=True, current_snapshot=None) == status)
                rejected('failure/cannot-claim-mutation-' + fault, ValueError, 'READ_CANNOT_MUTATE', lambda:
                    http.check_error_context(rid, result, validator=validate,
                        effect='CONFIRMED_ROLLBACK', dispatched=True, current_snapshot=None))
                check('failure/no-mutation-' + fault, repo.state == live_after_writer)
                if fault != 'API_READ_CANCELLED':
                    retry, retry_row = repo.snapshot().response(rid, selector['pathParameters'], trace)
                    check('recovery/' + fault + '-original-selector',
                          consume(retry, retry_row, retry['meta']) == 200 and retry['output'] == value)
            # A lost HTTP response has no outcome object. Re-reading the same ID
            # leaves the committed publication intact, without a new command/key.
            retry, retry_row = repo.snapshot().response(rid, paths, {**trace, 'correlationId': JOB})
            check('disconnect/refetch-original-selector', consume(retry, retry_row, retry['meta']) == 200
                  and retry['output'] == value and not retry['meta']['idempotencyReplay'])
            check('recovery/published-event-and-outbox-preserved', repo.state == live_after_writer)

            # The consumer cursor is advanced only by stream delivery predicates.
            # A read returns no cursor. A newer meta.eventSequence is diagnostic.
            cursor = '4'
            consume(fresh_response, fresh_row, fresh_response['meta'])
            action = native.generation_event_delivery_action(document, event,
                stream_job_id=JOB, last_sequence=cursor)
            check('stream/read-meta-does-not-skip-event', action == 'APPLY'
                  and fresh_response['meta']['eventSequence'] == '9' and cursor == '4')
            if action == 'APPLY':
                cursor = event['eventId']
            check('stream/only-event-advances-cursor', cursor == '5')
            check('stream/duplicate-not-reapplied', native.generation_event_delivery_action(document,
                event, stream_job_id=JOB, last_sequence=cursor,
                previous_event_digest=native.semantic_digest(event)) == 'DUPLICATE')
            check('stream/gap-still-needs-replay', native.generation_event_delivery_action(document,
                {**event, 'eventId': '7'}, stream_job_id=JOB, last_sequence=cursor) == 'REPLAY_REQUIRED')
            event_mask = next(r['eventSchema'] for r in payload['records'] if r['routeId'] == rid)
            check('read/no-public-event-boundary', all(not validate(event_mask).is_valid(v)
                for v in [event, response, {}, None]))
            check('read/all-effects-unchanged', repo.state == live_after_writer)
            # Returned documents and metadata cannot alias stored state.
            detached, _ = fresh.response(rid, paths, trace)
            detached['output']['jobId'] = OTHER
            detached['meta']['eventSequence'] = '999'
            check('read/output-cannot-overwrite-repository', fresh.response(rid, paths, trace)[0] == fresh_response
                  and repo.state == live_after_writer)
            for result in checks[start:]:
                result['case'] = rid + '/' + result['case']
    return checks


def main():
    raw = SSOT.read_bytes()
    text = raw.decode('utf8')
    rs = resource_index(resources(text))
    section_hashes = {}
    for number in SECTIONS:
        match = re.search(r'^(#{2,5}) ' + re.escape(number) + r'\s[^\n]*', text, re.M)
        if match is None:
            raise ValueError('Missing authoritative SSOT section ' + number)
        end = re.search(r'^#{1,' + str(len(match[1])) + r'} ', text[match.end():], re.M)
        section = text[match.start():match.end() + end.start() if end else len(text)]
        section_hashes[number] = hashlib.sha256(section.encode('utf8')).hexdigest()
    checks = run_checks(raw, rs)
    failed = sum(not c['passed'] for c in checks)
    report = {
        'sourceSha256': hashlib.sha256(raw).hexdigest(),
        'scriptSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'resourceVersions': {p: rs[p]['sha256'] for p in (http.GEN, http.PAYLOAD, http.PATH, CONTROL, EVENTS)},
        'helperVersions': {'generation_http_contract.py': hashlib.sha256(Path(http.__file__).read_bytes()).hexdigest()},
        'authoritySections': section_hashes, 'scope': __doc__, 'evidenceClass': 'DESIGN',
        'evidenceKind': 'DESIGN_MODEL', 'evidenceGate': 'SSOT_CONTRACT_READY',
        'gate': 'SSOT_CONTRACT_READY', 'passed': failed == 0,
        'checked': len(checks), 'failed': failed, 'checks': checks,
        'routeDesignEvidence': {rid: {'passed': all(c['passed'] for c in checks if c['case'].startswith(rid + '/')),
            'scope': 'Exact immutable repository lookup, snapshot, event/HTTP/native read composition and recovery'}
            for rid in BINDINGS},
        'wholeRoutesClosed': [],
        'remainingDesign': ['Route gate must join same-source HTTP evidence for OWNER authentication, exact wire normalization and all applicable error/retry contexts',
                            'Route gate must join same-source document-event and stream boundary evidence with these repository/read checks, verifying exact route coverage and resource/helper hashes'],
        'outOfScopeDesign': ['Plan DAG conformance and IMPLEMENTING guards belong to the producer, not these read routes'],
        'productionObligations': ['Execute immutable constraints/triggers and parent foreign keys in PostgreSQL',
            'Verify CONSISTENT_READ isolation, transaction limits/session reset, concurrent reads and writes',
            'Verify authentication, separate read audit, repository corruption handling and actual SSE replay/outbox delivery'],
    }
    out = ROOT / os.environ.get('KCML_AUDIT_OUTPUT', 'audit/generated/continuation-7006785/read-design')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'read-design.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps({k: report[k] for k in ('sourceSha256', 'checked', 'failed', 'evidenceClass', 'evidenceGate')}))
    return int(bool(failed))


if __name__ == '__main__':
    raise SystemExit(main())
