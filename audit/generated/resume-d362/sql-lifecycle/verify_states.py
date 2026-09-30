from pathlib import Path
import json,copy,sys
from jsonschema import Draft202012Validator
from state_reference import *
OUT=Path(__file__).resolve().parent;patch=json.loads((OUT/'field-patch.json').read_text());cases=[]
def check(name,fn):
 try:fn();cases.append({'id':name,'status':'PASS'})
 except Exception as e:cases.append({'id':name,'status':'FAIL','error':str(e)})
def eq(a,b):assert a==b,(a,b)
def expect(code,fn):
 try:fn()
 except Violation as e:eq(e.code,code)
 else:raise AssertionError('accepted')
for p in patch['patch']:
 mask=p['value'];pos=mask.get('const',mask.get('enum',[None])[0]);v=Draft202012Validator(mask)
 check(p['operationId']+p['path']+':positive',lambda v=v,pos=pos:eq(list(v.iter_errors(pos)),[]))
 for x in [None,1,{},'UNSPECIFIED']:check(p['operationId']+p['path']+':negative:'+str(x),lambda v=v,x=x:eq(bool(list(v.iter_errors(x))),True))
def fixture():
 ob={'runId':'run-1','releaseSha':'a'*40,'planDigest':'b'*64,'fixtureNamespace':'isolated-1','cleanup':['clean-1'],'effects':['effect-1'],'checks':['check-1']}
 inv={k:ob[k] for k in ['runId','releaseSha','planDigest','fixtureNamespace']};store={}
 def put(obj):key=digest(obj);store[key]=canonical(obj);return key
 for family,outcome in [('cleanup','COMPLETE'),('effects','KNOWN'),('checks','TERMINAL')]:
  ev={k:ob[k] for k in ['runId','releaseSha','planDigest','fixtureNamespace']};ev.update(kind='ACCEPTANCE_INVENTORY_EVIDENCE_V1',family=family,itemId=ob[family][0],outcome=outcome)
  inv[family]=[{'id':ob[family][0],'outcome':outcome,'evidenceDigest':put(ev)}]
 inv.update(orphans=[],manualResolutionIds=[]);inventory_digest=digest(inv)
 final={k:ob[k] for k in ['runId','releaseSha','planDigest','fixtureNamespace']};final.update(kind='ACCEPTANCE_CANCEL_FINALIZATION_V1',id='final-1',inventoryDigest=inventory_digest,logicalOperationId='op-1',fence=4,transactionId='tx-1',state='CANCELLED')
 member=[]
 for family in ['event','outbox','audit']:
  ev={'kind':family.upper()+'_ACCEPTANCE_CANCEL_V1','transactionId':'tx-1','logicalOperationId':'op-1','runId':ob['runId'],'inventoryDigest':inventory_digest,'fence':4,'state':'CANCELLED'}
  final[family+'Digest']=put(ev);member.append(final[family+'Digest'])
 final['commitReceiptDigest']=put({'kind':'ATOMIC_TRANSACTION_COMMIT_V1','transactionId':'tx-1','state':'COMMITTED','memberDigests':member})
 retained={'final-1':put(final)}
 return ob,inv,store,retained
ob,inv,store,retained=fixture()
def project(ob,inv,store,retained,terminal=True,finalization_id='final-1',fence=4):return cancellation_projection(ob,inv,digest(inv),store,finalization_id=finalization_id if terminal else None,retained_finalizations=retained,expected_fence=fence)
check('terminal-positive-retained-record',lambda:eq(project(ob,inv,store,retained),{'state':'CANCELLED','cleanupStatus':'COMPLETE','reconciliationStatus':'COMPLETE'}))
check('no-retained-finalization-no-terminal',lambda:eq(project(ob,inv,store,retained,False)['state'],'CANCEL_REQUESTED'))
for family,outcome in [('cleanup','PENDING'),('cleanup','FAILED'),('effects','UNKNOWN'),('effects','PENDING'),('checks','PENDING')]:
 o,v,s,r=fixture();row=v[family][0];ev=json.loads(s[row['evidenceDigest']]);ev['outcome']=outcome;row.update(outcome=outcome,evidenceDigest=digest(ev));s[digest(ev)]=canonical(ev)
 check(family+outcome+':terminal-rejected',lambda o=o,v=v,s=s,r=r:expect('CANCELLED_CLOSURE_INCOMPLETE',lambda:project(o,v,s,r)))
 expected='FAILED' if outcome=='FAILED' else 'UNKNOWN' if outcome=='UNKNOWN' else 'PENDING';field='cleanupStatus' if family=='cleanup' else 'reconciliationStatus'
 check(family+outcome+':own-stage',lambda o=o,v=v,s=s,r=r,field=field,expected=expected:eq(project(o,v,s,r,False)[field],expected))
