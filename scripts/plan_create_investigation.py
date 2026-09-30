"""Executable, partial plan-create derivation; never closes the operation pair.

Only the trusted allocation -> committed event -> immutable read boundary is
implemented. Allocation, commit and repository arguments MUST be collected by
the server, not copied from a model or request. This module does not write DB,
outbox, SSOT, schemas or audit files. CLI reports the current source to stdout.
"""
import copy
import hashlib
import json
import sys
import tempfile
import types
from contextlib import contextmanager
from pathlib import Path

from ssot_sources import SSOT, resource_index, resources

GEN = 'contracts/generation/generation-contracts.schema.json'
CONTROL = 'scripts/ssot/ssot_control.py'
EVENT_SCHEMA = 'contracts/generation/document-events.schema.json'
OPERATION = 'generation.plan.create'


@contextmanager
def current_native():
    """Use one immutable byte snapshot even while another worker edits SSOT."""
    raw = SSOT.read_bytes()
    rs = resource_index(resources(raw.decode('utf8').replace('\r\n', '\n')))
    module = types.ModuleType('_plan_create_native_snapshot')
    previous = sys.modules.get(module.__name__)
    sys.modules[module.__name__] = module
    try:
        exec(compile(rs[CONTROL]['raw'], 'SSOT:' + CONTROL, 'exec'), module.__dict__)
        for name in ('validate_generation_document_event', 'validate_generation_read_handoff'):
            if not callable(getattr(module, name, None)):
                raise RuntimeError('Required current native helper missing: ' + name)
        with tempfile.TemporaryDirectory(prefix='kcml-plan-create-') as directory:
            snapshot = Path(directory) / 'SSOT.md'
            snapshot.write_bytes(raw.replace(b'\r\n', b'\n'))
            yield module, module.Document(snapshot), raw, rs
    finally:
        if previous is None:
            sys.modules.pop(module.__name__, None)
        else:
            sys.modules[module.__name__] = previous


def allocation_schema():
    """Local technical mask, not a registered whole-operation command schema."""
    return {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        'type': 'object',
        'properties': {k: {'$ref': 'urn:kcml:generation-contracts:2#/$defs/' + v}
                       for k, v in [('jobId', 'Uuid'), ('planId', 'Uuid'), ('scopeLock', 'ScopeLock')]},
        'required': ['jobId', 'planId', 'scopeLock'], 'additionalProperties': False,
    }


def _closed(native, value, fields, pointer):
    native.require(isinstance(value, dict) and set(value) == set(fields),
                   'ARTIFACT_VALIDATION_FAILED', pointer, 'Exact trusted projection fields required')


def validate_plan_allocation(doc, native, plan, *, allocation):
    """12.18/56.10: accept only server-preallocated identity and frozen scope.

    No DAG, artifact hydration, admission, authority or commit is asserted.
    Returning a digest is validation output, not a persisted creation receipt.
    """
    doc.validate('GenerationPlan', plan)
    _closed(native, allocation, ('jobId', 'planId', 'scopeLock'), '/allocation')
    for field, definition in [('jobId', 'Uuid'), ('planId', 'Uuid'), ('scopeLock', 'ScopeLock')]:
        doc.validate(definition, allocation[field])
    for field in ('jobId', 'planId', 'scopeLock'):
        native.require(plan[field] == allocation[field], 'GENERATION_PLAN_INVALID',
                       '/' + field, 'Plan differs from trusted server allocation/frozen scope')
    native.require(plan['specificationDigest'] == allocation['scopeLock']['approvedSpecificationDigest'],
                   'SPECIFICATION_DIGEST_STALE', '/specificationDigest', 'Wrong frozen approved specification')
    return native.semantic_digest(plan)


