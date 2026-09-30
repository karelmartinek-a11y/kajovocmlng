import copy,hashlib,json
from pathlib import Path
from owner_ui_native_contracts import *
HERE=Path(__file__).parent
ID='11111111-1111-4111-8111-111111111111';OTHER='22222222-2222-4222-8222-222222222222';checks=[]
def neg(name,code,fn):
 try:fn()
 except ContractFailure as e:
  assert e.code==code,(name,e.code,code);checks.append({'id':name,'status':'PASS','actualDiagnostic':e.code,'expectedDiagnostic':code});return
 raise AssertionError(name+' accepted')
def positive(name,fn):fn();checks.append({'id':name,'status':'PASS'})
def resign(r):r['resultDigest']=outcome_digest(r);return r
def event(r):return {'eventType':'OPERATION_ADMITTED' if r['status']=='ACCEPTED' else 'OPERATION_TERMINAL','operationId':r['operationId'],'logicalOperationId':r['logicalOperationId'],'intentId':r['intentId'],'immutableEventId':OTHER,'sequence':'1','occurredAt':'2026-09-30T12:00:00Z','payloadDigest':canonical_digest(r),'payload':copy.deepcopy(r)}
outputs={'dashboard.start':{'outcome':'RUNTIME_READY','runtimeInstanceId':ID,'runtimeGeneration':'2','readinessReceiptId':OTHER,'launchSnapshotDigest':'sha256:'+'a'*64},'dashboard.stop':{'outcome':'RUNTIME_CLEANUP_COMPLETE','runtimeInstanceId':ID,'runtimeGeneration':'2','cleanupOperationId':OTHER,'cleanupReceiptId':OTHER,'cleanupState':'COMPLETE'},'gen.editSpec':{'outcome':'NEW_DRAFT','jobId':ID,'revisionId':OTHER,'state':'DRAFT','specificationDigest':'sha256:'+'b'*64,'diffArtifactId':ID,'requirementCoverageArtifactId':OTHER}}
for action in OPS:
 accepted=resign({'operationId':OPS[action][0],'logicalOperationId':ID,'intentId':OTHER,'status':'ACCEPTED','terminal':False,'output':None,'error':None,'resultDigest':'sha256:'+'0'*64,'idempotencyReplay':False})
 positive(action+'/accepted-own-intent',lambda:validate_outcome(action,accepted,event(accepted)))
 replay={**accepted,'idempotencyReplay':True};positive(action+'/frozen-admit-event-replay',lambda:validate_outcome(action,replay,event(accepted)))
 success=resign({**accepted,'status':'SUCCEEDED','terminal':True,'output':outputs[action]});raw=json.dumps(success['output'],separators=(',',':')).encode();worker={'workerOperationId':OPS[action][1],'parentLogicalOperationId':ID,'intentId':OTHER,'bytes':raw,'contentDigest':'sha256:'+hashlib.sha256(raw).hexdigest()}
 positive(action+'/complete-typed-worker-output',lambda:validate_outcome(action,success,event(success),retained_worker_receipt=worker))
 replay={**success,'idempotencyReplay':True};positive(action+'/frozen-terminal-event-replay',lambda:validate_outcome(action,replay,event(success),retained_worker_receipt=worker))
 neg(action+'/missing-worker-receipt','OWNER_UI_WORKER_RECEIPT_MISSING',lambda:validate_outcome(action,success,event(success)))
 bad={**worker,'parentLogicalOperationId':OTHER};neg(action+'/wrong-worker-parent','OWNER_UI_WORKER_RECEIPT_IDENTITY_MISMATCH',lambda:validate_outcome(action,success,event(success),retained_worker_receipt=bad))
 bad={**worker,'bytes':raw+b' '};neg(action+'/actual-worker-bytes-digest','OWNER_UI_WORKER_RECEIPT_BYTES_DIGEST_MISMATCH',lambda:validate_outcome(action,success,event(success),retained_worker_receipt=bad))
 invalid=b'{"outcome":"INVALID"}';bad={**worker,'bytes':invalid,'contentDigest':'sha256:'+hashlib.sha256(invalid).hexdigest()};neg(action+'/digest-valid-invalid-worker-mask','OWNER_UI_WORKER_RECEIPT_PAYLOAD_INVALID',lambda:validate_outcome(action,success,event(success),retained_worker_receipt=bad))
 duplicate=b'{"outcome":"x","outcome":"y"}';bad={**worker,'bytes':duplicate,'contentDigest':'sha256:'+hashlib.sha256(duplicate).hexdigest()};neg(action+'/actual-worker-json-duplicates','DUPLICATE_JSON_KEY',lambda:validate_outcome(action,success,event(success),retained_worker_receipt=bad))
 ev=event(accepted);ev['eventType']='OPERATION_TERMINAL';neg(action+'/accepted-not-terminal-event','OWNER_UI_EVENT_PHASE_MISMATCH',lambda:validate_outcome(action,accepted,ev))
 ev=event(accepted);ev['intentId']=ID;neg(action+'/event-wrong-intent','OWNER_UI_EVENT_IDENTITY_MISMATCH',lambda:validate_outcome(action,accepted,ev))
 for c,cl,retry,h,_ in ERRORS:
  failure=resign({**accepted,'status':'CANCELLED' if c=='OWNER_UI_CANCELLED' else 'FAILED','terminal':cl!='UNKNOWN' and retry!='RETRY_SAME_OPERATION','error':{'stableCode':c,'classification':cl,'retryDirective':retry,'httpStatus':h,'detailsDigest':'sha256:'+'c'*64}})
  positive(action+'/'+c,lambda failure=failure:validate_outcome(action,failure,event(failure) if failure['terminal'] else None))
  contradictory=copy.deepcopy(failure);contradictory['error']['classification']='UNDECLARED';resign(contradictory);neg(action+'/'+c+'/wrongclass','OWNER_UI_OUTCOME_SCHEMA_INVALID',lambda contradictory=contradictory:validate_outcome(action,contradictory,None))
  if not failure['terminal']:
   neg(action+'/'+c+'/no-false-terminal-event','OWNER_UI_NONTERMINAL_TERMINAL_EVENT',lambda failure=failure:validate_outcome(action,failure,event(failure)))
   bad=resign({**failure,'terminal':True});neg(action+'/'+c+'/no-terminal-unknown','OWNER_UI_OUTCOME_SCHEMA_INVALID',lambda bad=bad:validate_outcome(action,bad,None))
