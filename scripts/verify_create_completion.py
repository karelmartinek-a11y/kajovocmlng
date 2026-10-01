"""Synthetic create completion/commit/hydration witnesses; not production runtime acceptance."""
import copy,hashlib,json,os
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
from ssot_sources import ROOT,SSOT,resource_index
from create_completion_contracts import OPERATIONS,ERRORS,canonical_digest
from create_operation_contracts import ContractFailure,decode_http,admit
UID='00000000-0000-4000-8000-000000000001'
ROOT_ID='00000000-0000-4000-8000-000000000002'
VERSION_ID='00000000-0000-4000-8000-000000000003'
OTHER_ID='00000000-0000-4000-8000-000000000004'
TIME='2026-09-30T12:00:00Z'

def canonical_bytes(value):
 return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')

def pointer(parts):return ''.join('/'+str(v).replace('~','~0').replace('/','~1') for v in parts)
def diagnostics(error):
 base=pointer(error.absolute_path)
 if error.validator=='required' and isinstance(error.instance,dict):
  missing=[v for v in error.validator_value if v not in error.instance]
  # jsonschema emits a separate error per missing property.
  missing=[v for v in missing if repr(v)+' is a required property'==error.message] or missing
  yield from ((error.validator,base+'/'+v) for v in missing)
 elif error.validator=='additionalProperties' and isinstance(error.instance,dict):
  known=error.schema.get('properties',{})
  yield from ((error.validator,base+'/'+v) for v in error.instance if v not in known)
 else:yield error.validator,base
 for child in error.context:yield from diagnostics(child)

def witnesses(operation,row):
 if operation=='generation.job.create':
  output={'jobId':ROOT_ID,'kind':'CREATE','state':'DISCUSSING','stateVersion':'1','initialRequestDigest':canonical_digest({'intent':'Create fixture component'}),'createdAt':TIME,'frozenBasis':None}
 else:
  output={'secretId':ROOT_ID,'stableName':'FIXTURE_SECRET','type':'PASSWORD','versionId':VERSION_ID,'versionNumber':'1','versionState':'CREATED','recordStatus':'INACTIVE','activeVersionId':None,'stateVersion':'1','createdAt':TIME}
 response={'routeId':row['routeId'],'operationId':operation,'logicalOperationId':UID,'correlationId':UID,'status':'SUCCEEDED','terminal':True,'output':output,'error':None,'resultDigest':'sha256:'+'0'*64,'stateVersion':'1','eventSequence':'1','activationEpoch':None,'idempotencyReplay':False}
 response['resultDigest']=canonical_digest({k:v for k,v in response.items() if k not in ['resultDigest','idempotencyReplay']})
 event={'routeId':row['routeId'],'operationId':operation,'eventType':OPERATIONS[operation][1],'logicalOperationId':UID,'correlationId':UID,'sequence':'1','payload':copy.deepcopy(output),'payloadDigest':canonical_digest(output),'immutableEventId':OTHER_ID,'aggregateId':ROOT_ID,'occurredAt':TIME}
 return response,event

