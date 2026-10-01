from pathlib import Path
import sys,os,runpy,json,hashlib
ROOT=Path('/workspace/kajovocmlng');OWN=Path(__file__).parent
phase=sys.argv[1];names=sys.argv[2:];sys.path.insert(0,str(ROOT/'scripts'));sys.argv=['review']
from ssot_sources import SSOT
source=hashlib.sha256(SSOT.read_bytes()).hexdigest();result=[]
for n in names:
 script=OWN/'before'/n if phase=='before'else ROOT/'scripts'/n
 out=OWN/phase/n.removesuffix('.py');out.mkdir(parents=True,exist_ok=True)
 os.environ['KCML_AUDIT_OUTPUT']=str(out)
 old=Path.write_text
 def write(self,data,*a,**kw):
  if self==ROOT/'audit/generated/preserved-policy.json':self=out/'preserved-policy.json'
  return old(self,data,*a,**kw)
 Path.write_text=write
 try:
  try:runpy.run_path(str(script),run_name='__main__');code=0
  except SystemExit as e:code=int(e.code or 0)
 finally:Path.write_text=old
 result.append({'script':n,'scriptSha256':hashlib.sha256(script.read_bytes()).hexdigest(),'exit':code,'output':str(out)})
assert source==hashlib.sha256(SSOT.read_bytes()).hexdigest()
(OWN/phase/'execution.json').write_text(json.dumps({'sourceSha256':source,'scripts':result},indent=2)+'\n')