def plan_created_handoff(doc, native, plan, *, allocation, persisted_event,
                         commit_snapshot, committed):
    """Validate persisted publication; no event is returned before known commit.

    Replay uses the ORIGINAL allocation/event/commit, even after cancellation or
    a later job revision. Current admission guards belong to the writer, not to
    replay of this immutable outcome (49.4/49.10/49.27).
    """
    validate_plan_allocation(doc, native, plan, allocation=allocation)
    _closed(native, commit_snapshot, ('jobId', 'documentId', 'documentDigest',
                                      'eventSequence', 'approvedSpecificationDigest'), '/commitSnapshot')
    doc.validate('SseEnvelope', persisted_event)
    native.require(persisted_event['type'] == 'generation.plan.created',
                   'ARTIFACT_VALIDATION_FAILED', '/type', 'Only plan publication is in scope')
    selector = native.validate_generation_document_event(
        doc, persisted_event, plan, persisted_event=persisted_event,
        commit_snapshot=commit_snapshot, committed=committed)
    return {'event': copy.deepcopy(persisted_event), 'readSelector': copy.deepcopy(selector)}


def plan_created_read_handoff(doc, native, plan, *, allocation, persisted_event,
                              commit_snapshot, committed, response, repository_snapshot):
    """Independently compare event pointer with the trusted immutable repository.

    response is the status/output projection AFTER transport validation. False
    means no document handed onward, not that the committed event was undone.
    """
    handoff = plan_created_handoff(doc, native, plan, allocation=allocation,
                                  persisted_event=persisted_event,
                                  commit_snapshot=commit_snapshot, committed=committed)
    _closed(native, response, ('status', 'output'), '/response')
    native.require(response['status'] in ('SUCCEEDED', 'FAILED', 'CANCELLED', 'ACCEPTED', 'RUNNING'),
                   'ARTIFACT_VALIDATION_FAILED', '/response/status', 'Unknown read status')
    selector = handoff['readSelector']
    if response['status'] != 'SUCCEEDED':
        native.require(response['output'] is None, 'ARTIFACT_VALIDATION_FAILED',
                       '/response/output', 'A failed or pending read has no document')
        return native.validate_generation_read_handoff(
            doc, selector['operationId'], selector['pathParameters'], response)
    _closed(native, repository_snapshot, ('jobId', 'documentId', 'documentDigest'), '/repositorySnapshot')
    for field, definition, selected in (
        ('jobId', 'Uuid', 'persisted_job_id'),
        ('documentId', 'Uuid', 'persisted_document_id'),
        ('documentDigest', 'Digest', 'persisted_document_digest'),
    ):
        doc.validate(definition, repository_snapshot[field])
        native.require(repository_snapshot[field] == selector[selected],
                       'ARTIFACT_VALIDATION_FAILED', '/repositorySnapshot/' + field,
                       'Immutable repository pointer differs from committed event')
    return native.validate_generation_read_handoff(
        doc, selector['operationId'], selector['pathParameters'], response,
        persisted_job_id=repository_snapshot['jobId'],
        persisted_document_id=repository_snapshot['documentId'],
        persisted_document_digest=repository_snapshot['documentDigest'])


