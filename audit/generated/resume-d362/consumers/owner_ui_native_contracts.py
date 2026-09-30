"""Concrete review-only native facade completion/dispatch contracts."""
import copy,json
from ui_facade_pipeline_reference import *
ERRORS=[
 ('OWNER_UI_INPUT_INVALID','VALIDATION','DO_NOT_RETRY',400,'Exact HTTP UTF8/JSON/native input mask rejected'),
 ('OWNER_UI_AUTH_REQUIRED','AUTHENTICATION','DO_NOT_RETRY',401,'Current fresh OWNER credential acceptance missing or stale'),
 ('STATE_VERSION_CONFLICT','CONFLICT','DO_NOT_RETRY',409,'Same target current own version/generation/revision/activation differs from expected selector'),
 ('IDEMPOTENCY_CONFLICT','CONFLICT','DO_NOT_RETRY',409,'Same stable locator has a different original caller request digest'),
 ('OWNER_UI_REFERENCE_INVALID','VALIDATION','DO_NOT_RETRY',422,'Actual target/revision/launch bytes, identity, digest or schema pin invalid'),
 ('OWNER_UI_DEPENDENCY_BLOCKED','DEPENDENCY','DO_NOT_RETRY',503,'Required current native resolver/worker schema/receipt chain absent'),
 ('OWNER_UI_CANCELLED','CANCELLED','DO_NOT_RETRY',409,'Cancellation won and canonical evidence proves no unresolved effect remains'),
 ('OWNER_UI_ROLLED_BACK','INTERNAL','RETRY_SAME_OPERATION',500,'Atomic intent transaction rollback positively established'),
 ('SIDE_EFFECT_OUTCOME_UNKNOWN','UNKNOWN','RECONCILE_THEN_RETRY',503,'Current intent/effect outcome not established by persisted canonical evidence'),
]
OPS={'dashboard.start':('runtime.owner.start.request','runtime.instance.start','AUTOMATED_MAINTENANCE'),
     'dashboard.stop':('runtime.owner.stop.request','runtime.stop','AUTOMATED_MAINTENANCE'),
     'gen.editSpec':('generation.spec.owner_input.append','generation.spec.propose','INTERNAL_PROTOCOL')}
PATHS={'dashboard.start':'/runtime/owner/start-requests','dashboard.stop':'/runtime/owner/stop-requests','gen.editSpec':'/generation/specifications/owner-inputs'}

def worker_request_schema(action):
 p={'schemaVersion':{'const':'OWNER_INTENT_WORKER_REQUEST/1'},'operationId':{'const':OPS[action][1]},'workerContextId':UID,'intentId':UID,'parentLogicalOperationId':UID,'targetSnapshotDigest':DIGEST}
 if action in ['dashboard.start','dashboard.stop']:
  p.update(runtimeInstanceId=UID,runtimeGeneration=COUNTER)
  if action=='dashboard.start':p['launchSnapshotDigest']=DIGEST
  else:p['cleanupOperationId']=UID
 else:p.update(jobId=UID,ownerInputId=UID,baseRevisionId=UID,baseSpecificationDigest=DIGEST)
 result=obj(p);result['$id']='urn:kcml:r9:operation:'+OPS[action][1]+':command';result['$schema']='https://json-schema.org/draft/2020-12/schema'
 return result

def success_schema(action):
 if action=='dashboard.start':return obj({'outcome':{'const':'RUNTIME_READY'},'runtimeInstanceId':UID,'runtimeGeneration':COUNTER,'readinessReceiptId':UID,'launchSnapshotDigest':DIGEST})
 if action=='dashboard.stop':return obj({'outcome':{'const':'RUNTIME_CLEANUP_COMPLETE'},'runtimeInstanceId':UID,'runtimeGeneration':COUNTER,'cleanupOperationId':UID,'cleanupReceiptId':UID,'cleanupState':{'const':'COMPLETE'}})
 return {'oneOf':[obj({'outcome':{'const':'NEW_DRAFT'},'jobId':UID,'revisionId':UID,'state':{'const':'DRAFT'},'specificationDigest':DIGEST,'diffArtifactId':UID,'requirementCoverageArtifactId':UID}),obj({'outcome':{'const':'SAME_CANONICAL_REVISION'},'jobId':UID,'revisionId':UID,'specificationDigest':DIGEST})]}

