"""Resumable explicit design-check universe; never certifies unreviewed contracts."""
import argparse,hashlib,importlib.metadata,json,os,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from ssot_sources import ROOT,SSOT
CHECKS=[
 'phase1_schema_closure.py','verify_schema_references.py','verify_phase1_contracts.py',
 'verify_phase2_handoffs.py','verify_phase3_semantics.py','verify_phase4_ui.py',
 'verify_acceptance_gates.py','verify_authority_excerpt_coverage.py','verify_component_protocol_examples.py',
 'verify_create_completion.py','verify_create_http_errors.py','verify_follow_up_contracts.py','verify_create_operation_requests.py','verify_config_rollback_state.py','verify_backup_restore_state.py','verify_control_counter_masks.py','verify_errors.py','verify_experience.py',
 'verify_generation_atomic_model.py','verify_generation_document_events.py','verify_generation_domain_payloads.py',
 'verify_generation_event_boundaries.py','verify_generation_http_contract.py','verify_generation_operation_masks.py',
 'verify_generation_read_design.py','verify_generation_read_errors.py','verify_mask_parity.py',
 'verify_native_manifest_continuation.py','verify_observability.py','verify_operation_sql_literals.py',
 'verify_plan_create_handoff.py','verify_preserved_policy.py','verify_provider_mapping.py',
 'verify_provider_outcome_mask.py','verify_read_boundary_completion.py','verify_retry_profile.py',
 'verify_route_guard_counters.py','verify_saga_handoffs.py','verify_transitive_mask_detection.py',
 'verify_create_storage_invariants.py','verify_visual_contracts.py','run_baseline_gates.py','verify_package.py']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

EVIDENCE_INPUTS={
 'verify_phase4_ui.py':['audit/phase4-ui-action-matrix.json','audit/phase4-current-handoff-matrix.json','audit/phase4-unresolved.json'],
 'verify_package.py':['audit/visual-validation.json'],
}
def evidence_inputs_hash(name):
 h=hashlib.sha256()
 for relative in EVIDENCE_INPUTS.get(name,[]):
  path=ROOT/relative
  h.update(relative.encode()+b'\0'+(path.read_bytes() if path.exists() else b'MISSING')+b'\0')
 return h.hexdigest()

def produced_json_hashes(name):
 # Evidence consumers join dedicated per-check JSON reports. Missing, changed
 # or unexpected reports invalidate cached results even when log bytes match.
 directory=ROOT/'audit/generated/repair-2026-09-30/design-current'/Path(name).stem
 return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(directory.rglob('*.json')) if p.is_file()}

def main():
 p=argparse.ArgumentParser();p.add_argument('--resume',action='store_true');p.add_argument('--workers',type=int,default=2);a=p.parse_args()
 out=ROOT/'audit/generated/repair-2026-09-30/design-current';out.mkdir(parents=True,exist_ok=True)
 source=sha(SSOT);deps=sha(ROOT/'requirements-audit.txt');target=out/'commands.json'
 support=hashlib.sha256()
 for base in ['scripts','01_UI_CONTRACT','03_UI_REFERENCE']:
  for path in sorted((ROOT/base).rglob('*')):
   if path.is_file() and '__pycache__' not in path.parts:
    support.update(path.relative_to(ROOT).as_posix().encode()+b'\0'+path.read_bytes()+b'\0')
 support_hash=support.hexdigest()
 packages={line.split('==')[0]:importlib.metadata.version(line.split('==')[0])
  for line in (ROOT/'requirements-audit.txt').read_text().splitlines() if '==' in line}
 environment_hash=hashlib.sha256(json.dumps({'python':sys.version,'packages':packages},sort_keys=True).encode()).hexdigest()
 records={}
 if a.resume and target.exists():
  for r in json.loads(target.read_text()).get('commands',[]):
   if 'producedEvidenceHashes' in r and r['producedEvidenceHashes']==produced_json_hashes(Path(r['script']).name) and r.get('evidenceInputsSha256')==evidence_inputs_hash(Path(r['script']).name) and (ROOT/r['evidence']).is_file() and r.get('evidenceLogSha256')==sha(ROOT/r['evidence']) and r.get('sourceSha256')==source and r.get('supportInputsSha256')==support_hash and r.get('environmentSha256')==environment_hash and r.get('requirementsSha256')==deps and r.get('scriptSha256')==sha(ROOT/r['script']):records[r['script']]=r
 def save():
  report={'sourceSha256':source,'requirementsSha256':deps,'supportInputsSha256':support_hash,'environmentSha256':environment_hash,'installedAuditPackages':packages,'python':sys.version,'requiredChecks':CHECKS,
   'commands':list(records.values()),'allCommandsFinished':len(records)==len(CHECKS),
   'scope':'Explicit available design regression tools and six legacy resource validators; normative per-operation semantic, SQL helper/runtime and full pipeline obligations remain separately required.',
   'SSOT_CONTRACT_READY':'BLOCKED','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED',
   'excluded':'No freeze flag, application generation, paid API, production, release or deployment execution. Inventory/receipt verified after evidence writes.'}
  temporary=ROOT/'.cache/repair-commands.json'
  temporary.parent.mkdir(parents=True,exist_ok=True)
  temporary.write_text(json.dumps(report,indent=2)+'\n');temporary.replace(target)
 def run(name):
  script='scripts/'+name;args=[sys.executable,script]+(['--skip-manifest'] if name=='verify_package.py' else [])
  begun=time.monotonic();log=out/(name+'.log');input_hash=evidence_inputs_hash(name)
  try:
   r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=240,
    env={**os.environ,'KCML_AUDIT_OUTPUT':str(out/name.removesuffix('.py')),'PYTHONUTF8':'1'})
   log.write_text(r.stdout+r.stderr)
   diagnostic='VALIDATOR_EXCEPTION' if 'Traceback (most recent call last)' in r.stderr else 'PASS' if r.returncode==0 else 'CHECK_FAILED_OR_BLOCKED'
   code=r.returncode
  except subprocess.TimeoutExpired as exc:
   log.write_text((exc.stdout or b'').decode(errors='replace')+(exc.stderr or b'').decode(errors='replace'));diagnostic='TIMEOUT';code=None
  if evidence_inputs_hash(name)!=input_hash:diagnostic='EVIDENCE_INPUT_CHANGED';code=1
  return {'script':script,'command':' '.join(args[1:]),'sourceSha256':source,'requirementsSha256':deps,
   'evidenceInputsSha256':input_hash,'producedEvidenceHashes':produced_json_hashes(name),'producedEvidenceScope':'Dedicated per-check JSON reports; log and consumed input hashes verified separately','evidenceLogSha256':sha(log),'scriptSha256':sha(ROOT/script),'supportInputsSha256':support_hash,'environmentSha256':environment_hash,'exitCode':code,'diagnostic':diagnostic,'seconds':round(time.monotonic()-begun,2),'evidence':str(log.relative_to(ROOT))}
 save()
 with ThreadPoolExecutor(max_workers=a.workers) as pool:
  tasks=[pool.submit(run,n) for n in CHECKS if 'scripts/'+n not in records]
  for task in as_completed(tasks):
   r=task.result();records[r['script']]=r;save();print(json.dumps({k:r[k] for k in ['script','exitCode','diagnostic']}),flush=True)
   if sha(SSOT)!=source:raise ValueError('SSOT_INPUT_CHANGED')
 return int(any(r['exitCode']!=0 for r in records.values()))
if __name__=='__main__':raise SystemExit(main())
