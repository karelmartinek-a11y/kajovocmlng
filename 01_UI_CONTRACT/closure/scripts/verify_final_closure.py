#!/usr/bin/env python3
from pathlib import Path
import re,json,hashlib,sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'KájovoCMLNG_SSOT.md')
t=p.read_text('utf-8'); b=t.encode('utf-8')
DIALECT='https://json-schema.org/draft/2020-12/schema'

def extract(fam):
 pat=re.compile(r'^<!-- KCML-'+re.escape(fam)+r'-RESOURCE path="([^"]+)" kind="([^"]+)" bytes="(\d+)" sha256="([0-9a-f]{64})" encoding="plain" -->\n```([^\n]*)\n(.*?)\n```\n<!-- KCML-'+re.escape(fam)+r'-RESOURCE-END -->$',re.S|re.M)
 out={}
 for m in pat.finditer(t):
  path,kind,n,sha,lang,body=m.groups(); raw=(body+'\n').encode(); assert len(raw)==int(n),(fam,path,'bytes'); assert hashlib.sha256(raw).hexdigest()==sha,(fam,path,'sha'); assert path not in out; out[path]=(kind,body+'\n')
 return out

def closed_schema(s,where):
 assert isinstance(s,dict),(where,'schema-not-object')
 if '$schema' in s: assert s['$schema']==DIALECT,(where,'dialect')
 if s.get('type')=='object':
  assert s.get('additionalProperties') is False,(where,'open-object')
  props=s.get('properties'); req=s.get('required')
  assert isinstance(props,dict) and isinstance(req,list),(where,'properties-required')
  assert len(req)==len(set(req)) and set(req)<=set(props),(where,'required')
 for key in ('properties','$defs'):
  for k,v in s.get(key,{}).items(): closed_schema(v,where+'/'+key+'/'+k)
 for key in ('items','contains','not','if','then','else'):
  v=s.get(key)
  if isinstance(v,dict): closed_schema(v,where+'/'+key)
 for key in ('allOf','anyOf','oneOf','prefixItems'):
  for i,v in enumerate(s.get(key,[])): closed_schema(v,where+'/'+key+'/'+str(i))

# Generic embedded blocks must be structurally paired; markers inside code are ignored by anchored matching.
active=None
for no,line in enumerate(t.splitlines(),1):
 if line.startswith('<!-- KCML-EMBEDDED path='):
  assert active is None,('nested generic embedded',active,no,line)
  active=(no,line)
 elif line.startswith('<!-- KCML-EMBEDDED-END'):
  assert active is not None,('orphan generic end',no)
  active=None
assert active is None,('unclosed generic embedded',active)
r16=extract('R16'); ui=extract('UI'); fin=extract('CLOSURE')
required={'closure/contracts/ui-action-resolution.json','closure/contracts/operation-overlay.json','closure/contracts/operation-payloads.json','closure/contracts/storage-closure.json','closure/audit/structural-closure.json','closure/scripts/verify_final_closure.py'}
assert set(fin)==required,(set(fin)^required)
base=json.loads(r16['r16/contracts/effective-operation-universe.json'][1]); reg=json.loads(ui['ui/contracts/ui-control-registry.json'][1]); bp=json.loads(fin['closure/contracts/ui-action-resolution.json'][1]); ov=json.loads(fin['closure/contracts/operation-overlay.json'][1]); pl=json.loads(fin['closure/contracts/operation-payloads.json'][1]); st=json.loads(fin['closure/audit/structural-closure.json'][1]); storage=json.loads(fin['closure/contracts/storage-closure.json'][1])
baseU=set(base['operationIds']); assert len(baseU)==base['operationCount']==605
add=[x['operationId'] for x in ov['operations']]; assert len(add)==len(set(add)) and not (set(add)&baseU)
finalU=baseU|set(add); assert len(finalU)==ov['finalOperationCount']==bp['finalOperationUniverseCount']==619; assert set(ov['finalOperationIds'])==finalU
mandatory={'operationId','sourceUiActions','purpose','exposureClass','method','path','canonicalWriter','aggregateRoot','sideEffectClass','idempotencyScope','concurrencyGuard','linearizationPoint','cancellation','recovery','terminalClosure','requestSchemaSummary','responseSchemaSummary','requestSchemaRef','responseSchemaRef','errorCodes','processFamilies','audit','apiChatParity'}
for op in ov['operations']:
 assert mandatory<=set(op),('operation contract incomplete',op.get('operationId'),sorted(mandatory-set(op)))
 assert op['method'] in {'GET','POST','PUT','PATCH','DELETE'} and op['path'].startswith('/api/v1/')
 assert op['errorCodes'] and op['processFamilies'] and isinstance(op['sourceUiActions'],list)