def completion_schema(action):
 error=obj({'stableCode':{'enum':[e[0] for e in ERRORS]},'classification':{'type':'string'},'retryDirective':{'type':'string'},'httpStatus':{'type':'integer'},'detailsDigest':DIGEST})
 error['oneOf']=[{'properties':{'stableCode':{'const':c},'classification':{'const':cl},'retryDirective':{'const':r},'httpStatus':{'const':h}}} for c,cl,r,h,_ in ERRORS]
 mask=obj({'operationId':{'const':OPS[action][0]},'logicalOperationId':UID,'intentId':UID,'status':{'enum':['ACCEPTED','SUCCEEDED','FAILED','CANCELLED']},'terminal':{'type':'boolean'},'output':nullable(success_schema(action)),'error':nullable(error),'resultDigest':DIGEST,'idempotencyReplay':{'type':'boolean'}})
 mask['allOf']=[
  {'if':{'properties':{'status':{'const':'ACCEPTED'}}},'then':{'properties':{'terminal':{'const':False},'output':{'type':'null'},'error':{'type':'null'}}}},
  {'if':{'properties':{'status':{'const':'SUCCEEDED'}}},'then':{'properties':{'terminal':{'const':True},'output':success_schema(action),'error':{'type':'null'}}}},
  {'if':{'properties':{'status':{'enum':['FAILED','CANCELLED']}}},'then':{'properties':{'output':{'type':'null'},'error':error}}},
  {'if':{'properties':{'status':{'const':'CANCELLED'}}},'then':{'properties':{'terminal':{'const':True},'error':{'properties':{'stableCode':{'const':'OWNER_UI_CANCELLED'}}}}}},
  {'if':{'properties':{'error':{'type':'object','properties':{'stableCode':{'const':'OWNER_UI_CANCELLED'}}}}},'then':{'properties':{'status':{'const':'CANCELLED'}}}},
  {'if':{'properties':{'error':{'type':'object','properties':{'classification':{'const':'UNKNOWN'}}}}},'then':{'properties':{'terminal':{'const':False}}}},
  {'if':{'properties':{'error':{'type':'object','properties':{'retryDirective':{'const':'RETRY_SAME_OPERATION'}}}}},'then':{'properties':{'terminal':{'const':False}}}},
  {'if':{'properties':{'status':{'const':'FAILED'},'error':{'type':'object','properties':{'classification':{'not':{'const':'UNKNOWN'}},'retryDirective':{'not':{'const':'RETRY_SAME_OPERATION'}}}}}},'then':{'properties':{'terminal':{'const':True}}}}
 ]
 return mask

def event_schema(action):
 frozen=completion_schema(action);frozen['properties']['idempotencyReplay']={'const':False}
 return obj({'eventType':{'enum':['OPERATION_ADMITTED','OPERATION_TERMINAL']},'operationId':{'const':OPS[action][0]},'logicalOperationId':UID,'intentId':UID,'immutableEventId':UID,'sequence':{**COUNTER,'not':{'const':'0'}},'occurredAt':TIME,'payloadDigest':DIGEST,'payload':frozen})

def outcome_digest(response):return canonical_digest({k:v for k,v in response.items() if k not in ['resultDigest','idempotencyReplay']})

