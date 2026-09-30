"""Own receipt reference. Stores are server-owned; this is not an origin/DB proof."""
import json,hashlib
class Violation(ValueError):
 def __init__(self,code):self.code=code;super().__init__(code)
def fail(code):raise Violation(code)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(v):return hashlib.sha256(canonical(v)).hexdigest()
def shape(v,keys,code):
 if type(v) is not dict or set(v)!=set(keys):fail(code)
def identifier(v):return type(v) is str and bool(v)
def hex_digest(v):return type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v)
def unique_ids(v,code):
 if type(v) is not list or any(not identifier(x) for x in v) or len(v)!=len(set(v)):fail(code)
def decoded_receipt(store,key):
 if not hex_digest(key) or key not in store:fail('EVIDENCE_BYTES_UNAVAILABLE')
 raw=store[key]
 if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=key:fail('EVIDENCE_DIGEST_MISMATCH')
 def object_pairs(pairs):
  r={}
  for k,v in pairs:
   if k in r:fail('EVIDENCE_DUPLICATE_JSON_KEY')
   r[k]=v
  return r
 try:value=json.loads(raw,object_pairs_hook=object_pairs,parse_constant=lambda _:fail('EVIDENCE_INVALID_JSON'))
 except Violation:raise
 except (ValueError,UnicodeError):fail('EVIDENCE_INVALID_JSON')
 if type(value) is not dict or canonical(value)!=raw:fail('EVIDENCE_NONCANONICAL_BYTES')
 return value
def inventory_validate(ob,inv,pinned_digest,evidence_store):
 shape(ob,['runId','releaseSha','planDigest','fixtureNamespace','cleanup','effects','checks'],'OBLIGATION_MASK_INVALID')
 for k in ['runId','fixtureNamespace']:
  if not identifier(ob[k]):fail('OBLIGATION_ID_INVALID')
 if not hex_digest(ob['planDigest']) or type(ob['releaseSha']) is not str or len(ob['releaseSha'])!=40 or any(c not in '0123456789abcdef' for c in ob['releaseSha']):fail('OBLIGATION_ID_INVALID')
 for k in ['cleanup','effects','checks']:unique_ids(ob[k],'OBLIGATION_ID_INVALID')
 shape(inv,['runId','releaseSha','planDigest','fixtureNamespace','cleanup','effects','checks','orphans','manualResolutionIds'],'INVENTORY_MASK_INVALID')
 if not hex_digest(pinned_digest) or digest(inv)!=pinned_digest:fail('INVENTORY_DIGEST_MISMATCH')
 for k in ['runId','releaseSha','planDigest','fixtureNamespace']:
  if inv[k]!=ob[k]:fail('INVENTORY_IDENTITY_MISMATCH')
 for family,outcomes in [('cleanup',{'COMPLETE','PENDING','FAILED'}),('effects',{'KNOWN','PENDING','UNKNOWN'}),('checks',{'TERMINAL','PENDING'})]:
  rows=inv[family]
  if type(rows) is not list:fail('INVENTORY_ENTRY_MASK_INVALID')
  for r in rows:
   shape(r,['id','outcome','evidenceDigest'],'INVENTORY_ENTRY_MASK_INVALID')
   if not identifier(r['id']):fail('INVENTORY_ENTRY_ID_INVALID')
  ids=[r['id'] for r in rows]
  if len(ids)!=len(set(ids)):fail('INVENTORY_DUPLICATE_ID')
  if set(ids)!=set(ob[family]):fail('INVENTORY_OBLIGATION_SET_MISMATCH')
  for r in rows:
   if type(r['outcome']) is not str or r['outcome'] not in outcomes:fail('INVENTORY_OUTCOME_INVALID')
   ev=decoded_receipt(evidence_store,r['evidenceDigest'])
   shape(ev,['kind','runId','releaseSha','planDigest','fixtureNamespace','family','itemId','outcome'],'EVIDENCE_MASK_INVALID')
   expected={k:ob[k] for k in ['runId','releaseSha','planDigest','fixtureNamespace']};expected.update(kind='ACCEPTANCE_INVENTORY_EVIDENCE_V1',family=family,itemId=r['id'],outcome=r['outcome'])
   if ev!=expected:fail('EVIDENCE_BINDING_MISMATCH')
 for k in ['orphans','manualResolutionIds']:unique_ids(inv[k],'INVENTORY_ENTRY_MASK_INVALID')
 return inv
