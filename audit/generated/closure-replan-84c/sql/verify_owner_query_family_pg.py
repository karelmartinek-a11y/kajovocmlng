from pathlib import Path
import sys,json,secrets,hashlib
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(OUT),str(ROOT/'scripts'),str(ROOT/'audit/generated/resume-8cc/native'),str(ROOT/'audit/generated/resume-8cc/native/credential-root')]
from native_auth_factory import Factory,uid,lit,b,sha,OWNER,DB,SSOT
from credential_root_fixture import install_current_credential_secret
from owner_query_context import prepare,create_temp,finish
admin=DB('postgres')
if not admin.query("SELECT 1 FROM pg_database WHERE datname='helper_owner_queries_utf8_84c'"):admin.query("CREATE DATABASE helper_owner_queries_utf8_84c TEMPLATE template0 ENCODING 'UTF8'")
admin.close()
f=Factory('helper_owner_queries_utf8_84c');sid,vid=install_current_credential_secret(f);db=f.db;checks=[]
family=json.loads((OUT/'owner-query-family.json').read_text())['family'];byop={v['operationId']:v for v in family}
db.query((OUT/'owner-query-helpers.sql').read_text());db.query((OUT/'owner-query-original-wrappers.sql').read_text())
for v in family:db.query('REVOKE ALL ON FUNCTION public.'+v['functionName']+'(public.kcml_operation_context_v1) FROM PUBLIC')
# Isolated issuer fixture: actual randomly created session bytes, hash and epoch.
# Login/MFA/API-key-exchange producer is explicitly a separate shared obligation.
cookie=secrets.token_urlsafe(32).encode('ascii');session=uid(8800);dg=sha(cookie)
db.query('INSERT INTO public.owner_session(id,owner_identity_id,lookup_digest,session_hash,created_at,last_seen_at,expires_at,session_epoch)VALUES('+','.join([lit(session),lit(OWNER),b(dg),lit('KCML_OWNER_SESSION_SHA256_V1:'+dg.hex()),'clock_timestamp()','clock_timestamp()',"clock_timestamp()+interval '1 hour'",db.query('SELECT session_epoch FROM public.owner_identity WHERE singleton_key=1')[0][0]])+');')
def rec(n,ok,diagnostic=None):assert ok,(n,diagnostic);checks.append({'case':n,'passed':True,'actualDiagnostic':diagnostic})
def begin():
 create_temp(db);db.query("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;SET LOCAL lock_timeout='3000ms';SET LOCAL statement_timeout='60s';SET LOCAL idle_in_transaction_session_timeout='60s'")
def end():db.query('ROLLBACK');finish(db)
def invoke(op,c):return json.loads(db.query('SELECT public.'+byop[op]['functionName']+'('+lit(c)+'::public.kcml_operation_context_v1)')[0][0])
for op in byop:
 begin();ctx=prepare(db,op,cookie,'OWNER_SESSION',byop[op]['descriptorDigest']);value=invoke(op,ctx)
 if op.endswith('.read'):rec('actual-original-read-wrapper-4helpers-metadata-only',set(value)=={'secretId','secretVersionId','fingerprint','credentialVersion','credentialActivationEpoch','createdAt','rotatedAt','lastUsedAt'}and'value'not in value and'verifierHash'not in value)
 else:rec('actual-original-reveal-wrapper-4helpers-typed-internal-row',value['secretVersionId']==vid and'ciphertextHex'in value and'verifierHash'not in value)
 end()
def negative(n,op,preparefn,code):
 begin()
 try:
  c=preparefn();invoke(op,c);raise AssertionError('INVALID_ACCEPTED')
 except (ValueError,RuntimeError)as e:rec(n,code in str(e),str(e).splitlines()[0])
 end()
