from pathlib import Path
import sys,ast,copy,json,hashlib
HERE=Path(__file__).parent;D=HERE.parent/'sql-lifecycle';sys.path.insert(0,str(D))
import state_reference as s
ns={k:getattr(s,k) for k in ['canonical','digest']};ns['json']=json
tree=ast.parse((D/'verify_states.py').read_text());factory=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fixture')
exec(compile(ast.Module(body=[factory],type_ignores=[]),'isolated-author-fixture','exec'),ns)
cases=[]
def project(ob,inv,store,retained):return s.cancellation_projection(ob,inv,s.digest(inv),store,finalization_id='final-1',retained_finalizations=retained,expected_fence=4)
o,v,st,r=ns['fixture']();assert project(o,v,st,r)['state']=='CANCELLED';cases.append({'id':'corrected-domain-positive','passed':True})
def check(name,expected,mutate):
 o,v,st,r=ns['fixture']();mutate(o,v,st,r)
 try:project(o,v,st,r);actual='ACCEPTED'
 except s.Violation as e:actual=e.code
 except Exception as e:actual=type(e).__name__+':'+str(e)
 cases.append({'id':name,'expected':expected,'actual':actual,'passed':expected==actual})
check('zero-hash-no-bytes','EVIDENCE_BYTES_UNAVAILABLE',lambda o,v,st,r:v['cleanup'][0].update(evidenceDigest='0'*64))
check('integer-id-both-obligation-and-item','OBLIGATION_ID_INVALID',lambda o,v,st,r:(o['cleanup'].__setitem__(0,17),v['cleanup'][0].update(id=17)))
check('boolean-finalization-is-not-record','FINALIZATION_UNAVAILABLE',lambda o,v,st,r:r.clear())
def forged_receipt(o,v,st,r):
 key=v['effects'][0]['evidenceDigest'];receipt=json.loads(st[key]);receipt['fixtureNamespace']='other-fixture';new=s.digest(receipt);st[new]=s.canonical(receipt);v['effects'][0]['evidenceDigest']=new
check('same-valid-shape-other-namespace','EVIDENCE_BINDING_MISMATCH',forged_receipt)
def wrong_member(o,v,st,r):
 final=json.loads(st[r['final-1']]);outbox=json.loads(st[final['outboxDigest']]);outbox['logicalOperationId']='other-op';new=s.digest(outbox);st[new]=s.canonical(outbox);final['outboxDigest']=new;newfinal=s.digest(final);st[newfinal]=s.canonical(final);r['final-1']=newfinal
check('outbox-same-transaction-other-operation','ATOMIC_MEMBER_BINDING_MISMATCH',wrong_member)
report={'scope':'Independent exact domain witness, corrected lifecycle reference. No old-signature TypeError accepted as proof.','cases':cases,'checks':len(cases),'failed':sum(not c['passed'] for c in cases),'consumedSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'state_reference.py',D/'verify_states.py']},'trustedOriginAndRealCommit':'NOT_PROVEN'}
(HERE/'corrected-state-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(cases),'failed':report['failed']}))
