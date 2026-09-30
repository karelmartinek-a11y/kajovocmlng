import copy,hashlib,json
from pathlib import Path
from generation_consumer_reference import *
OUT=Path(__file__).parent
J='11111111-1111-4111-8111-111111111111';S='22222222-2222-4222-8222-222222222222';OTHER='33333333-3333-4333-8333-333333333333'
body={'intent':'Synthetic isolated component','kind':'CREATE'}
raw=json.dumps(body,ensure_ascii=False,separators=(',',':')).encode()
r={'jobId':J,'state':'DISCUSSING','stateVersion':'1','initialRequestDigest':canonical_digest(body),'createdAt':'2026-09-30T12:00:00Z','kind':'CREATE','frozenBasis':None}
p={**r,'state':'ANALYZING','stateVersion':'2','eventSequence':'3','initialRequestRef':{'snapshotId':S,'contentDigest':'sha256:'+hashlib.sha256(raw).hexdigest(),'mediaType':'application/json'}}
stored={'snapshotId':S,'jobId':J,'bytes':raw};producer=('CANONICAL_OWNER_API','generation.job.read',J)
rows=[]
def positive(name,fn):
    fn();rows.append({'id':name,'expected':'ACCEPT','actual':'ACCEPT','status':'PASS'})
def negative(name,code,fn):
    try:fn()
    except ContractFailure as e:
        assert e.code==code,(name,code,e.code);rows.append({'id':name,'expectedDiagnostic':code,'actualDiagnostic':e.code,'status':'PASS'});return
    raise AssertionError(name+' accepted')
def run(proj=None,st=None,**kw):return consume(r,p if proj is None else proj,stored if st is None else st,selected_job_id=J,producer=producer,**kw)
positive('domain-positive',run)
for name,code,field,value in [('wrong-job','READ_JOB_IDENTITY_MISMATCH','jobId',OTHER),('changed-kind','IMMUTABLE_CREATE_LINK_MISMATCH','kind','UPDATE'),('changed-created-at','IMMUTABLE_CREATE_LINK_MISMATCH','createdAt','2026-09-30T13:00:00Z'),('changed-initial-digest','IMMUTABLE_CREATE_LINK_MISMATCH','initialRequestDigest','sha256:'+'a'*64),('state-version-regression','READ_STATE_VERSION_REGRESSION','stateVersion','0'),('unknown-state','READ_PROJECTION_SCHEMA_INVALID','state','CREATED'),('counter-wrong-type','READ_PROJECTION_SCHEMA_INVALID','stateVersion',2),('unknown-field','READ_PROJECTION_SCHEMA_INVALID','authority','MODEL')]:
 q=copy.deepcopy(p);q[field]=value;negative(name,code,lambda q=q:run(q))
q=copy.deepcopy(p);del q['initialRequestRef'];negative('required-ref','READ_PROJECTION_SCHEMA_INVALID',lambda:run(q))
negative('missing-actual-bytes','INITIAL_REQUEST_BYTES_UNAVAILABLE',lambda:run(st={'jobId':J,'snapshotId':S}))
negative('wrong-snapshot','INITIAL_SNAPSHOT_IDENTITY_MISMATCH',lambda:run(st={**stored,'snapshotId':OTHER}))
negative('wrong-content-bytes','INITIAL_REQUEST_BYTES_DIGEST_MISMATCH',lambda:run(st={**stored,'bytes':raw+b' '}))
for name,encoded,code in [('duplicate-json',b'{"intent":"x","intent":"y"}','DUPLICATE_JSON_KEY'),('invalid-json',b'{"intent":','INVALID_JSON')]:
 q=copy.deepcopy(p);q['initialRequestRef']['contentDigest']='sha256:'+hashlib.sha256(encoded).hexdigest()
 negative(name,code,lambda q=q,encoded=encoded:run(q,{**stored,'bytes':encoded}))
