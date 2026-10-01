"""Independent adversarial execution of retained consumer candidate, no peer writes."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];HERE=Path(__file__).parent
PEER=ROOT/'audit/generated/resume-905/consumers'
sys.path[:0]=[str(ROOT/'scripts'),str(PEER),str(ROOT/'audit/generated/resume-d362/consumers')]
source=(PEER/'verify_terminal_read.py').read_text();ns={'__file__':str(PEER/'verify_terminal_read.py')};exec(source.split('\nfor action in OPS:')[0],ns)
import owner_ui_terminal_read
assert Path(owner_ui_terminal_read.__file__).resolve()==ROOT/'scripts/owner_ui_terminal_read.py'
assert (ROOT/'scripts/owner_ui_terminal_read.py').read_bytes()==(PEER/'owner_ui_terminal_read.py').read_bytes(),'CANONICAL_CONSUMER_CANDIDATE_BYTE_MISMATCH'
checks=[];defects=[]
def check(name,ok,**data):checks.append(dict(id=name,status='PASS'if ok else'FAIL',**data))
def sign(f):
 f[0]['resultDigest']=ns['outcome_digest'](f[0]);f[1]=ns['event'](f[0]);raw=json.dumps(f[0]['output'],separators=(',',':')).encode();f[3].update(resultBytes=raw,contentDigest=ns['digest'](raw))
def reject(action,f,expected):
 try:ns['run'](action,f);return False,'ACCEPTED'
 except ns['ContractFailure']as e:return e.code==expected,e.code
for action in ns['OPS']:
 f=ns['fixture'](action);positive=ns['run'](action,f);check(action+'/valid-domain-selected-reference-positive',positive['display']=='BLOCKED_PENDING_EFFECT_HYDRATION')
 bad=copy.deepcopy(f);bad[0]['output']['jobId'if action=='gen.editSpec'else'runtimeInstanceId']=ns['THIRD'];sign(bad)
 retained={k:bad[3][k]for k in ['workerOperationId','parentLogicalOperationId','intentId']};retained.update(bytes=bad[3]['resultBytes'],contentDigest=bad[3]['contentDigest'])
 old=ns['validate_outcome'](action,bad[0],bad[1],retained_worker_receipt=retained)
 good,actual=reject(action,bad,'OWNER_UI_WORKER_TARGET_MISMATCH');check(action+'/actual-old-self-consistent-wrong-target-now-rejected',old=='DISPLAY_CANONICAL_OUTCOME'and good,oldAcceptance=old,currentDiagnostic=actual,positiveWitness=action+'/valid-domain-selected-reference-positive')
 if action!='gen.editSpec':
  for field,value in [('runtimeInstanceId',ns['THIRD']),('runtimeGeneration','3')]:
   bad=copy.deepcopy(f);bad[2]['workerArguments'][field]=value
   good,actual=reject(action,bad,'OWNER_UI_WORKER_ARGUMENT_BINDING_MISMATCH')
   check(action+'/worker-arguments-'+field,good,actualDiagnostic=actual,positiveWitness=action+'/valid-domain-selected-reference-positive')
   if not good:defects.append(dict(action=action,field=field,actual=actual,required='workerArguments selected runtime identity/generation equals accepted intent arguments; output to correct intent cannot excuse command sent to different target'))
 else:
  bad=copy.deepcopy(f);bad[0]['output']['revisionId']=bad[2]['arguments']['expectedRevisionId'];sign(bad)
  good,actual=reject(action,bad,'OWNER_UI_NEW_DRAFT_REUSES_BASE_REVISION');check(action+'/new-draft-must-not-reuse-base',good,actualDiagnostic=actual)
  bad=copy.deepcopy(f);bad[0]['output'].update(outcome='SAME_CANONICAL_REVISION',revisionId=bad[2]['arguments']['expectedRevisionId'],specificationDigest=bad[2]['arguments']['expectedSpecificationDigest']);bad[0]['output'].pop('state');bad[0]['output'].pop('diffArtifactId');bad[0]['output'].pop('requirementCoverageArtifactId');sign(bad)
  good,actual=reject(action,bad,'OWNER_UI_BASE_REVISION_PRODUCER_UNRESOLVED');check(action+'/same-canonical-explicit-historical-block',good,actualDiagnostic=actual)
report=dict(sourceSha256=hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),effectiveHelperSha256=hashlib.sha256((ROOT/'scripts/owner_ui_terminal_read.py').read_bytes()).hexdigest(),reviewer='sql_helpers; not consumer designer',checks=checks,failed=sum(c['status']!='PASS'for c in checks),defects=defects,scope='Actual reference adapter execution with three independently adversarial selected-target successes, runtime command argument mutations and draft/same-canonical negatives; no producer/SQL/runtime proof.')
(HERE/'independent-consumer-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(checks=len(checks),failed=report['failed'],defects=defects)))
