"""Actual updated verifier metamorphic rejections, using local source copies only."""
from pathlib import Path
import sys,json,copy,hashlib,subprocess,os
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index,resources
from author_resource_updates import rewrite
ENTRY=SSOT.read_bytes();rs=resource_index(resources(ENTRY.decode()));cases=[]
def run_case(name,path,doc,script,expected):
 fixture=OUT/(name+'.md');fixture.write_text(rewrite(ENTRY.decode(),list(resources(ENTRY.decode())),{path:(json.dumps(doc)+'\n').encode()}))
 command='import sys;from pathlib import Path;import '+script+' as m;m.SSOT=Path(sys.argv[1]);sys.argv=[sys.argv[0],"--check"] if sys.argv[2]=="check" else [sys.argv[0]];raise SystemExit(m.main())'
 result=subprocess.run([sys.executable,'-c',command,str(fixture),'check'if script=='close_operation_state_receipts'else'run'],cwd=ROOT/'scripts',text=True,capture_output=True,env={**os.environ,'KCML_AUDIT_OUTPUT':str(OUT/'mutant-reports')})
 actual=result.stdout+result.stderr;cases.append({'id':name,'passed':result.returncode!=0 and expected in actual,'expectedDiagnostic':expected,'returncode':result.returncode,'actualDiagnostic':actual[-1600:],'fixtureSha256':hashlib.sha256(fixture.read_bytes()).hexdigest()});fixture.unlink() # Only this generated local source copy; canonical/user files untouched.
payload=json.loads(rs['contracts/payload-contracts.json']['raw']);m=copy.deepcopy(payload);next(r for r in m['records']if r['operationId']=='owner.session.list')['requestSchema']['properties']['query']['additionalProperties']=True
run_case('owner-mask-mutation','contracts/payload-contracts.json',m,'verify_route_guard_counters','Unexpected change beyond guard domains: route.0018')
m=copy.deepcopy(payload);next(r for r in m['records']if r['operationId']=='audit.event.read')['responseSchema'].pop('allOf',None)
route=next(r['routeId']for r in m['records']if r['operationId']=='audit.event.read');run_case('audit-mask-mutation','contracts/payload-contracts.json',m,'verify_route_guard_counters','Unexpected change beyond guard domains: '+route)
m=json.loads(rs['manifest.json']['raw']);m['resources']['closure/contracts/operation-state-receipts.json']['sha256']='sha256:'+'0'*64
run_case('own-manifest-entry-mutation','manifest.json',m,'close_operation_state_receipts','manifest.json#/resources/closure/contracts/operation-state-receipts.json')
m=json.loads(rs['closure/contracts/operation-payloads.json']['raw']);row=next(r for r in m['records']if r['operationId']=='owner.mfa.reset');row['responseSchema']['required'].remove('enrollmentState')
run_case('own-state-required-mutation','closure/contracts/operation-payloads.json',m,'close_operation_state_receipts','REQUIRED_STATE_FIELD_REMOVED')
report={'sourceDocumentSha256':hashlib.sha256(ENTRY).hexdigest(),'sourceUnchanged':SSOT.read_bytes()==ENTRY,'cases':cases,'checked':len(cases),'failed':sum(not c['passed']for c in cases),'class':'ACTUAL_VERIFIER_LOCAL_SOURCE_MUTATIONS_NOT_RUNTIME','scriptsSha256':{p:hashlib.sha256((ROOT/'scripts'/p).read_bytes()).hexdigest()for p in ['verify_route_guard_counters.py','verify_create_operation_requests.py','verify_operation_state_receipts.py','close_operation_state_receipts.py']}};(OUT/'mutation-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':len(cases),'failed':report['failed']}));raise SystemExit(report['failed']!=0 or not report['sourceUnchanged'])
