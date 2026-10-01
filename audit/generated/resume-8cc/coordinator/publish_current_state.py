"""Publish exact current bounded closure; never self-commit identity or whole PASS."""
import collections,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
source=hashlib.sha256(SSOT.read_bytes()).hexdigest();rs=resource_index()
def load(p):return json.loads((ROOT/p).read_text())
def save(p,q):(ROOT/p).write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
secret='audit/generated/resume-8cc/secrets/review-status-ui/canonical-final/DELIVERY.json'
ledger='audit/generated/resume-8cc/ledger/canonical-final/DELIVERY.json'
for p,key in [(secret,'sourceSha256'),(ledger,'canonicalSourceSha256')]:
 q=load(p)
 if q[key]!=source:raise ValueError('STALE_REQUIRED_PROOF:'+p)
checks=[]
for p,fields in [(secret,'consumedCanonicalResources'),(ledger,'canonicalResourceHashes')]:
 for n,d in load(p)[fields].items():
  ok=rs[n]['sha256']==d;checks.append({'input':n,'passed':ok})
  if not ok:raise ValueError('CANONICAL_INPUT_DRIFT:'+n)
oldpeer='audit/generated/resume-8cc/key/review-eligibility-integrated/canonical-integration-review.json'
peer=load(oldpeer)
# Reuse only the unchanged status and create-eligibility subfixtures. The old
# OWNER-read/schema/transport reports are superseded, never called current.
for n in ['database/secret-command-chain.sql','database/secret-record-status.sql']:
 if peer['canonicalRawResourceSha256'][n]!=rs[n]['sha256']:raise ValueError('SELECTED_OLD_FIXTURE_SOURCE_CHANGED:'+n)
for n in ['scripts/secret_command_chain.py','scripts/generation_auth_crypto.py','scripts/secret_profile_reference.py']:
 if peer['actualRootSupportSha256'][n]!=sha(n):raise ValueError('SELECTED_OLD_HELPER_CHANGED:'+n)
