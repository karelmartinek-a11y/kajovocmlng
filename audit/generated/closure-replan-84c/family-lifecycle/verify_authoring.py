"""Pure in-memory publication/idempotence/generic overwrite proof; no shared writes."""
from pathlib import Path
import sys,json,copy,hashlib
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
from close_owner_session_family import updates
from jsonschema import Draft202012Validator
rs=resource_index();original=copy.copy(rs);first=updates(rs)
for path,raw in first.items():rs[path]={**rs.get(path,{}),'raw':raw}
second=updates(rs);checks=[{'id':'authoring-exact-resource-bytes-idempotent','status':'PASS'if first==second else'FAIL'}]
for path in ['contracts/owner-session-family.schema.json']:
 for key,mask in json.loads(first[path])['$defs'].items():
  Draft202012Validator.check_schema(mask);checks.append({'id':'published-schema-valid/'+key,'status':'PASS'})
import subprocess
from ssot_sources import resources,resource_index
legacy=resource_index(list(resources(subprocess.check_output(['git','show','84c41ba:00_SSOT/KajovoCMLNG_SSOT.md']).decode())))
legacy_rows={r['operationId']:r for r in json.loads(legacy['contracts/payload-contracts.json']['raw'])['records']}
payload=json.loads(first['contracts/payload-contracts.json'])
for oid in ['owner.session.list','owner.session.revoke']:
 for field in ['requestSchema','responseSchema','eventSchema']:
  mutant=copy.copy(rs);changed=copy.deepcopy(payload);selected=next(r for r in changed['records']if r['operationId']==oid);old=legacy_rows[oid];selected[field]=copy.deepcopy(old[field]);changed.pop('canonicalDigest',None)
  mutant['contracts/payload-contracts.json']={**rs['contracts/payload-contracts.json'],'raw':(json.dumps(changed)+'\n').encode()};restored=updates(mutant);got=next(r for r in json.loads(restored['contracts/payload-contracts.json'])['records']if r['operationId']==oid)
  checks.append({'id':'generic-regeneration-respecialized/'+oid+'/'+field,'status':'PASS'if got[field]==next(r for r in payload['records']if r['operationId']==oid)[field]else'FAIL'})
report={'genericBaselineHead':'84c41ba80af35d5d13f64cf8177ce551c2188e27','genericBaselineResourceSha256':legacy['contracts/payload-contracts.json']['sha256'],'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'consumedSourceHashes':{p:hashlib.sha256(original[p]['raw']).hexdigest()for p in ['contracts/payload-contracts.json','contracts/operation-contracts.json']},'authoringScriptSha256':hashlib.sha256((ROOT/'scripts/close_owner_session_family.py').read_bytes()).hexdigest(),'contractsScriptSha256':hashlib.sha256((ROOT/'scripts/owner_session_family_contracts.py').read_bytes()).hexdigest(),'candidateResourceSha256':{p:hashlib.sha256(raw).hexdigest()for p,raw in first.items()},'checks':checks,'checkCount':len(checks),'failedCount':sum(x['status']!='PASS'for x in checks),'wholeOperationsClosed':0,'canonicalWritten':False};(OUT/'authoring-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(checks),'failed':report['failedCount']}));raise SystemExit(report['failedCount']!=0)
