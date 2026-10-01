from pathlib import Path
import sys,json,copy,hashlib,importlib.util
OUT=Path(__file__).parent;ROOT=Path('/workspace/kajovocmlng');sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index
spec=importlib.util.spec_from_file_location('frozen_first',(OUT/'owner_session_family_contracts.first.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=resource_index();first=m.contracts(r);p=json.loads(r['contracts/payload-contracts.json']['raw']);ops={x['operationId']:x for x in first['operations']}
for row in p['records']:
 if row['operationId']in ops:
  op=ops[row['operationId']]
  for name in ['requestSchema','responseSchema','eventSchema']:row[name]=copy.deepcopy(op[name])
new=dict(r);new['contracts/payload-contracts.json']={**r['contracts/payload-contracts.json'],'raw':json.dumps(p).encode()}
try:
 second=m.contracts(new);status='PASS'if first==second else'FAIL';diagnostic='same'if first==second else'NONIDEMPOTENT_OUTPUT'
except Exception as e:status='FAIL';diagnostic=type(e).__name__+': '+str(e)
rev=next(x for x in first['operations']if x['operationId']=='owner.session.revoke');old=next(x for x in json.loads(r['contracts/payload-contracts.json']['raw'])['records']if x['operationId']=='owner.session.revoke')['requestSchema']['properties']['guards']['properties']['idempotencyKey'];candidate=rev['requestSchema']['properties']['guards']['properties']['idempotencyKey']
report={'inputHelperSha256':hashlib.sha256((OUT/'owner_session_family_contracts.first.py').read_bytes()).hexdigest(),'authoringIdempotence':{'status':status,'diagnostic':diagnostic},'idempotencyGuardPreservation':{'status':'PASS'if old.get('maxLength')==candidate.get('maxLength')else'FAIL','oldMaxLength':old.get('maxLength'),'candidateMaxLength':candidate.get('maxLength')},'wholeOperationClosed':False};(OUT/'authoring-idempotence-first.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
