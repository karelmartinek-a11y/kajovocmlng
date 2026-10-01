"""Current connected pre-generation fixtures; whole operation and systemd remain open."""
import hashlib,json,os
from ssot_sources import ROOT,SSOT,resource_index
BASE='audit/generated/resume-905/'
PROOFS={
 'joined':BASE+'archive/review-joined/joined-chain-proof.json',
 'retry':BASE+'sql/review-consumers/retry/producer-child-tests.json',
 'archive':BASE+'sql/review-consumers/archive/archive-proof.json',
 'aad':BASE+'archive/review-key/peer-key-fixed-proof.json',
 'secret':BASE+'consumers/review-secrets/canonical-independent-review.json',
 'ui':BASE+'sql/review-consumers/independent-consumer-review.json',
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=sha(SSOT);rs=resource_index();checks=[];evidence=[]
 def check(n,ok):checks.append({'case':n,'passed':bool(ok)})
 for label,name in PROOFS.items():
  p=ROOT/name
  if not p.exists():check(label+'/missing-required-proof',False);continue
  q=json.loads(p.read_text());evidence.append({'path':name,'sha256':sha(p),'executionSource':q.get('sourceDocumentSha256',q.get('sourceSha256'))})
  check(label+'/current-execution-source',q.get('sourceDocumentSha256',q.get('sourceSha256'))==source)
  if label=='secret':
   check(label+'/actual-PG18_6',q.get('postgresVersion')=='18.6')
   for path,d in q.get('reportsSha256',{}).items():check(label+'/bound-report:'+path,(p.parent/path).exists()and sha(p.parent/path)==d)
   modules=q.get('canonicalResources',{})
  else:
   rows=q.get('checks',[])
   check(label+'/actual-positive-derived-results',bool(rows)and all(x.get('passed',x.get('status')=='PASS')for x in rows)and q.get('failed',q.get('failedCount',0))==0)
   if label!='ui':check(label+'/actual-PG18_6',q.get('postgresqlVersion')=='18.6')
   modules=q.get('canonicalInputs',{})
  for path,d in modules.items():check(label+'/canonical-resource:'+path,path in rs and rs[path]['sha256']==d)
  for path,d in q.get('supportSha256',{}).items():
   consumed=ROOT/path
   if label=='archive'and '/'not in path:consumed=ROOT/'scripts'/path if path!='verify_archive.py'else p.parent/path
   check(label+'/consumed-code:'+path,consumed.exists()and sha(consumed)==d)
  if label=='retry':check(label+'/exact-producer-child-SQL',q.get('canonicalExtensionSqlSha256')==rs['database/generation-retry-producer-child.sql']['sha256'])
  if label=='archive':check(label+'/exact-durable-archive-SQL',q.get('canonicalArchiveSha256')==rs['database/generation-frozen-archive.sql']['sha256'])
  if label=='aad':check(label+'/exact-byte-guard-SQL',q.get('candidateSqlSha256')==rs['database/generation-protected-registry-link.sql']['sha256'])
  if label=='ui':check(label+'/actual-root-adapter',q.get('effectiveHelperSha256')==sha(ROOT/'scripts/owner_ui_terminal_read.py'))
  if label=='joined':
   actual={x['id']for x in q['checks']if x['passed']}
   for n in ['one-auth-protected-archive-root-event-commit','independent-observer-sees-entire-committed-chain','actual-postcommit-protected-open-archive-hydration-domain-consumer','missing-archive-rollback-removes-whole-connected-chain','protected-context-swap-rejected-after-valid-archive','available-historical-mask-cannot-replace-root-frozen-pin']:check('joined/required:'+n,n in actual)
 report={'sourceDocumentSha256':source,'status':'PASS'if all(x['passed']for x in checks)else'BLOCKED','checked':len(checks),'failed':sum(not x['passed']for x in checks),'checks':checks,'evidence':evidence,'scope':__doc__,'wholeOperationClosed':False,'systemdSourceProof':'BLOCKED_ENVIRONMENT','SSOT_CONTRACT_READY':'BLOCKED','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT',BASE+'coordinator');out.mkdir(parents=True,exist_ok=True);(out/'producer-archive-chain-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));return int(report['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
