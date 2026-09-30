from pathlib import Path
import sys, json, hashlib, secrets, copy, subprocess, threading, time, importlib.util
HERE=Path(__file__).parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'audit/generated/resume-d362/persistence'))
from ssot_sources import resource_index,SSOT
from auth_crypto_reference import *
from acceptance_reference import authenticate_owner_api
from libpq_fixture import DB,lit
from context_fixture_exports import common,call
from generation_descriptor_registry import pin,descriptor
from create_operation_contracts import strict_json,validate_body
checks=[]
def test(name,fn,code=None):
 try:
  fn();ok=code is None;actual=None
 except Exception as e:
  actual=str(e);ok=code is not None and code in actual
 checks.append({'case':name,'passed':ok,'expectedDiagnostic':code,'actualDiagnostic':actual})
def capture(fn):
 try:fn()
 except Exception as e:return str(e)
 return None
raw=SSOT.read_bytes();rs=resource_index();sql=rs['database/generation-create-foundations.sql']['raw'].decode();database='auth_crypto_34d'
admin=DB('postgres')
if not admin.query('SELECT 1 FROM pg_database WHERE datname='+lit(database)):admin.query('CREATE DATABASE '+database)
admin.close();db=DB(database);db.query('DROP SCHEMA public CASCADE;CREATE SCHEMA public;');db.query(sql);auth_sql=rs.get('database/generation-create-authentication.sql',{}).get('raw',(HERE/'authentication-request-binding-proposed.sql').read_bytes())
assert auth_sql==(HERE/'authentication-request-binding-proposed.sql').read_bytes(),'AUTH_EXTENSION_EMBEDDED_BYTES_DIFFER_FROM_REVIEWED_CANDIDATE'
db.query(auth_sql.decode())
# Actual current embedded SQL is executed unchanged before scoped extension.
token=secrets.token_urlsafe(32).encode('ascii');owner='00000000-0000-4000-8000-000000000005';auth='00000000-0000-4000-8000-000000000007';job='00000000-0000-4000-8000-000000000002';snap='00000000-0000-4000-8000-000000000008';op='00000000-0000-4000-8000-000000000001'
body={'intent':'Create a synthetic component.','kind':'CREATE','targetKind':'PLATFORM_COMPONENT','sources':[{'kind':'TEXT','text':'Synthetic positive fixture input.'}]};plain=canonical(body);request_digest=sha(b'request-scope'+plain)
# Isolated gateway fixture ceiling only: production effective ceiling must be pinned
# to actual gateway transport policy; 4096 is not imposed on product credentials.
HEADER_FIXTURE_CEILING=4096
base=common(owner,owner,1)+f"INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,state_version,credential_activation_epoch,created_at)VALUES(1,'90000000-0000-4000-8000-000000000001','90000000-0000-4000-8000-000000000002',{lit(verifier_hash(token))},{lit(fingerprint(token))},1,0,1,clock_timestamp());"
db.query(base)
def auth_call(t=token,digest=request_digest):return authenticate_owner_api(db,t,digest,HEADER_FIXTURE_CEILING,descriptor(owner,'sha256:'+bytes.fromhex('05'*32).hex(),pin()))
def with_tx(fn):
 db.query('BEGIN')
 try:return fn()
 finally:db.query('ROLLBACK')
