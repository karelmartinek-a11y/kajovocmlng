"""Native actual ledger positives and exact side-effect inventory mutants."""
import copy,hashlib,json,sys
from pathlib import Path
from generation_admission_fixtures import *
from generation_retry_inventory import *
from ssot_sources import SSOT
OUT=Path(__file__).resolve().parent
from generation_retry_inventory_fixtures import *
checks=[]
def positive(name,fn):
 try:fn();checks.append({'case':name,'passed':True})
 except Exception as e:checks.append({'case':name,'passed':False,'unexpected':type(e).__name__+':'+str(e)})
def negative(name,fn,code):
 try:fn();checks.append({'case':name,'passed':False,'actualCode':'ACCEPTED','expectedCode':code})
 except ContractFailure as e:checks.append({'case':name,'passed':e.code==code,'actualCode':e.code,'expectedCode':code,'pointer':e.pointer})
 except Exception as e:checks.append({'case':name,'passed':False,'unexpected':type(e).__name__+':'+str(e),'expectedCode':code})
def rewrite(f,key,edit):
 repo=f[0];r=repo.records[key];v=source_json(r['bytes']);edit(v);r['bytes']=canonical(v);r['contentDigest']=digest(r['bytes']);return r['contentDigest']
positive('actual/nonempty-owned-phase-operation-attempt-evidence',lambda:call(fixture()))
f=list(fixture());older=f[0].records[ids(530)]
f[4]=rewrite(f,INVENTORY,lambda v:v['operations'][0].update(attemptStateId=ids(530),attemptStateDigest=older['contentDigest']))
negative('actual/valid-older-same-attempt-state-cannot-replace-current',lambda:call(f),'GENERATION_RETRY_CURRENT_ATTEMPT_STATE_DRIFT')
f=list(fixture());sd=rewrite(f,ids(522),lambda v:v.update(stateVersion='1'));f[4]=rewrite(f,INVENTORY,lambda v:v['operations'][0].update(attemptStateDigest=sd))
negative('actual/same-current-state-id-stale-version',lambda:call(f),'GENERATION_RETRY_CURRENT_ATTEMPT_STATE_DRIFT')
f=list(fixture());f[5]={}
negative('actual/declared-inventory-vs-empty-physical-scan',lambda:call(f),'GENERATION_RETRY_INVENTORY_INCOMPLETE')
f=list(fixture());f[0].records.pop(INVENTORY)
negative('actual/missing-required-inventory',lambda:call(f),'GENERATION_RETRY_INVENTORY_UNAVAILABLE')
f=list(fixture());f[4]=rewrite(f,INVENTORY,lambda v:v.update(operations=[]))
negative('actual/empty-list-cannot-hide-real-operation',lambda:call(f),'GENERATION_RETRY_INVENTORY_INCOMPLETE')
for state in ['INTENT_RECORDED','DISPATCHING','OUTCOME_RECORDED','RECONCILING','UNKNOWN']:
 f=list(fixture());od=rewrite(f,ids(520),lambda v,state=state:v.update(state=state));sd=rewrite(f,ids(522),lambda v,state=state:v.update(state=state));f[5][ids(520)]=od;f[4]=rewrite(f,INVENTORY,lambda v:v['operations'][0].update(operationDigest=od,attemptStateDigest=sd))
 negative('actual/'+state+'-even-when-phase-pending-empty',lambda f=f:call(f),'GENERATION_RETRY_EFFECT_RECONCILIATION_REQUIRED')
