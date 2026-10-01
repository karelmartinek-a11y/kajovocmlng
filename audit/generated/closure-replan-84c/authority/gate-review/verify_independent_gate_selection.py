from pathlib import Path
import sys,copy,json,hashlib,subprocess
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'));sys.dont_write_bytecode=True
from ssot_resources import SSOT,resources
from final_gate_set import FINAL_GATE_FAMILIES,run_final_gates
source=SSOT.read_bytes();original=list(resources());checks=[]
def record(id,passed,**detail):checks.append({'id':id,'passed':bool(passed),**detail})
positive=run_final_gates(original,OUT,SSOT)
record('actual-five-canonical-executions',len(positive)==5 and all(r['status']=='PASS'for r in positive),results=positive)
assert checks[-1]['passed'],positive
record('exact73.7-five-universe',[f for f,p in FINAL_GATE_FAMILIES]==['R10','R16','UI','CLOSURE','R17'] and 'Finální whole-package gate families jsou `R10`, `R16`, `UI`, `CLOSURE`, `R17`.'in source.decode())
def success(*a,**kw):return subprocess.CompletedProcess([],0,'injected unaffected sibling (actual positives above)','')
for family,path in FINAL_GATE_FAMILIES:
 selected=next(r for r in original if r['family']=='KCML-'+family+'-RESOURCE'and r['path']==path)
 for kind in ['missing','raw-hash','declared-hash','duplicate','wrong-family']:
  entries=copy.deepcopy(original);row=next(r for r in entries if r['family']==selected['family']and r['path']==path)
  if kind=='missing':entries.remove(row)
  elif kind=='raw-hash':row['raw']+=b'\n# deliberately changed bytes\n'
  elif kind=='declared-hash':row.get('declared',row['attrs'])['sha256']='0'*64
  elif kind=='duplicate':entries.append(copy.deepcopy(row))
  else:row['family']='KCML-R9-RESOURCE'
  result=run_final_gates(entries,OUT,SSOT,success);bad=next(r for r in result if r['family']==family);expected={'missing':'MISSING_REQUIRED_GATE','raw-hash':'SCRIPT_HASH_MISMATCH','declared-hash':'SCRIPT_HASH_MISMATCH','duplicate':'DUPLICATE_REQUIRED_GATE','wrong-family':'MISSING_REQUIRED_GATE'}[kind]
  record(family+'/'+kind,len(result)==5 and bad['status']=='BLOCKED'and bad['reason']==expected and all(r['status']=='PASS'for r in result if r['family']!=family),expected=expected,actual=bad.get('reason'))
# A real deliberately slow subprocess demonstrates TimeoutExpired conversion.
# It tests invocation failure classification, not an assertion that canonical gates hang.
hang=OUT/'deliberate_slow_invocation.py';hang.write_text('import time\ntime.sleep(2)\n')
def timed(argv,**kwargs):return subprocess.run([sys.executable,str(hang)],capture_output=True,text=True,timeout=.03)
r=run_final_gates(original,OUT,SSOT,timed);record('actual-subprocess-timeout-is-structured',len(r)==5 and all(x['reason']=='GATE_TIMEOUT'and x['status']=='BLOCKED'for x in r))
def unavailable(*a,**kw):raise FileNotFoundError('INDEPENDENT_FIXTURE_UNAVAILABLE_INTERPRETER')
r=run_final_gates(original,OUT,SSOT,unavailable);record('OS-invocation-error-blocked',all(x['reason']=='GATE_INVOCATION_UNAVAILABLE'and x['status']=='BLOCKED'for x in r))
def rejects(*a,**kw):return subprocess.CompletedProcess([],7,'','INDEPENDENT_FIXTURE_GATE_REJECTED')
r=run_final_gates(original,OUT,SSOT,rejects);record('nonzero-not-PASS',all(x['reason']=='GATE_REJECTED'and x['exitCode']==7 and x['status']=='BLOCKED'for x in r))
# A scoped R9 row is an input; it cannot add a sixth final family.
r9=next(r for r in original if r['path']=='scripts/verify_r9.py')if any(r['path']=='scripts/verify_r9.py'for r in original)else next(r for r in original if r['family']=='KCML-R9-RESOURCE')
r=run_final_gates(original+[copy.deepcopy(r9)],OUT,SSOT,success);record('R9-does-not-expand-final-universe',len(r)==5 and [x['family']for x in r]==[x[0]for x in FINAL_GATE_FAMILIES])
record('source-unchanged',source==SSOT.read_bytes())
inputs={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['scripts/final_gate_set.py','scripts/run_baseline_gates.py','scripts/verify_package.py']}
report={'sourceSha256':hashlib.sha256(source).hexdigest(),'status':'PASS'if all(x['passed']for x in checks)else'BLOCKED','checked':len(checks),'failed':sum(not x['passed']for x in checks),'checks':checks,'inputs':inputs,'scope':'Actual five canonical positive executions; valid-positive-derived resource selector/digest faults and real deliberate subprocess timeout. Unaffected siblings/nonzero/OS diagnostics are explicit controlled invocation fixtures, not domain/runtime proof.','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED','wholeOperationClosed':False}
(OUT/'independent-final-gate-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));raise SystemExit(report['failed']!=0)
