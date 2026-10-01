"""Current connected pre-generation fixtures; whole operation and systemd remain open."""
import hashlib,json,os
from ssot_sources import ROOT,SSOT,resource_index
BASE='audit/generated/resume-905/'
PROOFS={
 'joined':BASE+'archive/review-joined/joined-chain-proof.json',
 'retry':'audit/generated/resume-8cc/coordinator/preserved-retry/producer-child-tests.json',
 'archive':BASE+'sql/review-consumers/archive/archive-proof.json',
 'aad':BASE+'archive/review-key/peer-key-fixed-proof.json',
 'secret':BASE+'consumers/review-secrets/canonical-independent-review.json',
 'ui':BASE+'sql/review-consumers/independent-consumer-review.json',
 'preroot':BASE+'sql/review-preroot-archive/independent-transfer-proof.json',
 'retry-stage':'audit/generated/resume-8cc/key/review-stage/integrated-stage-proof.json',
}
# A fixed complete label universe; an explicitly selected current execution map
# cannot remove obligations. Missing/malformed maps produce structured BLOCKED.
PROOF_MAPPING='audit/generated/resume-8cc/coordinator/current-bounded-evidence.json'
MAPPING_ERROR=None
if (ROOT/PROOF_MAPPING).exists():
 try:
  current=json.loads((ROOT/PROOF_MAPPING).read_text())
  if set(current)!=set(PROOFS) or not all(isinstance(p,str) and p.startswith('audit/') and '..'not in p.split('/') for p in current.values()):raise ValueError('INVALID_COMPLETE_EVIDENCE_MAP')
  PROOFS=current
 except (OSError,ValueError,TypeError) as exc:MAPPING_ERROR=type(exc).__name__+': '+str(exc)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=sha(SSOT);rs=resource_index();checks=[];evidence=[]
 def check(n,ok):checks.append({'case':n,'passed':bool(ok)})
 check('complete-selected-evidence-map',MAPPING_ERROR is None)
 if (ROOT/PROOF_MAPPING).exists():evidence.append({'path':PROOF_MAPPING,'sha256':sha(ROOT/PROOF_MAPPING),'diagnostic':MAPPING_ERROR})
 for label,name in PROOFS.items():
  p=ROOT/name
  if not p.exists():check(label+'/missing-required-proof',False);continue
  try:q=json.loads(p.read_text())
  except (ValueError,UnicodeError):check(label+'/malformed-required-proof',False);continue
  if not isinstance(q,dict):check(label+'/required-proof-object',False);continue
  evidence.append({'path':name,'sha256':sha(p),'executionSource':q.get('sourceDocumentSha256',q.get('sourceSha256'))})
  check(label+'/current-execution-source',q.get('sourceDocumentSha256',q.get('sourceSha256'))==source)
  if label=='secret':
   check(label+'/actual-PG18_6',q.get('postgresVersion')=='18.6')
   required_reports={'publication-postgres-tests.json','owner-binding-postgres-tests.json','safe-role-postgres-tests.json','additional-tests.json'}
   check(label+'/all-required-subproofs',required_reports<=set(q.get('reportsSha256',{})))
   check(label+'/all-required-canonical-modules',{'database/secret-profile-roots.sql','database/secret-profile-publication.sql','database/secret-owner-binding.sql'}<=set(q.get('canonicalResources',{})))
   for path,d in q.get('reportsSha256',{}).items():
    sub=p.parent/path;bound=sub.exists()and sha(sub)==d;check(label+'/bound-report:'+path,bound)
    if not bound:continue
    try:subq=json.loads(sub.read_text())
    except (ValueError,UnicodeError):check(label+'/malformed-subproof:'+path,False);continue
    if not isinstance(subq,dict):check(label+'/malformed-subproof-object:'+path,False);continue
    rows=subq.get('cases',[])
    check(label+'/subproof-current:'+path,subq.get('sourceSha256')==source and subq.get('postgresVersion')=='18.6')
    check(label+'/subproof-executed-results:'+path,bool(rows)and subq.get('failed')==0 and all(x.get('status')=='PASS'for x in rows)and len(rows)==subq.get('checked'))
   modules=q.get('canonicalResources',{})
  else:
   rows=q.get('checks',[])
   check(label+'/actual-positive-derived-results',bool(rows)and all(x.get('passed',x.get('status')=='PASS')for x in rows)and q.get('failed',q.get('failedCount',0))==0)
   if label not in ('ui','retry-stage'):check(label+'/actual-PG18_6',q.get('postgresqlVersion')=='18.6')
   modules=q.get('canonicalInputs',{})
  for path,d in modules.items():check(label+'/canonical-resource:'+path,path in rs and rs[path]['sha256']==d)
  for path,d in q.get('supportSha256',{}).items():
   consumed=ROOT/path
   if label=='archive'and '/'not in path:consumed=ROOT/'scripts'/path if path!='verify_archive.py'else p.parent/path
   check(label+'/consumed-code:'+path,consumed.exists()and sha(consumed)==d)
  if label=='retry':
   check(label+'/exact-producer-child-SQL',q.get('canonicalExtensionSqlSha256')==rs['database/generation-retry-producer-child.sql']['sha256'])
   for path in ['scripts/generation_locked_retry.py','scripts/generation_retry_inventory.py','scripts/generation_admission_contracts.py']:
    check(label+'/required-code-binding:'+path,q.get('supportSha256',{}).get(path)==sha(ROOT/path))
  if label=='retry-stage':
   check(label+'/integrated-helper-bound',q.get('supportSha256',{}).get('scripts/generation_locked_retry.py')==sha(ROOT/'scripts/generation_locked_retry.py'))
   actual={x.get('case')for x in q.get('checks',[])if x.get('passed')}
   for name in ['integrated-discussion-CONFIRMED_APPLIED','integrated-discussion-FAILED_FINAL','integrated-execution-CONFIRMED_APPLIED','integrated-execution-FAILED_FINAL','actual-scan-byte-mutation','classifier-digest-mutation']:
    check(label+'/required:'+name,name in actual)
  if label=='preroot':
   check(label+'/exact-canonical-preroot-archive-SQL',q.get('candidateSqlSha256')==rs['database/generation-preroot-frozen-archive.sql']['sha256']and q.get('canonicalExtensionExecuted')is True)
  if label=='archive':check(label+'/exact-durable-archive-SQL',q.get('canonicalArchiveSha256')==rs['database/generation-frozen-archive.sql']['sha256'])
  if label=='aad':check(label+'/exact-byte-guard-SQL',q.get('candidateSqlSha256')==rs['database/generation-protected-registry-link.sql']['sha256'])
  if label=='ui':check(label+'/actual-root-adapter',q.get('effectiveHelperSha256')==sha(ROOT/'scripts/owner_ui_terminal_read.py'))
  if label=='joined':
   actual={x['id']for x in q['checks']if x['passed']}
   for n in ['one-auth-protected-archive-root-event-commit','independent-observer-sees-entire-committed-chain','actual-postcommit-protected-open-archive-hydration-domain-consumer','missing-archive-rollback-removes-whole-connected-chain','protected-context-swap-rejected-after-valid-archive','available-historical-mask-cannot-replace-root-frozen-pin']:check('joined/required:'+n,n in actual)
 report={'sourceDocumentSha256':source,'status':'PASS'if all(x['passed']for x in checks)else'BLOCKED','checked':len(checks),'failed':sum(not x['passed']for x in checks),'checks':checks,'evidence':evidence,'scope':__doc__,'wholeOperationClosed':False,'systemdSourceProof':'BLOCKED_ENVIRONMENT','SSOT_CONTRACT_READY':'BLOCKED','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT',BASE+'coordinator');out.mkdir(parents=True,exist_ok=True);(out/'producer-archive-chain-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));return int(report['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
