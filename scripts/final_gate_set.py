"""Exact §73.7 final gate universe, with fail-closed structured invocation results."""
import hashlib,subprocess,sys
from pathlib import Path
FINAL_GATE_FAMILIES=(('R10','r10/scripts/verify_r10.py'),('R16','r16/scripts/verify_r16.py'),('UI','ui/scripts/verify_ui.py'),('CLOSURE','closure/scripts/verify_final_closure.py'),('R17','r17/scripts/verify_r17.py'))

def run_final_gates(entries,root,source,invoke=subprocess.run):
 results=[]
 for family,name in FINAL_GATE_FAMILIES:
  rows=[r for r in entries if r['path']==name and r['family']=='KCML-'+family+'-RESOURCE']
  def blocked(code,**detail):results.append({'family':family,'gate':name,'status':'BLOCKED','reason':code,**detail})
  if len(rows)!=1:blocked('MISSING_REQUIRED_GATE'if not rows else'DUPLICATE_REQUIRED_GATE');continue
  item=rows[0];actual=hashlib.sha256(item['raw']).hexdigest();declared=item.get('declared',item.get('attrs',{})).get('sha256')
  if actual!=item['sha256'] or declared!=actual:blocked('SCRIPT_HASH_MISMATCH');continue
  target=Path(root)/'.cache/final-gates'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(item['raw'])
  try:r=invoke([sys.executable,str(target),str(source)],cwd=root,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=180)
  except subprocess.TimeoutExpired:blocked('GATE_TIMEOUT',scriptSha256=actual);continue
  except OSError as exc:blocked('GATE_INVOCATION_UNAVAILABLE',scriptSha256=actual,diagnostic=str(exc));continue
  results.append({'family':family,'gate':name,'status':'PASS'if r.returncode==0 else'BLOCKED','reason':None if r.returncode==0 else'GATE_REJECTED','scriptSha256':actual,'exitCode':r.returncode,'stdout':r.stdout.strip(),'stderr':r.stderr.strip()})
 return results
