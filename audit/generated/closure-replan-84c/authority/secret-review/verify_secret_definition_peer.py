from pathlib import Path
import sys,json,copy,hashlib
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;AUTHOR=ROOT/'audit/generated/closure-replan-84c/secret';sys.path[:0]=[str(AUTHOR),str(ROOT/'scripts')];sys.dont_write_bytecode=True
source=(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes();program=(AUTHOR/'verify_definition_package.py').read_bytes();original_write=Path.write_text
writes=[]
def owned_write(p,data,*args,**kw):
 dest=OUT/p.name;writes.append(str(dest));return original_write(dest,data,*args,**kw)
Path.write_text=owned_write
try:ns={'__file__':str(AUTHOR/'verify_definition_package.py')};exec(compile(program,str(AUTHOR/'verify_definition_package.py'),'exec'),ns)
finally:Path.write_text=original_write
assert len(ns['cases'])==14 and all(x['status']=='PASS'for x in ns['cases'])
schema=json.loads((AUTHOR/'retained-command-outcome.proposed.schema.json').read_text())['payload'];validate=Draft202012Validator(schema,format_checker=FormatChecker()).validate
u='abcdef12-3456-4789-8abc-abcdef123456';digest='sha256:'+'a'*64;error={'stableCode':'CREATE_INPUT_INVALID','classification':'VALIDATION','retryDirective':'DO_NOT_RETRY','message':'Synthetic invalid input','detailsDigest':None};w={'operationId':'secret.create','logicalOperationId':u,'acceptedContextId':u,'operationContractRevision':'synthetic-revision','requestDigest':digest,'schemaArchiveDigest':digest,'policyArchiveDigest':digest,'outcomeSequence':'1','state':'FAILED_FINAL','terminal':True,'secretId':None,'output':None,'error':error,'evidenceDigest':digest,'recordedAt':'2026-10-01T00:00:00Z'}
validate(w);checks=[{'id':'exact-rootless-final-failure-positive','passed':True}]
for id,mut in [('invented-root',lambda x:x.update(secretId=u)),('success-output-on-failure',lambda x:x.update(output={'secretId':u})),('zero-stream-sequence',lambda x:x.update(outcomeSequence='0')),('retryable-as-final',lambda x:x['error'].update(retryDirective='RETRY_SAME_OPERATION')),('cancel-as-failure',lambda x:x['error'].update(stableCode='CREATE_CANCELLED',classification='CANCELLED')),('unknown-as-final',lambda x:x['error'].update(stableCode='SIDE_EFFECT_OUTCOME_UNKNOWN',classification='UNKNOWN',retryDirective='RECONCILE_THEN_RETRY'))]:
 validate(w);bad=copy.deepcopy(w);mut(bad)
 try:validate(bad);checks.append({'id':id,'passed':False,'accepted':True})
 except ValidationError as e:checks.append({'id':id,'passed':True,'validator':e.validator,'path':list(e.absolute_path)})
unknown=copy.deepcopy(w);unknown.update(state='WAITING_FOR_RECONCILIATION',terminal=False,error={'stableCode':'SIDE_EFFECT_OUTCOME_UNKNOWN','classification':'UNKNOWN','retryDirective':'RECONCILE_THEN_RETRY','message':'Synthetic unknown outcome','detailsDigest':None});validate(unknown);checks.append({'id':'unknown-rootless-nonterminal-positive','passed':True});assert len(checks)==8
# Original valid tombstone proposal, one-factor terminal mutation.
validate_response=Draft202012Validator(ns['proposed'],format_checker=FormatChecker()).validate;validate_response(ns['tomb']);bad=copy.deepcopy(ns['tomb']);bad['terminal']=False
try:validate_response(bad);terminal_result={'id':'tombstone-reason-on-nonterminal','accepted':True}
except ValidationError as e:terminal_result={'id':'tombstone-reason-on-nonterminal','accepted':False,'validator':e.validator,'path':list(e.absolute_path)}
report={'sourceSha256':hashlib.sha256(source).hexdigest(),'sourceUnchanged':source==(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes(),'originalDefinitionCases':ns['cases'],'retainedDefinitionCases':checks,'reproducedChecks':22,'failed':sum(not x['passed']for x in checks),'additionalPeerObservation':terminal_result,'inputs':{n:hashlib.sha256((AUTHOR/n).read_bytes()).hexdigest()for n in ['contract_delta.py','NORMATIVE_DELTA.md','response-with-retained-reason.proposed.schema.json','retained-command-outcome.proposed.schema.json','verify_definition_package.py']},'scope':'Original14 definition fixtures plus independently constructed matching8 retained schema cases only; no new SQL/event namespace/lock producer approval.','wholeOperationClosed':False,'implementationAcceptance':'NOT_EVALUATED'}
(OUT/'definition-peer-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'reproducedChecks':22,'failed':report['failed'],'observation':terminal_result}))