negative('unknown-context-does-not-grant-authority','ownerApiKey.read',lambda:uid(990),'OWNER_QUERY_TRUSTED_CONTEXT_REQUIRED')
negative('wrong-owner-session-raw-bytes-rejected','ownerApiKey.read',lambda:prepare(db,'ownerApiKey.read',cookie+b'x','OWNER_SESSION',byop['ownerApiKey.read']['descriptorDigest']),'OWNER_SESSION_STALE')
begin();ctx=prepare(db,'ownerApiKey.reveal',f.token,'OWNER_API_KEY',byop['ownerApiKey.reveal']['descriptorDigest']);value=invoke('ownerApiKey.reveal',ctx);rec('actual-API-owner-dedicated-reveal-supported',value['secretVersionId']==vid and 'ciphertextHex' in value);end()
negative('wrong-owner-API-raw-bytes-rejected','ownerApiKey.reveal',lambda:prepare(db,'ownerApiKey.reveal',f.token+b'x','OWNER_API_KEY',byop['ownerApiKey.reveal']['descriptorDigest']),'OWNER_API_AUTHENTICATION_FAILED')
negative('read-context-cannot-dispatch-reveal-wrapper','ownerApiKey.reveal',lambda:prepare(db,'ownerApiKey.read',cookie,'OWNER_SESSION',byop['ownerApiKey.read']['descriptorDigest']),'OWNER_QUERY_DESCRIPTOR_MISMATCH')
# Exact helper-plan negatives derived from a successful read context/static plan.
begin();ctx=prepare(db,'ownerApiKey.read',cookie,'OWNER_SESSION',byop['ownerApiKey.read']['descriptorDigest'])
positive_plan=json.loads(db.query("SELECT public.kcml_owner_query_expected_plan_v1('ownerApiKey.read')")[0][0])
mutant=dict(positive_plan);mutant['unknownTrustedField']=True
try:db.query('SELECT public.kcml_apply_exact_domain_plan_v1('+lit(ctx)+'::public.kcml_operation_context_v1,'+lit(json.dumps(mutant))+'::jsonb)');raise AssertionError('PLAN_EXTRA_ACCEPTED')
except RuntimeError as e:rec('extra-helper-plan-field-rejected-specific','OWNER_QUERY_EXACT_PLAN_MISMATCH'in str(e),str(e).splitlines()[0])
end()
# Dedicated OWNER key catalog supports both verified OWNER channels (§7.2); generic Secret read restriction is separate.
begin();ctx=prepare(db,'ownerApiKey.read',f.token,'OWNER_API_KEY',byop['ownerApiKey.read']['descriptorDigest']);value=invoke('ownerApiKey.read',ctx);rec('actual-API-owner-metadata-read-supported',value['credentialVersion']=='1');end()
db.query('UPDATE public.owner_session SET revoked_at=clock_timestamp()WHERE id='+lit(session))
negative('persisted-revocation-rejected','ownerApiKey.read',lambda:prepare(db,'ownerApiKey.read',cookie,'OWNER_SESSION',byop['ownerApiKey.read']['descriptorDigest']),'OWNER_SESSION_STALE')
assert SSOT.read_bytes()==f.source
report={'status':'PASS','passed':len(checks),'checks':checks,'sourceDocumentSha256':sha(f.source).hex(),'postgresqlVersion':db.query('SHOW server_version')[0][0],'serverEncoding':db.query('SHOW server_encoding')[0][0],'actualOriginalWrapperSha256':sha((OUT/'owner-query-original-wrappers.sql').read_bytes()).hex(),'helperSqlSha256':sha((OUT/'owner-query-helpers.sql').read_bytes()).hex(),'originalWrapperFamily':['ownerApiKey.read','ownerApiKey.reveal'],'helperCallsExecutedPerPositive':4,'wholeOperationsClosed':[],'remaining':['Precise normative technical session verifier profile/actual session issuer integration','Canonical key/nonce source and actual authenticated reveal hydration','Audit attribution and HTTP response/consumer exact masks','Runtime role/grant profile and replacement typed plans','All260 sibling wrappers/domain plans']}
(OUT/'owner-query-postgres-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':len(checks)}))