def validate_outcome(action,response,event,*,retained_worker_receipt=None):
 validate_schema(completion_schema(action),response,'OWNER_UI_OUTCOME_SCHEMA_INVALID')
 if response['resultDigest']!=outcome_digest(response):fail('OWNER_UI_OUTCOME_DIGEST_MISMATCH')
 if response['status'] in ['FAILED','CANCELLED'] and not response['terminal']:
  if event is not None:fail('OWNER_UI_NONTERMINAL_TERMINAL_EVENT')
  return 'RECONCILE_OR_RETRY_ORIGINAL_OPERATION'
 if event is None:fail('OWNER_UI_COMMITTED_EVENT_MISSING')
 validate_schema(event_schema(action),event,'OWNER_UI_EVENT_SCHEMA_INVALID')
 if any(event[k]!=response[k] for k in ['operationId','logicalOperationId','intentId']):fail('OWNER_UI_EVENT_IDENTITY_MISMATCH')
 if {k:v for k,v in event['payload'].items() if k!='idempotencyReplay'}!={k:v for k,v in response.items() if k!='idempotencyReplay'} or event['payloadDigest']!=canonical_digest(event['payload']):fail('OWNER_UI_EVENT_RECEIPT_MISMATCH')
 expected='OPERATION_ADMITTED' if response['status']=='ACCEPTED' else 'OPERATION_TERMINAL'
 if event['eventType']!=expected:fail('OWNER_UI_EVENT_PHASE_MISMATCH')
 if response['status']=='SUCCEEDED':
  if retained_worker_receipt is None:fail('OWNER_UI_WORKER_RECEIPT_MISSING')
  if retained_worker_receipt.get('workerOperationId')!=OPS[action][1] or retained_worker_receipt.get('parentLogicalOperationId')!=response['logicalOperationId'] or retained_worker_receipt.get('intentId')!=response['intentId']:fail('OWNER_UI_WORKER_RECEIPT_IDENTITY_MISMATCH')
  raw=retained_worker_receipt.get('bytes')
  if not isinstance(raw,bytes) or 'sha256:'+hashlib.sha256(raw).hexdigest()!=retained_worker_receipt.get('contentDigest'):fail('OWNER_UI_WORKER_RECEIPT_BYTES_DIGEST_MISMATCH')
  parsed=strict_json(raw);validate_schema(success_schema(action),parsed,'OWNER_UI_WORKER_RECEIPT_PAYLOAD_INVALID')
  if parsed!=response['output']:fail('OWNER_UI_WORKER_RECEIPT_OUTCOME_MISMATCH')
  # These bytes are necessary, not sufficient to prove live pidfd/cleanup or
  # canonical DRAFT publication. Exact source-owned producer joins remain.
 return 'DISPLAY_CANONICAL_OUTCOME'

def project_failure(code):
    groups={
      'OWNER_UI_INPUT_INVALID':{'INVALID_UTF8','INVALID_JSON','INVALID_UNICODE','DUPLICATE_JSON_KEY','UNKNOWN_QUERY_PARAMETER','DUPLICATE_HEADER','CONTENT_TYPE_MISMATCH','IDEMPOTENCY_KEY_REQUIRED','REQUEST_TOO_LARGE','OWNER_UI_CLIENT_AUTHORITY_FORBIDDEN','OWNER_UI_ROUTE_MISMATCH','OWNER_FACADE_INPUT_INVALID'},
      'OWNER_UI_AUTH_REQUIRED':{'OWNER_UI_SESSION_STALE','OWNER_UI_API_STALE','OWNER_UI_PRODUCER_RECEIPT_FUTURE'},
      'STATE_VERSION_CONFLICT':{'STATE_VERSION_CONFLICT'},
      'IDEMPOTENCY_CONFLICT':{'IDEMPOTENCY_CONFLICT','OWNER_UI_IDEMPOTENCY_CONFLICT'},
      'OWNER_UI_REFERENCE_INVALID':{'OWNER_FACADE_TARGET_IDENTITY_MISMATCH','OWNER_FACADE_LAUNCH_SNAPSHOT_DIGEST_MISMATCH','OWNER_FACADE_LAUNCH_SNAPSHOT_INVALID','OWNER_FACADE_MANIFEST_TARGET_MISMATCH','OWNER_FACADE_BASE_SPECIFICATION_INVALID','OWNER_FACADE_SPECIFICATION_JOB_MISMATCH','OWNER_FACADE_SPECIFICATION_DIGEST_CONFLICT','OWNER_FACADE_CANDIDATE_JOB_MISMATCH'},
      'OWNER_UI_DEPENDENCY_BLOCKED':{'OWNER_UI_ADMISSION_DEPENDENCY_UNAVAILABLE','OWNER_UI_WORKER_DEPENDENCY_UNAVAILABLE','OWNER_UI_COMMAND_SCOPE_MISMATCH','OWNER_UI_INPUT_SCHEMA_PIN_MISMATCH','OWNER_UI_HEAD_MISMATCH','OWNER_UI_WORKER_HEAD_CHANGED','OWNER_UI_WORKER_REGISTRY_CHANGED','OWNER_UI_WORKER_INTENT_LINK_MISMATCH','OWNER_UI_WORKER_PARENT_NOT_ADMISSIBLE','OWNER_UI_TRANSPORT_LIMIT_UNRESOLVED','OWNER_FACADE_CONTEXT_UNAVAILABLE','OWNER_FACADE_TARGET_UNAVAILABLE','OWNER_FACADE_LAUNCH_SNAPSHOT_UNAVAILABLE','OWNER_FACADE_SPECIFICATION_BYTES_UNAVAILABLE'},
      'OWNER_UI_CANCELLED':{'OWNER_UI_CANCELLED'},
      'OWNER_UI_ROLLED_BACK':{'OWNER_FACADE_REFERENCE_ROLLBACK'},
      'SIDE_EFFECT_OUTCOME_UNKNOWN':{'SIDE_EFFECT_OUTCOME_UNKNOWN','OWNER_UI_WORKER_RECONCILIATION_REQUIRED'}
    }
    found=[stable for stable,codes in groups.items() if code in codes]
    if len(found)!=1:fail('OWNER_UI_ERROR_PROJECTION_UNRESOLVED')
    c,cl,r,h,_=next(e for e in ERRORS if e[0]==found[0])
    return {'stableCode':c,'classification':cl,'retryDirective':r,'httpStatus':h,'detailsDigest':canonical_digest({'reason':code})}