test('actual-token-authenticated-under-share-lock',lambda:with_tx(auth_call))
test('authentication-requires-transaction',auth_call,'OWNER_API_ACCEPTANCE_TRANSACTION_REQUIRED')
test('wrong-token',lambda:with_tx(lambda:auth_call(secrets.token_bytes(32))),'OWNER_API_AUTHENTICATION_FAILED')
test('old-token-exact-bytes-no-trim',lambda:with_tx(lambda:auth_call(token+b' ')),'OWNER_API_AUTHENTICATION_FAILED')
test('missing-policy-not-contract-pass',lambda:verify_token(token,verifier_hash(token),None),'OWNER_API_TRANSPORT_POLICY_UNRESOLVED')
test('unknown-verifier-codec',lambda:verify_token(token,'synthetic-not-verifier',4096),'OWNER_API_VERIFIER_PROFILE_UNSUPPORTED')
test('actual-bearer-header-no-value-normalization',lambda: (_ for _ in ()).throw(AssertionError()) if extract_owner_api_token([('aUtHoRiZaTiOn',b'BeArEr '+token)],4096)!=token else None)
test('duplicate-auth-header',lambda:extract_owner_api_token([('Authorization',b'Bearer '+token),('authorization',b'Bearer '+token)],4096),'OWNER_API_AUTHORIZATION_HEADER_CARDINALITY_INVALID')
test('bearer-trailing-space-no-trim',lambda:extract_owner_api_token([('Authorization',b'Bearer '+token+b' ')],4096),'OWNER_API_TOKEN_ENCODING_INVALID')
test('wrong-auth-scheme',lambda:extract_owner_api_token([('Authorization',b'Basic '+token)],4096),'OWNER_API_AUTHORIZATION_SCHEME_INVALID')
test('bearer-header-too-large',lambda:extract_owner_api_token([('Authorization',b'Bearer '+token)],8),'OWNER_API_AUTHORIZATION_HEADER_TOO_LARGE')
# Real context constructor with exact server pin and receipt request binding.
def context(d=request_digest):
 a=auth_call();db.query(call(owner,a['authenticationAcceptanceId'],d.hex()));return a
test('native-context-positive',lambda:with_tx(context))
test('verified-receipt-cannot-authorize-other-request',lambda:with_tx(lambda:context(bytes(32))),'GENERATION_AUTH_REQUEST_BINDING_MISMATCH')
def stale_epoch():
 a=auth_call();db.query('UPDATE owner_api_credential SET credential_activation_epoch=credential_activation_epoch+1');db.query(call(owner,a['authenticationAcceptanceId'],request_digest.hex()))
test('stale-credential-epoch',lambda:with_tx(stale_epoch),'GENERATION_AUTH_CREDENTIAL_EPOCH_MISMATCH')
# Actual concurrency: rotation FOR UPDATE cannot commit while verifier-to-acceptance
# transaction retains FOR SHARE. Native command/queue fixture is separately joined.
rotation=DB(database);started=threading.Event();finished=threading.Event();race=[]
new_token=secrets.token_urlsafe(32).encode('ascii')
def rotate():
 started.set()
 try:
  rotation.query('BEGIN');rotation.query('UPDATE owner_api_credential SET verifier_hash='+lit(verifier_hash(new_token))+',fingerprint='+lit(fingerprint(new_token))+',credential_version=credential_version+1,credential_activation_epoch=credential_activation_epoch+1,state_version=state_version+1');rotation.query('COMMIT');race.append('committed')
 except Exception as e:race.append(str(e));rotation.query('ROLLBACK')
 finally:finished.set()
db.query('BEGIN');a=auth_call();db.query(call(owner,a['authenticationAcceptanceId'],request_digest.hex()));worker=threading.Thread(target=rotate);worker.start();started.wait(3);time.sleep(.2)
checks.append({'case':'rotation-blocked-during-authenticated-acceptance','passed':not finished.is_set()})
db.query('COMMIT');worker.join(10);checks.append({'case':'rotation-proceeds-only-after-acceptance-commit','passed':race==['committed']})
test('old-token-after-rotation',lambda:with_tx(auth_call),'OWNER_API_AUTHENTICATION_FAILED')
test('new-token-after-rotation',lambda:with_tx(lambda:auth_call(new_token)))
# AES actual native input and typed AAD mutation cases. No plaintext/token appears in report.
key=secrets.token_bytes(32);p=pin();desc=descriptor(owner,'sha256:'+sha(b'synthetic-key').hex(),p)
meta={'ownerId':owner,'jobId':job,'snapshotId':snap,'logicalOperationId':op,'requestSchemaId':'urn:kcml:r9:semantic:route.0215:body','requestSchemaDigest':'sha256:'+p['domainSchemaDigest'].hex(),'contentDigest':'sha256:'+sha(plain).hex(),'trustedContextId':str(uuid.uuid4()),'platformIncarnationId':owner,'applicationDeploymentEpoch':1,'executionDescriptorDigest':'sha256:'+sha(desc).hex(),'initiatingAccessChannel':'OWNER_API_KEY'}
envelope=seal(plain,key,'synthetic-immutable-master-generation-1',meta)
def domain(raw):validate_body('generation.job.create',strict_json(raw))
def opened(e=envelope,k=key,m=meta):
 with open_snapshot(e,k,'synthetic-immutable-master-generation-1',m,domain) as view:
  assert bytes(view)==plain
 return view