f=list(fixture());sd=rewrite(f,ids(522),lambda v:v.update(state='CONFIRMED_APPLIED'));f[4]=rewrite(f,INVENTORY,lambda v:v['operations'][0].update(attemptStateDigest=sd))
negative('actual/operation-attempt-state-drift',lambda:call(f),'GENERATION_RETRY_ATTEMPT_STATE_DRIFT')
f=list(fixture());ad=rewrite(f,ids(521),lambda v:v.update(targetIdempotencyKey='different-target-key'));f[4]=rewrite(f,INVENTORY,lambda v:v['operations'][0].update(attemptDigest=ad))
negative('actual/attempt-target-key-drift',lambda:call(f),'GENERATION_RETRY_ATTEMPT_BINDING_DRIFT')
f=list(fixture());ed=rewrite(f,ids(523),lambda v:v['observations'].update(afterVersion='8',appliedOperationId=ids(520)));sd=rewrite(f,ids(522),lambda v:v.update(evidenceDigest=ed));f[4]=rewrite(f,INVENTORY,lambda v:v['operations'][0].update(attemptStateDigest=sd))
negative('actual/receipt-claims-not-applied-but-readback-shows-applied',lambda:call(f),'GENERATION_RETRY_OUTCOME_CLASSIFIER_MISMATCH')
f=list(fixture());f[6]={}
negative('actual/undeclared-domain-classifier',lambda:call(f),'GENERATION_RETRY_OUTCOME_CLASSIFIER_UNRESOLVED')
f=list(fixture());f[0].records[CLASSIFIER_ID]['bytes']=b'def classify(o,p,a): return True\n'
negative('actual/wrong-classifier-bytes',lambda:call(f),'GENERATION_RETRY_OUTCOME_CLASSIFIER_DIGEST_MISMATCH')
# A classifier returning a generic validity flag is never a known outcome.
f=list(fixture());raw=b'def classify(o,p,a): return True\n';f[0].records[CLASSIFIER_ID]['bytes']=raw;f[0].records[CLASSIFIER_ID]['contentDigest']=digest(raw);ed=rewrite(f,ids(523),lambda v:v.update(classifierDigest=digest(raw)));sd=rewrite(f,ids(522),lambda v:v.update(evidenceDigest=ed));f[4]=rewrite(f,INVENTORY,lambda v:v['operations'][0].update(attemptStateDigest=sd))
f[6]['SyntheticCASReadBack']['activeSourceDigest']=digest(raw)
f[6]['SyntheticCASReadBack']['evaluate']=lambda observation,operation,attempt:True
negative('actual/generic-valid-flag-is-not-outcome-proof',lambda:call(f),'GENERATION_RETRY_OUTCOME_CLASSIFIER_MISMATCH')
f=list(fixture());f[5]=None
negative('actual/missing-physical-scan-is-blocked',lambda:call(f),'GENERATION_RETRY_PHYSICAL_SCAN_UNVERIFIED')
f=list(fixture());f[6]=None
negative('actual/missing-declared-consumer-context-is-blocked',lambda:call(f),'GENERATION_RETRY_OUTCOME_CLASSIFIER_UNRESOLVED')
f=list(fixture());f[6]['SyntheticCASReadBack'].pop('sourceRecordId')
negative('context/incomplete-consumer-declaration-blocked',lambda:call(f),'GENERATION_RETRY_OUTCOME_CLASSIFIER_DECLARATION_INVALID')
def unavailable_classifier(observation,operation,attempt):raise RuntimeError('synthetic unavailable consumer; not sensitive data')
f=list(fixture());f[6]['SyntheticCASReadBack']['evaluate']=unavailable_classifier
negative('context/consumer-execution-unavailable-blocked-not-domain-proof',lambda:call(f),'GENERATION_RETRY_OUTCOME_CLASSIFIER_EXECUTION_FAILED')
report={'proofKind':'SYNTHETIC_NATIVE_LEDGER_BYTES_AND_ACTUAL_PINNED_CAS_READBACK_CLASSIFIER','fixtureSourceCommit':PIN,'fixtureNativeBundleDigest':gb,'fixtureLocalProposalBundleDigest':lb,'inventoryProposalBundleDigest':ib,'coordinatorSsotSha256AtExecution':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'checkCount':len(checks),'failedCount':sum(not c['passed'] for c in checks),'checks':checks,
 'consumedClassifierDigest':digest(CLASSIFIER),'supportSha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),OUT/'generation_retry_inventory.py',OUT/'generation_admission_fixtures.py',OUT/'generation_retry_inventory_fixtures.py',ROOT/'scripts/generation_admission_contracts.py']},
 'physicalProof':'NOT_EVALUATED_REQUIRED_POSTGRESQL_LOCKED_TABLE_SCAN_AND_PRODUCER_FKS','consumerScope':'One synthetic compare-and-set receipt/read-back consumer; no universal external consumer claim','runtimeAcceptance':'NOT_EVALUATED'}
(OUT/'retry-inventory-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(OUT/'retry-inventory.schema.json').write_text(json.dumps(bundle(),indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failed':report['failedCount']}))
for c in checks:
 if not c['passed']:print(json.dumps(c))
sys.exit(1 if report['failedCount'] else 0)
