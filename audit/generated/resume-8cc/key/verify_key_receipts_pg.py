from pathlib import Path
import sys,json,secrets,hashlib,tempfile,os
from unittest.mock import patch
HERE=Path(__file__).parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'audit/generated/resume-34d/auth-crypto'))
from ssot_sources import SSOT,resource_index
from generation_auth_crypto import profile_bytes,profile_digest
from libpq_fixture import DB,lit
rs=resource_index();raw=SSOT.read_bytes();name='key_receipts_8cc';admin=DB('postgres')
if not admin.query('SELECT 1 FROM pg_database WHERE datname='+lit(name)):admin.query('CREATE DATABASE '+name)
admin.close();db=DB(name);db.query('DROP SCHEMA public CASCADE;CREATE SCHEMA public;')
for n in ['database/generation-create-foundations.sql','database/canonical-crypto-registry.sql']:db.query(rs[n]['raw'].decode())
sql=(HERE/'key-invocation-receipts.sql').read_bytes();db.query(sql.decode())
def b(v):return "decode('"+v.hex()+"','hex')"
fixture_key=secrets.token_bytes(32);fp=hashlib.sha256(fixture_key).digest();blob=hashlib.sha256(b'isolated synthetic encrypted blob NOT systemd provider').digest()
base="INSERT INTO canonical_authenticated_crypto_profile VALUES('KCML_PROTECTED_INPUT_AES256_GCM_V1',"+b(profile_bytes())+','+b(profile_digest())+",'AES_256_GCM');INSERT INTO canonical_master_key_generation VALUES('synthetic-key',"+b(fp)+",1,'kcml-master-key','fixture-platform.service',"+b(profile_digest())+",clock_timestamp());INSERT INTO canonical_encrypted_key_source_version VALUES('synthetic-key',"+b(blob)+",1,2,0,384,clock_timestamp());"
receipt="INSERT INTO canonical_key_invocation_receipt VALUES('synthetic-key',1,'fixture-platform.service',"+b(bytes([1]*16))+",123,1234,':1.7',"+b(blob)+','+b(fp)+",ARRAY['GENERATION_INITIAL_REQUEST','SECRET_IMMUTABLE_VERSION'],clock_timestamp());"
checks=[]
def run(name,stmt,code=None):
 db.query('BEGIN')
 try:db.query(stmt);ok=code is None;diag=None
 except Exception as e:diag=str(e);ok=code is not None and code in diag
 finally:db.query('ROLLBACK')
 checks.append({'case':name,'passed':ok,'expectedDiagnostic':code,'actualDiagnostic':diag})
run('reference-receipt-positive-not-provider-attestation',base+receipt)
for name,stmt,code in [
 ('wrong-source-owner',base.replace(',1,2,0,384,',',1,2,1000,384,')+receipt,'source_uid_check'),
 ('wrong-source-mode',base.replace(',1,2,0,384,',',1,2,0,420,')+receipt,'source_mode_check'),
 ('wrong-key-fingerprint',base+receipt.replace(b(fp),b(bytes(32))),'CRYPTO_KEY_FINGERPRINT_MISMATCH'),
 ('wrong-source-digest',base+receipt.replace(b(blob),b(bytes(32))),'key_receipt_encrypted_source_fkey'),
 ('wrong-service',base+receipt.replace("'fixture-platform.service'","'other.service'"),'key_receipt_key_generation_fkey'),
 ('wrong-generation',base+receipt.replace("('synthetic-key',1,","('synthetic-key',2,"),'key_receipt_key_generation_fkey'),
 ('zero-invocation',base+receipt.replace(b(bytes([1]*16)),b(bytes(16))),'invocation_id_check'),
 ('duplicate-purposes',base+receipt.replace("'SECRET_IMMUTABLE_VERSION'","'GENERATION_INITIAL_REQUEST'"),'key_receipt_purpose_unique'),
 ('array-offset-purpose-mask',base+receipt.replace("ARRAY['GENERATION_INITIAL_REQUEST','SECRET_IMMUTABLE_VERSION']","'[0:1]={GENERATION_INITIAL_REQUEST,SECRET_IMMUTABLE_VERSION}'::text[]"),'key_receipt_purpose_mask'),
 ('unknown-purpose',base+receipt.replace("'SECRET_IMMUTABLE_VERSION'","'MODEL_SUPPLIED_AUTHORITY'"),'key_receipt_purpose_mask'),
 ('immutable-invocation',base+receipt+'DELETE FROM canonical_key_invocation_receipt;','CANONICAL_CRYPTO_REGISTRY_IMMUTABLE'),
 ('immutable-source',base+receipt+'DELETE FROM canonical_encrypted_key_source_version;','CANONICAL_CRYPTO_REGISTRY_IMMUTABLE')]:run(name,stmt,code)