mutations=[('missing-bytes',lambda o,v,s,r:s.clear(),'EVIDENCE_BYTES_UNAVAILABLE'),('all-zero-evidence',lambda o,v,s,r:v['cleanup'][0].update(evidenceDigest='0'*64),'EVIDENCE_BYTES_UNAVAILABLE'),('extra-valid-flag',lambda o,v,s,r:v.update(valid=True),'INVENTORY_MASK_INVALID'),('integer-obligation',lambda o,v,s,r:o['cleanup'].__setitem__(0,17),'OBLIGATION_ID_INVALID'),('integer-row',lambda o,v,s,r:v['cleanup'][0].update(id=17),'INVENTORY_ENTRY_ID_INVALID'),('foreign-run',lambda o,v,s,r:v.update(runId='foreign'),'INVENTORY_IDENTITY_MISMATCH'),('missing-check',lambda o,v,s,r:v.update(checks=[]),'INVENTORY_OBLIGATION_SET_MISMATCH'),('duplicate-item',lambda o,v,s,r:v['cleanup'].append(copy.deepcopy(v['cleanup'][0])),'INVENTORY_DUPLICATE_ID'),('claimed-other-outcome',lambda o,v,s,r:v['cleanup'][0].update(outcome='FAILED'),'EVIDENCE_BINDING_MISMATCH'),('tampered-evidence-bytes',lambda o,v,s,r:s.update({v['cleanup'][0]['evidenceDigest']:b'{}'}),'EVIDENCE_DIGEST_MISMATCH')]
for name,mut,code in mutations:
 o,v,s,r=fixture();mut(o,v,s,r);check(name,lambda o=o,v=v,s=s,r=r,code=code:expect(code,lambda:project(o,v,s,r)))
for final_id in [True,False,'false',17]:check('nonrecord-finalization:'+str(final_id),lambda final_id=final_id:expect('FINALIZATION_UNAVAILABLE',lambda:project(ob,inv,store,retained,finalization_id=final_id)))
check('stale-fence',lambda:expect('FINALIZATION_FENCE_MISMATCH',lambda:project(ob,inv,store,retained,fence=3)))
for field,value,code in [('inventoryDigest','0'*64,'FINALIZATION_INVENTORY_MISMATCH'),('fixtureNamespace','other','FINALIZATION_BINDING_MISMATCH'),('state','PENDING','FINALIZATION_BINDING_MISMATCH')]:
 o,v,s,r=fixture();f=json.loads(s[r['final-1']]);f[field]=value;r['final-1']=digest(f);s[digest(f)]=canonical(f)
 check('finalization-'+field,lambda o=o,v=v,s=s,r=r,code=code:expect(code,lambda:project(o,v,s,r)))
for family in ['event','outbox','audit']:
 o,v,s,r=fixture();f=json.loads(s[r['final-1']]);ev=json.loads(s[f[family+'Digest']]);ev['transactionId']='foreign-tx';f[family+'Digest']=digest(ev);s[digest(ev)]=canonical(ev);r['final-1']=digest(f);s[digest(f)]=canonical(f)
 check('atomic-'+family+'-other-transaction',lambda o=o,v=v,s=s,r=r:expect('ATOMIC_MEMBER_BINDING_MISMATCH',lambda:project(o,v,s,r)))
o,v,s,r=fixture();f=json.loads(s[r['final-1']]);c=json.loads(s[f['commitReceiptDigest']]);c['state']='ROLLED_BACK';f['commitReceiptDigest']=digest(c);s[digest(c)]=canonical(c);r['final-1']=digest(f);s[digest(f)]=canonical(f)
check('rolled-back-transaction',lambda:expect('COMMIT_RECEIPT_BINDING_MISMATCH',lambda:project(o,v,s,r)))
o,v,s,r=fixture();raw=b'{"kind":"A","kind":"B"}';key=__import__('hashlib').sha256(raw).hexdigest();s[key]=raw;v['cleanup'][0]['evidenceDigest']=key
check('duplicate-json-evidence',lambda:expect('EVIDENCE_DUPLICATE_JSON_KEY',lambda:project(o,v,s,r)))
report={'sourceHead':patch['sourceHead'],'sourceSha256':patch['sourceSha256'],'resourceBindings':patch['resourceBindings'],'cases':cases,'checks':len(cases),'failed':sum(c['status']!='PASS' for c in cases),'referenceOnly':True,'implementationAcceptance':'NOT_EVALUATED','limitations':['Obligation sets and retained evidence stores must originate at the server-owned persistence boundary; this reference does not prove that origin.','Typed transaction commit/member records verify semantic binding, not a real PostgreSQL commit or fence acquisition.','Six field dictionaries do not close complete operations.']}
(OUT/'state-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':report['checks'],'failed':report['failed']}));sys.exit(bool(report['failed']))