def main():
 input_source_sha=hashlib.sha256(SSOT.read_bytes()).hexdigest();support_paths=['scripts/create_completion_contracts.py','scripts/create_operation_contracts.py','scripts/follow_up_contracts.py'];input_support_sha={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in support_paths}
 rs=resource_index();rows={r['operationId']:r for r in json.loads(rs['contracts/payload-contracts.json']['raw'])['records'] if r['operationId'] in OPERATIONS};checks=[];domain_witnesses={}
 def check(name,actual,expected=True):checks.append({'case':name,'passed':actual==expected,'actual':actual,'expected':expected})
 def reject(name,fn,code,at):
  try:fn();checks.append({'case':name,'passed':False,'diagnostic':'ACCEPTED_INVALID','expectedCode':code,'expectedPointer':at})
  except ContractFailure as exc:checks.append({'case':name,'passed':exc.code==code and exc.pointer==at,'expectedCode':code,'actualCode':exc.code,'expectedPointer':at,'actualPointer':exc.pointer})
  except Exception as exc:checks.append({'case':name,'passed':False,'diagnostic':'UNRELATED_EXCEPTION','exceptionType':type(exc).__name__,'reason':str(exc)})
 def schema_reject(name,validator,bad,keyword,at):
  errs=list(validator.iter_errors(bad));found={pair for e in errs for pair in diagnostics(e)}
  checks.append({'case':name,'passed':(keyword,at) in found,'expectedKeyword':keyword,'expectedPointer':at,'actualDiagnostics':[{'keyword':k,'pointer':p} for k,p in sorted(found)]})
 for operation,row in rows.items():
  response,event=witnesses(operation,row);domain_witnesses[operation]={'response':response,'event':event}
  rv=Draft202012Validator(row['responseSchema'],format_checker=FormatChecker());ev=Draft202012Validator(row['eventSchema'],format_checker=FormatChecker())
  check(operation+'/response/positive',rv.is_valid(response));check(operation+'/event/positive',ev.is_valid(event))
  check(operation+'/event/explicit-applicability',row.get('eventApplicability'),'AGGREGATE_STREAM')
  for role,valid,v in [('response',response,rv),('event',event,ev)]:
   for key,value in valid.items():
    bad=copy.deepcopy(valid);del bad[key];schema_reject(operation+'/'+role+'/missing/'+key,v,bad,'required','/'+key)
    if value is not None:
     bad=copy.deepcopy(valid);bad[key]=None
     null_errors={pair for e in v.iter_errors(bad) for pair in diagnostics(e)}
     # A nullable branch is tested separately under success below.
     if key=='error' or (role=='response' and key=='activationEpoch'):continue
     expected_keyword='const' if key in ['operationId','routeId','eventType','terminal'] else 'type'
     schema_reject(operation+'/'+role+'/null/'+key,v,bad,expected_keyword,'/'+key)
   bad=copy.deepcopy(valid);bad['modelReceipt']='untrusted';schema_reject(operation+'/'+role+'/extra',v,bad,'additionalProperties','/modelReceipt')
   nested='output' if role=='response' else 'payload'
   for key,value in valid[nested].items():
    bad=copy.deepcopy(valid);del bad[nested][key];schema_reject(operation+'/'+role+'/receipt-missing/'+key,v,bad,'required','/'+nested+'/'+key)
    if value is not None:
     bad=copy.deepcopy(valid);bad[nested][key]=None
     expected_keyword='enum' if key=='kind' else 'const' if key in ['state','versionState'] else 'type'
     schema_reject(operation+'/'+role+'/receipt-null/'+key,v,bad,expected_keyword,'/'+nested+'/'+key)
   if operation=='secret.create':
    for forbidden in ['ACTIVE','DELETED','CREATED']:
     bad=copy.deepcopy(valid);bad[nested]['recordStatus']=forbidden
     schema_reject(operation+'/'+role+'/derived-create-status/'+forbidden,v,bad,'const','/'+nested+'/recordStatus')
   bad=copy.deepcopy(valid);bad[nested]['authorityId']=UID;schema_reject(operation+'/'+role+'/receipt-extra',v,bad,'additionalProperties','/'+nested+'/authorityId')
   for key in ['stateVersion','versionNumber']:
    if key not in valid[nested]:continue
    for invalid,keyword in [('01','pattern'),('9223372036854775808','pattern'),(1,'type')]:
     bad=copy.deepcopy(valid);bad[nested][key]=invalid;schema_reject(operation+'/'+role+'/counter/'+key+'/'+str(invalid),v,bad,keyword,'/'+nested+'/'+key)
   for key in ['jobId','secretId','versionId']:
    if key not in valid[nested]:continue
    bad=copy.deepcopy(valid);bad[nested][key]='not-a-uuid';schema_reject(operation+'/'+role+'/uuid/'+key,v,bad,'format','/'+nested+'/'+key)
   bad=copy.deepcopy(valid);bad[nested]['createdAt']='2026-99-99T12:00:00Z';schema_reject(operation+'/'+role+'/timestamp',v,bad,'format','/'+nested+'/createdAt')

  schema_reject(operation+'/success-null-output',rv,{**response,'output':None},'type','/output')
  schema_reject(operation+'/success-nonterminal',rv,{**response,'terminal':False},'const','/terminal')
  pending={**response,'status':'ACCEPTED','terminal':False,'output':None,'stateVersion':None,'eventSequence':None}
  check(operation+'/accepted-positive',rv.is_valid(pending));schema_reject(operation+'/accepted-terminal',rv,{**pending,'terminal':True},'const','/terminal')
  for error in ERRORS:
   if operation=='generation.job.create' and error['stableCode']=='CREATE_STABLE_NAME_CONFLICT':continue
   if error.get('operationIds') and operation not in error['operationIds']:continue
   e={k:error[k] for k in ['stableCode','classification','retryDirective']};e.update(message='Synthetic '+error['stableCode'],detailsDigest=None)
   failure={**response,'status':'CANCELLED' if error['stableCode']=='CREATE_CANCELLED' else 'FAILED','terminal':error['classification']!='UNKNOWN' and error['retryDirective']!='RETRY_SAME_OPERATION','output':None,'error':e,'stateVersion':None,'eventSequence':None}
   check(operation+'/error-positive/'+error['stableCode'],rv.is_valid(failure))
   for field,wrong in [('classification','UNDECLARED'),('retryDirective','UNDECLARED')]:
    bad=copy.deepcopy(failure);bad['error'][field]=wrong;schema_reject(operation+'/error-contradiction/'+error['stableCode']+'/'+field,rv,bad,'const','/error/'+field)
   if error['classification']=='UNKNOWN':schema_reject(operation+'/unknown-terminal',rv,{**failure,'terminal':True},'const','/terminal')
   if error['retryDirective']=='RETRY_SAME_OPERATION':schema_reject(operation+'/retryable-attempt-not-terminal',rv,{**failure,'terminal':True},'const','/terminal')
  error_detail={'stableCode':'CREATE_INPUT_INVALID','classification':'VALIDATION','retryDirective':'DO_NOT_RETRY','message':'Synthetic invalid input','detailsDigest':None}
  error_response={**response,'status':'FAILED','output':None,'error':error_detail,'stateVersion':None,'eventSequence':None}
  check(operation+'/error-fields/positive',rv.is_valid(error_response))
  for field,value in error_detail.items():
   bad=copy.deepcopy(error_response);del bad['error'][field];schema_reject(operation+'/error-fields/missing/'+field,rv,bad,'required','/error/'+field)
   if value is not None:
    bad=copy.deepcopy(error_response);bad['error'][field]=None;schema_reject(operation+'/error-fields/null/'+field,rv,bad,'type','/error/'+field)
  bad=copy.deepcopy(error_response);bad['error']['httpStatus']=200;schema_reject(operation+'/error-fields/extra',rv,bad,'additionalProperties','/error/httpStatus')
  bad=copy.deepcopy(error_response);bad['error']['stableCode']='UNDECLARED';schema_reject(operation+'/error-fields/unknown-code',rv,bad,'enum','/error/stableCode')
  bad=copy.deepcopy(error_response);bad['error']['detailsDigest']='sha256:'+'0'*64+'\n';schema_reject(operation+'/error-fields/noncanonical-digest',rv,bad,'pattern','/error/detailsDigest')
  failure={**response,'status':'FAILED','output':None,'error':None}
  schema_reject(operation+'/failure-null-error',rv,failure,'type','/error')
  wrongcancel={**response,'status':'CANCELLED','output':None,'error':{'stableCode':'CREATE_INPUT_INVALID','classification':'VALIDATION','retryDirective':'DO_NOT_RETRY','message':'Synthetic invalid input','detailsDigest':None}}
  schema_reject(operation+'/cancel-wrong-code',rv,wrongcancel,'const','/error/stableCode')
  cancelled_error={'stableCode':'CREATE_CANCELLED','classification':'CANCELLED','retryDirective':'DO_NOT_RETRY','message':'Cancellation won before commit','detailsDigest':None}
  schema_reject(operation+'/cancel-error-requires-cancel-status',rv,{**response,'status':'FAILED','output':None,'error':cancelled_error},'const','/status')
  if operation=='generation.job.create':
   conflict={'stableCode':'CREATE_STABLE_NAME_CONFLICT','classification':'CONFLICT','retryDirective':'DO_NOT_RETRY','message':'Secret name already exists','detailsDigest':None}
   schema_reject(operation+'/reject-secret-only-error',rv,{**response,'status':'FAILED','output':None,'error':conflict},'enum','/error/stableCode')
  for key,v,valid in [('resultDigest',rv,response),('payloadDigest',ev,event)]:
   bad=copy.deepcopy(valid);bad[key]+='\n';schema_reject(operation+'/digest-no-trailing-newline/'+key,v,bad,'pattern','/'+key)
  schema_reject(operation+'/event-sequence-positive',ev,{**event,'sequence':'0'},'not','/sequence')

  if operation=='secret.create':
   bad=copy.deepcopy(response);bad['output']['versionState']='ACTIVE';schema_reject(operation+'/first-version-not-active',rv,bad,'const','/output/versionState')
   bad=copy.deepcopy(event);bad['payload']['activeVersionId']=VERSION_ID;schema_reject(operation+'/event-no-active-pointer',ev,bad,'type','/payload/activeVersionId')
  else:
   bad=copy.deepcopy(event);bad['payload']['state']='COMPLETED';schema_reject(operation+'/create-not-job-completed',ev,bad,'const','/payload/state')
   for role,valid,v,nested in [('response',response,rv,'output'),('event',event,ev,'payload')]:
    bad=copy.deepcopy(valid);bad[nested]['kind']='FOLLOW_UP';schema_reject(operation+'/'+role+'/follow-up-cannot-omit-basis',v,bad,'type','/'+nested+'/frozenBasis')
    bad=copy.deepcopy(valid);bad[nested]['frozenBasis']={};schema_reject(operation+'/'+role+'/create-cannot-assert-follow-up-basis',v,bad,'type','/'+nested+'/frozenBasis')

  from create_completion_contracts import validate_completion
  persisted={'response':copy.deepcopy(response),'event':copy.deepcopy(event)};hydrated={'bytes':canonical_bytes(response['output']),'contentDigest':canonical_digest(response['output'])}
  def completed(r=response,e=event,p=persisted,h=hydrated,c=True):return validate_completion(operation,r,e,committed=c,persisted=p,hydrated=h)
  selector=completed();check(operation+'/hydration-positive',selector,{'jobId':ROOT_ID} if operation=='generation.job.create' else {'secretId':ROOT_ID,'versionId':VERSION_ID})
  # Exact helper diagnostics are populated from the canonical helper below;
  # none of these cases tolerates an unrelated exception or invalid fixture.
  helper_cases(operation,response,event,persisted,hydrated,completed,reject,check)
 server={'owner':UID,'actor':'OWNER','authenticated':True,'recovery':'READY','stableNames':[],'valuePolicyTypes':['CERTIFICATE'],'artifacts':{ROOT_ID:{'artifactId':ROOT_ID,'owner':UID,'immutable':True,'bytes':b'fixture','contentSha256':hashlib.sha256(b'fixture').hexdigest(),'mediaType':'text/plain'}}}
 headers=[('Content-Type','application/json'),('Idempotency-Key','fixture-key')]
 def native(op,body):return decode_http(op,'POST','/secrets' if op=='secret.create' else '/generation/jobs',[],headers,canonical_bytes(body))
 gen=native('generation.job.create',{'intent':'Create fixture component','sources':[{'kind':'FILE','artifactId':ROOT_ID}]})
 check('admission/file-positive',admit(gen,server)['dispatchNew'])
 bad=copy.deepcopy(server);del bad['artifacts'][ROOT_ID]['contentSha256'];reject('admission/missing-artifact-digest',lambda:admit(gen,bad),'ARTIFACT_DIGEST_UNAVAILABLE','$.sources[0]')
 secbody={'stableName':'FIXTURE_SECRET','displayName':'Fixture','type':'PASSWORD','value':{'encoding':'UTF8','text':'synthetic fixture'}}
 check('admission/opaque-password-positive',admit(native('secret.create',secbody),server)['dispatchNew'])
 reject('admission/certificate-whitelist-not-validator',lambda:admit(native('secret.create',{**secbody,'type':'CERTIFICATE','value':{'encoding':'UTF8','text':'not a certificate'}}),server),'SECRET_PROFILE_REQUIRED','/value')
 check('input-source-unchanged',hashlib.sha256(SSOT.read_bytes()).hexdigest(),input_source_sha)
 check('input-support-unchanged',{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in support_paths},input_support_sha)
 report={'sourceDocumentSha256':input_source_sha,'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'supportSha256':input_support_sha,'resourceSha256':{p:rs[p]['sha256'] for p in ['contracts/payload-contracts.json','contracts/create-completion.json']},'scope':__doc__+' Hydration tests cover frozen creation receipt bytes only; full domain/read hydration remains OPEN.','witnesses':domain_witnesses,'checked':len(checks),'failed':sum(not x['passed'] for x in checks),'checks':checks,'wholeOperationsClosed':[],'implementationProductionAcceptance':'NOT_EVALUATED','remaining':['Complex Secret type policies','Parent/target lifecycle admission matrix','Physical SQL/encryption/runtime UI and consumer handoffs']}
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/create-review-negatives');out.mkdir(parents=True,exist_ok=True);(out/'completion-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['sourceDocumentSha256','checked','failed']}))
 for item in checks:
  if not item['passed']:print(json.dumps(item))
 return int(bool(report['failed']))

