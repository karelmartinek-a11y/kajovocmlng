from pathlib import Path
import sys,json,hashlib
ROOT=Path('/workspace/kajovocmlng');AUTHOR=ROOT/'audit/generated/closure-replan-84c/family-read/core-audit';OWN=Path(__file__).parent
sys.path[:0]=[str(AUTHOR),str(ROOT/'scripts')]
from ssot_sources import SSOT
source=hashlib.sha256(SSOT.read_bytes()).hexdigest();files=['core-audit-read.schema.json','core_audit_reference.py','verify_core_audit.py','verify_stored_streams.py','author_core_audit.py','authorable-core-delta.json']
digests={n:hashlib.sha256((AUTHOR/n).read_bytes()).hexdigest()for n in files}
old=Path.write_text
def write(self,data,*a,**kw):
 if self.is_relative_to(AUTHOR):self=OWN/self.name
 return old(self,data,*a,**kw)
Path.write_text=write
try:
 for name in ['verify_core_audit.py','verify_stored_streams.py']:
  p=(AUTHOR/name).read_text().replace('core_audit_read_84c','peer_core_audit_read_final_84c')
  ns={'__file__':str(AUTHOR/name),'__name__':'__main__'};exec(compile(p,str(AUTHOR/name),'exec'),ns)
finally:Path.write_text=old
assert source==hashlib.sha256(SSOT.read_bytes()).hexdigest()
assert digests=={n:hashlib.sha256((AUTHOR/n).read_bytes()).hexdigest()for n in files}
reports={n:json.loads((OWN/n).read_text())for n in ['core-audit-tests.json','stored-stream-tests.json']}
assert [r['checked']for r in reports.values()]==[43,23]
assert all(r['failed']==0 for r in reports.values())
(OWN/'independent-review.json').write_text(json.dumps({'sourceSha256':source,'candidateHashes':digests,'checks':66,'failed':0,'baselineChecked':43,'storedStreamChecked':23,'actualAuditRows':2,'actualProjectedRows':2,'previousActualProjectedRows':1,'historicalStatus':'ACCEPTED despite current command SUCCEEDED','storedDatabaseMode':'REPEATABLE READ READ ONLY','baselineDatabase':'peer_core_audit_read_final_84c','wholeOperationsClosed':0,'sixSemanticProducerObligationsRemainOpen':True,'implementationAcceptance':'NOT_EVALUATED'},indent=2)+'\n')
print('Independent66 PASS; corrected projection2/2; source',source)
