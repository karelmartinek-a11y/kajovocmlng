"""Structural and semantic checks for the shared visual contract; no runtime claim."""
from pathlib import Path
import json,csv,sys
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1];C=ROOT/'01_UI_CONTRACT/ui/contracts'
def read(n):return json.loads((C/n).read_text())
def verify():
 problems=[]
 def check(ok,label):
  if not ok:problems.append(label)
 reg=read('ui-control-registry.json');actions={a['id']:a for p in reg['pages'] for a in p['actions']};res=json.loads((ROOT/'01_UI_CONTRACT/closure/contracts/ui-action-resolution.json').read_text());bind={b['actionId']:b for b in res['bindings']};ops=set(json.loads((ROOT/'01_UI_CONTRACT/closure/contracts/operation-overlay.json').read_text())['finalOperationIds'])
 check(len(actions)==sum(len(p['actions']) for p in reg['pages']),'duplicate action ID');check(set(actions)==set(bind),'action binding coverage')
 for aid,a in actions.items():
  check(all(k in a for k in ['dashboard','chat','permission','validationContract','auditContract','help_cs','help_en']),aid+' parity/help incomplete')
  check(set(a['validationContract']['canonicalOperationIds'])<=ops,aid+' unknown operation')
  if a['dashboard']['availability']=='AVAILABLE':check(a['chat']['availability'] in ['CANONICAL_DISPATCH','CLIENT_ACTION_CARD'],aid+' no chat path')
 rows=list(csv.DictReader((ROOT/'01_UI_CONTRACT/UI_FUNCTION_PARITY.csv').open()));check({r['ui_function'] for r in rows}==set(actions),'CSV parity drift')
 controls=list(csv.DictReader((ROOT/'01_UI_CONTRACT/UI_CONTROLS.csv').open(encoding='utf-8-sig')));check(len(controls)==sum(len(p['actions'])+len(p['fields']) for p in reg['pages']),'control inventory drift')
 visual=read('process-visual-registry.json');states={x['state_id'] for x in visual['steps']};statuses={x['state_id'] for x in visual['statuses']};check(set(visual['statusTransitions'])==statuses,'status transition universe')
 for p in visual['plans']:
  check(all(x in states for x in p['steps']),p['process_family']+' unknown step');check(p['steps'][-1]=='step.done',p['process_family']+' lacks terminal projection')
 for state,targets in visual['statusTransitions'].items():check(set(targets)<=statuses,'unknown status edge '+state)
 for path in C.glob('*.schema.json'):
  try:Draft202012Validator.check_schema(json.loads(path.read_text()))
  except Exception as e:problems.append(path.name+': '+str(e))
 errors=read('error-message-registry.json');check(len({e['error_code'] for e in errors['records']})==len(errors['records']),'duplicate error code');v=Draft202012Validator(read('error-record.schema.json'))
 for e in errors['records']:
  for x in v.iter_errors(e):problems.append(e['error_code']+': '+x.message)
 for a in read('visual-artifact-bindings.json')['artifacts']:
  check((ROOT/a['source'].split('?')[0]).is_file(),'missing view '+a['id']);check(a['backendOperation'] in ops,'unknown view operation '+a['id'])
  for p in a['screenshots']:check((ROOT/p).is_file(),'missing screenshot '+p)
 for op in read('observability-query-contract.json')['canonicalOperations']:check(op in ops,'unknown history operation '+op)
 return {'status':'FAIL' if problems else 'PASS','actions':len(actions),'controls':len(controls),'processFamilies':len(visual['plans']),'steps':len(states),'statuses':len(statuses),'errors':len(errors['records']),'failures':problems}
if __name__=='__main__':
 r=verify();print(json.dumps(r,ensure_ascii=False));sys.exit(bool(r['failures']))