def helper_cases(operation,response,event,persisted,hydrated,completed,reject,check):
 def failure(name,fn,code,at):reject(operation+'/relations/'+name,fn,code,at)
 def recompute(r):r['resultDigest']=canonical_digest({k:v for k,v in r.items() if k not in ['resultDigest','idempotencyReplay']});return r
 for value in [False,None]:failure('uncommitted/'+str(value),lambda value=value:completed(c=value),'COMMIT_NOT_VERIFIED','/commit')
 failure('bad-result-digest',lambda:completed(r={**response,'resultDigest':'sha256:'+'0'*64}),'RESULT_DIGEST_MISMATCH','/response/resultDigest')
 for name,field,value,code,at in [
  ('state-version','stateVersion','2','RESPONSE_STATE_VERSION_MISMATCH','/response/stateVersion'),
  ('activation','activationEpoch','1','CREATE_ACTIVATION_FORBIDDEN','/response/activationEpoch')]:
  failure(name,lambda field=field,value=value:completed(r=recompute({**response,field:value})),code,at)
 for name,field,value,code,at in [
  ('sequence','sequence','2','EVENT_SEQUENCE_MISMATCH','/event/sequence'),
  ('aggregate-id','aggregateId',OTHER_ID,'EVENT_AGGREGATE_ID_MISMATCH','/event/aggregateId'),
  ('logical-id','logicalOperationId',OTHER_ID,'EVENT_OPERATION_CONTEXT_MISMATCH','/event/logicalOperationId'),
  ('correlation-id','correlationId',OTHER_ID,'EVENT_OPERATION_CONTEXT_MISMATCH','/event/correlationId'),
  ('payload-digest','payloadDigest','sha256:'+'0'*64,'EVENT_PAYLOAD_DIGEST_MISMATCH','/event/payloadDigest')]:
  failure(name,lambda field=field,value=value:completed(e={**event,field:value}),code,at)
 altered=copy.deepcopy(event);altered['payload']['createdAt']='2026-09-30T12:00:01Z';altered['payloadDigest']=canonical_digest(altered['payload'])
 failure('payload-receipt',lambda:completed(e=altered),'EVENT_PAYLOAD_RECEIPT_MISMATCH','/event/payload')
 for missing in [None,{}, {'response':response}]:failure('persisted-missing/'+str(len(missing) if isinstance(missing,dict) else None),lambda missing=missing:completed(p=missing),'PERSISTED_COMPLETION_UNAVAILABLE','/persisted')
 alteredp=copy.deepcopy(persisted);alteredp['response']['correlationId']=OTHER_ID
 failure('persisted-response',lambda:completed(p=alteredp),'PERSISTED_RESPONSE_MISMATCH','/persisted/response')
 alterede=copy.deepcopy(persisted);alterede['event']['occurredAt']='2026-09-30T12:00:01Z'
 failure('persisted-event',lambda:completed(p=alterede),'PERSISTED_EVENT_MISMATCH','/persisted/event')
 for h in [None,{}, {'bytes':'client text'}]:failure('hydration-bytes/'+str(type(h).__name__),lambda h=h:completed(h=h),'HYDRATION_BYTES_UNAVAILABLE','/hydrated/bytes')
 failure('hydration-digest-missing',lambda:completed(h={'bytes':hydrated['bytes']}),'HYDRATION_DIGEST_UNAVAILABLE','/hydrated/contentDigest')
 failure('hydration-digest-mismatch',lambda:completed(h={**hydrated,'contentDigest':'sha256:'+'0'*64}),'HYDRATION_CONTENT_DIGEST_MISMATCH','/hydrated/contentDigest')
 different={**response['output'],'createdAt':'2026-09-30T12:00:01Z'};raw=canonical_bytes(different)
 failure('hydration-valid-other-receipt',lambda:completed(h={'bytes':raw,'contentDigest':'sha256:'+hashlib.sha256(raw).hexdigest()}),'HYDRATION_RECEIPT_MISMATCH','/hydrated/bytes')
 goodraw=hydrated['bytes'];field=next(iter(response['output']));dup=goodraw[:-1]+b','+json.dumps(field).encode()+b':'+json.dumps(response['output'][field]).encode()+b'}'
 for name,raw,code in [('invalid-json',goodraw[:-1],'HYDRATION_INVALID_JSON'),('duplicate-json-key',dup,'HYDRATION_DUPLICATE_JSON_KEY'),('invalid-utf8',b'"\xff"','HYDRATION_INVALID_UTF8')]:
  failure('hydration-'+name,lambda raw=raw:completed(h={'bytes':raw,'contentDigest':'sha256:'+hashlib.sha256(raw).hexdigest()}),code,'/hydrated/bytes')
 replay=completed(r={**response,'idempotencyReplay':True})
 check(operation+'/relations/replay-marker-preserves-frozen-selector',replay,completed())
 unknown=next(x for x in ERRORS if x['classification']=='UNKNOWN');error={k:unknown[k] for k in ['stableCode','classification','retryDirective']};error.update(message='Unknown fixture outcome',detailsDigest=None)
 uncertain=recompute({**response,'status':'FAILED','terminal':False,'output':None,'error':error,'stateVersion':None,'eventSequence':None})
 check(operation+'/relations/unknown-no-new-create',completed(r=uncertain,e=None,p=None,h=None,c=None),{'action':'RECONCILE_ORIGINAL_OPERATION'})
 failure('unknown-forbids-event',lambda:completed(r=uncertain,e=event,p=None,h=None,c=None),'UNCOMMITTED_CREATE_EVENT','/event')


if __name__=='__main__':raise SystemExit(main())
