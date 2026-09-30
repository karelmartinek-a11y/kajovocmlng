"""Exact staged OWNER facade reference. All worker effects remain separately proved."""
import copy,hashlib,json
from generation_consumer_reference import *
from ssot_sources import resource_index
from functools import lru_cache

@lru_cache(maxsize=1)
def native_bundle():
    return json.loads(resource_index()['contracts/generation/generation-contracts.schema.json']['raw'])

def launch_snapshot_schema():
    # Exact §50.10 members; controlled server text identifiers remain subject
    # to existing service/profile registries, never model authority.
    return obj({'componentId':UID,'sourceRevisionId':UID,'releaseId':UID,
        'artifactDigest':DIGEST,'runtimeDigest':DIGEST,'dependencyLockDigest':DIGEST,
        'bindingSetRevision':COUNTER,'activationEpoch':COUNTER,
        'applicationDeploymentEpoch':COUNTER,'platformIncarnationId':UID,
        'runtimeInstanceId':UID,'runtimeGeneration':COUNTER,
        'systemdUnitName':{'type':'string','minLength':1},
        'expectedServiceClass':{'type':'string','minLength':1},
        'resourceProfileDigest':DIGEST,'namespaceProfileDigest':DIGEST,
        'seccompProfileDigest':DIGEST,'environmentProfileDigest':DIGEST,'fdProfileDigest':DIGEST,
        'handlerEntrypoint':{'type':'string','minLength':1},'exportSchemaDigest':DIGEST,
        'stateSchemaRevision':{'type':'string','minLength':1},
        'cleanupInventoryTemplateDigest':DIGEST})

@lru_cache(maxsize=1)
def schemas():
    bundle=native_bundle()
    edit_base={'schemaVersion':{'const':'SPECIFICATION_OWNER_INPUT/1'},'jobId':UID,'expectedStateVersion':COUNTER,'expectedRevisionId':UID,'expectedSpecificationDigest':DIGEST}
    text=obj({**edit_base,'variant':{'const':'OWNER_TEXT'},'text':{'type':'string','minLength':1}})
    # Complete typed candidate, never a server-approved specification/revision.
    candidate=obj({**edit_base,'variant':{'const':'SPECIFICATION_CANDIDATE'},'candidate':{'$ref':'#/$defs/GenerationSpecification'}})
    edit={'$schema':bundle['$schema'],'$defs':bundle['$defs'],'oneOf':[text,candidate]}
    return {'dashboard.start':runtime_facade_schema('START'),'dashboard.stop':runtime_facade_schema('STOP'),'gen.editSpec':edit}

def request_digest(action,body):return canonical_digest({'actionId':action,'body':body})

def validate_binding(action,body,root):
    validate_schema(schemas()[action],body,'OWNER_FACADE_INPUT_INVALID')
    if action in ['dashboard.start','dashboard.stop']:
        if root['componentId']!=body['componentId'] or root['runtimeInstanceId']!=body['runtimeInstanceId']:fail('OWNER_FACADE_TARGET_IDENTITY_MISMATCH')
        for k in ['expectedComponentStateVersion','expectedRuntimeGeneration','expectedActivationEpoch']:
            if body[k]!=root[k]:fail('STATE_VERSION_CONFLICT','/'+k)
        for k in ['launchSnapshotBytes','launchSnapshotDigest']:
            if k not in root:fail('OWNER_FACADE_LAUNCH_SNAPSHOT_UNAVAILABLE')
        if not isinstance(root['launchSnapshotBytes'],bytes):fail('OWNER_FACADE_LAUNCH_SNAPSHOT_UNAVAILABLE')
        if 'sha256:'+hashlib.sha256(root['launchSnapshotBytes']).hexdigest()!=root['launchSnapshotDigest']:fail('OWNER_FACADE_LAUNCH_SNAPSHOT_DIGEST_MISMATCH')
        manifest=strict_json(root['launchSnapshotBytes'])
        validate_schema(launch_snapshot_schema(),manifest,'OWNER_FACADE_LAUNCH_SNAPSHOT_INVALID')
        for m,b in [('componentId','componentId'),('runtimeInstanceId','runtimeInstanceId'),('runtimeGeneration','expectedRuntimeGeneration'),('activationEpoch','expectedActivationEpoch')]:
            if manifest[m]!=body[b]:fail('OWNER_FACADE_MANIFEST_TARGET_MISMATCH','/'+m)
    else:
        if root['jobId']!=body['jobId'] or root['revisionId']!=body['expectedRevisionId']:fail('OWNER_FACADE_TARGET_IDENTITY_MISMATCH')
        if root['stateVersion']!=body['expectedStateVersion']:fail('STATE_VERSION_CONFLICT','/expectedStateVersion')
        raw=root.get('specificationBytes')
        if not isinstance(raw,bytes):fail('OWNER_FACADE_SPECIFICATION_BYTES_UNAVAILABLE')
        spec=strict_json(raw)
        bundle=native_bundle()
        mask={**bundle,'$ref':'#/$defs/GenerationSpecification'}
        validate_schema(mask,spec,'OWNER_FACADE_BASE_SPECIFICATION_INVALID')
        if spec['jobId']!=body['jobId']:fail('OWNER_FACADE_SPECIFICATION_JOB_MISMATCH')
        if canonical_digest(spec)!=body['expectedSpecificationDigest'] or root['specificationDigest']!=body['expectedSpecificationDigest']:fail('OWNER_FACADE_SPECIFICATION_DIGEST_CONFLICT')
        if body['variant']=='SPECIFICATION_CANDIDATE' and body['candidate']['jobId']!=body['jobId']:fail('OWNER_FACADE_CANDIDATE_JOB_MISMATCH')
        # Same canonical candidate produces no duplicate revision (§43.3).
        if body['variant']=='SPECIFICATION_CANDIDATE' and canonical_digest(body['candidate'])==canonical_digest(spec):return 'NO_DUPLICATE_REVISION'
    return 'PERSIST_OWNER_INTENT'