def finalization_validate(ob,inventory_digest,finalization_id,retained_finalizations,evidence_store,expected_fence):
 if not identifier(finalization_id) or finalization_id not in retained_finalizations:fail('FINALIZATION_UNAVAILABLE')
 final=decoded_receipt(evidence_store,retained_finalizations[finalization_id])
 shape(final,['kind','id','runId','releaseSha','planDigest','fixtureNamespace','inventoryDigest','logicalOperationId','fence','transactionId','commitReceiptDigest','eventDigest','outboxDigest','auditDigest','state'],'FINALIZATION_MASK_INVALID')
 if final['kind']!='ACCEPTANCE_CANCEL_FINALIZATION_V1' or final['state']!='CANCELLED' or final['id']!=finalization_id:fail('FINALIZATION_BINDING_MISMATCH')
 for k in ['runId','releaseSha','planDigest','fixtureNamespace']:
  if final[k]!=ob[k]:fail('FINALIZATION_BINDING_MISMATCH')
 if final['inventoryDigest']!=inventory_digest:fail('FINALIZATION_INVENTORY_MISMATCH')
 if type(final['fence']) is not int or type(expected_fence) is not int or final['fence']!=expected_fence:fail('FINALIZATION_FENCE_MISMATCH')
 if not identifier(final['logicalOperationId']) or not identifier(final['transactionId']):fail('FINALIZATION_BINDING_MISMATCH')
 commit=decoded_receipt(evidence_store,final['commitReceiptDigest'])
 shape(commit,['kind','transactionId','state','memberDigests'],'COMMIT_RECEIPT_MASK_INVALID')
 if commit['kind']!='ATOMIC_TRANSACTION_COMMIT_V1' or commit['state']!='COMMITTED' or commit['transactionId']!=final['transactionId']:fail('COMMIT_RECEIPT_BINDING_MISMATCH')
 unique_ids(commit['memberDigests'],'COMMIT_RECEIPT_MASK_INVALID')
 for family in ['event','outbox','audit']:
  key=final[family+'Digest'];r=decoded_receipt(evidence_store,key)
  shape(r,['kind','transactionId','logicalOperationId','runId','inventoryDigest','fence','state'],'ATOMIC_MEMBER_MASK_INVALID')
  expected={'kind':family.upper()+'_ACCEPTANCE_CANCEL_V1','transactionId':final['transactionId'],'logicalOperationId':final['logicalOperationId'],'runId':ob['runId'],'inventoryDigest':inventory_digest,'fence':expected_fence,'state':'CANCELLED'}
  if r!=expected or key not in commit['memberDigests']:fail('ATOMIC_MEMBER_BINDING_MISMATCH')
 return final
def cancellation_projection(ob,inv,pinned_digest,evidence_store,*,finalization_id=None,retained_finalizations=None,expected_fence=None):
 v=inventory_validate(ob,inv,pinned_digest,evidence_store)
 cleanup='FAILED' if any(r['outcome']=='FAILED' for r in v['cleanup']) else 'PENDING' if v['orphans'] or any(r['outcome']=='PENDING' for r in v['cleanup']) else 'COMPLETE'
 rec='UNKNOWN' if any(r['outcome']=='UNKNOWN' for r in v['effects']) else 'MANUAL_REVIEW' if v['manualResolutionIds'] else 'PENDING' if any(r['outcome']=='PENDING' for r in v['effects']+v['checks']) else 'COMPLETE'
 closed=cleanup=='COMPLETE' and rec=='COMPLETE'
 if finalization_id is not None:
  if not closed:fail('CANCELLED_CLOSURE_INCOMPLETE')
  finalization_validate(ob,pinned_digest,finalization_id,retained_finalizations or {},evidence_store,expected_fence)
 state='CANCELLED' if finalization_id is not None else 'MANUAL_REVIEW' if cleanup=='FAILED' or rec in ['UNKNOWN','MANUAL_REVIEW'] else 'RECONCILING' if not closed else 'CANCEL_REQUESTED'
 return {'state':state,'cleanupStatus':cleanup,'reconciliationStatus':rec}
def validate_receipt(receipt,expected):
 if receipt!=expected:fail('RECEIPT_INVENTORY_PROJECTION_MISMATCH')
 return True
