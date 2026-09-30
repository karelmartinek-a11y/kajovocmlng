"""Synthetic producer-allocation/event/read tests; not deployed DB evidence.

Reports JSON to stdout only. Unexpected exceptions fail rejection tests too.
"""
import copy
import hashlib
import json
from pathlib import Path

from plan_create_investigation import (
    current_native, investigation, allocation_schema, validate_plan_allocation,
    plan_created_handoff, plan_created_read_handoff,
)
from verify_phase2_handoffs import witness
from jsonschema import Draft202012Validator, FormatChecker

OTHER_ID = '00000000-0000-4000-8000-000000000099'
OTHER_DIGEST = 'sha256:' + 'f' * 64
NOW = '2026-09-25T00:00:00.000Z'


def main():
    checks = []
    with current_native() as (native, doc, raw, rs):
        def check(name, fn, expected=True, rejection=False, expected_code=None):
            try:
                value = fn()
                passed = not rejection and value == expected
                error = None
            except native.ContractFailure as exc:
                passed = rejection and (expected_code is None or exc.code == expected_code)
                error = str(exc)
            except Exception as exc:
                passed = False
                error = type(exc).__name__ + ': ' + str(exc)
            checks.append({'case': name, 'passed': passed, 'error': error,
                           'expectedErrorCode': expected_code})

        defs = copy.deepcopy(doc.schema['$defs'])
        for key, value in {'Counter': '0', 'PositiveCounter': '1', 'Timestamp': NOW,
                           'RelPath': 'fixture.json', 'JsonPointer': '', 'NonemptyJsonPointer': '/fixture'}.items():
            defs[key] = {'const': value}
        plan = witness(defs['GenerationPlan'], defs)
        plan['specificationDigest'] = plan['scopeLock']['approvedSpecificationDigest']
        allocation = {k: copy.deepcopy(plan[k]) for k in ('jobId', 'planId', 'scopeLock')}
        digest = native.semantic_digest(plan)
        event = {'eventId': '1', 'type': 'generation.plan.created', 'objectId': plan['jobId'],
                 'emittedAt': NOW, 'payload': {'planId': plan['planId'], 'planDigest': digest,
                                             'specificationDigest': plan['specificationDigest']}}
        snapshot = {'jobId': plan['jobId'], 'documentId': plan['planId'], 'documentDigest': digest,
                    'eventSequence': '1', 'approvedSpecificationDigest': plan['specificationDigest']}
        repository = {k: snapshot[k] for k in ('jobId', 'documentId', 'documentDigest')}
        arguments = dict(allocation=allocation, persisted_event=event, commit_snapshot=snapshot, committed=True)

        def publish(document=None, **overrides):
            return plan_created_handoff(doc, native, plan if document is None else document,
                                        **{**arguments, **overrides})

        def read(response=None, repository_snapshot=repository, **overrides):
            return plan_created_read_handoff(doc, native, plan, **{**arguments, **overrides},
                response={'status': 'SUCCEEDED', 'output': plan} if response is None else response,
                repository_snapshot=repository_snapshot)

        mask = allocation_schema()
        Draft202012Validator.check_schema(mask)
        embedded=json.loads(rs['contracts/generation/document-events.schema.json']['raw'])['$defs']['PlanAllocation']
        check('allocation-mask/exact-authoritative-specialization',
              lambda: {k:v for k,v in mask.items() if k!='$schema'}==embedded)
        validator = Draft202012Validator(mask, registry=doc.registry, format_checker=FormatChecker())
        check('allocation-mask/native', lambda: validator.is_valid(allocation))
        check('native-plan', lambda: doc.validate('GenerationPlan', plan) is None)
        check('producer-digest', lambda: validate_plan_allocation(doc, native, plan, allocation=allocation), digest)
        expected = {'event': event, 'readSelector': {
            'operationId': 'generation.plan.read', 'pathParameters': {'id': plan['jobId'], 'planId': plan['planId']},
            'persisted_job_id': plan['jobId'], 'persisted_document_id': plan['planId'],
            'persisted_document_digest': digest}}
        check('exact-producer-event-selector', publish, expected)
        check('independent-immutable-repository-read', read)

        for field in allocation:
            for variant in ('missing', 'null', 'wrong-type'):
                bad = copy.deepcopy(allocation)
                if variant == 'missing':
                    del bad[field]
                else:
                    bad[field] = None if variant == 'null' else 17
                check('allocation-mask/' + field + '/' + variant, lambda b=bad: validator.is_valid(b), False)
                check('allocation-adapter/' + field + '/' + variant,
                      lambda b=bad: publish(allocation=b), rejection=True)
        extra = {**allocation, 'committed': True}
        check('allocation-mask/extra', lambda: validator.is_valid(extra), False)
        check('allocation-adapter/extra', lambda: publish(allocation=extra), rejection=True)

        for field in ('planId', 'jobId'):
            bad = copy.deepcopy(plan)
            bad[field] = OTHER_ID
            check('still-native/' + field, lambda b=bad: doc.validate('GenerationPlan', b) is None)
            check('model-chosen/' + field, lambda b=bad: publish(b), rejection=True,
                  expected_code='GENERATION_PLAN_INVALID')
            # A self-consistent forged event and snapshot still cannot override allocation.
            forged_event = copy.deepcopy(event)
            forged_snapshot = copy.deepcopy(snapshot)
            if field == 'planId':
                forged_event['payload']['planId'] = OTHER_ID
                forged_snapshot['documentId'] = OTHER_ID
            else:
                forged_event['objectId'] = OTHER_ID
                forged_snapshot['jobId'] = OTHER_ID
            forged_event['payload']['planDigest'] = native.semantic_digest(bad)
            forged_snapshot['documentDigest'] = native.semantic_digest(bad)
            check('self-consistent-forgery/' + field,
                  lambda b=bad, e=forged_event, s=forged_snapshot: publish(b, persisted_event=e, commit_snapshot=s),
                  rejection=True)

        for field, value in [('approvedSpecificationId', OTHER_ID), ('approvedSpecificationDigest', OTHER_DIGEST),
                             ('ownerDecisionSetDigest', OTHER_DIGEST), ('requirementSetDigest', OTHER_DIGEST),
                             ('approvedTargetKeys', ['another-target']), ('approvedRequirementIds', ['another-requirement'])]:
            bad = copy.deepcopy(plan)
            bad['scopeLock'][field] = value
            check('scope/' + field, lambda b=bad: publish(b), rejection=True,
                  expected_code='GENERATION_PLAN_INVALID')
        bad = copy.deepcopy(plan)
        bad['specificationDigest'] = OTHER_DIGEST
        check('wrong-specification-digest', lambda: publish(bad), rejection=True,
              expected_code='SPECIFICATION_DIGEST_STALE')
        bad_plan = copy.deepcopy(plan)
        bad_plan['nodes'][0]['purpose'] = 'Changed schema-valid content'
        check('changed-content/native', lambda: doc.validate('GenerationPlan', bad_plan) is None)
        check('changed-content/stale-committed-digest', lambda: publish(bad_plan), rejection=True,
              expected_code='ARTIFACT_VALIDATION_FAILED')
        proposal = {'schemaVersion': '1.0', 'role': 'IMPLEMENTATION_PLANNER', 'proposal': plan,
                    'questions': [], 'blocker': None}
        check('model-wrapper-is-not-plan', lambda: publish(proposal), rejection=True)
        check('model-wrapper-is-not-event', lambda: publish(persisted_event=proposal), rejection=True)

        for committed in (False, None, 0, 1, 'true'):
            outputs = []
            def premature(value=committed):
                outputs.append(publish(committed=value))
            check('no-publication-without-exact-commit/' + repr(committed), premature, rejection=True,
                  expected_code='ARTIFACT_VALIDATION_FAILED')
            check('no-returned-event/' + repr(committed), lambda: not outputs)
        for field, value in [('jobId', OTHER_ID), ('documentId', OTHER_ID), ('documentDigest', OTHER_DIGEST),
                             ('eventSequence', '2'), ('approvedSpecificationDigest', OTHER_DIGEST)]:
            check('commit-snapshot/' + field,
                  lambda f=field, v=value: publish(commit_snapshot={**snapshot, f: v}), rejection=True)
        check('wrong-event-kind', lambda: publish(persisted_event={**event, 'type': 'generation.spec.proposed'}), rejection=True)
        check('missing-event', lambda: publish(persisted_event=None), rejection=True)
        for field, value in [('planId', OTHER_ID), ('planDigest', OTHER_DIGEST), ('specificationDigest', OTHER_DIGEST)]:
            check('event-payload/' + field,
                  lambda f=field, v=value: publish(persisted_event={**event, 'payload': {**event['payload'], f: v}}), rejection=True)

        for status in ('FAILED', 'CANCELLED', 'ACCEPTED', 'RUNNING'):
            check('read/no-document/' + status, lambda s=status: read({'status': s, 'output': None}, None), False)
            check('read/no-success-injection/' + status, lambda s=status: read({'status': s, 'output': plan}), rejection=True)
        for field, value in [('jobId', OTHER_ID), ('documentId', OTHER_ID), ('documentDigest', OTHER_DIGEST)]:
            check('repository/' + field,
                  lambda f=field, v=value: read(repository_snapshot={**repository, f: v}), rejection=True)
        check('repository/absent-on-success', lambda: read(repository_snapshot=None), rejection=True)
        check('read/changed-native-document', lambda: read({'status': 'SUCCEEDED', 'output': bad_plan}), rejection=True)
        check('read/recover-exact-document', read)

        frozen = copy.deepcopy((plan, arguments, repository))
        first = publish()
        current_job = {'state': 'CANCELLED', 'eventSequence': '9', 'specificationDigest': OTHER_DIGEST}
        check('cancellation-after-commit/replay-frozen', publish, first)
        check('cancellation-after-commit/immutable-read', read)
        check('cancellation-after-commit/current-snapshot-substitution-rejected',
              lambda: publish(commit_snapshot={**snapshot, 'eventSequence': current_job['eventSequence'],
                                                'approvedSpecificationDigest': current_job['specificationDigest']}), rejection=True)
        check('cancel-before-commit/no-event', lambda: publish(committed=False, persisted_event=None), rejection=True)
        # Returned values must not alias trusted snapshots or alter the next replay.
        first['event']['payload']['planId'] = OTHER_ID
        first['readSelector']['pathParameters']['planId'] = OTHER_ID
        check('replay/returned-mutation-isolated', publish, expected)
        check('inputs-remain-frozen', lambda: (plan, arguments, repository) == frozen)
        check('consumer/exact-delivery', lambda: native.generation_event_delivery_action(
            doc, event, stream_job_id=plan['jobId'], last_sequence='0'), 'APPLY')
        check('consumer/replay-deduplicates', lambda: native.generation_event_delivery_action(
            doc, event, stream_job_id=plan['jobId'], last_sequence='1',
            previous_event_digest=native.semantic_digest(event)), 'DUPLICATE')

        report = investigation(doc, raw, rs)
        report.update(checked=len(checks), failed=sum(not c['passed'] for c in checks), checks=checks,
                      verification='SYNTHETIC_HANDOFF_ONLY',
                      scriptSha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (
                          Path(__file__), Path(__file__).with_name('plan_create_investigation.py'))})
        print(json.dumps(report, indent=2))
    return int(report['failed'] != 0)


if __name__ == '__main__':
    raise SystemExit(main())