def investigation(doc, raw, rs):
    sources = {
        'schemaVersion': ('56.13', 'Native constant; no new model wrapper.'),
        'planId': ('56.10', 'Exact server-preallocated plan ID; model may only quote it.'),
        'jobId': ('12.23,56.10', 'Exact job owning the trusted plan allocation.'),
        'specificationDigest': ('12.22,56.8', 'Equals frozen approved digest in trusted scope lock.'),
        'scopeLock': ('12.22,56.8', 'Full native value must equal frozen allocation scope; not digest alone.'),
        'pathPlan': ('56.4,56.5,56.8', 'Native PATH_PLAN ref; actual hydration remains required.'),
        'sdkLock': ('56.5,56.8', 'Native SDK_LOCK ref; actual bytes/profile verification remains required.'),
        'rootArtifacts': ('56.5,56.8', 'Native refs; actual bytes/provenance and slot hydration remain required.'),
        'nodes': ('12.23,56.8', 'Native nodes; DAG, producer, phase and side-effect ordering remain required.'),
        'coverage': ('12.23,56.5', 'Native coverage; equality with approved requirements remains required.'),
    }
    definition = doc.schema['$defs']['GenerationPlan']
    if set(sources) != set(definition['properties']):
        raise RuntimeError('GenerationPlan fields changed; update this per-field derivation')
    rows = [{'field': name, 'required': name in definition['required'],
             'schema': definition['properties'][name], 'sourceSections': sources[name][0],
             'derivation': sources[name][1]} for name in definition['properties']]
    return {
        'sourceSha256': hashlib.sha256(raw).hexdigest(),
        'resourceSha256': {p: rs[p]['sha256'] for p in (GEN, CONTROL, EVENT_SCHEMA)},
        'operationId': OPERATION, 'classification': 'INVESTIGATION_OPEN',
        'wholePairReady': False, 'solvedOperationReferences': [], 'ownerDecisionRequired': False,
        'implementedBoundary': 'TRUSTED_ALLOCATION_TO_COMMITTED_PLAN_EVENT_TO_IMMUTABLE_READ',
        'evidenceKind': 'TECHNICAL_DERIVATION_NOT_PRODUCTION_EVIDENCE',
        'allocationMask': allocation_schema(), 'fields': rows,
        'output': {'event': 'urn:kcml:generation-document-events:1#/$defs/PlanCreated',
                   'readOperation': 'generation.plan.read',
                   'document': 'urn:kcml:generation-contracts:2#/$defs/GenerationPlan',
                   'readSelectorProducer': 'validate_generation_document_event'},
        'errorBindingsImplemented': [
            {'predicate': 'native masks / event / commit / repository mismatch',
             'code': 'ARTIFACT_VALIDATION_FAILED', 'effect': 'No adapter output; no writes'},
            {'predicate': 'allocation jobId / planId / full scopeLock mismatch',
             'code': 'GENERATION_PLAN_INVALID', 'effect': 'No publication'},
            {'predicate': 'plan specificationDigest differs from frozen approval',
             'code': 'SPECIFICATION_DIGEST_STALE', 'effect': 'No publication'},
        ],
        'remainingPredicatesAndErrorBindings': [
            {'sections': '49.3-49.4,51.12', 'predicate': 'Stable allocation/idempotency lookup and same-key digest comparison',
             'errors': ['IDEMPOTENCY_CONFLICT'], 'remaining': 'Trusted DB collector and admission/replay transaction; adapter arguments are not proof of origin.'},
            {'sections': '49.15,51.5,56.5', 'predicate': 'Current job/phase/fence/incarnation/cancellation/deadline and authority before creation',
             'errors': ['STATE_VERSION_CONFLICT', 'FENCING_TOKEN_STALE', 'PLATFORM_INCARNATION_STALE'],
             'remaining': 'Operation-specific code/required snapshot/retry bindings; replay must not rerun fresh admission.'},
            {'sections': '12.23,56.5,56.8', 'predicate': 'Artifact hydration, exact scope coverage, DAG, node kinds, slots, SDK and path closure',
             'errors': ['GENERATION_PLAN_INVALID', 'CONTRACT_PACK_REFERENCE_INVALID', 'ARTIFACT_VALIDATION_FAILED'],
             'remaining': 'Run full validators against actual registry/bytes; creation is not phase success or permission to enter IMPLEMENTING.'},
            {'sections': '49.5,49.10,51.5,51.32', 'predicate': 'Atomic plan/outcome/checkpoint/event/audit/outbox; cancel-versus-commit ordering',
             'errors': ['MANUAL_OUTCOME_CONFLICT', 'SIDE_EFFECT_OUTCOME_UNKNOWN'],
             'remaining': 'SQLSTATE/reconciliation and known failed/cancelled/unknown operation response masks. Never infer no commit from timeout.'},
            {'sections': '12.44.2,49.5,49.27', 'predicate': 'Trusted outbox/inbox and immutable repository lookup',
             'errors': ['SEQUENCE_GAP'], 'remaining': 'Real delivery dedupe, retention/resync and transport error bindings; frozen terminal replay after cancellation.'},
        ],
    }


def main():
    with current_native() as (_, doc, raw, rs):
        print(json.dumps(investigation(doc, raw, rs), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
