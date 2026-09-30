"""Complete response witnesses for backup restore; not apply-service/runtime proof."""
import copy,hashlib,json
from jsonschema import Draft202012Validator
from ssot_sources import ROOT,SSOT,resources,resource_index
from close_backup_restore_state import PATH,authority,expected
from verify_phase2_handoffs import witness

def main():
 text=SSOT.read_text(encoding='utf8');items=list(resources(text));rs=resource_index(items)
 model,source,section=authority(text,items);payload=json.loads(rs[PATH]['raw'])
 row=next(r for r in payload['records'] if r['operationId']=='backup.restore');schema=row['responseSchema']
 validator=Draft202012Validator(schema);Draft202012Validator.check_schema(schema)
 sample=witness(schema,{})
 checks=[]
 def check(name,value,valid):
  errors=list(validator.iter_errors(value))
  checks.append({'case':name,'expectedValid':valid,'passed':(not errors)==valid,
   'rejections':[{'pointer':e.json_path,'keyword':e.validator} for e in errors]})
 # Every negative derives from this valid response and must fail its exact field.
 sample['state']=model['initialStates'][0];validator.validate(sample)
 for state in model['states']:check('lifecycle/'+state,{**sample,'state':state},True)
 for value in ['NOT_A_VALID_STATE','APPLIED','SUCCEEDED',None,0,'', 'QUEUED ']:
  check('invalid-state/'+repr(value),{**sample,'state':value},False)
 missing=copy.deepcopy(sample);del missing['state'];check('required-state',missing,False)
 check('unknown-result-field',{**sample,'unknownField':True},False)
 expected_raw,_,_=expected(text,items)
 exact=rs[PATH]['raw']==expected_raw and (ROOT/'01_UI_CONTRACT'/PATH).read_bytes()==expected_raw
 failed=sum(not c['passed'] for c in checks)
 negative_paths=all(any(r['pointer']=='$.state' and r['keyword'] in ['enum','type','minLength','pattern','maxLength'] for r in c['rejections'])
  for c in checks if c['case'].startswith('invalid-state/'))
 report={'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'source':source,
  'resourceSha256':rs[PATH]['sha256'],'projectionExact':exact,'positiveWitness':sample,
  'states':model['states'],'checked':len(checks),'failed':failed,'negativeRejectionSpecific':negative_paths,'checks':checks,
  'status':'PASS' if not failed and exact and negative_paths else 'BLOCKED',
  'scope':__doc__,'remaining':'Other restore request/response/event/error semantics and persistence/recovery remain independently required.'}
 out=ROOT/'audit/generated/repair-2026-09-30/restore-state';out.mkdir(parents=True,exist_ok=True)
 (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['checks','positiveWitness']}))
 return int(report['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