q=copy.deepcopy(p);badraw=b'{"intent":"different","kind":"CREATE"}';q['initialRequestRef']['contentDigest']='sha256:'+hashlib.sha256(badraw).hexdigest()
negative('semantic-bytes-link','INITIAL_REQUEST_SEMANTIC_DIGEST_MISMATCH',lambda:run(q,{**stored,'bytes':badraw}))
negative('model-producer','UNTRUSTED_READ_PRODUCER',lambda:consume(r,p,stored,selected_job_id=J,producer=('MODEL','generation.job.read',J)))
negative('latest-global-substitution','READ_JOB_IDENTITY_MISMATCH',lambda:consume(r,p,stored,selected_job_id=OTHER,producer=('CANONICAL_OWNER_API','generation.job.read',OTHER)))
previous={**p,'stateVersion':'3','eventSequence':'4'};negative('current-version-regression','READ_CURRENT_VERSION_REGRESSION',lambda:run(previous=previous))
previous={**p,'state':'FAILED'};negative('terminal-state-rewrite','TERMINAL_STATE_REWRITE',lambda:run(previous=previous))
from ssot_sources import resource_index
from verify_create_completion import witnesses
from create_completion_contracts import semantic_result,ERRORS
native_row=next(row for row in json.loads(resource_index()['contracts/payload-contracts.json']['raw'])['records'] if row['operationId']=='generation.job.create')
complete,_=witnesses('generation.job.create',native_row)
def resign(v):v['resultDigest']=canonical_digest(semantic_result(v));return v
unknown=copy.deepcopy(complete)
err=next(e for e in ERRORS if e['stableCode']=='SIDE_EFFECT_OUTCOME_UNKNOWN')
unknown.update(status='FAILED',terminal=False,output=None,stateVersion=None,eventSequence=None,error={k:err[k] for k in ['stableCode','classification','retryDirective']}|{'message':'Synthetic unknown','detailsDigest':None});resign(unknown)
assert retry_action(unknown,'same','same')=='RECONCILE_ORIGINAL_LOGICAL_OPERATION';rows.append({'id':'unknown-reconcile','status':'PASS'})
negative('retry-key-changed','UI_CREATE_RETRY_KEY_CHANGED',lambda:retry_action(unknown,'new','old'))
for name,mut in [('unknown-status',lambda v:v.update(status='UNDECLARED')),('unknown-classification',lambda v:v['error'].update(classification='UNDECLARED')),('contradictory-success-unknown',lambda v:v.update(status='SUCCEEDED')),('contradictory-pending-unknown',lambda v:v.update(status='ACCEPTED')),('wrong-retry-directive',lambda v:v['error'].update(retryDirective='DO_NOT_RETRY')),('unknown-terminal',lambda v:v.update(terminal=True))]:
 v=copy.deepcopy(unknown);mut(v);resign(v)
 negative(name,'UI_CREATE_OUTCOME_SCHEMA_INVALID',lambda v=v:retry_action(v,'same','same'))
v=copy.deepcopy(unknown);v['resultDigest']='sha256:'+'0'*64;negative('outcome-digest-corrupt','UI_CREATE_OUTCOME_DIGEST_MISMATCH',lambda:retry_action(v,'same','same'))
positive('valid-success-outcome',lambda:retry_action(complete,'same','same'))
pending=resign({**complete,'status':'ACCEPTED','terminal':False,'output':None,'error':None,'stateVersion':None,'eventSequence':None})
assert retry_action(pending,'same','same')=='WAIT_OR_READ_ORIGINAL_LOGICAL_OPERATION';rows.append({'id':'valid-pending-outcome','status':'PASS'})
for action in ['START','STOP']:
 fac={'schemaVersion':'RUNTIME_OWNER_INTENT/1','action':action,'componentId':J,'expectedComponentStateVersion':'2','runtimeInstanceId':S,'expectedRuntimeGeneration':'1','expectedActivationEpoch':'4'}
 positive(action+'-closed-intent',lambda fac=fac,action=action:validate_schema(runtime_facade_schema(action),fac,'FACADE_SCHEMA_INVALID'))
 bad={**fac,'executionContext':'AUTOMATED_MAINTENANCE'};negative(action+'-client-context-forbidden','FACADE_SCHEMA_INVALID',lambda bad=bad,action=action:validate_schema(runtime_facade_schema(action),bad,'FACADE_SCHEMA_INVALID'))
report={'inputCommit':'34d3a75c47a92ab7d8e0dac84f581549a15445ca','sourceDocumentSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'scope':'Proposed bounded create-read consumer, immutable bytes/identity/retry semantics; not complete job.read or runtime facade dispatch','checks':len(rows),'failed':0,'cases':rows,'implementationProductionAcceptance':'NOT_EVALUATED','wholeOperationsClosed':0,'supportingFiles':{f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in ['generation_consumer_reference.py','verify_consumer_reference.py']}}
(OUT/'consumer-reference-tests.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'consumer-projections.proposed.json').write_text(json.dumps({'createReadProjection':schema(),'runtimeOwnerIntentStart':runtime_facade_schema('START'),'runtimeOwnerIntentStop':runtime_facade_schema('STOP'),'activationStatus':'PROPOSED_NOT_NORMATIVE'},indent=2)+'\n')
print(len(rows),'checks PASS')
