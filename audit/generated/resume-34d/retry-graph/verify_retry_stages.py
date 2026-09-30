from pathlib import Path
import sys,copy,json,hashlib
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(1,str(ROOT/'audit/generated/resume-d362/admission'))
from generation_retry_inventory_fixtures import fixture,ids,INVENTORY
from retry_inventory_staged import verify_retry_inventory,source_json,canonical,digest,ContractFailure
checks=[]
def call(f,stage):return verify_retry_inventory(f[0],f[1],f[2],f[3],INVENTORY,f[4],f[5],f[6],stage)
def put(f,key,edit):
 r=f[0].records[key];v=source_json(r['bytes']);edit(v);r['bytes']=canonical(v);r['contentDigest']=digest(r['bytes']);return r['contentDigest']
def rebind(f,state='CONFIRMED_NOT_APPLIED'):
 ed=put(f,ids(523),lambda v:v.update(outcome=state));sd=put(f,ids(522),lambda v:v.update(state=state,evidenceDigest=ed));od=put(f,ids(520),lambda v:v.update(state=state));f[5][ids(520)]=od
 f[4]=put(f,INVENTORY,lambda v:v['operations'][0].update(operationDigest=od,attemptStateDigest=sd))
 return f
def pos(name,f,stage,decision):
 try:r=call(f,stage);checks.append({'case':name,'passed':r['selectedTechnicalPartEffectDecisions'][0]['decision']==decision and r['permitsExternalDispatch']is False})
 except Exception as e:checks.append({'case':name,'passed':False,'actual':str(e)})
def neg(name,f,stage,code):
 try:call(f,stage);checks.append({'case':name,'passed':False,'actual':'ACCEPTED'})
 except ContractFailure as e:checks.append({'case':name,'passed':e.code==code,'actual':e.code,'expected':code})
f=list(fixture());pos('known-not-applied/discussion',f,'ADMISSION_DISCUSSION','REUSE_KNOWN_NOT_APPLIED_OPERATION_AND_TARGET_KEY')
f=list(fixture());pos('known-not-applied/dispatch-still-not-authorized',f,'EXECUTION_DISPATCH','REUSE_KNOWN_NOT_APPLIED_OPERATION_AND_TARGET_KEY')
f=list(fixture());f[3]['nodes'][0]['retryClass']='NO_AUTOMATIC_RETRY';pd=digest(canonical(f[3]));f[1]['planDigest']=pd;f[2]=digest(canonical(f[1]));put(f,ids(520),lambda v:v.update(retryClass='NO_AUTOMATIC_RETRY'));f[5][ids(520)]=f[0].records[ids(520)]['contentDigest'];f[4]=put(f,INVENTORY,lambda v:(v.update(phaseRunDigest=f[2]),v['operations'][0].update(operationDigest=f[5][ids(520)])))
pos('no-auto-retry/discussion',f,'ADMISSION_DISCUSSION','ADMIT_DISCUSSION_WITH_NO_AUTOMATIC_RETRY');neg('no-auto-retry/dispatch-policy-unresolved',f,'EXECUTION_DISPATCH','GENERATION_RETRY_MANUAL_DISPATCH_POLICY_UNRESOLVED')
f=list(fixture());put(f,ids(523),lambda v:v['observations'].update(afterVersion='8',appliedOperationId=ids(520)));rebind(f,'CONFIRMED_APPLIED')
pos('applied-effect/discussion-preserves-no-repeat',f,'ADMISSION_DISCUSSION','PRESERVE_CONFIRMED_EFFECT_NO_REPEAT');neg('applied-effect/repeat-dispatch-forbidden',f,'EXECUTION_DISPATCH','GENERATION_RETRY_CONFIRMED_EFFECT_REPEAT_FORBIDDEN')
f=list(fixture());rebind(f,'UNKNOWN');neg('unknown/not-completed-source/discussion',f,'ADMISSION_DISCUSSION','GENERATION_RETRY_EFFECT_RECONCILIATION_REQUIRED');neg('unknown/dispatch',f,'EXECUTION_DISPATCH','GENERATION_RETRY_EFFECT_RECONCILIATION_REQUIRED')
f=list(fixture());neg('unknown-stage-rejected',f,'CURRENT','GENERATION_RETRY_STAGE_INVALID')
report={'status':'PASS'if all(c['passed']for c in checks)else'BLOCKED','checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'stageInterpretation':'§12.51 ADMIT_DISCUSSION is not §49.8 dispatch authority; known outcomes retain no-repeat/no-auto policy rather than requiring new dispatch policy to create discussion. Unknown source eligibility remains blocked by effective §12.51 source known-failure requirement.','normativeStatus':'PROPOSED_STAGE_SPECIALIZATION_NOT_EFFECTIVE_UNTIL_COORDINATOR_REVIEW','wholeOperationClosed':False,'supportSha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),OUT/'retry_inventory_staged.py',ROOT/'scripts/generation_retry_inventory.py']}}
(OUT/'retry-stage-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':report['checked'],'failed':report['failed']}));sys.exit(bool(report['failed']))