# route method+path unique within additions
mp=[(x['method'],x['path']) for x in ov['operations']]; assert len(mp)==len(set(mp))
# strict payload closure
assert pl['format']=='KCML-FINAL-OPERATION-PAYLOADS/1' and pl['schemaDialect']==DIALECT and pl['unresolved']==[]
assert pl['count']==len(pl['records'])==len(add)==14
prec={x['operationId']:x for x in pl['records']}; assert set(prec)==set(add)
for i,op in enumerate(ov['operations']):
 rec=pl['records'][i]; oid=op['operationId']
 assert rec['operationId']==oid and rec['method']==op['method'] and rec['path']==op['path']
 assert rec.get('reservedPlatformFieldsForbidden') is True
 assert op['requestSchemaRef']==f'closure/contracts/operation-payloads.json#/records/{i}/requestSchema'
 assert op['responseSchemaRef']==f'closure/contracts/operation-payloads.json#/records/{i}/responseSchema'
 for direction in ('requestSchema','responseSchema'):
  s=rec[direction]; assert s.get('$schema')==DIALECT and s.get('$id')==f'urn:kcml:closure:{oid}:{"request" if direction=="requestSchema" else "response"}'
  closed_schema(s,oid+'/'+direction)
# UI action/binding universe is exact and duplicate-free
pages=[p['id'] for p in reg['pages']]; assert len(pages)==len(set(pages))
actions={}
for pg in reg['pages']:
 ids=[a['id'] for a in pg['actions']]; assert len(ids)==len(set(ids)),('duplicate action',pg['id'])
 for a in pg['actions']:
  key=(pg['id'],a['id']); assert key not in actions; actions[key]=a
rows={(x['pageId'],x['actionId']):x for x in bp['bindings']}; assert len(rows)==len(bp['bindings']); assert set(rows)==set(actions),(set(actions)-set(rows),set(rows)-set(actions))
for key,r in rows.items():
 a=actions[key]; k=r['bindingKind']; assert k in bp['bindingKinds']
 assert set(r.get('followOnCanonicalOperations',[]))<=finalU,(key,'bad-follow-on')
 if k=='CANONICAL_OPERATION':
  assert r['canonicalOperationId'] in finalU,(key,r['canonicalOperationId'])
 elif k=='DYNAMIC_CANONICAL_DISPATCH':
  c=r['candidateOperationIds']; assert r.get('canonicalOperationId') in (None,'') and c and len(c)==len(set(c)) and set(c)<=finalU and r['discriminator']
 elif k=='CLIENT_ONLY':
  assert not r['mutatesServer'] and r.get('canonicalOperationId') in (None,'')
 elif k=='PROJECTION_ONLY':
  assert not r['mutatesServer'] and r.get('canonicalOperationId') in finalU
 elif k=='FORBIDDEN':
  assert not r['mutatesServer'] and r.get('canonicalOperationId') in (None,'') and r.get('candidateOperationIds',[])==[]
 else: raise AssertionError((key,k))
# Each added operation is reached by its declared source UI action and no source action maps elsewhere.
assert len({x['actionId'] for x in bp['bindings']})==len(bp['bindings']),('non-global-unique-actionId')
by_action={x['actionId']:x for x in bp['bindings']}
for op in ov['operations']:
 for source in op['sourceUiActions']:
  assert source in by_action,(op['operationId'],source,'missing-source-action')
  row=by_action[source]
  assert row['bindingKind']=='CANONICAL_OPERATION' and row['canonicalOperationId']==op['operationId'],(op['operationId'],source,row)
# storage closure: exact child table, valid PK column/FK/partial unique index representation
assert storage['format']=='KCML-FINAL-STORAGE-CLOSURE/1' and len(storage['tables'])==1
q=storage['tables'][0]; assert q['table']=='owner_saved_audit_query' and q['primaryKey']=='PRIMARY KEY(id)'
assert 'id uuid NOT NULL' in q['columns'] and 'owner_id uuid NOT NULL' in q['columns']
assert 'FOREIGN KEY(owner_id) REFERENCES owner_identity(id) ON DELETE RESTRICT' in q['constraints']
assert not any(c.startswith('UNIQUE(') and ' WHERE ' in c for c in q['constraints'])
assert q['indexes']==['CREATE UNIQUE INDEX uq_owner_saved_audit_query_owner_name_live ON owner_saved_audit_query(owner_id,name) WHERE deleted_at IS NULL']
assert set(storage['existingRootBindings'])==set(add)-{'audit.savedQuery.create'}
assert st['unresolved']==[] and st['strictPayloadSchemasRequiredForAddedOperations'] is True and st['addedOperationPayloadSchemaCount']==14 and st['storagePrimaryKeyAndPartialUniquenessClosed'] is True
assert ov['unresolved']==[] and pl['unresolved']==[] and st['unresolved']==[]
print(json.dumps({'status':'PASS','bytes':len(b),'baseOperations':len(baseU),'addedOperations':len(add),'finalOperations':len(finalU),'strictPayloadSchemas':pl['count'],'uiActions':len(actions),'uiBindings':len(rows),'genericEmbeddedFraming':'PASS','storageClosure':'PASS','unresolved':0},sort_keys=True))
