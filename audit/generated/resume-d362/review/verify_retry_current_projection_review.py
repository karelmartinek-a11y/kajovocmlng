from pathlib import Path
import sys,json,hashlib
HERE=Path(__file__).parent; D=HERE.parent/'admission'
sys.path.insert(0,str(D));sys.path.insert(0,str(HERE.parents[3]/'scripts'))
import generation_retry_inventory_fixtures as f
from generation_retry_inventory import verify_retry_inventory,ContractFailure
cases=[]
def call(x):return verify_retry_inventory(x[0],x[1],x[2],x[3],f.INVENTORY,x[4],x[5],x[6])
def run(name,x,expected=None):
 try:r=call(x);actual=r['decision'];ok=expected is None
 except ContractFailure as e:actual=e.code;ok=actual==expected
 except Exception as e:actual=type(e).__name__+':'+str(e);ok=False
 cases.append({'id':name,'expected':expected or 'SOURCE_PHASE_EFFECT_INVENTORY_CONTENT_VALIDATED','actual':actual,'passed':ok})
run('actual-current-positive',f.fixture())
x=list(f.fixture());repo=x[0];r=repo.records[f.INVENTORY];v=f.source_json(r['bytes']);v['operations'][0].update(attemptStateId=f.ids(530),attemptStateDigest=repo.records[f.ids(530)]['contentDigest']);r['bytes']=f.canonical(v);r['contentDigest']=f.digest(r['bytes']);x[4]=r['contentDigest'];run('older-valid-same-attempt-and-state-projection',x,'GENERATION_RETRY_CURRENT_ATTEMPT_STATE_DRIFT')
x=list(f.fixture());repo=x[0];r=repo.records[f.ids(522)];v=f.source_json(r['bytes']);v['stateVersion']='1';r['bytes']=f.canonical(v);r['contentDigest']=f.digest(r['bytes']);inv=repo.records[f.INVENTORY];v=f.source_json(inv['bytes']);v['operations'][0]['attemptStateDigest']=r['contentDigest'];inv['bytes']=f.canonical(v);inv['contentDigest']=f.digest(inv['bytes']);x[4]=inv['contentDigest'];run('same-identity-old-version-valid-bytes',x,'GENERATION_RETRY_CURRENT_ATTEMPT_STATE_DRIFT')
report={'scope':'Independent real nonempty content reference using server-owned current operation/state JOIN snapshot; no actual PostgreSQL locked scan completeness proof. Old absent-selector finding corrected and reexecuted, not replayed by hash.','cases':cases,'checks':len(cases),'failed':sum(not c['passed']for c in cases),'consumed':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in [D/'generation_retry_inventory.py',D/'generation_retry_inventory_fixtures.py']},'wholeOperationClosed':False}
(HERE/'retry-current-projection-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(cases),'failed':report['failed']}))