def decode_owner_http(action,method,path,query,headers,raw,*,transport_max_bytes):
 if action not in OPS or method!='POST' or path!=PATHS[action]:fail('OWNER_UI_ROUTE_MISMATCH')
 if query:fail('UNKNOWN_QUERY_PARAMETER')
 seen={}
 for k,v in headers:
  k=k.lower()
  if k in seen:fail('DUPLICATE_HEADER')
  seen[k]=v
 if seen.get('content-type','').lower() not in ['application/json','application/json; charset=utf-8']:fail('CONTENT_TYPE_MISMATCH')
 if not isinstance(seen.get('idempotency-key'),str) or not 1<=len(seen['idempotency-key'])<=512:fail('IDEMPOTENCY_KEY_REQUIRED')
 if any(k in seen for k in ['if-match','x-state-version','x-activation-epoch','x-authority-id','x-execution-authority-id','x-execution-context-id','x-worker-context-id']):fail('OWNER_UI_CLIENT_AUTHORITY_FORBIDDEN')
 if not isinstance(transport_max_bytes,int) or isinstance(transport_max_bytes,bool) or transport_max_bytes<1:fail('OWNER_UI_TRANSPORT_LIMIT_UNRESOLVED')
 if len(raw)>transport_max_bytes:fail('REQUEST_TOO_LARGE')
 body=strict_json(raw);validate_schema(schemas()[action],body,'OWNER_UI_INPUT_INVALID')
 return {'operationId':OPS[action][0],'body':body,'idempotencyKey':seen['idempotency-key'],'requestDigest':request_digest(action,body)}

if __name__=='__main__':
 from pathlib import Path
 here=Path(__file__).parent
 values={a:{'ownerOperationId':OPS[a][0],'workerOperationId':OPS[a][1],'workerExposure':OPS[a][2],'method':'POST','path':PATHS[a],'query':{'additionalProperties':False,'properties':{},'type':'object'},'inputSchema':schemas()[a],'workerRequestSchema':worker_request_schema(a),'responseSchema':completion_schema(a),'eventSchema':event_schema(a)} for a in OPS}
 (here/'owner-ui-native-contracts.proposed.json').write_text(json.dumps({'format':'KCML-OWNER-UI-NATIVE-CONTRACTS/1','activationStatus':'REVIEW_PENDING_DEPENDENCY_JOINS','operations':values,'errorPredicates':[{'stableCode':c,'classification':cl,'retryDirective':r,'httpStatus':h,'predicate':p,'sources':['49.3','49.4','49.5']} for c,cl,r,h,p in ERRORS]},indent=2)+'\n')
