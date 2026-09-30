"""Author bounded own-kind selectors and content policy; no whole-operation closure."""
import argparse,ast,hashlib,json,re
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
from generation_admission_contracts import local_bundle
from generation_retry_inventory import bundle as retry_bundle
BASE=ROOT/'audit/generated/resume-d362/admission'
PATH='contracts/generation/admission-basis.schema.json'
def materialize():
 fields=json.loads((BASE/'generation-admission-contract-proposed.json').read_text())
 diagnostics=json.loads((BASE/'diagnostics-proposed.json').read_text())
 module=ROOT/'scripts/generation_admission_contracts.py';tree=ast.parse(module.read_text());lines={}
 for node in ast.walk(tree):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='fail' and node.args and isinstance(node.args[0],ast.Constant):lines.setdefault(node.args[0].value,[]).append(node.lineno)
 for row in json.loads((BASE/'retry-inventory-diagnostics-proposed.json').read_text())['diagnostics']:
  diagnostics['diagnostics'].append({'diagnostic':row['diagnostic'],'stableCode':row['stableCode'],'httpStatus':row['httpStatus'],'predicate':[{'condition':condition} for condition in row['predicate']['anyOf']], 'pointerRule':row['pointer'],'sources':row['authority'],'implementation':{'path':'scripts/generation_retry_inventory.py','sha256':hashlib.sha256((ROOT/'scripts/generation_retry_inventory.py').read_bytes()).hexdigest()}})
 current={row['diagnostic'] for row in diagnostics['diagnostics']}
 for node in ast.walk(tree):
  if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name):continue
  arg=node.args[0] if node.func.id=='fail' and node.args else node.args[3] if node.func.id=='validate' and len(node.args)>=4 else None
  if not isinstance(arg,ast.Constant) or not isinstance(arg.value,str) or not arg.value.startswith(('GENERATION_','MONITORING_')) or arg.value in current:continue
  code=arg.value;stable='CREATE_POLICY_UNRESOLVED' if code.endswith(('_UNAVAILABLE','_UNRESOLVED')) else 'CREATE_REFERENCE_INVALID'
  diagnostics['diagnostics'].append({'diagnostic':code,'stableCode':stable,'httpStatus':503 if stable=='CREATE_POLICY_UNRESOLVED' else 422,'predicate':[{'condition':'Exact '+ast.unparse(node)+' evaluated against actual native bytes/retained declared publication and output schema; no client authority'}],'pointerRule':'Exact RFC6901 source pointer, empty for cross-record invariant','sources':['SSOT §12.49','SSOT §12.51','SSOT §49.4']});current.add(code)
 for row in diagnostics['diagnostics']:
  row['sources']=[v.replace('PROPOSED SSOT','SSOT') for v in row['sources']]
  if row['diagnostic'].startswith('GENERATION_RETRY_') and 'implementation' in row:continue
  row['implementation']={'path':'scripts/generation_admission_contracts.py','sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'directDiagnosticLines':lines.get(row['diagnostic'],[])}
  for condition in row['predicate']:condition.pop('implementationLine',None)
 fields['proposalInput']={'commit':fields.pop('inputCommit',None),'ssotSha256':fields.pop('ssotSha256',None)}
 fields['status']='EFFECTIVE_BOUNDED_DISCUSSION_ADMISSION'
 fields['requestSchema']=local_bundle()['$defs']['GenerationJobCreateBody']
 fields['activationScope']='Own-kind discussion admission selectors/native bytes only; full operation, execution graph/dispatch/auth/crypto remain OPEN'
 return {'contracts/generation/retry-inventory.schema.json':retry_bundle(),PATH:local_bundle(),'contracts/generation/admission-basis.json':fields,'contracts/generation/admission-diagnostics.json':diagnostics}
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();text=SSOT.read_text();items=list(resources(text));rs=resource_index(items)
 updates={path:(json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode() for path,doc in materialize().items()}
 manifest=json.loads(rs['manifest.json']['raw'])
 for path,raw in updates.items():manifest['resources'][path]={'kind':'JSON','sizeBytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()}
 manifest['resourceCount']=len(manifest['resources']);updates['manifest.json']=encoded(manifest,rs['manifest.json']['raw'])
 normative=(BASE/'normative-amendment-12.51.md').read_text().rstrip()+'\n\n'+(BASE/'retry-inventory-amendment.md').read_text().rstrip()+'\n\n';pending=[p for p,raw in updates.items() if p not in rs or rs[p]['raw']!=raw]
 if a.check:print(json.dumps({'status':'PASS' if not pending and normative in text else 'BLOCKED','pending':pending,'normativePresent':normative in text}));return int(bool(pending) or normative not in text)
 text=rewrite(text,items,updates);m=re.search(r'^### 12\.51 .*?(?=^### 12\.|^## 13\.)',text,re.M|re.S)
 if m:text=text[:m.start()]+normative+text[m.end():]
 else:
  m=re.search(r'^## 13\.',text,re.M);assert m;text=text[:m.start()]+normative+text[m.start():]
 SSOT.write_text(text,encoding='utf8',newline='\n')
 for path,raw in updates.items():
  if path=='manifest.json':continue
  p=ROOT/'01_UI_CONTRACT'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 print(json.dumps({'authored':list(updates),'wholeOperationsClosed':0}));return 0
if __name__=='__main__':raise SystemExit(main())
