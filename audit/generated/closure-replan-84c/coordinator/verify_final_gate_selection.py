"""Actual five-gate positive + targeted selection/invocation regression witnesses."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_resources import resources,SSOT
from final_gate_set import FINAL_GATE_FAMILIES,run_final_gates
source=hashlib.sha256(SSOT.read_bytes()).hexdigest();original=list(resources());positive=json.loads((ROOT/'audit/generated/baseline-gates.json').read_text());assert positive['ssotSha256']==source
assert [(q['family'],q['gate'])for q in positive['checks']]==list(FINAL_GATE_FAMILIES) and all(q['status']=='PASS'for q in positive['checks'])
checks=[{'id':'actual-current-five-family-execution','passed':True}]
prose=SSOT.read_text();clause='Finální whole-package gate families jsou `R10`, `R16`, `UI`, `CLOSURE`, `R17`.'
checks.append({'id':'exact-effective-73.7-universe','passed':clause in prose and [f for f,n in FINAL_GATE_FAMILIES]==['R10','R16','UI','CLOSURE','R17']})
def successful(**kwargs):return subprocess.CompletedProcess([],0,'already-proved-in-real-positive','')
def invoke(argv,**kwargs):return successful(**kwargs)
for family,path in FINAL_GATE_FAMILIES:
 selected=next(r for r in original if r['path']==path and r['family']=='KCML-'+family+'-RESOURCE')
 for kind in ['missing','wrong-hash','duplicate']:
  rows=copy.deepcopy(original)
  if kind=='missing':rows=[r for r in rows if not(r['family']==selected['family']and r['path']==path)]
  elif kind=='wrong-hash':next(r for r in rows if r['family']==selected['family']and r['path']==path)['raw']+=b'\n# modification without matching digest\n'
  else:rows.append(copy.deepcopy(selected))
  results=run_final_gates(rows,ROOT,SSOT,invoke);bad=next(q for q in results if q['family']==family)
  expected={'missing':'MISSING_REQUIRED_GATE','wrong-hash':'SCRIPT_HASH_MISMATCH','duplicate':'DUPLICATE_REQUIRED_GATE'}[kind]
  checks.append({'id':family+'/'+kind,'passed':len(results)==5 and bad['status']=='BLOCKED'and bad['reason']==expected and all(q['status']=='PASS'for q in results if q['family']!=family),'diagnostic':bad.get('reason')})
def timed(argv,**kwargs):raise subprocess.TimeoutExpired(argv,180)
results=run_final_gates(original,ROOT,SSOT,timed);checks.append({'id':'timeout-is-structured-BLOCKED','passed':len(results)==5 and all(q['status']=='BLOCKED'and q['reason']=='GATE_TIMEOUT'for q in results)})
q={'sourceSha256':source,'status':'PASS'if all(x['passed']for x in checks)else'BLOCKED','checks':checks,'checked':len(checks),'failed':sum(not x['passed']for x in checks),'authority':{'pointer':'SSOT73.7','quote':clause},'scope':'Five actual gate executions are positive evidence; mocks only inject specific selector/hash/invocation faults. No domain/runtime/whole readiness certification.','inputs':{'scripts/final_gate_set.py':hashlib.sha256((ROOT/'scripts/final_gate_set.py').read_bytes()).hexdigest(),'audit/generated/baseline-gates.json':hashlib.sha256((ROOT/'audit/generated/baseline-gates.json').read_bytes()).hexdigest()}}
Path(__file__).with_name('final-gate-selection-tests.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:q[k]for k in ['status','checked','failed']}));raise SystemExit(q['failed']!=0)
