"""Candidate retained worker-result read adapter; repository authority remains A.

Source authorities §§43.3,49.3–5,50.11,50.25,50.31. This is a pure
producer-consumer adapter, not an authenticated repository or live effect proof.
"""
import hashlib
from create_operation_contracts import ContractFailure, strict_json
from jsonschema import Draft202012Validator, FormatChecker

WORKERS = {'dashboard.start':'runtime.instance.start', 'dashboard.stop':'runtime.stop',
           'gen.editSpec':'generation.spec.propose'}
def fail(code): raise ContractFailure(code, '')
def digest(raw): return 'sha256:'+hashlib.sha256(raw).hexdigest()
def closed(row, keys, code):
    if not isinstance(row,dict) or set(row)!=set(keys): fail(code)

def read_terminal(action, response, event, intent, repository, validate_outcome, worker_request_mask):
    """Repository loads retained rows by server IDs, never client-supplied bytes.

    A resolver callback alone is not proof of its producer/authentication. Caller
    must run under its own current trusted read context and exact SQL joins.
    validate_outcome is the pinned native code validator, not a validity flag.
    """
    if action not in WORKERS: fail('OWNER_UI_ACTION_UNDECLARED')
    closed(intent, ('intentId','logicalOperationId','workerContextId','workerCommandId',
                    'workerOperationId','targetSnapshotDigest','arguments','workerArguments'), 'OWNER_UI_INTENT_SHAPE_INVALID')
    if intent['workerOperationId']!=WORKERS[action] or any(intent[k]!=response.get(k) for k in ['intentId','logicalOperationId']):
        fail('OWNER_UI_RETAINED_INTENT_IDENTITY_MISMATCH')
    if response.get('status')!='SUCCEEDED':
        # No worker-result publication is inferred from ACCEPTED, UNKNOWN or a
        # cancellation alone; the native status/error/event relation is decisive.
        return {'display':validate_outcome(action,response,event),'output':None}
    row=repository('worker_command_result',intent['workerCommandId'])
    closed(row, ('commandId','workerContextId','parentLogicalOperationId','intentId',
                 'workerOperationId','targetSnapshotDigest','resultBytes','contentDigest'),
           'OWNER_UI_WORKER_RESULT_UNAVAILABLE')
    pairs=[('commandId','workerCommandId'),('workerContextId','workerContextId'),
           ('parentLogicalOperationId','logicalOperationId'),('intentId','intentId'),
           ('workerOperationId','workerOperationId'),('targetSnapshotDigest','targetSnapshotDigest')]
    if any(row[k]!=intent[v] for k,v in pairs): fail('OWNER_UI_WORKER_COMMAND_BINDING_MISMATCH')
    raw=row['resultBytes']
    if not isinstance(raw,bytes) or digest(raw)!=row['contentDigest']: fail('OWNER_UI_WORKER_RESULT_DIGEST_MISMATCH')
    output=strict_json(raw)
    result={'workerOperationId':row['workerOperationId'],'parentLogicalOperationId':row['parentLogicalOperationId'],
            'intentId':row['intentId'],'bytes':raw,'contentDigest':row['contentDigest']}
    validate_outcome(action,response,event,retained_worker_receipt=result)
    args=intent['arguments']
    worker_args=intent['workerArguments']
    if list(Draft202012Validator(worker_request_mask,format_checker=FormatChecker()).iter_errors(worker_args)):
        fail('OWNER_UI_WORKER_ARGUMENT_SCHEMA_INVALID')
    for k,v in [('operationId','workerOperationId'),('workerContextId','workerContextId'),('intentId','intentId'),('parentLogicalOperationId','logicalOperationId'),('targetSnapshotDigest','targetSnapshotDigest')]:
        if worker_args.get(k)!=intent[v]: fail('OWNER_UI_WORKER_ARGUMENT_BINDING_MISMATCH')
    if action in ['dashboard.start','dashboard.stop']:
        if worker_args['runtimeInstanceId']!=args['runtimeInstanceId'] or worker_args['runtimeGeneration']!=args['expectedRuntimeGeneration']:
            fail('OWNER_UI_WORKER_ARGUMENT_BINDING_MISMATCH')
        if output['runtimeInstanceId']!=args['runtimeInstanceId'] or output['runtimeGeneration']!=args['expectedRuntimeGeneration']:
            fail('OWNER_UI_WORKER_TARGET_MISMATCH')
        if action=='dashboard.start' and output['launchSnapshotDigest']!=worker_args.get('launchSnapshotDigest'):
            fail('OWNER_UI_READINESS_SNAPSHOT_MISMATCH')
        if action=='dashboard.stop' and output['cleanupOperationId']!=worker_args['cleanupOperationId']:
            fail('OWNER_UI_CLEANUP_OPERATION_MISMATCH')
    else:
        if worker_args['jobId']!=args['jobId'] or worker_args['baseRevisionId']!=args['expectedRevisionId'] or worker_args['baseSpecificationDigest']!=args['expectedSpecificationDigest']:
            fail('OWNER_UI_WORKER_ARGUMENT_BINDING_MISMATCH')
        if output['jobId']!=args['jobId']: fail('OWNER_UI_WORKER_TARGET_MISMATCH')
        if output['outcome']=='SAME_CANONICAL_REVISION':
            if output['revisionId']!=args['expectedRevisionId'] or output['specificationDigest']!=args['expectedSpecificationDigest']:
                fail('OWNER_UI_SAME_REVISION_MISMATCH')
            # The unchanged immutable revision was produced by an earlier
            # command, not this child. Its historical producer/archive join is
            # an explicit dependency; never rewrite its creation lineage.
            fail('OWNER_UI_BASE_REVISION_PRODUCER_UNRESOLVED')
        elif output['revisionId']==args['expectedRevisionId']:
            fail('OWNER_UI_NEW_DRAFT_REUSES_BASE_REVISION')
    # Resolve effect receipt/artifacts rather than trusting reference presence.
    kinds={'dashboard.start':[('readinessReceiptId','RUNTIME_READINESS')],
           'dashboard.stop':[('cleanupReceiptId','RUNTIME_CLEANUP_COMPLETE')],
           'gen.editSpec': [('revisionId','GENERATION_SPECIFICATION_REVISION')]}
    if action=='gen.editSpec' and output['outcome']=='NEW_DRAFT':
        kinds[action]+=[('diffArtifactId','GENERATION_SPECIFICATION_DIFF'),('requirementCoverageArtifactId','GENERATION_REQUIREMENT_COVERAGE')]
    for field, kind in kinds[action]:
        artifact=repository('worker_artifact',output[field])
        closed(artifact,('id','kind','workerCommandId','workerContextId','bytes','contentDigest'), 'OWNER_UI_EFFECT_ARTIFACT_UNAVAILABLE')
        if artifact['id']!=output[field] or artifact['kind']!=kind or artifact['workerCommandId']!=intent['workerCommandId'] or artifact['workerContextId']!=intent['workerContextId']:
            fail('OWNER_UI_EFFECT_ARTIFACT_BINDING_MISMATCH')
        if not isinstance(artifact['bytes'],bytes) or digest(artifact['bytes'])!=artifact['contentDigest']:
            fail('OWNER_UI_EFFECT_ARTIFACT_DIGEST_MISMATCH')
        # Domain-native typed readiness/cleanup/diff/coverage hydration is still
        # required; bytes/digest/kind existence alone never declares its validity.
    return {'display':'BLOCKED_PENDING_EFFECT_HYDRATION','output':output,
            'effectSemanticHydration':'REQUIRED_NOT_PROVED_BY_THIS_ADAPTER'}