reuse={'currentSourceSha256':source,'executionSourcePreserved':peer['sourceSha256'],'method':'Only exact unchanged canonical status/create-command and their declared helpers; old OWNER read/transport superseded','subproofs':[peer['evidence']['eligibility45'],peer['evidence']['status23']],'wholeOperationClosed':False,'limits':['No real credential provisioning, retention, complete invalidation or systemd source'],'checks':checks}
save('audit/generated/resume-8cc/coordinator/selected-proof-reuse.json',reuse)
conds=[
 ('SECRET.AUTH.LOCKED_ACCEPTANCE','SECRET.AUTH.CREDENTIAL_ROOT_ELIGIBILITY','Current locked OWNER API credential/root guards for fresh/replay/deletion wait; API-use/retention/provisioning/systemd OPEN','audit/generated/resume-8cc/coordinator/selected-proof-reuse.json'),
 ('SECRET.ATOMIC.COMMAND_ROOT','SECRET.ATOMIC.SEMANTIC_RESULT_BINDING','Exact bounded create semantic-result bytes/digest; full failure/unknown/retention decision producers OPEN','audit/generated/resume-8cc/coordinator/selected-proof-reuse.json'),
 ('SECRET.ATOMIC.COMMAND_ROOT','SECRET.RECORD.STATUS.PERSISTED_PROJECTION','Approved derived INACTIVE/ACTIVE/DELETED projection, actual transition/concurrency/integrity/replay fixture; complete invalidation command not asserted','audit/generated/resume-8cc/coordinator/selected-proof-reuse.json'),
 ('SECRET.READ.IMMUTABLE','SECRET.READ.OWNER_API_IMMUTABLE','Actual non-reserved OWNER API metadata/current/history read plus authenticated typed original-byte open; reserved OWNER session/broker/historical recovery OPEN',secret),
 ('SECRET.UI.REVEAL','SECRET.UI.OWNER_TYPED_REVEAL_COPY','Actual closed native masks/GET decoder; same root/stateVersion/version readonly status and exact revealed-byte COPY; complete UI backend runtime OPEN',secret),
 ('GENERATION.BASIS.RETRY_PRODUCER','GEN.RETRY.PRODUCER.FINITE_ORDERED_LEDGER','Canonical SQL48 actual typed evidence/CAS/classifier/allocator/checkpoint order/atomic dispatch/concurrency/replay/rollback cases; full audit/unknown/reconcile/compensation and source authority OPEN',ledger),
]
checklist=load('audit/SSOT_CREATE_CLOSURE_CHECKLIST.json');checklist['sourceSha256']=source
missing={
 'GENERATION.AUTH.API_ACCEPTANCE':'Bounded real API-token acceptance/native RETRY reproduced; remaining trusted credential genesis/historical references, full API-use and physical H receipt/context registry; genuine systemd invocation transitively blocked',
 'GENERATION.BASIS.RETRY_PRODUCER':'Ordered intent/evidence/checkpoint finite producer reproduced; complete audit/unknown/reconciliation/compensation outcomes, trusted parent/cancel/deadline/binding/budget producers and full physical lock registration remain',
 'GENERATION.BASIS.RETRY_CHILD_COMMIT':'Bounded authenticated native child/source-parent commit installed; complete trusted source approval/budget, all implicit FK physical H ordering, ledger exceptional decision outcomes, credential genesis/historical references and genuine key authority remain',
 'GENERATION.ARCHIVE.PRODUCER':'Late same-TX archive ticket and scoped publisher primitive installed; actual deployment/installer capability issuer and full kind-policy/dependency producer coverage remain',
 'GENERATION.ARCHIVE.HISTORICAL_POLICY':'Frozen exact historical bytes/two policies reproduced; all UPDATE/RETRY/REPAIR/FOLLOW_UP accept/reject dependency classifier coverage remains',
 'SECRET.OWNER_CREDENTIAL':'Scoped exact E20 credential-root guards verified; independently corrected rotation proposal remains inactive until authoritative complete invalidation inventory and retained result/consumer authority; real genesis/systemd/historical references remain',
 'SECRET.READ.IMMUTABLE':'Bounded typed current/history OWNER API metadata/value producer installed; reserved credential OWNER-session reveal, full audit/usage/bindings/rotation policy/history codec/recovery and broker consumers remain',
 'SECRET.UI.REVEAL':'Bounded typed readonly root-status metadata and exact same-version reveal/COPY installed; full import/activation/worker/read-result pipeline, reserved session reveal and generated backend runtime remain',
 'UI.MANUAL_VISUAL':'Actual96 live+4 Secret canonical captures with selected-source bindings and four-crop review; remaining124 admin screenshots HISTORICAL_UNBOUND, full mandatory manual universe PENDING',
}
for row in checklist['obligations']:
 row['sourceSha256']=source
 if row['id']in missing:row['missing']=missing[row['id']];row['state']='IN_PROGRESS'if row['state']!='BLOCKED'else'BLOCKED'
 previous=row.pop('verifiedSubconditions',[])
 if previous:row.setdefault('historicalSubconditions',[]).extend(previous)
 subs=[]
 for parent,id_,scope,p in conds:
  if row['id']==parent:subs.append({'id':id_,'state':'VERIFIED','scope':scope,'authority':['SSOT8.16'if parent.startswith('SECRET')else'SSOT12.57','SSOT51.6','SSOT51.20'],'sourceSha256':source,'evidence':p,'evidenceSha256':sha(p),'independentReview':p,'implementationAcceptance':'NOT_EVALUATED'})
 if subs:row['verifiedSubconditions']=subs;row['state']='IN_PROGRESS'