v=opened();checks.append({'case':'native-consumer-positive-and-managed-buffer-cleared','passed':bytes(v)==bytes(len(v))})
for field in ('ownerId','jobId','snapshotId','logicalOperationId','trustedContextId','platformIncarnationId'):
 m=copy.deepcopy(meta);m[field]=str(uuid.uuid4());test('aad-'+field,lambda m=m:opened(m=m),'PROTECTED_INPUT_AUTHENTICATION_FAILED')
for field,new in [('applicationDeploymentEpoch',2),('initiatingAccessChannel','OWNER_SESSION'),('requestSchemaId','urn:kcml:wrong:1'),('requestSchemaDigest','sha256:'+'00'*32),('contentDigest','sha256:'+'00'*32),('executionDescriptorDigest','sha256:'+'00'*32)]:
 m=copy.deepcopy(meta);m[field]=new;test('aad-'+field,lambda m=m:opened(m=m),'PROTECTED_INPUT_AUTHENTICATION_FAILED')
test('wrong-key',lambda:opened(k=secrets.token_bytes(32)),'PROTECTED_INPUT_AUTHENTICATION_FAILED')
e=copy.deepcopy(envelope);e['ciphertext']=e['ciphertext'][:-1]+bytes([e['ciphertext'][-1]^1]);test('corrupt-ciphertext',lambda:opened(e=e),'PROTECTED_INPUT_AUTHENTICATION_FAILED')
e=copy.deepcopy(envelope);e['keyId']='other';test('key-id-swap',lambda:opened(e=e),'PROTECTED_INPUT_KEY_ID_MISMATCH')
e=copy.deepcopy(envelope);e['nonce']=b'short';test('invalid-nonce',lambda:opened(e=e),'PROTECTED_INPUT_NONCE_INVALID')
m=copy.deepcopy(meta);m['jobId']='example';test('typed-identity-mask',lambda:seal(plain,key,'synthetic',m),'PROTECTED_INPUT_IDENTITY_INVALID')
test('missing-mask-structured-diagnostic',lambda:seal(plain,key,'synthetic',{}),'PROTECTED_INPUT_METADATA_MASK_INVALID')
# Auth-valid encrypted malformed domain bytes must fail actual native validator.
bad=b'{"intent":null}';m=copy.deepcopy(meta);m['contentDigest']='sha256:'+sha(bad).hex();e=seal(bad,key,'synthetic-immutable-master-generation-1',m)
test('authenticated-but-invalid-domain',lambda:opened(e=e,m=m),'SCHEMA')
version=db.query('SELECT version()')[0][0];db.close();rotation.close()
report={'sourceDocumentSha256':sha(raw).hex(),'canonicalSqlSha256':rs['database/generation-create-foundations.sql']['sha256'],'status':'PASS'if all(c['passed']for c in checks)else'BLOCKED','postgresqlVersion':version,'checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'proofScope':'Exact current embedded SQL unchanged + explicitly proposed request-binding extension; real constant-time SHA256 verifier and AES256GCM native-body reference. Concurrency binds acceptance receipt/context COMMIT; full command/queue join is still mandatory. No systemd provisioning/R17 claim. No sensitive fixture bytes emitted.','wholeOperationClosed':False,'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED','supportSha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()).hex()for p in [Path(__file__),HERE/'auth_crypto_reference.py',HERE/'acceptance_reference.py',HERE/'libpq_fixture.py',HERE/'authentication-request-binding-proposed.sql']}}
(HERE/'auth-crypto-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ('status','checked','failed')}))
