"""Synthetic SSOT 12.44.2 contract checks; no production acceptance claim.

Trusted commit/repository snapshots are fixtures, not evidence of real database
atomicity, provenance, outbox delivery, transport, or plan conformance.
"""
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import types
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from ssot_sources import ROOT, SSOT, resource_index, resources
from verify_phase2_handoffs import witness

BASELINE = '7006785'
SCHEMA = 'contracts/generation/document-events.schema.json'
GEN = 'contracts/generation/generation-contracts.schema.json'
CONTROL = 'scripts/ssot/ssot_control.py'
EVENTS = {
    'generation.spec.proposed': ('SpecificationProposed', 'GenerationSpecification',
                                 'specificationRevisionId', 'specificationDigest',
                                 'revisionId', 'generation.spec.revision.read'),
    'generation.plan.created': ('PlanCreated', 'GenerationPlan', 'planId',
                                'planDigest', 'planId', 'generation.plan.read'),
}
OTHER_ID = '00000000-0000-4000-8000-000000000099'
REVISION = '00000000-0000-4000-8000-000000000002'
OTHER_DIGEST = 'sha256:' + 'f' * 64
TIMESTAMP = '2026-09-25T00:00:00.000Z'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    current_raw = SSOT.read_bytes()
    raw = (subprocess.check_output(
        ['git', 'show', BASELINE + ':00_SSOT/KajovoCMLNG_SSOT.md'], cwd=ROOT)
        if args.baseline else current_raw)
    rs = resource_index(resources(raw.decode('utf8')))
    checks = []

    def check(name, actual, expected=True):
        checks.append({'case': name, 'actual': actual, 'expected': expected,
                       'passed': actual == expected})

    def case(name, fn, expected=True):
        # Unexpected exceptions must fail even a rejection test.
        try:
            check(name, fn(), expected)
        except Exception as exc:
            checks.append({'case': name, 'expected': expected, 'passed': False,
                           'error': type(exc).__name__ + ': ' + str(exc)})

    for path in (SCHEMA, GEN, CONTROL):
        check('resource-present/' + path, path in rs)

    def exercise():
        bundle = json.loads(rs[GEN]['raw'])
        defs = copy.deepcopy(bundle['$defs'])
        for key, value in {'Counter': '0', 'PositiveCounter': '1',
                           'Timestamp': TIMESTAMP, 'RelPath': 'fixture.json',
                           'JsonPointer': '', 'NonemptyJsonPointer': '/fixture'}.items():
            defs[key] = {'const': value}
        spec = witness(defs['GenerationSpecification'], defs)
        question = witness(defs['Question'], defs)
        question['blocking'] = True
        spec['openQuestions'] = [question]
        plan = witness(defs['GenerationPlan'], defs)
        plan['specificationDigest'] = plan['scopeLock']['approvedSpecificationDigest']
        documents = {'GenerationSpecification': spec, 'GenerationPlan': plan}
        registry = Registry().with_resource(bundle['$id'], Resource.from_contents(bundle))
        event_schema = json.loads(rs[SCHEMA]['raw']) if SCHEMA in rs else None
        if event_schema is not None:
            Draft202012Validator.check_schema(event_schema)
            registry = registry.with_resource(event_schema['$id'], Resource.from_contents(event_schema))
        validator = lambda schema: Draft202012Validator(
            schema, registry=registry, format_checker=FormatChecker())
        module = types.ModuleType('document_events_embedded_control')
        sys.modules[module.__name__] = module
        exec(compile(rs[CONTROL]['raw'], 'SSOT:ssot_control.py', 'exec'), module.__dict__)
        publisher = getattr(module, 'validate_generation_document_event', None)
        reader = getattr(module, 'validate_generation_read_handoff', None)
        delivery = getattr(module, 'generation_event_delivery_action', None)
        check('native/document-event-helper-present', callable(publisher))
        check('native/read-helper-present', callable(reader))
        check('native/delivery-helper-present', callable(delivery))

        def admitted(fn):
            try:
                fn()
                return True
            except module.ContractFailure:
                return False

        with tempfile.TemporaryDirectory(prefix='kcml-document-events-') as directory:
            source = Path(directory) / 'SSOT.md'
            source.write_bytes(raw)
            doc = module.Document(source)
            for kind, binding in EVENTS.items():
                name, definition, id_key, digest_key, path_key, operation = binding
                document = documents[definition]
                case(kind + '/native-document', lambda: admitted(lambda: doc.validate(definition, document)))
                check(kind + '/fixture-schema', validator(
                    {'$ref': bundle['$id'] + '#/$defs/' + definition}).is_valid(document))
                document_id = REVISION if definition == 'GenerationSpecification' else document['planId']
                digest = module.semantic_digest(document)
                payload = {id_key: document_id, digest_key: digest}
                if definition == 'GenerationPlan':
                    payload['specificationDigest'] = document['specificationDigest']
                event = {'eventId': '1', 'type': kind, 'objectId': document['jobId'],
                         'emittedAt': TIMESTAMP, 'payload': payload}
                snapshot = {'jobId': document['jobId'], 'eventSequence': '1',
                            'documentId': document_id, 'documentDigest': digest}
                if definition == 'GenerationPlan':
                    snapshot['approvedSpecificationDigest'] = document['specificationDigest']

                def publish(e=event, d=document, persisted=event, snap=snapshot, committed=True):
                    return publisher(doc, e, d, persisted_event=persisted,
                                     commit_snapshot=snap, committed=committed)

                def reject(label, **kwargs):
                    case(kind + '/publisher/' + label,
                         lambda: admitted(lambda: publish(**kwargs)), False)

                # Apply each mask to the standalone union, its named branch,
                # and the native publisher, always retaining a trusted snapshot.
                def mask(label, value, expected=False):
                    if event_schema is not None:
                        case(kind + '/schema/' + label,
                             lambda: validator(event_schema).is_valid(value), expected)
                        case(kind + '/schema-definition/' + label,
                             lambda: validator({'$ref': event_schema['$id'] + '#/$defs/' + name}).is_valid(value), expected)
                    if callable(publisher):
                        case(kind + '/native-mask/' + label,
                             lambda: admitted(lambda: publish(e=value, persisted=value)), expected)

                mask('exact', event, True)
                for location, fields in [('envelope', event), ('payload', payload)]:
                    for key in fields:
                        bad = copy.deepcopy(event)
                        target = bad if location == 'envelope' else bad['payload']
                        del target[key]
                        mask(location + '/missing/' + key, bad)
                        for index, value in enumerate([None, False, 7, [], {}, 'invalid']):
                            bad = copy.deepcopy(event)
                            target = bad if location == 'envelope' else bad['payload']
                            target[key] = value
                            mask(location + '/invalid/' + key + '/' + str(index), bad)
                    bad = copy.deepcopy(event)
                    target = bad if location == 'envelope' else bad['payload']
                    target['undeclared'] = True
                    mask(location + '/extra', bad)
                for index, value in enumerate([None, False, 7, [], {}, 'generation.spec.proposed']):
                    mask('generic/' + str(index), value)
                for value in ['ACCEPTED', 'PROGRESS', 'WAITING_FOR_INPUT', 'RECONCILING',
                              'TERMINAL', 'generation.spec.approved', 'generation.unknown']:
                    mask('wrong-event-type/' + value, {**event, 'type': value})
                for value in ['01', '-1', '9223372036854775808']:
                    mask('invalid-sequence/' + value, {**event, 'eventId': value})
                mask('invalid-timestamp', {**event, 'emittedAt': '2026-99-25T00:00:00.000Z'})
                generic = {'schemaId': 'urn:kcml:generic:event-payload', 'values': []}
                mask('generic-payload', {**event, 'payload': generic})
                proposal = {'schemaVersion': '1.0', 'role': 'REQUIREMENTS_ANALYST',
                            'proposal': document, 'questions': [], 'blocker': None}
                mask('model-proposal-as-receipt', proposal)
                mask('model-proposal-as-payload', {**event, 'payload': proposal})
                if not callable(publisher):
                    continue
                case(kind + '/publisher/exact-committed', lambda: admitted(publish))
                for value in [False, None, 1]:
                    reject('precommit/' + repr(value), committed=value)
                reject('missing-snapshot', snap={})
                for key, value in [('jobId', OTHER_ID), ('eventSequence', '2'),
                                   ('documentId', OTHER_ID), ('documentDigest', OTHER_DIGEST)]:
                    reject('wrong-snapshot/' + key, snap={**snapshot, key: value})
                reject('wrong-event-job', e={**event, 'objectId': OTHER_ID},
                       persisted={**event, 'objectId': OTHER_ID})
                for key, value in [(id_key, OTHER_ID), (digest_key, OTHER_DIGEST)]:
                    bad = {**event, 'payload': {**payload, key: value}}
                    reject('wrong-event/' + key, e=bad, persisted=bad)
                reject('wrong-event-sequence', e={**event, 'eventId': '2'},
                       persisted={**event, 'eventId': '2'})
                reject('rewritten-persisted-envelope', e={**event, 'emittedAt': '2026-09-25T00:00:01.000Z'})
                reject('model-document-as-receipt', persisted=proposal)
                reject('model-proposal-as-native-document', d=proposal)
                modified = copy.deepcopy(document)
                if definition == 'GenerationSpecification':
                    modified['objective']['statement'] = 'Changed immutable specification'
                    check(kind + '/blocking-question-allowed', spec['openQuestions'][0]['blocking'])
                else:
                    modified['planId'] = OTHER_ID
                    reject('wrong-approved-snapshot', snap={**snapshot, 'approvedSpecificationDigest': OTHER_DIGEST})
                    bad = {**event, 'payload': {**payload, 'specificationDigest': OTHER_DIGEST}}
                    reject('wrong-approved-event', e=bad, persisted=bad)
                    wrong = copy.deepcopy(document)
                    wrong['scopeLock']['approvedSpecificationDigest'] = OTHER_DIGEST
                    wrong_digest = module.semantic_digest(wrong)
                    bad = {**event, 'payload': {**payload, digest_key: wrong_digest}}
                    reject('wrong-approved-scope-lock-with-matching-document-digest', d=wrong,
                           e=bad, persisted=bad, snap={**snapshot, 'documentDigest': wrong_digest})
                    bad = {**event, 'payload': {**payload, id_key: OTHER_ID}}
                    reject('plan-id-not-native-id', e=bad, persisted=bad,
                           snap={**snapshot, 'documentId': OTHER_ID})
                case(kind + '/modified-document-still-native',
                     lambda: admitted(lambda: doc.validate(definition, modified)))
                reject('changed-immutable-document', d=modified)

                expected_selector = {'operationId': operation,
                                     'pathParameters': {'id': document['jobId'], path_key: document_id},
                                     'persisted_job_id': document['jobId'],
                                     'persisted_document_id': document_id,
                                     'persisted_document_digest': digest}
                selector = publish()
                check(kind + '/exact-read-selector', selector, expected_selector)
                frozen = copy.deepcopy((event, document, snapshot, selector))
                if callable(reader):
                    def read(status='SUCCEEDED', output=document, selected=selector):
                        return reader(doc, selected['operationId'], selected['pathParameters'],
                                      {'status': status, 'output': output},
                                      **{k: selected[k] for k in (
                                          'persisted_job_id', 'persisted_document_id', 'persisted_document_digest')})

                    case(kind + '/read/exact-native-document', read)
                    for status in ['FAILED', 'CANCELLED', 'ACCEPTED', 'RUNNING']:
                        case(kind + '/read/no-document/' + status,
                             lambda: read(status, None), False)
                    for status in ['FAILED', 'CANCELLED']:
                        case(kind + '/read/error-cannot-publish/' + status,
                             lambda: admitted(lambda: read(status, document)), False)
                    for label, output in [('missing', None), ('generic', generic),
                                          ('proposal', proposal), ('changed', modified)]:
                        case(kind + '/read/reject/' + label,
                             lambda: admitted(lambda: read(output=output)), False)
                    for key, value in [('persisted_job_id', OTHER_ID),
                                       ('persisted_document_id', OTHER_ID),
                                       ('persisted_document_digest', OTHER_DIGEST)]:
                        case(kind + '/read/wrong-pointer/' + key,
                             lambda: admitted(lambda: read(selected={**selector, key: value})), False)
                    for key, value in [('id', OTHER_ID), (path_key, OTHER_ID), (path_key, 'latest')]:
                        bad = {**selector, 'pathParameters': {**selector['pathParameters'], key: value}}
                        case(kind + '/read/wrong-path/' + key + '/' + value,
                             lambda: admitted(lambda: read(selected=bad)), False)
                    case(kind + '/recovery/refetch-same-immutable-document', read)
                case(kind + '/recovery/exact-outbox-redelivery', publish, expected_selector)
                if callable(delivery):
                    def deliver(e=event, **kw):
                        return delivery(doc, e, stream_job_id=event['objectId'], **kw)
                    case(kind + '/recovery/apply', lambda: deliver(last_sequence='0'), 'APPLY')
                    case(kind + '/recovery/deduplicate', lambda: deliver(
                        last_sequence='1', previous_event_digest=module.semantic_digest(event)), 'DUPLICATE')
                    case(kind + '/recovery/missing-history', lambda: deliver(last_sequence='1'), 'REPLAY_REQUIRED')
                    case(kind + '/recovery/gap', lambda: deliver(
                        e={**event, 'eventId': '3'}, last_sequence='1'), 'REPLAY_REQUIRED')
                    case(kind + '/recovery/changed-duplicate', lambda: admitted(lambda: deliver(
                        last_sequence='1', previous_event_digest=OTHER_DIGEST)), False)
                check(kind + '/recovery/inputs-remain-immutable', (event, document, snapshot, selector) == frozen)
        return True

    if GEN in rs and CONTROL in rs:
        case('exercise-completed', exercise)
    failed = sum(not row['passed'] for row in checks)
    report = {
        'sourceSha256': hashlib.sha256(raw).hexdigest(),
        'currentSourceSha256': hashlib.sha256(current_raw).hexdigest(),
        'scriptSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'baseline': args.baseline, 'baselineCommit': BASELINE,
        'resourceVersions': {p: rs[p]['sha256'] if p in rs else None for p in (SCHEMA, GEN, CONTROL)},
        'scope': __doc__, 'evidenceGate': 'SSOT_CONTRACT_READY',
        'gate': 'SSOT_CONTRACT_READY', 'evidenceKind': 'DESIGN_MODEL',
        'passed': failed == 0, 'checked': len(checks), 'failed': failed, 'checks': checks,
        'wholeRoutesClosed': [],
        'remainingDesign': ['Whole-route transport/repository predicate composition',
                            'Plan producer DAG conformance and IMPLEMENTING guard are outside this event-mask test'],
        'productionObligations': ['Production commit atomicity and trusted snapshot provenance',
                                  'Real outbox/inbox, SSE replay and read transport integration'],
    }
    out = ROOT / os.environ.get('KCML_AUDIT_OUTPUT', 'audit/generated/continuation-7006785/document-events')
    out.mkdir(parents=True, exist_ok=True)
    destination = out / ('document-events-baseline.json' if args.baseline else 'document-events-current.json')
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps({k: report[k] for k in ('sourceSha256', 'checked', 'failed', 'baseline', 'evidenceGate')}))
    return int(bool(failed))


if __name__ == '__main__':
    raise SystemExit(main())