# Actual facade HTTPdecoder: valid runtime domain input first.
body={'schemaVersion':'RUNTIME_OWNER_INTENT/1','action':'START','componentId':ID,'expectedComponentStateVersion':'2','runtimeInstanceId':OTHER,'expectedRuntimeGeneration':'2','expectedActivationEpoch':'2'};raw=json.dumps(body).encode();headers=[('Content-Type','application/json'),('Idempotency-Key','same')]
positive('HTTP/positive',lambda:decode_owner_http('dashboard.start','POST',PATHS['dashboard.start'],[],headers,raw,transport_max_bytes=1048576))
neg('HTTP/unknownquery','UNKNOWN_QUERY_PARAMETER',lambda:decode_owner_http('dashboard.start','POST',PATHS['dashboard.start'],[('extra','1')],headers,raw,transport_max_bytes=1048576))
neg('HTTP/duplicatekey','DUPLICATE_JSON_KEY',lambda:decode_owner_http('dashboard.start','POST',PATHS['dashboard.start'],[],headers,b'{"action":"START","action":"STOP"}',transport_max_bytes=1048576))
neg('HTTP/invalid-json','INVALID_JSON',lambda:decode_owner_http('dashboard.start','POST',PATHS['dashboard.start'],[],headers,b'{',transport_max_bytes=1048576))
neg('HTTP/client-worker-authority','OWNER_UI_CLIENT_AUTHORITY_FORBIDDEN',lambda:decode_owner_http('dashboard.start','POST',PATHS['dashboard.start'],[],headers+[('x-worker-context-id',ID)],raw,transport_max_bytes=1048576))
assert project_failure('OWNER_UI_SESSION_STALE')['stableCode']=='OWNER_UI_AUTH_REQUIRED';checks.append({'id':'projection/fresh-auth-specific','status':'PASS'})
assert project_failure('OWNER_UI_WORKER_DEPENDENCY_UNAVAILABLE')['stableCode']=='OWNER_UI_DEPENDENCY_BLOCKED';checks.append({'id':'projection/worker-dependency-specific','status':'PASS'})
neg('projection/unmapped-exception-not-domain-pass','OWNER_UI_ERROR_PROJECTION_UNRESOLVED',lambda:project_failure('UNRELATED_EXCEPTION'))
neg('HTTP/unresolved-transport-cap','OWNER_UI_TRANSPORT_LIMIT_UNRESOLVED',lambda:decode_owner_http('dashboard.start','POST',PATHS['dashboard.start'],[],headers,raw,transport_max_bytes=None))
neg('HTTP/declared-transport-cap','REQUEST_TOO_LARGE',lambda:decode_owner_http('dashboard.start','POST',PATHS['dashboard.start'],[],headers,raw,transport_max_bytes=len(raw)-1))
report={'inputCommit':'6ac0e89','scope':'Precise proposed OWNERfacade response/error/event and worker-output byte relations; server producer SQL/current root effect joins remain separately required','checks':len(checks),'failed':0,'cases':checks,'implementationProductionAcceptance':'NOT_EVALUATED','exposuresClosed':0,'supportingFiles':{f:hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in ['owner_ui_native_contracts.py','verify_owner_ui_native_contracts.py','ui_facade_pipeline_reference.py']}}
(HERE/'owner-ui-native-contract-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checks),'PASS')
