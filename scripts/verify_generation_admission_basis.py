"""Current selector/native-byte proof, strict HTTP and finite diagnostic projection."""
import copy,hashlib,json,os,sys
from pathlib import Path
from ssot_sources import ROOT,SSOT,resource_index
import generation_admission_contracts as g
from create_operation_contracts import admit,decode_http,ContractFailure
from create_completion_contracts import http_failure
BASE=ROOT/'audit/generated/resume-d362/admission'
def main():
 source=SSOT.read_bytes();rs=resource_index();sys.path.insert(0,str(BASE));sys.modules['generation_admission_reference']=g
 import generation_admission_fixtures as f
 assert f.gen_raw==rs['contracts/generation/generation-contracts.schema.json']['raw'],'NATIVE_FIXTURE_SCHEMA_STALE'
 namespace=vars(f).copy();namespace['__file__']=str(BASE/'verify_generation_admission_reference.py')
 program=(BASE/'verify_generation_admission_reference.py').read_text().split("report={'inputCommit':",1)[0]
 exec(compile(program,str(BASE/'verify_generation_admission_reference.py'),'exec'),namespace)
 checks=namespace['checks']
 import generation_retry_inventory as retry
 sys.modules['generation_retry_inventory']=retry
 retry_ns={'__file__':str(BASE/'verify_generation_retry_inventory.py')}
 retry_program=(BASE/'verify_generation_retry_inventory.py').read_text().split("report={'proofKind':",1)[0]
 exec(compile(retry_program,str(BASE/'verify_generation_retry_inventory.py'),'exec'),retry_ns)
 checks.extend(retry_ns['checks'])
 check_bundle=retry.bundle()
 assert json.loads(rs['contracts/generation/retry-inventory.schema.json']['raw'])==check_bundle
 records=copy.deepcopy(f.records)
 local_raw=rs['contracts/generation/admission-basis.schema.json']['raw'];new_lb=g.digest(local_raw)
 def replace(v,mapping):
  if isinstance(v,str):return mapping.get(v,v)
  if isinstance(v,list):return [replace(x,mapping) for x in v]
  if isinstance(v,dict):return {k:replace(x,mapping) for k,x in v.items()}
  return v
 mapping={f.lb:new_lb}
 for _ in range(4):
  next_map={}
  for rec in records.values():
   rec['schema']=replace(rec['schema'],mapping);old=rec['contentDigest'];value=replace(g.source_json(rec['bytes']),mapping);rec['bytes']=g.canonical(value);rec['contentDigest']=g.digest(rec['bytes'])
   if old!=rec['contentDigest']:next_map[old]=rec['contentDigest']
  mapping.update(next_map)
 bodies=replace(copy.deepcopy(f.bodies),mapping)
 def check(name,ok):checks.append({'case':name,'passed':bool(ok)})
 for kind,body in bodies.items():
  repository=g.Repository.from_current_ssot(copy.deepcopy(records),'synthetic-owner',{f.TARGET:{'snapshotId':f.SNAP,'contentDigest':records[f.SNAP]['contentDigest']}})
  server={'owner':'synthetic-owner','actor':'OWNER','authenticated':True,'recovery':'READY','targets':{f.TARGET:{'objectId':f.TARGET,'kind':'PLATFORM_COMPONENT'}},'jobs':{f.JOB:{'jobId':f.JOB}},'generationBasisRepository':repository}
  headers=[('Content-Type','application/json'),('Idempotency-Key','current-native-'+kind)]
  request=decode_http('generation.job.create','POST','/generation/jobs',[],headers,g.canonical(body));result=admit(request,server)
  check(kind+'/HTTP-to-current-registry-admission',result['generationAdmission']['decision']=='ADMIT_DISCUSSION')
  check(kind+'/frozen-actual-byte-closure',bool(result['generationAdmission']['frozenInputs']))
  try:decode_http('generation.job.create','POST','/generation/jobs',[('unknown','x')],headers,g.canonical(body));check(kind+'/query',False)
  except ContractFailure as e:check(kind+'/query',e.code=='UNKNOWN_QUERY_PARAMETER' and e.pointer=='/query')
  try:admit(request,{**server,'owner':'different-owner'});check(kind+'/server-repository-owner',False)
  except ContractFailure as e:check(kind+'/server-repository-owner',e.code=='GENERATION_BASIS_OWNER_MISMATCH')
 diagnostics=json.loads(rs['contracts/generation/admission-diagnostics.json']['raw'])['diagnostics']
 for row in diagnostics:
  result=http_failure('generation.job.create',ContractFailure(row['diagnostic'],'/synthetic'),request_id=f.JOB,correlation_id=f.TARGET)
  check('diagnostic/'+row['diagnostic'],result['error']['stableCode']==row['stableCode'] and result['statusCode']==row['httpStatus'])
 try:http_failure('generation.job.create',ContractFailure('GENERATION_NOT_DECLARED'),request_id=f.JOB,correlation_id=f.TARGET);check('unknown-diagnostic-fail-closed',False)
 except ContractFailure as e:check('unknown-diagnostic-fail-closed',e.code=='HTTP_FAILURE_PROJECTION_UNRESOLVED')
 assert source==SSOT.read_bytes(),'SSOT_INPUT_CHANGED'
 report={'sourceDocumentSha256':hashlib.sha256(source).hexdigest(),'checked':len(checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'scope':__doc__,'resourceSha256':{p:rs[p]['sha256'] for p in ['contracts/generation/admission-basis.schema.json','contracts/generation/admission-diagnostics.json','contracts/create-operation-design.schema.json','contracts/generation/generation-contracts.schema.json']},'supportSha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE/'generation_admission_fixtures.py',BASE/'verify_generation_admission_reference.py',ROOT/'scripts/generation_admission_contracts.py',ROOT/'scripts/generation_basis_selectors.py',ROOT/'scripts/generation_retry_inventory.py',ROOT/'scripts/create_operation_contracts.py']},'wholeOperationClosure':False,'remaining':'Complete graph/monitoring consumer predicates, secret-source/navigation/ephemeral policies, physical auth/crypto/atomic fixture joins remain required','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/resume-d362/coordinator');out.mkdir(parents=True,exist_ok=True);(out/'generation-admission-current-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['checked','failed','sourceDocumentSha256']}))
 for c in checks:
  if not c['passed']:print(json.dumps(c))
 return int(bool(report['failed']))
if __name__=='__main__':raise SystemExit(main())
