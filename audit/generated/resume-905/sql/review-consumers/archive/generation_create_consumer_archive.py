"""Proposed bounded DESIGN consumer; not a full job read or deployed browser."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from jsonschema import Draft202012Validator,FormatChecker
from create_completion_contracts import UID,DIGEST,COUNTER,TIME,obj,nullable,definitions,canonical_digest
from create_operation_contracts import strict_json,validate_body,ContractFailure
from follow_up_contracts import STATES

def schema():
    p=copy.deepcopy(definitions()['GenerationCreated']['properties'])
    p['state']={'enum':STATES}
    p['eventSequence']=copy.deepcopy(COUNTER)
    p['initialRequestRef']=obj({'snapshotId':UID,'contentDigest':DIGEST,'mediaType':{'const':'application/json'}})
    result=obj(p)
    result['allOf']=copy.deepcopy(definitions()['GenerationCreated']['allOf'])
    result['$id']='urn:kcml:design:generation-created-read-projection:v1'
    result['$comment']='Closed create-consumer projection, NOT replacement for the complete generation.job.read or snapshot.read entity.'
    return result

def fail(code,p=''):
    raise ContractFailure(code,p)

def validate_schema(s,v,code):
    errors=list(Draft202012Validator(s,format_checker=FormatChecker()).iter_errors(v))
    if errors:fail(code,errors[0].json_path)

def consume(receipt,projection,stored,*,selected_job_id,producer,previous=None,request_validator=None):
    """Producer is server-transport provenance supplied outside model JSON.

    Reference fixture binds canonical API origin+operation+job ID. It does not
    demonstrate real TLS/session verification or current PostgreSQL reads.
    Stored contains decrypted bytes supplied by trusted repository boundary;
    these bytes and credentials never appear in public return/evidence.
    """
    validate_schema(definitions()['GenerationCreated'],receipt,'RECEIPT_SCHEMA_INVALID')
    validate_schema(schema(),projection,'READ_PROJECTION_SCHEMA_INVALID')
    if producer != ('CANONICAL_OWNER_API','generation.job.read',selected_job_id):fail('UNTRUSTED_READ_PRODUCER')
    if selected_job_id!=receipt['jobId'] or projection['jobId']!=receipt['jobId']:fail('READ_JOB_IDENTITY_MISMATCH')
    for k in ['kind','createdAt','initialRequestDigest','frozenBasis']:
        if projection[k]!=receipt[k]:fail('IMMUTABLE_CREATE_LINK_MISMATCH','/'+k)
    if int(projection['stateVersion'])<int(receipt['stateVersion']):fail('READ_STATE_VERSION_REGRESSION')
    if previous is not None:
        if previous['jobId']!=projection['jobId']:fail('PREVIOUS_JOB_IDENTITY_MISMATCH')
        if int(projection['stateVersion'])<int(previous['stateVersion']) or int(projection['eventSequence'])<int(previous['eventSequence']):fail('READ_CURRENT_VERSION_REGRESSION')
        if previous['state'] in ['COMPLETED','FAILED','CANCELLED'] and previous['state']!=projection['state']:fail('TERMINAL_STATE_REWRITE')
    ref=projection['initialRequestRef']
    if stored.get('snapshotId')!=ref['snapshotId'] or stored.get('jobId')!=projection['jobId']:fail('INITIAL_SNAPSHOT_IDENTITY_MISMATCH')
    raw=stored.get('bytes')
    if not isinstance(raw,bytes):fail('INITIAL_REQUEST_BYTES_UNAVAILABLE')
    if 'sha256:'+hashlib.sha256(raw).hexdigest()!=ref['contentDigest']:fail('INITIAL_REQUEST_BYTES_DIGEST_MISMATCH')
    value=strict_json(raw)
    if request_validator is None:fail('FROZEN_DOMAIN_POLICY_UNAVAILABLE')
    request_validator(value)
    if canonical_digest(value)!=projection['initialRequestDigest']:fail('INITIAL_REQUEST_SEMANTIC_DIGEST_MISMATCH')
    if value.get('kind','CREATE')!=projection['kind']:fail('INITIAL_REQUEST_KIND_MISMATCH')
    # Create is admission into discussion, never execution or activation proof.
    return {'jobId':projection['jobId'],'state':projection['state'],'stateVersion':projection['stateVersion'],
            'eventSequence':projection['eventSequence'],'nextAction':'READ_SELECTED_JOB',
            'executionApproved':False,'activationAuthorized':False}

def retry_action(response,key,original_key):
    # Consume the complete canonical response mask, never independently trusted
    # status/classification strings. Specific stable-code/classification/retry
    # tuples and terminal/output relations must all validate first.
    from ssot_sources import resource_index
    from create_completion_contracts import semantic_result
    rows=json.loads(resource_index()['contracts/payload-contracts.json']['raw'])['records']
    mask=next(row['responseSchema'] for row in rows if row['operationId']=='generation.job.create')
    validate_schema(mask,response,'UI_CREATE_OUTCOME_SCHEMA_INVALID')
    if canonical_digest(semantic_result(response))!=response['resultDigest']:
        fail('UI_CREATE_OUTCOME_DIGEST_MISMATCH')
    if key!=original_key:fail('UI_CREATE_RETRY_KEY_CHANGED')
    error=response['error']
    if error is not None and error['classification']=='UNKNOWN':return 'RECONCILE_ORIGINAL_LOGICAL_OPERATION'
    if response['status']=='ACCEPTED':return 'WAIT_OR_READ_ORIGINAL_LOGICAL_OPERATION'
    if error is not None and error['retryDirective']=='RETRY_SAME_OPERATION':return 'RETRY_ORIGINAL_LOGICAL_OPERATION'
    return 'DISPLAY_CANONICAL_OUTCOME'

def runtime_facade_schema(action):
    if action not in ['START','STOP']:fail('FACADE_ACTION_INVALID')
    return obj({'schemaVersion':{'const':'RUNTIME_OWNER_INTENT/1'},'action':{'const':action},
                'componentId':UID,'expectedComponentStateVersion':COUNTER,
                'runtimeInstanceId':UID,'expectedRuntimeGeneration':COUNTER,
                'expectedActivationEpoch':COUNTER})
