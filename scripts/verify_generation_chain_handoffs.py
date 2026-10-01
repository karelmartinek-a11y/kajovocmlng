"""Source-bound independent actual PG authentication/persistence/read chain evidence.

This verifies the reproducible independent fixture's consumed modules, not runtime
acceptance or whole-operation readiness. Missing/stale evidence is BLOCKED.
"""
import hashlib,json,os
from ssot_sources import ROOT,SSOT,resource_index
PROOF='audit/generated/closure-replan-84c/secret/compatibility/runs/final-116e/authchain/tree/audit/generated/resume-905/sql/review-current/authenticated-chain-review.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/resume-34d/coordinator');out.mkdir(parents=True,exist_ok=True)
 path=ROOT/PROOF;checks=[];rs=resource_index()
 def check(name,ok):checks.append({'case':name,'passed':bool(ok)})
 if path.exists():
  q=json.loads(path.read_text());check('actual-independent-native-chain',q.get('status')=='PASS' and q.get('failed')==0 and q.get('checked',0)>=14)
  check('actual-PostgreSQL18_6',q.get('postgresqlVersion')=='18.6')
  check('current-source',q.get('sourceDocumentSha256')==sha(SSOT))
  modules=q.get('integratedSqlDigests',{})
  required={'database/generation-create-authentication.sql','database/generation-create-preroot.sql','database/generation-create-read.sql','database/generation-locked-retry.sql'}
  check('all-named-modules',required<=set(modules))
  for p,d in modules.items():check('canonical-sql:'+p,p in rs and rs[p]['sha256']==d)
  implementations=q.get('rootImplementationDigests',{})
  check('root-auth-and-read-executed',{'generation_auth_crypto.py','generation_auth_acceptance.py','generation_read_hydration.py'}<=set(implementations))
  for p,d in implementations.items():check('actual-root-helper:'+p,(ROOT/'scripts'/p).exists() and sha(ROOT/'scripts'/p)==d)
  check('canonical-foundation',q.get('canonicalSqlSha256')==rs['database/generation-create-foundations.sql']['sha256'])
  support=q.get('supportSha256',{})
  required_support={'audit/generated/resume-34d/auth-crypto/verify_authenticated_full_chain.py','audit/generated/resume-34d/auth-crypto/auth_crypto_reference.py','audit/generated/resume-34d/auth-crypto/acceptance_reference.py','audit/generated/resume-34d/auth-crypto/libpq_fixture.py','audit/generated/resume-34d/auth-crypto/authentication-request-binding-proposed.sql','audit/generated/resume-d362/events/verify_combined_generation.py'}
  check('all-named-consumed-support',isinstance(support,dict) and required_support<=set(support))
  if isinstance(support,dict):
   for p,d in support.items():
    scoped=isinstance(p,str) and not p.startswith('/') and '..'not in p.split('/')
    check('consumed-support:'+str(p),scoped and (ROOT/p).is_file() and sha(ROOT/p)==d)
 else:check('independent-evidence-available',False)
 report={'sourceDocumentSha256':sha(SSOT),'status':'PASS' if all(c['passed']for c in checks) else 'BLOCKED','checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'evidence':str(path.relative_to(ROOT)),'evidenceSha256':sha(path) if path.exists() else None,'scope':__doc__,'wholeOperationClosed':False,'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 (out/'generation-chain-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','checked','failed']}));return int(report['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
