"""Actual resumable runner invalidation, restoring original proof before return."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
proof=ROOT/'audit/generated/resume-905/archive/review-joined/joined-chain-proof.json'
commands=ROOT/'audit/generated/repair-2026-09-30/design-current/commands.json'
original=proof.read_bytes();initial=json.loads(commands.read_text());checks=[];stages=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(label):
 r=subprocess.run([sys.executable,'scripts/run_ssot_repair_design_checks.py','--resume','--workers','3'],cwd=ROOT,capture_output=True,text=True,timeout=300)
 (HERE/(label+'.log')).write_text(r.stdout+r.stderr)
 q=json.loads(commands.read_text());executed=[json.loads(l)['script']for l in r.stdout.splitlines()if l.startswith('{')]
 stages.append({'label':label,'exitCode':r.returncode,'executed':executed,'reused':len(q['commands'])-len(executed),'sourceSha256':q['sourceSha256'],'commandsSha256':sha(commands)})
 return q,executed
try:
 q,executed=run('cache-clean')
 checks.append({'case':'unchanged-all49-proof-results-reused','passed':q['allCommandsFinished']and not executed})
 changed=json.loads(original);changed['sourceDocumentSha256']='0'*64;proof.write_text(json.dumps(changed,indent=2)+'\n')
 q,executed=run('cache-stale-proof')
 c=next(x for x in q['commands']if x['script']=='scripts/verify_producer_archive_handoffs.py')
 tests=json.loads((ROOT/'audit/generated/repair-2026-09-30/design-current/verify_producer_archive_handoffs/producer-archive-chain-tests.json').read_text())
 checks.append({'case':'changed-required-proof-invalidates-only-connected-consumer','passed':executed==['scripts/verify_producer_archive_handoffs.py']and c['exitCode']==1})
 checks.append({'case':'stale-execution-source-specifically-blocked','passed':any(x['case']=='joined/current-execution-source'and not x['passed']for x in tests['checks'])})
 (HERE/'cache-stale-proof-result.json').write_text(json.dumps(tests,indent=2)+'\n')
finally:
 proof.write_bytes(original)
 q,executed=run('cache-restored-proof')
 checks.append({'case':'restored-proof-reruns-only-connected-consumer-and-passes','passed':executed==['scripts/verify_producer_archive_handoffs.py']and next(x for x in q['commands']if x['script']=='scripts/verify_producer_archive_handoffs.py')['exitCode']==0})
 checks.append({'case':'proof-exactly-restored','passed':proof.read_bytes()==original})
 checks.append({'case':'original-seven-blockers-unchanged','passed':{x['script']for x in q['commands']if x['exitCode']!=0}=={x['script']for x in initial['commands']if x['exitCode']!=0}})
 report={'sourceDocumentSha256':sha(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md'),'status':'PASS'if all(x['passed']for x in checks)else'BLOCKED','checks':checks,'checked':len(checks),'failed':sum(not x['passed']for x in checks),'stages':stages,'proofRestoredSha256':sha(proof),'scope':'Cache acceptance of a changed real consumed independent proof, not additional domain closure','wholeOperationClosed':False}
 (HERE/'connected-cache-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));sys.exit(report['failed']!=0)
