from pathlib import Path
import sys,runpy,json,hashlib
ROOT=Path('/workspace/kajovocmlng');OWN=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
import ssot_sources
from close_secret_retention_contract import TEXT as RET
from close_owner_key_reveal_scope import TEXT as REV
from close_scoped_sql_helpers import TEXT as SQL
real=ssot_sources.SSOT;text=real.read_text();virtual=text
for norm in [RET,REV,SQL]:virtual=virtual.replace(norm,norm.replace('\n\n','\nREPRODUCED_INVALID_SUPPLEMENT\n',1),1)
header='### 8.3 Datový kontrakt secretu\n';assert header in virtual;virtual=virtual.replace(header,header+'REPRODUCED_UNAUTHORIZED_ORIGINAL_POLICY_CHANGE\n',1)
class Input:
 def read_text(self,**kw):return virtual
 def read_bytes(self):return virtual.encode()
ssot_sources.SSOT=Input();old=Path.write_text
out=OWN/'policy-mutation-result.json'
def write(self,data,*a,**kw):
 if self==ROOT/'audit/generated/preserved-policy.json':self=out
 return old(self,data,*a,**kw)
Path.write_text=write
try:
 try:runpy.run_path(str(ROOT/'scripts/verify_preserved_policy.py'),run_name='__main__')
 except SystemExit as e:assert e.code==1,e.code
finally:ssot_sources.SSOT=real;Path.write_text=old
report=json.loads(out.read_text());failed={c['section']for c in report['checks']if c['status']=='FAIL'}
assert {'8.17','8.18','51.39','8.3 Datový kontrakt secretu'} <= failed,failed
(OWN/'policy-mutation-review.json').write_text(json.dumps({'sourceSha256':hashlib.sha256(text.encode()).hexdigest(),'mutatedVirtualSourceSha256':hashlib.sha256(virtual.encode()).hexdigest(),'positiveDerived':True,'actualVerifierExit':1,'specificRejectedSections':sorted(failed),'requiredNamedRejections':4,'wholeOperationsClosed':0},indent=2)+'\n');print('Actual policy checker rejected all4 named supplement/original-policy violations')
