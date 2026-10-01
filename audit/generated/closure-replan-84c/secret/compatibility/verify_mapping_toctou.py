"""Runtime selected-map mutations after valid import; no filesystem proof edits."""
from pathlib import Path
import hashlib,json,os,sys
R=Path('/workspace/kajovocmlng');D=Path(__file__).parent;sys.path.insert(0,str(R/'scripts'))
import verify_producer_archive_handoffs as m
selected=R/m.PROOF_MAPPING;raw=selected.read_bytes();exists=Path.exists;read=Path.read_bytes;checks=[]
def run(case):
 out=D/'map-toctou'/case;os.environ['KCML_AUDIT_OUTPUT']=str(out.relative_to(R));e=m.main();q=json.loads((out/'producer-archive-chain-tests.json').read_text());return e,q
exit,q=run('valid-positive');checks.append({'case':'valid-positive-123-preserved','passed':exit==0 and q['checked']==123 and q['failed']==0})
changed=json.loads(raw);changed['joined']=changed['retry'];changed=json.dumps(changed).encode()
for case,replacement,diagnostic in [('missing',None,'REQUIRED_EVIDENCE_MAP_MISSING'),('malformed',b'{','JSONDecodeError'),('changed-complete-eight-labels',changed,'EVIDENCE_MAP_CHANGED_SINCE_IMPORT')]:
 try:
  if replacement is None:Path.exists=lambda p:False if p==selected else exists(p)
  else:Path.read_bytes=lambda p:replacement if p==selected else read(p)
  exit,q=run(case)
  failed={c['case']for c in q['checks']if not c['passed']};err=next(c for c in q['evidence']if c['path']==m.PROOF_MAPPING)['diagnostic']
  checks.append({'case':case,'passed':exit!=0 and q['status']=='BLOCKED' and failed=={'complete-selected-evidence-map'} and diagnostic in err,'checked':q['checked'],'failedCases':sorted(failed),'actualDiagnostic':err})
 finally:Path.exists=exists;Path.read_bytes=read
report={'sourceDocumentSha256':hashlib.sha256((R/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'validatorSha256':hashlib.sha256((R/'scripts/verify_producer_archive_handoffs.py').read_bytes()).hexdigest(),'checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'actualMapUnchanged':selected.read_bytes()==raw,'wholeOperationClosed':False};(D/'map-toctou-tests.json').write_text(json.dumps(report,indent=2)+'\n');raise SystemExit(report['failed']!=0)
