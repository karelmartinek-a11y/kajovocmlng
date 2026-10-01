"""Independent positive-derived mutations on owned copies of the actual SSOT.

The global ssot_sources path is redirected before module import; merely changing
one verifier's SSOT variable would miss resource_index() callers.
"""
import sys,subprocess,copy,json,hashlib,os
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');O=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resources,resource_index
from author_resource_updates import rewrite
ENTRY=SSOT.read_bytes();RS=resource_index(resources(ENTRY.decode()));cases=[]
PAYLOAD='contracts/payload-contracts.json';STATE='closure/contracts/operation-payloads.json';OWN='closure/contracts/operation-state-receipts.json'
PY=sys.executable
runner="""import sys;from pathlib import Path;sys.path.insert(0,sys.argv[3]);import ssot_sources;ssot_sources.SSOT=Path(sys.argv[1]);import importlib;m=importlib.import_module(sys.argv[2]);sys.argv=[sys.argv[0]]+(['--check']if hasattr(m,'PATCH')else[]);raise SystemExit(m.run() if hasattr(m,'run')else m.main())"""
def call(id,path,doc,module,check):
 source=O/(id+'.md');source.write_text(rewrite(ENTRY.decode(),list(resources(ENTRY.decode())),{path:(json.dumps(doc,ensure_ascii=False)+'\n').encode()}))
 out=O/'mutation-reports'/id;out.mkdir(parents=True,exist_ok=True)
 p=subprocess.run([PY,'-c',runner,str(source),module,str(ROOT/'scripts')],cwd=ROOT,text=True,capture_output=True,env={**os.environ,'KCML_AUDIT_OUTPUT':str(out)},timeout=180)
 log=p.stdout+p.stderr;(O/(id+'.log')).write_text(log)
 result={'id':id,'script':module+'.py','passed':bool(check(p,log,out)),'exit':p.returncode,'diagnostic':log[-1000:],'mutantSourceSha256':hashlib.sha256(source.read_bytes()).hexdigest()};cases.append(result);source.unlink();print(id,result['passed'])
def rejected_message(text):return lambda p,log,out:p.returncode!=0 and text in log
def failed_case(name):
 def check(p,log,out):
  files=list(out.glob('*.json'))
  for f in files:
   r=json.loads(f.read_text())
   if any(x.get('case')==name and x.get('passed')is False for x in r.get('checks',[])):return p.returncode!=0
  return False
 return check
payload=json.loads(RS[PAYLOAD]['raw'])
m=copy.deepcopy(payload);row=next(r for r in m['records']if r['operationId']not in ['generation.job.create','secret.create','secret.metadata.read','secret.value.read'] and not r['operationId'].startswith(('owner.session.','audit.event.')));route=row['routeId'];row['authContract']='UNAUTHORIZED_READ_AUTH_REPLACEMENT';call('unrelated-route-auth-mutant',PAYLOAD,m,'verify_route_guard_counters',rejected_message('Unexpected change beyond guard domains: '+route))
m=copy.deepcopy(payload);row=next(r for r in m['records']if r['routeId']=='route.0452');row['eventSchema']['additionalProperties']=True;call('audit-event-extra-field-mutant',PAYLOAD,m,'verify_route_guard_counters',rejected_message('Unexpected change beyond guard domains: route.0452'))
m=copy.deepcopy(payload);row=next(r for r in m['records']if r['operationId']=='owner.session.revoke');row['requestSchema']['properties']['guards']['properties']['expectedStateVersion'].pop('pattern',None)
call('owner-counter-pattern-removal',PAYLOAD,m,'verify_route_guard_counters',lambda p,log,out:p.returncode!=0 and any(json.loads(f.read_text()).get('failed',0)>0 for f in out.glob('*.json')))
m=copy.deepcopy(payload);row=next(r for r in m['records']if r['operationId']=='owner.session.list');row['responseSchema']['additionalProperties']=True;call('source-reviewed-owner-family-not-blanket-allowed',PAYLOAD,m,'verify_create_operation_requests',failed_case('authoring/unrelated-routes-byte-shape-preserved'))
m=copy.deepcopy(payload);row=next(r for r in m['records']if r['routeId']=='route.0451');row['eventSchema']['properties']['payload']['additionalProperties']=True;call('source-reviewed-audit-family-not-blanket-allowed',PAYLOAD,m,'verify_create_operation_requests',failed_case('authoring/unrelated-routes-byte-shape-preserved'))
m=json.loads(RS[STATE]['raw']);row=next(r for r in m['records']if r['operationId']=='acceptance.run.cancel');row['responseSchema']['allOf']=[];call('cancel-tuple-guard-removal',STATE,m,'verify_operation_state_receipts',failed_case('cancel/reject-terminal-cleanupStatusPENDING'))
m=json.loads(RS[STATE]['raw']);row=next(r for r in m['records']if r['operationId']=='chat.turn.steer');row['responseSchema']['properties']['checkpointDisposition'].update(const='UNSPECIFIED');call('state-enum-silent-extension',STATE,m,'verify_operation_state_receipts',failed_case('chat.turn.steer.checkpointDisposition/own-mask'))
m=json.loads(RS['manifest.json']['raw']);m['resources'][OWN]['sizeBytes']+=1;call('own-manifest-size-still-blocked','manifest.json',m,'close_operation_state_receipts',rejected_message('manifest.json#/resources/'+OWN))
m=json.loads(RS['manifest.json']['raw']);m['resourceCount']+=1
call('global-count-scoped-pass-disclosed','manifest.json',m,'close_operation_state_receipts',lambda p,log,out:p.returncode==0 and json.loads(p.stdout)['globalManifestResourceCountMatches']is False and json.loads(p.stdout)['status']=='PASS')
report={'sourceDocumentSha256':hashlib.sha256(ENTRY).hexdigest(),'sourceUnchanged':SSOT.read_bytes()==ENTRY,'checked':len(cases),'failed':sum(not c['passed']for c in cases),'cases':cases,'scriptsSha256':{s:hashlib.sha256((ROOT/'scripts'/s).read_bytes()).hexdigest()for s in ['verify_route_guard_counters.py','verify_create_operation_requests.py','verify_operation_state_receipts.py','close_operation_state_receipts.py']},'classification':'ACTUAL_LOCAL_SOURCE_MUTATIONS; no current canonical or Git mutations'}
(O/'independent-mutation-tests.json').write_text(json.dumps(report,indent=2)+'\n');print('mutation checks',len(cases),'failed',report['failed']);raise SystemExit(report['failed']!=0)
