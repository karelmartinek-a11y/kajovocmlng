from native_auth_factory import *
sys.path.insert(0,str(ROOT/'audit/generated/resume-d362/admission'))
from generation_retry_inventory_fixtures import fixture,INVENTORY,ib,ids
from generation_locked_retry_admission import hydrate_locked_scan
from generation_admission_contracts import ContractFailure
checks=[]
def scan_for(outcome):
 repo,phase,rd,plan,ind,physical,classifiers=fixture()
 op=strict_json(repo.records[ids(520)]['bytes']);st=strict_json(repo.records[ids(522)]['bytes']);ev=strict_json(repo.records[ids(523)]['bytes'])
 if outcome=='CONFIRMED_APPLIED':
  op['state']=outcome;st['state']=outcome;ev['outcome']=outcome;ev['observations']['appliedOperationId']=op['operationId'];ev['observations']['afterVersion']='8'
  ed='sha256:'+sha(canonical_bytes(ev)).hex();st['evidenceDigest']=ed
  for id,val in [(ids(520),op),(ids(522),st),(ids(523),ev)]:repo.records[id].update(bytes=canonical_bytes(val),contentDigest='sha256:'+sha(canonical_bytes(val)).hex())
 rows={}
 for prefix,key in [('operation',ids(520)),('attempt',ids(521)),('state',ids(522)),('evidence',ids(523))]:
  r=repo.records[key];rows.update({prefix+'Id':key,prefix+'Bytes':r['bytes'].hex(),prefix+'Digest':r['contentDigest'][7:]})
 return repo,{'phaseBytes':canonical_bytes(phase).hex(),'phaseDigest':rd[7:],'rows':[rows]},plan,classifiers
for outcome in ['CONFIRMED_NOT_APPLIED','CONFIRMED_APPLIED']:
 repo,scan,plan,classifiers=scan_for(outcome)
 admission=hydrate_locked_scan(repo,scan,INVENTORY,'2026-09-30T00:00:00.000Z',ib,plan,classifiers,stage='ADMISSION_DISCUSSION')
 checks.append({'case':outcome+'-discussion-admitted','passed':admission['contentDecision']['decision']=='SOURCE_PHASE_EFFECT_INVENTORY_CONTENT_VALIDATED'})
 try:
  hydrate_locked_scan(repo,scan,INVENTORY,'2026-09-30T00:00:00.000Z',ib,plan,classifiers,stage='EXECUTION_DISPATCH');ok=outcome=='CONFIRMED_NOT_APPLIED';code=None
 except ContractFailure as e:code=e.code;ok=outcome=='CONFIRMED_APPLIED'and code=='GENERATION_RETRY_CONFIRMED_EFFECT_REPEAT_FORBIDDEN'
 checks.append({'case':outcome+'-execution-own-policy','passed':ok,'actualDiagnostic':code})
 try:hydrate_locked_scan(repo,scan,INVENTORY,'2026-09-30T00:00:00.000Z',ib,plan,classifiers,stage='OTHER');ok=False
 except ContractFailure as e:code=e.code;ok=code=='GENERATION_RETRY_STAGE_INVALID'
 checks.append({'case':outcome+'-invalid-stage','passed':ok,'actualDiagnostic':code})
assert all(x['passed']for x in checks),checks
report={'status':'PASS','checked':len(checks),'checks':checks,'sourceDocumentSha256':sha(SSOT.read_bytes()).hex(),'candidateSha256':sha(Path(__file__).with_name('generation_locked_retry_admission.py').read_bytes()).hex(),'scope':'Isolated valid-positive-derived admission vs execution semantics; synthetic evidence is not a producer proof','wholeOperationClosed':False}
Path(__file__).with_name('admission-stage-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':len(checks),'status':'PASS'}))