checklist['wholeOperationsClosed']=[];save('audit/SSOT_CREATE_CLOSURE_CHECKLIST.json',checklist)
previous=load('audit/SSOT_COMPLETION_REGISTER.json');current=load('audit/generated/resume-8cc/coordinator/current-register-inventory.json')
current['historicalRegisterSummary']={'sourceDocumentSha256':previous.get('sourceDocumentSha256'),'coverage':previous.get('coverage'),'note':'Fresh structural inventory re-counted. Prior overlays/proofs are retained in Git/history; inventory states do not invalidate exact selected fixture reuse or confer semantic closure.'}
current['createOperationVerifiedSubconditions']=[s for r in checklist['obligations']for s in r.get('verifiedSubconditions',[])]
current['currentFiniteChecklist']={'path':'audit/SSOT_CREATE_CLOSURE_CHECKLIST.json','sha256':sha('audit/SSOT_CREATE_CLOSURE_CHECKLIST.json'),'parentDenominator':36,'ownOperationDuties':24,'sharedDependencies':12,'wholeOperationsClosed':0,'limitation':'Six bounded subconditions overlap; no parent VERIFIED and no project percentage'}
save('audit/SSOT_COMPLETION_REGISTER.json',current)
c=load('audit/SSOT_REPAIR_CHECKPOINT.json');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();hs=hashlib.sha256(subprocess.check_output(['git','show',head+':00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT)).hexdigest()
c['sourceDocumentSha256']=c['currentSourceDocumentSha256']=source;c['continuationInput'].update(sourceSha256=source,lastVerifiedCommittedBlock=head,lastVerifiedCommittedBlockSSOTSha256=hs)
c['currentRun'].update(status='PARTIAL',currentSourceDocumentSha256=source,priorCommittedHead=head,completedSubconditions=[x[1]for x in conds],currentCanonicalReview=secret)
c['createBlock']['boundedIntegratedEvidence']=[{'path':p,'sha256':sha(p)}for p in sorted({x[3]for x in conds})]
c['createBlock']['canonicalGenerationResources']='01_UI_CONTRACT/contracts/generation/ordered-native-retry-handoffs.json'
c['createBlock']['closureChecklist']={'parentDuties':36,'boundedVerifiedSubconditions':6,'wholeOperationsClosed':0}
m=load('audit/phase1-operation-schema-matrix.json');boundaries=[b for o in m['operations']for b in o['boundaries']]+[b for o in m['operations']for r in o['routes']for b in r['boundaries']];unique={b['reference']:b for b in boundaries}
roles=dict(collections.Counter(b['role']for b in unique.values()if b.get('concreteness')=='GENERIC_ENVELOPE'))
c['currentMetrics']={**m['summary'],'genericBoundaryRoles':roles,'openStateFields':0,'UIExposureBlockers':3,'SQLHelpersMissing':4,'errorPredicatesPendingSemanticReview':current['coverage']['errorPredicatesNeedingExplicitReview'],'provenanceDetectorHits':current['coverage']['provenanceDetectorHits'],'wholeOperationsClosed':0}
c['metricChanges']={'genericBoundaryDefinitions':[1500,m['summary']['genericBoundaryDefinitions']],'genericRequests':[500,roles.get('request')],'genericResponses':[500,roles.get('response')],'genericEvents':[500,roles.get('event')],'genericRoutes':[500,m['summary']['genericRoutes']],'unresolvedReferences':[242,m['summary']['unresolvedOperationReferences']],'unspecifiedEvents':[152,m['summary']['unspecifiedEventApplicability']],'provenanceHits':[175,current['coverage']['provenanceDetectorHits']],'note':'Two OWNER read request+response masks made concrete; their event boundaries remain generic, so generic route count is unchanged. Lexical provenance extra hit is the approved root-status paragraph containing historická, not proof of a new defect.'}
c['environmentBlockers']=[{'id':'SHARED.CRYPTO.SYSTEMD_SOURCE','type':'ENVIRONMENT','reason':'PID1 tail; no actual systemd manager, bus socket or invocation credential socket; unsupported privileged/nested workaround not attempted','reproduction':'audit/generated/resume-8cc/key/INTEGRATION.md','transitivelyBlocked':['SHARED.CRYPTO.KEY_INVOCATION','SHARED.CRYPTO.GLOBAL_NONCE','GENERATION.AUTH.API_ACCEPTANCE','GENERATION.ATOMIC.ALL_KINDS','SECRET.AUTH.LOCKED_ACCEPTANCE','SECRET.ATOMIC.COMMAND_ROOT','SECRET.OWNER_CREDENTIAL'],'scope':'Finite isolated crypto/auth/PG proves only declared fixture boundaries, not genuine manager invocation'}]
c['productDecisionsRemaining']=[];c['SSOT_CONTRACT_READY']='BLOCKED';c['IMPLEMENTATION_PRODUCTION_ACCEPTANCE']='NOT_EVALUATED';save('audit/SSOT_REPAIR_CHECKPOINT.json',c)
print(json.dumps({'source':source,'parents':36,'verifiedBounded':6,'wholeClosed':0,'metrics':c['currentMetrics']}))
