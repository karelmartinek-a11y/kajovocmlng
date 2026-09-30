"""Current native FOLLOW_UP content/declared-final tests, values never reported."""
import copy,hashlib,json,sys
from pathlib import Path
from native_follow_up_fixture import factory,validate_declared_final_output
from generation_admission_contracts import ContractFailure,validate_follow_up_content,canonical,digest,GEN
from ssot_sources import SSOT,ROOT,load_resource
OUT=Path(__file__).resolve().parent
start=hashlib.sha256(SSOT.read_bytes()).hexdigest();ids=['00000000-0000-4000-8000-'+str(i).zfill(12) for i in range(1,7)];OTHER='00000000-0000-4000-8000-000000000099';checks=[]
def positive(name,fn):
 try:fn();checks.append({'case':name,'passed':True})
 except Exception as e:checks.append({'case':name,'passed':False,'unexpected':type(e).__name__+':'+str(e)})
def negative(name,fn,code,pointer=None):
 try:fn();checks.append({'case':name,'passed':False,'expectedCode':code,'actualCode':'ACCEPTED'})
 except ContractFailure as e:checks.append({'case':name,'passed':e.code==code and (pointer is None or pointer==e.pointer),'expectedCode':code,'actualCode':e.code,'expectedPointer':pointer,'actualPointer':e.pointer})
 except Exception as e:checks.append({'case':name,'passed':False,'expectedCode':code,'unexpected':type(e).__name__+':'+str(e)})
for kind in ['INITIAL_REQUEST','SPECIFICATION_REVISION','PUBLISHED_FINAL_OUTPUT']:
 b,s,key=factory(kind,*ids);r=s['sourceSnapshots'][key];repo=s['generationBasisRepository']
 positive(kind+'/actual-native-content',lambda:validate_follow_up_content(b,r['recordId'],repo))
 for raw,code,pointer in [(b'{"jobId":"one","jobId":"two"}','GENERATION_BASIS_DUPLICATE_JSON_KEY','/jobId'),(b'{"jobId":','GENERATION_BASIS_JSON_INVALID','')]:
  b2,s2,k2=factory(kind,*ids);r2=s2['sourceSnapshots'][k2];r2['bytes']=raw;r2['contentDigest']=digest(raw);b2['followUpBasis']['expectedDigest']=r2['contentDigest']
  negative(kind+'/'+code,lambda:validate_follow_up_content(b2,r2['recordId'],s2['generationBasisRepository']),code,pointer)
 b2,s2,k2=factory(kind,*ids);r2=s2['sourceSnapshots'][k2];r2['owner']='other-owner'
 negative(kind+'/actual-owner',lambda:validate_follow_up_content(b2,r2['recordId'],s2['generationBasisRepository']),'GENERATION_BASIS_OWNER_MISMATCH')
b,s,key=factory('PUBLISHED_FINAL_OUTPUT',*ids)
positive('FINAL/actual-declared-native-output',lambda:validate_declared_final_output(b,s['generationBasisRepository'],s['finalOutputDeclarations']))
negative('FINAL/missing-declaration',lambda:validate_declared_final_output(b,s['generationBasisRepository'],{}),'GENERATION_FINAL_OUTPUT_DECLARATION_UNAVAILABLE')
decls=copy.deepcopy(s['finalOutputDeclarations']);decls[key[:1]+(ids[4],)]['resultContractArtifactId']=OTHER
negative('FINAL/wrong-source-result-contract',lambda:validate_declared_final_output(b,s['generationBasisRepository'],decls),'GENERATION_FINAL_RESULT_CONTRACT_REFERENCE_MISMATCH')
repo=copy.deepcopy(s['generationBasisRepository']);schemaid='10000000-0000-4000-8000-000000000001';repo.records[schemaid]['bytes']=repo.records[schemaid]['bytes']+b' '
negative('FINAL/actual-consumer-schema-bytes',lambda:validate_declared_final_output(b,repo,s['finalOutputDeclarations']),'GENERATION_FINAL_OUTPUT_SCHEMA_BYTES_MISMATCH')
# An actual syntactically valid native monitoring artifact is not this declared
# final ArtifactManifest. Update all digests/receipt to avoid unrelated rejection.
b,s,key=factory('PUBLISHED_FINAL_OUTPUT',*ids);repo=s['generationBasisRepository'];record=s['sourceSnapshots'][key];bundle=json.loads(load_resource('contracts/generation/generation-contracts.schema.json')['raw']);defs=copy.deepcopy(bundle['$defs'])
from verify_phase2_handoffs import witness
for name,v in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-30T00:00:00.000Z','RelPath':'synthetic.json','JsonPointer':'','NonemptyJsonPointer':'/synthetic'}.items():defs[name]={'const':v}
monitor=witness(defs['EvidenceRecord'],defs);record['bytes']=canonical(monitor);record['contentDigest']=digest(record['bytes']);record['artifactKind']='MONITORING_EVIDENCE';record['schema']['definition']='EvidenceRecord';b['followUpBasis']['expectedDigest']=record['contentDigest']
receipt_record=repo.records[ids[5]];receipt=json.loads(receipt_record['bytes']);receipt['contentDigest']=record['contentDigest'];receipt_record['bytes']=canonical(receipt);receipt_record['contentDigest']=digest(receipt_record['bytes']);s['finalOutputDeclarations'][(ids[1],ids[4])]['contentDigest']=record['contentDigest']
positive('FINAL/mutant-monitoring-native-shape-valid',lambda:repo.artifact(ids[4],record['contentDigest'],job_id=ids[1]))
negative('FINAL/monitoring-is-not-declared-manifest-output',lambda:validate_declared_final_output(b,repo,s['finalOutputDeclarations']),'GENERATION_FINAL_OUTPUT_CONSUMER_SCHEMA_INVALID')
end=hashlib.sha256(SSOT.read_bytes()).hexdigest()
report={'ssotSha256':start,'sourceUnchangedDuringProof':start==end,'checkCount':len(checks),'failedCount':sum(not c['passed'] for c in checks),'checks':checks,'proofKind':'CURRENT_SYNTHETIC_NATIVE_FOLLOW_UP_CONTENT_AND_DECLARED_FINAL_SLOT',
 'supportSha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),OUT/'native_follow_up_fixture.py',ROOT/'scripts/generation_admission_contracts.py',ROOT/'scripts/create_operation_contracts.py',ROOT/'scripts/follow_up_contracts.py']},
 'scopeExclusions':['SQL producer publication-slot/FK/locking/closure enforcement is not established by this reference','Nested final artifact manifests still require downstream full graph/hydration proofs'],'implementationAcceptance':'NOT_EVALUATED'}
(OUT/'native-follow-up-content-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failed':report['failedCount'],'sourceUnchanged':start==end}))
for c in checks:
 if not c['passed']:print(json.dumps(c))
sys.exit(1 if report['failedCount'] or start!=end else 0)
