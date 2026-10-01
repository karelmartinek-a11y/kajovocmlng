"""Reusable authoring update provider; never writes the canonical SSOT itself.

Root coordinator can import updates(resource_index()) into its existing authoring
transaction. Run directly to save the exact replacement resource pack locally.
The authoring script rejects stale operation/path identity and unknown digest recipe.
"""
import sys,json,copy,hashlib
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');O=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index
PAYLOAD='contracts/payload-contracts.json'
RESOURCE='contracts/audit/core-read.schema.json'
def digest(v):return 'sha256:'+hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def updates(resources):
 patch=json.loads((O/'authorable-core-delta.json').read_text());old=json.loads(resources[PAYLOAD]['raw']);doc=copy.deepcopy(old)
 for p in patch['patches']:
  found=[r for r in doc['records'] if r['routeId']==p['routeId']]
  if len(found)!=1 or found[0]['operationId']!=p['operationId']:raise ValueError('AUDIT_AUTHORING_ROUTE_IDENTITY_CHANGED')
  row=found[0]
  if (row['method'],row['path'])!=('GET','/audit/events'+('/{id}'if p['operationId']=='audit.event.read'else'')):raise ValueError('AUDIT_AUTHORING_TRANSPORT_CHANGED')
  for k,v in p['replace'].items():row[k]=copy.deepcopy(v)
  # Do not retain meaningless generic slot/JSON consistency policies once there
  # is no such business payload. Shared server native validation stays mandatory.
  row['semanticRules']=[r for r in row.get('semanticRules',[]) if r not in ['DUPLICATE_SLOT_REJECT','CANONICAL_JSON_MUST_MATCH_VALUE_WHEN_NON_NULL','VALUE_DIGEST_OVER_CANONICAL_VALUE']]
  row['semanticRules']+=['AUDIT_CORE_200_QUERY_PROFILE' if p['operationId']=='audit.event.list' else 'AUDIT_READ_EXACT_UUID_NO_QUERY','AUDIT_ORIGINAL_BYTES_FRAMED_HASH_AND_PAYLOAD_DIGEST_VERIFY','AUDIT_BYTES_INSPECTION_NOT_BUSINESS_EVENT_EXECUTION']
  row['semanticRules']=list(dict.fromkeys(row['semanticRules']))
 prior=old['canonicalDigest']
 if prior==digest({**old,'canonicalDigest':None}):doc['canonicalDigest']=digest({**doc,'canonicalDigest':None})
 elif prior==digest(old['records']):doc['canonicalDigest']=digest(doc['records'])
 else:
  oldbase={k:v for k,v in old.items() if k!='canonicalDigest'}
  if prior!=digest(oldbase):raise ValueError('AUDIT_AUTHORING_UNKNOWN_DIGEST_RECIPE')
  doc['canonicalDigest']=digest({k:v for k,v in doc.items() if k!='canonicalDigest'})
 return {PAYLOAD:(json.dumps(doc,indent=2,ensure_ascii=False)+'\n').encode(),RESOURCE:(json.dumps(patch['resource'],indent=2,ensure_ascii=False)+'\n').encode()}
if __name__=='__main__':
 u=updates(resource_index());pack={'activation':'REQUEST_RESPONSE_INSPECTION_ONLY; wholeOperationClosed=false','resources':list(u),'digests':{k:hashlib.sha256(v).hexdigest() for k,v in u.items()},'normativeSupplement':'CORE_AUDIT_NORMATIVE_SUPPLEMENT.md'}
 (O/'authoring-update-pack.json').write_text(json.dumps(pack,indent=2)+'\n');print('2 replacement resources prepared; no shared writes')
