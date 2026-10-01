from pathlib import Path
import sys,subprocess,json,hashlib
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
r=resource_index(); source=SSOT.read_bytes(); base=r['database/secret-profile-roots.sql']['raw']; f=r['database/generation-create-foundations.sql']['raw']
a=f.index(b'CREATE TABLE owner_api_credential ('); z=f.index(b'\n);',a)+3; owner=f[a:z]
extra=(OUT/'owner-secret-binding.sql').read_bytes()
assert extra==r['database/secret-owner-binding.sql']['raw'], 'canonical owner binding byte mismatch'
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-v','ON_ERROR_STOP=1','-At']
def run(sql,db='secret_owner_review_905'):return subprocess.run(PSQL+['-d',db],input=sql,text=True,capture_output=True)
if not run("SELECT 1 FROM pg_database WHERE datname='secret_owner_review_905'",'postgres').stdout.strip():assert run('CREATE DATABASE secret_owner_review_905','postgres').returncode==0
q=run('DROP SCHEMA IF EXISTS kcml_secret_v1 CASCADE; DROP TABLE IF EXISTS owner_api_credential CASCADE;'+owner.decode()+base.decode()+extra.decode());assert q.returncode==0,q.stderr
cases=[]
def check(i,sql,err=None):
 q=run(sql); okay=q.returncode==0 if err is None else q.returncode!=0 and err in q.stderr
 cases.append({'id':i,'status':'PASS' if okay else 'FAIL','expectedDiagnostic':err})
 assert okay,(i,q.stderr)
sid='11111111-1111-4111-8111-111111111111';vid='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
sql=f"BEGIN; INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,state_version,secret_activation_epoch,created_at,updated_at) VALUES('{sid}','KCML_OWNER_API_KEY','SYNTHETIC','API_KEY','FIXTURE_UNREVIEWED_STATUS',0,0,now(),now());"
sql+=f"INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,creator_context_id) VALUES('{vid}','{sid}',1,'API_KEY','RAW_UTF8','EXACT_SECRET_BYTES_V1',9,decode('010203','hex'),decode('040506','hex'),'FIXTURE_OPAQUE_NOT_CRYPTO_EVIDENCE','FIXTURE_KEY','FIXTURE_FINGERPRINT',decode(repeat('00',32),'hex'),decode(repeat('00',32),'hex'),'CREATED',now(),'dddddddd-dddd-4ddd-8ddd-dddddddddddd');"
sql+=f"UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=now(),activation_logical_operation_id='ffffffff-ffff-4fff-8fff-ffffffffffff' WHERE id='{vid}'; UPDATE kcml_secret_v1.secret_record SET active_version_id='{vid}',state_version=1,secret_activation_epoch=1 WHERE id='{sid}';"
sql+=f"INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,credential_activation_epoch,created_at) VALUES(1,'{sid}','{vid}','FIXTURE_NO_VERIFIER_PROOF','FIXTURE_FINGERPRINT',1,1,now());COMMIT;"
check('canonical_physical_owner_secret_positive',sql)
check('wrong_credential_fingerprint',"UPDATE owner_api_credential SET fingerprint='WRONG';",'OWNER_CREDENTIAL_SECRET_BINDING_MISMATCH')
check('wrong_reserved_stable_name',"UPDATE kcml_secret_v1.secret_record SET stable_name='OTHER';",'OWNER_CREDENTIAL_SECRET_BINDING_MISMATCH')
check('missing_selected_version',"UPDATE owner_api_credential SET secret_version_id='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';",'owner_credential_secret_version_fk')
check('active_root_removed',"UPDATE kcml_secret_v1.secret_record SET active_version_id=NULL;",'OWNER_CREDENTIAL_SECRET_BINDING_MISMATCH')
check('positive_unchanged_owner_after_rejections',"DO $$BEGIN IF (SELECT fingerprint FROM owner_api_credential)<>'FIXTURE_FINGERPRINT' THEN RAISE EXCEPTION 'BAD_ROLLBACK'; END IF; END$$;")
report={'status':'PASS','checked':len(cases),'failed':0,'cases':cases,'sourceSha256':hashlib.sha256(source).hexdigest(),'sourceUnchangedDuringRun':source==SSOT.read_bytes(),'canonicalSecretRootsSha256':hashlib.sha256(base).hexdigest(),'canonicalOwnerTableStatementSha256':hashlib.sha256(owner).hexdigest(),'candidateSqlSha256':hashlib.sha256(extra).hexdigest(),'postgresVersion':run('SHOW server_version').stdout.strip(),'canonicalEmbeddedStatementsExecuted':True,'canonicalIntegratedSqlExecuted':True,'canonicalByteEqualityVerified':True,'cryptoOrVerifierProof':False,'wholeOperationClosed':False,'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
(OUT/'owner-binding-postgres-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','checked','failed','sourceUnchangedDuringRun']}))
