"""Publish current identities and exact bounded subconditions, never a self SHA."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
head_source=hashlib.sha256(subprocess.check_output(['git','show',head+':00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT)).hexdigest()
def load(n):return json.loads((ROOT/n).read_text())
def save(n,q):(ROOT/n).write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
proof='audit/generated/resume-8cc/key/review-eligibility-integrated/canonical-integration-review.json'
q=load(proof)
if q.get('sourceDocumentSha256',q.get('sourceSha256'))!=source:raise ValueError('CURRENT_SECRET_REVIEW_REQUIRED')
conditions=[
 ('SECRET.AUTH.LOCKED_ACCEPTANCE','SECRET.AUTH.CREDENTIAL_ROOT_ELIGIBILITY','Actual current OWNER verifier B, canonical C0/C1 and sorted E10/E20 roots, current same-root API_KEY ACTIVE version/fingerprint; fresh/replay and deletion-wait races; no API-use/retention/systemd proof'),
 ('SECRET.ATOMIC.COMMAND_ROOT','SECRET.ATOMIC.SEMANTIC_RESULT_BINDING','Frozen actual semantic-result bytes/digest equals exact finite receipt; coupled arbitrary digest and valid-SHA wrong bytes reject at COMMIT; no full retained-outcome producer proof'),
 ('SECRET.ATOMIC.COMMAND_ROOT','SECRET.RECORD.STATUS.PERSISTED_PROJECTION','Approved INACTIVE/ACTIVE/DELETED projection; actual create/activation/rotation/deactivation/delete/replay/integrity/concurrent fixture; no full activation/invalidation command authority proof'),
 ('SECRET.READ.IMMUTABLE','SECRET.READ.OWNER_API_IMMUTABLE','Actual current token, locked exact immutable row, typed authenticated original-byte open, private read evidence, explicit current/history selector; no reserved OWNER-session reveal/broker/full-browser proof'),
 ('SECRET.UI.REVEAL','SECRET.UI.OWNER_TYPED_REVEAL_COPY','Exact GET decoder, closed typed approved variants and original-byte copy of same revealed version; no generated backend/visual/runtime acceptance proof'),
]
checklist=load('audit/SSOT_CREATE_CLOSURE_CHECKLIST.json');checklist['sourceSha256']=source
for row in checklist['obligations']:
 row['sourceSha256']=source
 for parent,id_,scope in conditions:
  if row['id']!=parent:continue
  row['state']='IN_PROGRESS';subs=row.setdefault('verifiedSubconditions',[])
  subs[:]=[s for s in subs if s.get('id')!=id_]
  subs.append({'id':id_,'state':'VERIFIED','scope':scope,'authority':['SSOT8.3','SSOT8.16','SSOT25.6','SSOT51.6','SSOT51.20'],'sourceSha256':source,'evidence':proof,'evidenceSha256':hashlib.sha256((ROOT/proof).read_bytes()).hexdigest(),'independentReview':proof,'implementationAcceptance':'NOT_EVALUATED'})
checklist['wholeOperationsClosed']=[]
save('audit/SSOT_CREATE_CLOSURE_CHECKLIST.json',checklist)
register=load('audit/SSOT_COMPLETION_REGISTER.json');register['sourceDocumentSha256']=source
register['createOperationVerifiedSubconditions']=[s for r in checklist['obligations']for s in r.get('verifiedSubconditions',[])]
register['currentFiniteChecklist']={'path':'audit/SSOT_CREATE_CLOSURE_CHECKLIST.json','sha256':hashlib.sha256((ROOT/'audit/SSOT_CREATE_CLOSURE_CHECKLIST.json').read_bytes()).hexdigest(),'parentDenominator':len(checklist['obligations']),'wholeOperationsClosed':0,'limitation':'Parent duties remain open; bounded subconditions overlap and are not a project completion percentage'}
save('audit/SSOT_COMPLETION_REGISTER.json',register)
c=load('audit/SSOT_REPAIR_CHECKPOINT.json')
c.setdefault('historicalSnapshots',[]).append({'type':'prior-work-block','sourceDocumentSha256':c.get('sourceDocumentSha256'),'createBlock':c.get('createBlock'),'nextBlock':c.get('nextBlock')})
c['sourceDocumentSha256']=c['currentSourceDocumentSha256']=source
c['continuationInput'].update(sourceSha256=source,lastVerifiedCommittedBlock=head,lastVerifiedCommittedBlockSSOTSha256=head_source)
c['currentRun'].update(status='PARTIAL',currentSourceDocumentSha256=source,priorCommittedHead=head,currentCanonicalReview=proof,completedSubconditions=[x[1]for x in conditions],integrityDuringWork='INVALIDATED_BY_CURRENT_CHANGES; final manifests/receipt after frozen evidence')
c['createBlock']={'status':'PARTIAL','sourceSha256':source,'checklist':'audit/SSOT_CREATE_CLOSURE_CHECKLIST.json','operationDesignClosure':{'generation.job.create':'OPEN','secret.create':'OPEN'},'currentNormativeAdditions':['§8.3 OWNER approved projection','§25.6 OWNER approved projection','§8.15','§8.16','§12.56 key only'],'boundedIntegrated':conditions,'evidence':proof,'missing':['Full RETRY producer/native ordered transaction integration','Trusted complete archived policies/source authority','Real systemd source/invocation/global nonce producer','Secret API-use evidence/retained outcomes/retention','Rotation invalidation inventory/target/broker','Read/UI/full-browser and generic SQL helper callsites']}
c['nextBlock']={'id':'RETRY_AUTHENTICATED_NATIVE_CHILD_AND_FULL_LEDGER_PRODUCER','scope':'Integrate independently reproduced ordered ledger/native child and late-ticket publisher; complete exact H-order repairs/registry; preserve bounded Secret fixes and finish rotation inventory-dependent boundary','inputs':['audit/generated/resume-8cc/native/INSTALLATION.md','audit/generated/resume-8cc/ledger/order-repair/DELIVERY.json',proof],'generationWholeOperation':'OPEN','secretWholeOperation':'OPEN'}
c['SSOT_CONTRACT_READY']='BLOCKED';c['IMPLEMENTATION_PRODUCTION_ACCEPTANCE']='NOT_EVALUATED'
save('audit/SSOT_REPAIR_CHECKPOINT.json',c)
print(json.dumps({'source':source,'completedSubconditions':len(conditions),'wholeOperationsClosed':0}))
