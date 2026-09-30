"""Finite exact diagnostics from the proposed inventory implementation."""
import ast,json
from pathlib import Path
root=Path(__file__).resolve().parent;p=root/'generation_retry_inventory.py';node=ast.parse(p.read_text());parents={}
for n in ast.walk(node):
 for c in ast.iter_child_nodes(n):parents[c]=n
policy={'GENERATION_RETRY_INVENTORY_UNAVAILABLE','GENERATION_RETRY_PHYSICAL_SCAN_UNVERIFIED','GENERATION_RETRY_EFFECT_EVIDENCE_UNAVAILABLE','GENERATION_RETRY_FINAL_EFFECT_POLICY_UNRESOLVED','GENERATION_RETRY_MANUAL_DISPATCH_POLICY_UNRESOLVED','GENERATION_RETRY_OUTCOME_CLASSIFIER_UNRESOLVED','GENERATION_RETRY_OUTCOME_CLASSIFIER_BYTES_UNAVAILABLE','GENERATION_RETRY_OUTCOME_CLASSIFIER_DIGEST_MISMATCH','GENERATION_RETRY_OUTCOME_CLASSIFIER_IMPLEMENTATION_INVALID','GENERATION_RETRY_OUTCOME_CLASSIFIER_DECLARATION_INVALID','GENERATION_RETRY_OUTCOME_CLASSIFIER_EXECUTION_FAILED'}
rows=[]
for n in ast.walk(node):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='fail' and isinstance(n.args[0],ast.Constant):
  code=n.args[0].value;a=n
  while a in parents and not isinstance(a,(ast.If,ast.ExceptHandler)):a=parents[a]
  if not isinstance(a,(ast.If,ast.ExceptHandler)):raise ValueError('Unspecified predicate: '+code)
  predicate=ast.unparse(a.test) if isinstance(a,ast.If) else 'Declared compiled classifier raises an exception while evaluating schema-valid hydrated observations; no exception text is exposed'
  rows.append({'diagnostic':code,'stableCode':'CREATE_POLICY_UNRESOLVED' if code in policy else 'CREATE_REFERENCE_INVALID','httpStatus':503 if code in policy else 422,'predicate':predicate,'implementationFile':str(p.relative_to(p.parents[4])),'line':n.lineno,'pointer':'Server cross-record phase/effect invariant; empty RFC6901 pointer; sensitive values never returned','authority':['SSOT §49.8','SSOT §49.9','SSOT §49.15','SSOT §49.25','PROPOSED §12.51.1']})
composed={}
for row in rows:
 code=row['diagnostic']
 if code not in composed:
  composed[code]={**row,'predicate':{'anyOf':[row['predicate']]},'implementationLines':[row['line']]}
 else:
  composed[code]['predicate']['anyOf'].append(row['predicate']);composed[code]['implementationLines'].append(row['line'])
rows=list(composed.values())
(root/'retry-inventory-diagnostics-proposed.json').write_text(json.dumps({'format':'KCML-RETRY-INVENTORY-DIAGNOSTICS/1','diagnostics':rows,'unknown':'BLOCKED; no prefix fallback'},indent=2)+'\n')
print(json.dumps({'diagnostics':len(rows)}))
