from pathlib import Path
import sys,json,hashlib,copy
ROOT=Path('/workspace/kajovocmlng');AUTHOR=ROOT/'audit/generated/closure-replan-84c/family-read/core-audit';OWN=Path(__file__).parent
sys.path[:0]=[str(AUTHOR),str(ROOT/'scripts')]
from ssot_sources import SSOT,resource_index
source=hashlib.sha256(SSOT.read_bytes()).hexdigest()
inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in AUTHOR.iterdir() if p.is_file() and p.suffix in ('.py','.json','.md')}
program=(AUTHOR/'verify_core_audit.py').read_text().replace('core_audit_read_84c','peer_core_audit_read_84c')
old=Path.write_text
def write(self,data,*a,**kw):
 if self.is_relative_to(AUTHOR):self=OWN/self.name
 return old(self,data,*a,**kw)
Path.write_text=write
try:
 ns={'__file__':str(AUTHOR/'verify_core_audit.py'),'__name__':'__main__'};exec(compile(program,str(AUTHOR/'verify_core_audit.py'),'exec'),ns)
finally:Path.write_text=old
assert hashlib.sha256(SSOT.read_bytes()).hexdigest()==source
report=json.loads((OWN/'core-audit-tests.json').read_text());assert report['failed']==0
from core_audit_reference import inspect,AuditError
pre=copy.deepcopy(ns['row'])
for k in ['domainEventId','aggregateId','aggregateKind','eventType','eventSchemaId','eventSchemaDigest','eventPayloadBytesBase64','eventPayloadDigest']:pre[k]=None
try:inspect(pre)
except AuditError as e:assert str(e)=='AUDIT_RECORD_MASK_INVALID'; fault=str(e)
else:raise AssertionError('non-event pending unexpectedly supported')
review={'sourceSha256':source,'candidateDigestsAtExecution':inputs,'authorChecks':report['checked'],'failed':0,'ownCounterexample':{'case':'legitimate-before-root-command-outcome-audit','maskResult':fault,'classification':'REPRODUCED_CONTRACT_SCOPE_DEFECT','authority':'SSOT §12.54 / database/generation-create-preroot.sql','limitation':'Definition counterexample; separate read-only actual physical row inspection recorded independently.'},'wholeOperationsClosed':0}
(OWN/'peer-review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps({'checks':report['checked'],'source':source,'counterexample':fault}))
