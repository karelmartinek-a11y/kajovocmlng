"""Synthetic native decoder/admission diagnostics → exact HTTP error projection; no running HTTP server."""
import copy,hashlib,json,os
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
from ssot_sources import ROOT,SSOT,resource_index
from create_operation_contracts import ContractFailure,decode_http,admit,digest
from create_completion_contracts import ERRORS,http_failure
from verify_create_completion import diagnostics
UID='00000000-0000-4000-8000-000000000001'
REQUEST_ID='00000000-0000-4000-8000-000000000002'
CORRELATION_ID='00000000-0000-4000-8000-000000000003'
HEADERS=[('Content-Type','application/json'),('Idempotency-Key','fixture-key')]
BODIES={'generation.job.create':{'intent':'Create fixture component','sources':[{'kind':'TEXT','text':'Fixture requirements'}]},'secret.create':{'stableName':'FIXTURE_SECRET','displayName':'Fixture','type':'PASSWORD','value':{'encoding':'UTF8','text':'  Synthetic fixture bytes\n  '}}}

def encode(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf8')

def main():
 source_sha=hashlib.sha256(SSOT.read_bytes()).hexdigest();support_paths=['scripts/create_operation_contracts.py','scripts/create_completion_contracts.py','scripts/verify_create_completion.py'];support_sha={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in support_paths}
 rs=resource_index();schema=json.loads(rs['contracts/create-operation-design.schema.json']['raw'])['$defs']['HttpCreateFailure'];validator=Draft202012Validator(schema,format_checker=FormatChecker());checks=[];positives={};server={'owner':UID,'actor':'OWNER','authenticated':True,'recovery':'READY','stableNames':[]}
 def check(name,actual,expected=True):checks.append({'case':name,'passed':actual==expected,'actual':actual,'expected':expected})
 def decode(op,body=None,raw=None,headers=None,query=None):
  return decode_http(op,'POST','/generation/jobs' if op=='generation.job.create' else '/secrets',[] if query is None else query,HEADERS if headers is None else headers,encode(BODIES[op] if body is None else body) if raw is None else raw)
 def schema_reject(name,bad,keyword,at):
  found={pair for error in validator.iter_errors(bad) for pair in diagnostics(error)}
  checks.append({'case':name,'passed':(keyword,at) in found,'expectedKeyword':keyword,'expectedPointer':at,'actualDiagnostics':[{'keyword':k,'pointer':p} for k,p in sorted(found)]})
 def projection(op,failure,logical=None):return http_failure(op,failure,request_id=REQUEST_ID,correlation_id=CORRELATION_ID,logical_operation_id=logical)
 def reject_projection(name,op,code,at):
  try:projection(op,ContractFailure(code));checks.append({'case':name,'passed':False,'diagnostic':'UNKNOWN_DIAGNOSTIC_ACCEPTED'})
  except ContractFailure as exc:check(name,{'code':exc.code,'pointer':exc.pointer},{'code':'HTTP_FAILURE_PROJECTION_UNRESOLVED','pointer':at})
  except Exception as exc:checks.append({'case':name,'passed':False,'diagnostic':'UNRELATED_EXCEPTION','reason':str(exc)})
 def actual_failure(name,op,fn,expected_diag,expected_pointer,stable):
  try:fn();checks.append({'case':name,'passed':False,'diagnostic':'ACCEPTED_INVALID'});return
  except ContractFailure as exc:
   if (exc.code,exc.pointer)!=(expected_diag,expected_pointer):
    checks.append({'case':name,'passed':False,'diagnostic':'WRONG_REJECTION','actualCode':exc.code,'actualPointer':exc.pointer,'expectedCode':expected_diag,'expectedPointer':expected_pointer});return
   result=projection(op,exc);entry=next(e for e in ERRORS if e['stableCode']==stable)
   expected={'stableCode':stable,'classification':entry['classification'],'retryDirective':entry['retryDirective']}
   check(name+'/exact-tuple',{k:result['error'][k] for k in expected}|{'statusCode':result['statusCode']},expected|{'statusCode':entry['httpStatus']})
   check(name+'/exact-mask',validator.is_valid(result));check(name+'/no-logical-operation-before-admission',result['logicalOperationId'],None)
   check(name+'/details-bound-to-diagnostic',result['error']['detailsDigest'],digest({'reason':expected_diag,'pointer':expected_pointer}))
  except Exception as exc:checks.append({'case':name,'passed':False,'diagnostic':'UNRELATED_EXCEPTION','reason':str(exc)})
 for op,body in BODIES.items():
  native=decode(op);positives[op]={'body':body,'nativeRequest':native}
  if op=='generation.job.create':
   kind_request=decode(op,body={**body,'kind':'RETRY','parentJobId':UID,'generationBasis':{'basisKind':'RETRY_FAILED_TECHNICAL_PART','phaseRunId':UID,'expectedDigest':'sha256:'+'0'*64,'planId':UID,'expectedPlanDigest':'sha256:'+'0'*64,'approvedRevisionId':UID,'expectedSpecificationDigest':'sha256:'+'0'*64,'authorityId':UID,'expectedAuthorityDigest':'sha256:'+'0'*64}})
   actual_failure(op+'/own-kind-policy-required',op,lambda:admit(kind_request,{**server,'jobs':{UID:{'jobId':UID}}}),'PARENT_TARGET_ADMISSION_POLICY_UNVERIFIED','$.kind','CREATE_POLICY_UNRESOLVED')
  check(op+'/domain-positive-decoder',native['body'],body);check(op+'/domain-positive-admission',admit(native,server)['dispatchNew'])
  raw=encode(body);first=next(iter(body));first_value=encode(body[first]);key=encode(first)
  duplicate=raw[:-1]+b','+key+b':'+first_value+b'}'
  nested=raw.replace(b'"kind":"TEXT"',b'"kind":"TEXT","kind":"TEXT"',1) if op=='generation.job.create' else raw.replace(b'"encoding":"UTF8"',b'"encoding":"UTF8","encoding":"UTF8"',1)
  nested_pointer='/sources/0/kind' if op=='generation.job.create' else '/value/encoding'
  invalid_utf8=raw.replace(first_value,b'"\xff"',1);nonfinite=raw.replace(first_value,b'NaN',1);overflow=raw.replace(first_value,b'1e309',1);unicode=raw.replace(first_value,b'"\\ud800"',1)
  for name,bad,code,at in [('malformed-json',raw[:-1],'INVALID_JSON',''),('invalid-utf8',invalid_utf8,'INVALID_UTF8',''),('duplicate-root',duplicate,'DUPLICATE_JSON_KEY','/'+first),('duplicate-nested',nested,'DUPLICATE_JSON_KEY',nested_pointer),('nonfinite',nonfinite,'NONFINITE_JSON_NUMBER','/'+first),('numeric-overflow',overflow,'NONFINITE_JSON_NUMBER','/'+first),('invalid-unicode',unicode,'INVALID_UNICODE','')]:
   actual_failure(op+'/'+name,op,lambda bad=bad:decode(op,raw=bad),code,at,'CREATE_INPUT_INVALID')
  actual_failure(op+'/unknown-query',op,lambda:decode(op,query=[('unexpected','1')]),'UNKNOWN_QUERY_PARAMETER','/query','CREATE_INPUT_INVALID')
  actual_failure(op+'/duplicate-header',op,lambda:decode(op,headers=HEADERS+[('IDEMPOTENCY-KEY','other')]),'DUPLICATE_HEADER','/headers/idempotency-key','CREATE_INPUT_INVALID')
  actual_failure(op+'/missing-header',op,lambda:decode(op,headers=HEADERS[:1]),'IDEMPOTENCY_KEY_REQUIRED','/headers/idempotency-key','CREATE_INPUT_INVALID')
  actual_failure(op+'/extra-body',op,lambda:decode(op,body={**body,'authorityId':UID}),'SCHEMA_ADDITIONALPROPERTIES','$','CREATE_INPUT_INVALID')
  actual_failure(op+'/auth',op,lambda:admit(native,{**server,'authenticated':False}),'AUTHENTICATION_REQUIRED','','CREATE_AUTHENTICATION_REQUIRED')
  actual_failure(op+'/recovery',op,lambda:admit(native,{**server,'recovery':'RECOVERING'}),'RECOVERY_BARRIER','','CREATE_RECOVERY_BARRIER')
  if op=='secret.create':
   actual_failure(op+'/stable-name-conflict',op,lambda:admit(native,{**server,'stableNames':['FIXTURE_SECRET']}),'STABLE_NAME_UNAVAILABLE','$.stableName','CREATE_STABLE_NAME_CONFLICT')
   actual_failure(op+'/structured-type-policy',op,lambda:admit(decode(op,body={**body,'type':'CERTIFICATE'}),server),'TYPE_SPECIFIC_POLICY_UNVERIFIED','$.type','CREATE_POLICY_UNRESOLVED')
   text_json={**body,'type':'GENERIC_TEXT','value':{'encoding':'UTF8','text':'{"credential":"synthetic","nested":[1,2]}'}}
   check(op+'/permitted-json-secret-text-preserved',decode(op,body=text_json)['body']['value']['text'],text_json['value']['text'])
  fixture=projection(op,ContractFailure('IDEMPOTENCY_CONFLICT'),logical=UID);check(op+'/full-http-error-positive',validator.is_valid(fixture));positives[op]['httpFailure']=fixture
  for field in fixture:
   bad=copy.deepcopy(fixture);del bad[field];schema_reject(op+'/http-missing/'+field,bad,'required','/'+field)
   if field!='logicalOperationId':
    bad=copy.deepcopy(fixture);bad[field]=None;schema_reject(op+'/http-null/'+field,bad,'type' if field!='operationId' else 'enum','/'+field)
  bad=copy.deepcopy(fixture);bad['createdRoot']=UID;schema_reject(op+'/http-extra',bad,'additionalProperties','/createdRoot')
  for field in fixture['error']:
   bad=copy.deepcopy(fixture);del bad['error'][field];schema_reject(op+'/http-error-missing/'+field,bad,'required','/error/'+field)
   if field!='detailsDigest' and fixture['error'][field] is not None:
    bad=copy.deepcopy(fixture);bad['error'][field]=None;schema_reject(op+'/http-error-null/'+field,bad,'type','/error/'+field)
  for field,wrong in [('stableCode','UNDECLARED'),('classification','UNDECLARED'),('retryDirective','UNDECLARED')]:
   bad=copy.deepcopy(fixture);bad['error'][field]=wrong;schema_reject(op+'/http-error-wrong/'+field,bad,'const','/error/'+field)
  bad=copy.deepcopy(fixture);bad['statusCode']=200;schema_reject(op+'/http-error-wrong-status',bad,'const','/statusCode')
  for field in ['requestId','correlationId','logicalOperationId']:
   bad=copy.deepcopy(fixture);bad[field]='not-uuid';schema_reject(op+'/http-bad-server-id/'+field,bad,'format','/'+field)
  for unknown in ['MODEL_SAYS_SUCCESS','SCHEMA_MODEL_SAYS_SUCCESS','ARTIFACT_MODEL_SAYS_SUCCESS','TARGET_MODEL_SAYS_SUCCESS','PARENT_JOB_MODEL_SAYS_SUCCESS','OBJECT_REFERENCE_MODEL_SAYS_SUCCESS','SECRET_REFERENCE_MODEL_SAYS_SUCCESS','FOLLOW_UP_MODEL_SAYS_SUCCESS']:
   reject_projection(op+'/unknown-diagnostic/'+unknown,op,unknown,'/error')
 conflict=projection('secret.create',ContractFailure('STABLE_NAME_UNAVAILABLE','$.stableName'));conflict['operationId']='generation.job.create';schema_reject('generation/http-reject-secret-only-stable-name-error',conflict,'not','/error/stableCode')
 try:projection('generation.job.create',ContractFailure('STABLE_NAME_UNAVAILABLE','$.stableName'));check('generation/projector-secret-only-error-rejected',False)
 except ContractFailure as exc:check('generation/projector-secret-only-error-rejected',{'code':exc.code,'pointer':exc.pointer},{'code':'HTTP_FAILURE_OPERATION_MISMATCH','pointer':'/operationId'})
 check('input-source-unchanged',hashlib.sha256(SSOT.read_bytes()).hexdigest(),source_sha);check('input-support-unchanged',{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in support_paths},support_sha)
 report={'sourceDocumentSha256':source_sha,'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'supportSha256':support_sha,'resourceSha256':{p:rs[p]['sha256'] for p in ['contracts/create-operation-design.schema.json','contracts/create-completion.json']},'scope':__doc__,'authority':['SSOT §12.48','SSOT §49.4','SSOT §32.6','contracts/create-completion.json#/errorPredicates','contracts/create-operation-design.schema.json#/$defs/HttpCreateFailure'],'witnesses':positives,'checked':len(checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'wholeOperationsClosed':[],'runtimeAcceptance':'NOT_EVALUATED','remaining':['Actual HTTP server and preadmission authentication implementation','Structured Secret and parent/target admission policies','Full persistence/read/consumer pipeline']}
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/create-review-negatives');out.mkdir(parents=True,exist_ok=True);(out/'create-http-errors.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['sourceDocumentSha256','checked','failed']}))
 for c in checks:
  if not c['passed']:print(json.dumps(c))
 return int(bool(report['failed']))
if __name__=='__main__':raise SystemExit(main())
