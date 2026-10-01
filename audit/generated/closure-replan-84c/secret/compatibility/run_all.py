"""Fresh bounded reproduction of the eight existing handoff proof families."""
from pathlib import Path
import argparse,json,hashlib,subprocess,sys,os,datetime,importlib.util,signal
ROOT=Path('/workspace/kajovocmlng');HERE=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);parser.add_argument('--expected-source');parser.add_argument('--only',nargs='*');args=parser.parse_args()
assert args.run_id and all(c.isalnum()or c in '-_'for c in args.run_id),'INVALID_RUN_ID'
OUT=HERE/'runs'/args.run_id;OUT.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();SSOT=ROOT/'00_SSOT/KajovoCMLNG_SSOT.md';source=sha(SSOT)
if args.expected_source:assert source==args.expected_source,'SOURCE_DIFFERS_FROM_FROZEN_INPUT'
specs=json.loads((HERE/'bounded_spec.json').read_text());selected=args.only or list(specs);assert set(selected)<=set(specs)
state={'sourceDocumentSha256':source,'startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'labels':{},'wholeOperationClosed':False,'provider':'ENV_BLOCKED','scope':'Fresh actual bounded fixtures; no readiness/whole-operation inference.'}
proofs={}
for label in selected:
 assert sha(SSOT)==source,'SOURCE_CHANGED_BETWEEN_FAMILIES'
 labelout=OUT/label;labelout.mkdir();log=labelout/'execution.log'
 (OUT/'run-state.json').write_text(json.dumps(state,indent=2)+'\n')
 timed_out=False
 with log.open('w')as stream:
  child=subprocess.Popen([sys.executable,str(HERE/'run_bounded_fixture.py'),label,str(labelout)],cwd=ROOT,env={**os.environ,'PGOPTIONS':'-c client_min_messages=warning','PYTHONDONTWRITEBYTECODE':'1'},stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:child.wait(timeout=420);result=child
  except subprocess.TimeoutExpired:
   timed_out=True;os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
   result=type('TimedOut',(),{'returncode':124})();stream.write('BOUNDED_FIXTURE_TIMEOUT_420_SECONDS\n')
 manifest=labelout/'execution-manifest.json';path=labelout/'tree'/specs[label]['proof']
 if label=='archive':
  # Existing checker consumes the exact fixture source under proof-relative name.
  path.parent.mkdir(parents=True,exist_ok=True)
  (path.parent/'verify_archive.py').write_bytes((ROOT/specs[label]['scripts'][0]).read_bytes())
 if label=='secret'and result.returncode==0:
  sys.path.insert(0,str(ROOT/'scripts'));from ssot_sources import resource_index
  rs=resource_index();directory=path.parent;names=['publication-postgres-tests.json','owner-binding-postgres-tests.json','safe-role-postgres-tests.json','additional-tests.json'];subs={n:json.loads((directory/n).read_text())for n in names}
  assert all(q.get('failed')==0 and q.get('sourceSha256')==source and q.get('cases')for q in subs.values()),'SECRET_SUBPROOF_FAILED_OR_STALE'
  aggregate={'sourceSha256':source,'scope':'Fresh exact canonical Secret publication/OWNER binding bounded SQL fixtures; historical review artifact retained with its actual identity, no new semantic approval claimed.','postgresVersion':'18.6','counts':{n:subs[n]['checked']for n in names},'canonicalResources':{n:rs[n]['sha256']for n in ['database/secret-profile-roots.sql','database/secret-profile-publication.sql','database/secret-owner-binding.sql']},'reportsSha256':{n:sha(directory/n)for n in names},'wholeOperationClosed':False,'implementationAcceptance':'NOT_EVALUATED'}
  path.write_text(json.dumps(aggregate,indent=2)+'\n')
 status='EXECUTED'if result.returncode==0 and path.exists()else'BLOCKED'
 state['labels'][label]={'status':status,'exitCode':result.returncode,'timedOut':timed_out,'proof':str(path.relative_to(ROOT))if path.exists()else None,'proofSha256':sha(path)if path.exists()else None,'executionManifest':str(manifest.relative_to(ROOT))if manifest.exists()else None,'log':str(log.relative_to(ROOT))}
 proofs[label]=str(path.relative_to(ROOT))
 if path.exists():
  q=json.loads(path.read_text());recorded_failed=q.get('failed',q.get('failedCount',0))
  if recorded_failed:state['labels'][label]['status']='BLOCKED';state['labels'][label]['recordedFailedAssertions']=recorded_failed
 (OUT/'run-state.json').write_text(json.dumps(state,indent=2)+'\n');print(json.dumps({'label':label,'status':status,'exitCode':result.returncode}),flush=True)
 assert sha(SSOT)==source,'SOURCE_CHANGED_DURING_FAMILY'
(OUT/'EVIDENCE_MAPPING.json').write_text(json.dumps(proofs,indent=2)+'\n')
# Require the complete universe when running the shared checker, no silently omitted label.
if set(['joined','retry','archive','aad','secret','ui','preroot','retry-stage'])<=set(selected):
 module_path=ROOT/'scripts/verify_producer_archive_handoffs.py';sys.path.insert(0,str(ROOT/'scripts'));m=importlib.util.spec_from_file_location('actual_handoff_checker',module_path);checker=importlib.util.module_from_spec(m);m.loader.exec_module(checker);checker.PROOFS={k:v for k,v in proofs.items() if k in checker.PROOFS};os.environ['KCML_AUDIT_OUTPUT']=str(OUT.relative_to(ROOT));state['universeExitCode']=checker.main()
else:state['universeExitCode']=None
state['sourceUnchangedDuringRun']=sha(SSOT)==source;state['status']='PASS'if state['universeExitCode']==0 and state['sourceUnchangedDuringRun']else('PARTIAL'if set(selected)!=set(specs)and all(v['status']=='EXECUTED'for v in state['labels'].values())and state['sourceUnchangedDuringRun']else'BLOCKED')
(OUT/'run-state.json').write_text(json.dumps(state,indent=2)+'\n');print(json.dumps({'status':state['status'],'mapping':str(OUT/'EVIDENCE_MAPPING.json')}));raise SystemExit(int(state['status']=='BLOCKED'))
