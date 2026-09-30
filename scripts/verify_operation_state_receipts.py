"""Verify six own response dictionaries and terminal tuple, not entire operations."""
import hashlib,json,os,subprocess,sys
from jsonschema import Draft202012Validator
from ssot_sources import ROOT,SSOT,resource_index

def main():
 source=SSOT.read_bytes();rs=resource_index();contract=json.loads(rs['closure/contracts/operation-state-receipts.json']['raw']);payload=json.loads(rs['closure/contracts/operation-payloads.json']['raw']);rows={r['operationId']:r for r in payload['records']};checks=[]
 def check(name,condition):checks.append({'case':name,'passed':bool(condition)})
 for field in contract['fields']:
  oid,key=field['operationId'],field['field'];schema=rows[oid]['responseSchema'];mask=schema['properties'][key];v=Draft202012Validator(mask)
  check(oid+'.'+key+'/own-mask',mask==field['mask']);check(oid+'.'+key+'/required',key in schema['required'])
  for value in mask.get('enum',[mask.get('const')]):check(oid+'.'+key+'/positive/'+value,v.is_valid(value))
  for value in [None,0,True,{},'UNSPECIFIED']:check(oid+'.'+key+'/reject/'+str(value),not v.is_valid(value))
 cancel=rows['acceptance.run.cancel']['responseSchema'];keys=['state','cleanupStatus','reconciliationStatus'];projected={'type':'object','properties':{k:cancel['properties'][k] for k in keys},'required':keys,'additionalProperties':False,'allOf':cancel['allOf']};v=Draft202012Validator(projected)
 valid={'state':'CANCELLED','cleanupStatus':'COMPLETE','reconciliationStatus':'COMPLETE'};check('cancel/valid-terminal-tuple',v.is_valid(valid))
 for field,values in [('cleanupStatus',['PENDING','FAILED']),('reconciliationStatus',['PENDING','UNKNOWN','MANUAL_REVIEW'])]:
  for value in values:check('cancel/reject-terminal-'+field+value,not v.is_valid({**valid,field:value}))
 authored=subprocess.run([sys.executable,str(ROOT/'scripts/close_operation_state_receipts.py'),'--check'],capture_output=True,text=True,timeout=30)
 check('authoring/current',authored.returncode==0)
 assert SSOT.read_bytes()==source,'SSOT_INPUT_CHANGED'
 report={'sourceDocumentSha256':hashlib.sha256(source).hexdigest(),'checked':len(checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'scope':__doc__,'sourceResourceSha256':{p:rs[p]['sha256'] for p in ['closure/contracts/operation-state-receipts.json','closure/contracts/operation-payloads.json']},'requiredRemaining':'Actual authoritative inventory/evidence provenance, worker/fence/transaction joins and full operation transport/error/event/UI remain separate obligations','wholeOperationsClosed':0,'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/resume-d362/coordinator');out.mkdir(parents=True,exist_ok=True);(out/'operation-state-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['sourceDocumentSha256','checked','failed']}));return int(bool(report['failed']))
if __name__=='__main__':raise SystemExit(main())