def admit(db,action,body,*,locator,command_id,logical_id,context_id,crash=None):
    """Atomic reference repository, NOT proof of PostgreSQL/source auth tables.

    Authentication service verifies persisted context outside this function.
    The reference requires one exact stored context ID/digest and no client
    execution-context fields. Worker context must be independently server-built.
    """
    if action not in schemas():fail('OWNER_FACADE_ACTION_UNDECLARED')
    validate_schema(schemas()[action],body,'OWNER_FACADE_INPUT_INVALID')
    digest=request_digest(action,body)
    old=db['locators'].get(locator)
    if old:
        if old['requestDigest']!=digest:fail('IDEMPOTENCY_CONFLICT')
        return copy.deepcopy(db['commands'][old['logicalOperationId']]['receipt'])
    context=db['contexts'].get(context_id)
    if context is None or context['id']!=context_id:fail('OWNER_FACADE_CONTEXT_UNAVAILABLE')
    if context['operationId']!=action or context['requestDigest']!=digest:fail('OWNER_FACADE_CONTEXT_SCOPE_MISMATCH')
    if context['descriptorDigest']!=canonical_digest(context['descriptor']):fail('OWNER_FACADE_CONTEXT_DIGEST_MISMATCH')
    root=db['roots'].get(body.get('componentId',body.get('jobId')))
    if root is None:fail('OWNER_FACADE_TARGET_UNAVAILABLE')
    decision=validate_binding(action,body,root)
    saved=copy.deepcopy(db)
    try:
        intent={'commandId':command_id,'logicalOperationId':logical_id,'ownerContextId':context_id,'actionId':action,'requestDigest':digest,'arguments':copy.deepcopy(body),'frozenTargetDigest':canonical_digest({k:v for k,v in root.items() if not isinstance(v,bytes)}),'workerOperationId':{'dashboard.start':'runtime.instance.start','dashboard.stop':'runtime.stop','gen.editSpec':'generation.spec.propose'}[action]}
        receipt={'logicalOperationId':logical_id,'commandId':command_id,'actionId':action,'status':'ACCEPTED','terminal':False,'requestDigest':digest,'createdRevisionId':None,'runtimeReady':False,'decision':decision}
        event={'eventType':'OPERATION_ADMITTED','logicalOperationId':logical_id,'actionId':action,'payloadDigest':canonical_digest(receipt),'payload':copy.deepcopy(receipt)}
        db['commands'][logical_id]={'intent':intent,'receipt':receipt}
        db['locators'][locator]={'requestDigest':digest,'logicalOperationId':logical_id}
        db['events'].append(event)
        db['outbox'].append({'logicalOperationId':logical_id,'workerOperationId':intent['workerOperationId'],'intentDigest':canonical_digest(intent),'published':False})
        db['audit'].append({'logicalOperationId':logical_id,'requestDigest':digest,'eventDigest':canonical_digest(event)})
        if crash=='BEFORE_COMMIT':fail('OWNER_FACADE_REFERENCE_ROLLBACK')
        return copy.deepcopy(receipt)
    except Exception:
        db.clear();db.update(saved);raise

def read_receipt(db,logical_id):
    command=db['commands'].get(logical_id)
    if command is None:fail('OWNER_FACADE_RECEIPT_UNAVAILABLE')
    events=[e for e in db['events'] if e['logicalOperationId']==logical_id]
    outbox=[e for e in db['outbox'] if e['logicalOperationId']==logical_id]
    audits=[e for e in db['audit'] if e['logicalOperationId']==logical_id]
    if len(events)!=1 or len(outbox)!=1 or len(audits)!=1:fail('OWNER_FACADE_ATOMIC_LINK_INCOMPLETE')
    if events[0]['payload']!=command['receipt'] or events[0]['payloadDigest']!=canonical_digest(command['receipt']):fail('OWNER_FACADE_EVENT_RECEIPT_MISMATCH')
    if outbox[0]['intentDigest']!=canonical_digest(command['intent']):fail('OWNER_FACADE_OUTBOX_INTENT_MISMATCH')
    if audits[0]['eventDigest']!=canonical_digest(events[0]):fail('OWNER_FACADE_AUDIT_EVENT_MISMATCH')
    return copy.deepcopy(command['receipt'])
