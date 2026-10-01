from pathlib import Path
import sys,json,copy,hashlib,subprocess
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'));sys.dont_write_bytecode=True
from ssot_sources import SSOT,resource_index
from create_completion_contracts import canonical_digest,semantic_result
from verify_create_completion import witnesses
source=SSOT.read_bytes();rs=resource_index();rows={x['operationId']:x for x in json.loads(rs['contracts/payload-contracts.json']['raw'])['records']};design=json.loads(rs['contracts/create-operation-design.schema.json']['raw']);checks=[];u='abcdef12-3456-4789-8abc-abcdef123456'
def rec(id,ok,**kw):checks.append({'id':id,'passed':bool(ok),**kw})
def negative(id,validator,baseline,mutate):
 validator.validate(baseline);bad=copy.deepcopy(baseline);mutate(bad)
 try:validator.validate(bad);rec(id,False,diagnostic='ACCEPTED')
 except ValidationError as e:rec(id,True,validator=e.validator,path=list(e.absolute_path))
for op in ['generation.job.create','secret.create']:
 base,_=witnesses(op,rows[op]);err={'stableCode':'IDEMPOTENCY_CONFLICT','classification':'CONFLICT','retryDirective':'DO_NOT_RETRY','message':'Retained terminal detail unavailable','detailsDigest':None,'machineReason':'RESULT_RETAINED_AS_TOMBSTONE'};r=copy.deepcopy(base);r.update(status='FAILED',terminal=True,output=None,stateVersion=None,eventSequence=None,activationEpoch=None,error=err);r['resultDigest']=canonical_digest(semantic_result(r));v=Draft202012Validator(rows[op]['responseSchema'],format_checker=FormatChecker());v.validate(r);rec(op+'/response/retained-positive',True)
 for name,fn in [('wrong-reason',lambda x:x['error'].update(machineReason='SILENT_CREATE_NEW')),('wrong-classification',lambda x:x['error'].update(classification='VALIDATION')),('wrong-retry',lambda x:x['error'].update(retryDirective='RETRY_SAME_OPERATION')),('wrong-code',lambda x:x['error'].update(stableCode='CREATE_INPUT_INVALID')),('nonterminal',lambda x:x.update(terminal=False)),('extra-error',lambda x:x['error'].update(authority=True)),('sensitive-output',lambda x:x.update(output={'value':'synthetic-forbidden-echo'})),('sensitive-error-field',lambda x:x['error'].update(value='synthetic-forbidden-echo'))]:negative(op+'/response/'+name,v,r,fn)
 legacy=copy.deepcopy(r);del legacy['error']['machineReason'];v.validate(legacy);rec(op+'/response/reason-remains-optional',True)
 for key in ['stableCode','classification','retryDirective','message','detailsDigest']:negative(op+'/response/missing-required-'+key,v,r,lambda x,key=key:x['error'].pop(key))
 h={'operationId':op,'requestId':u,'correlationId':u,'logicalOperationId':u,'statusCode':409,'error':copy.deepcopy(err)};hv=Draft202012Validator(design['$defs']['HttpCreateFailure'],format_checker=FormatChecker());hv.validate(h);rec(op+'/HTTP/retained-positive',True)
 for name,fn in [('wrong-reason',lambda x:x['error'].update(machineReason='OTHER')),('wrong-classification',lambda x:x['error'].update(classification='VALIDATION')),('wrong-retry',lambda x:x['error'].update(retryDirective='RECONCILE_THEN_RETRY')),('wrong-status',lambda x:x.update(statusCode=400)),('extra-terminal',lambda x:x.update(terminal=False)),('sensitive-response-field',lambda x:x.update(value='synthetic-forbidden-echo'))]:negative(op+'/HTTP/'+name,hv,h,fn)
 old=copy.deepcopy(h);del old['error']['machineReason'];hv.validate(old);rec(op+'/HTTP/reason-remains-optional',True)
# Authoring checks execute actual root scripts read-only, do not replace their source.
commands=[]
for script in ['close_create_completion.py','close_create_operation_requests.py','close_secret_retention_contract.py']:
 p=subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--check'],cwd=ROOT,capture_output=True,text=True,timeout=90);commands.append({'command':[script,'--check'],'exitCode':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()});rec('authoring/'+script,p.returncode==0)
# New proposed stream was deliberately not integrated.
rec('new-command-stream-not-in-canonical-contract',b'domain.command.outcome.updated'not in rs['contracts/create-completion.json']['raw'] and b'domain.command.outcome.updated'not in rs['contracts/payload-contracts.json']['raw'])
rec('source-unchanged',source==SSOT.read_bytes())
report={'sourceSha256':hashlib.sha256(source).hexdigest(),'status':'PASS'if all(x['passed']for x in checks)else'BLOCKED','checked':len(checks),'failed':sum(not x['passed']for x in checks),'checks':checks,'commands':commands,'resources':{p:rs[p]['sha256']for p in ['contracts/create-completion.json','contracts/create-operation-design.schema.json','contracts/payload-contracts.json']},'supportHashes':{p:hashlib.sha256((ROOT/'scripts'/p).read_bytes()).hexdigest()for p in ['create_completion_contracts.py','close_create_completion.py','close_create_operation_requests.py','close_secret_retention_contract.py']},'scope':'Actual canonical definition masks/authoring only. Field-based sensitive echo is rejected; message confidentiality remains the safe producer contract, not a claim arbitrary strings can be forbidden by JSON Schema. No new command stream/retention PG/runtime producer activation.','wholeOperationClosed':False,'implementationAcceptance':'NOT_EVALUATED'};(OUT/'integrated-retained-mask-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['sourceSha256','status','checked','failed']}));raise SystemExit(report['failed']!=0)