run('restricted-publisher-insert-positive-reference',base+'SET LOCAL ROLE kcml_key_invocation_publisher;'+receipt)
run('publisher-cannot-change-source-or-identity',base+'SET LOCAL ROLE kcml_key_invocation_publisher;DELETE FROM canonical_master_key_generation;','permission denied')
run('publisher-cannot-update-retained-receipts',base+receipt+'SET LOCAL ROLE kcml_key_invocation_publisher;UPDATE canonical_key_invocation_receipt SET main_pid=456;','permission denied')
for role in ['kcml_key_source_installer','kcml_key_invocation_publisher']:
 row=db.query("SELECT rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,rolinherit FROM pg_roles WHERE rolname="+lit(role))[0]
 checks.append({'case':'restricted-role-attributes-'+role,'passed':row==['f']*7})
# Actual publisher code + real SQL, with explicitly synthetic manager/path
# adapters. This proves its DB handoff, not canonical systemd provenance.
import systemd_key_authority as adapter
from generation_auth_crypto import SystemdInvocationKey
observer=adapter.SystemdManagerObserver()
observation={'managerUniqueOwner':':1.7','serviceUnit':'fixture-platform.service','invocationId':'01'*16,'mainPid':os.getpid(),'startMonotonicUsec':1234}
with tempfile.TemporaryDirectory(prefix='kcml-key-publisher-reference-')as tmp:
 f=Path(tmp)/'kcml-master-key';f.write_bytes(fixture_key);f.chmod(0o400)
 with patch.object(observer,'observe',lambda unit:observation),patch.object(adapter,'SystemdInvocationKey',lambda directory,name:SystemdInvocationKey(tmp,name)):
  db.query('BEGIN');db.query(base+'SET LOCAL ROLE kcml_key_invocation_publisher;')
  one=adapter.publish_current_invocation(db,observer,'synthetic-key');two=adapter.publish_current_invocation(db,observer,'synthetic-key')
  retained=db.query('SELECT count(*) FROM canonical_key_invocation_receipt')[0][0]
  checks.append({'case':'reference-actual-publisher-code-to-db-idempotent-receipt','passed':one==two and retained=='1'})
  db.query('ROLLBACK')
  db.query('BEGIN');db.query(base+receipt+'SET LOCAL ROLE kcml_key_invocation_publisher;')
  try:adapter.publish_current_invocation(db,observer,'synthetic-key');diag='ACCEPTED'
  except adapter.AuthorityError as e:diag=str(e)
  checks.append({'case':'reference-actual-publisher-replay-observer-metadata-conflict','passed':diag=='CRYPTO_INVOCATION_REPLAY_CONFLICT','actualDiagnostic':diag})
  db.query('ROLLBACK')
  try:adapter.publish_current_invocation(db,observer,'synthetic-key');diag='ACCEPTED'
  except adapter.AuthorityError as e:diag=str(e)
  checks.append({'case':'actual-publisher-requires-live-db-transaction','passed':diag=='CRYPTO_KEY_PUBLICATION_TRANSACTION_REQUIRED','actualDiagnostic':diag})
report={'status':'PASS'if all(c['passed']for c in checks)else'BLOCKED','checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'sourceDocumentSha256':hashlib.sha256(raw).hexdigest(),'canonicalInputs':{n:rs[n]['sha256']for n in ['database/generation-create-foundations.sql','database/canonical-crypto-registry.sql']},'candidateSqlSha256':hashlib.sha256(sql).hexdigest(),'postgresqlVersion':db.query('SHOW server_version')[0][0],'proofScope':'Actual PostgreSQL constraints/immutable reference receipts and actual publisher-code→DB handoff, synthetic source metadata/manager identity and explicit temporary-key path adapter only. Not verified source or systemd provider, exact publisher ACL or rotation confirmation.','providerStatus':'ENV_BLOCKED','wholeOperationClosed':False}
(HERE/'key-receipts-postgres-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));db.close()
