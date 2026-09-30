from pathlib import Path
import subprocess,json,hashlib
HERE=Path(__file__).parent;D=HERE.parent/'secrets'
CMD=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p55432','-d','secret_independent_review_fixture','-X','-At','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose']
def run(sql):return subprocess.run(CMD,input=sql,text=True,capture_output=True)
ddl=(D/'secret-profile-roots.sql').read_text();q=run('DROP SCHEMA IF EXISTS kcml_secret_v1 CASCADE;'+ddl);assert q.returncode==0,q.stderr
S='55555555-5555-4555-8555-555555555555';V='66666666-6666-4666-8666-666666666666'
base=f"INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,state_version,secret_activation_epoch,created_at,updated_at) VALUES('{S}','INDEPENDENT_FIXTURE','Synthetic','PASSWORD','FIXTURE_UNREVIEWED',0,0,clock_timestamp(),clock_timestamp());"
version=f"INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,creator_context_id) VALUES('{V}','{S}',1,'PASSWORD','RAW_UTF8','EXACT_SECRET_BYTES_V1',1,decode('0102','hex'),decode('03','hex'),'FIXTURE_ONLY','FIXTURE_ONLY','FIXTURE_ONLY',decode(repeat('00',32),'hex'),decode(repeat('00',32),'hex'),'CREATED',clock_timestamp(),'77777777-7777-4777-8777-777777777777');"
assert run(base+version).returncode==0
cases=[]
def test(name,sql,expected):
 q=run('BEGIN;'+sql+'SET CONSTRAINTS ALL IMMEDIATE;ROLLBACK;');actual='ACCEPTED' if q.returncode==0 else q.stderr.strip()[-1200:]
 cases.append({'id':name,'expected':expected,'accepted':q.returncode==0,'passed':q.returncode!=0 and expected in q.stderr and (expected!='secret_active_version_owns_parent' or '23503' in q.stderr),'diagnostic':actual})
test('child-kind-cannot-differ-parent',version.replace(V,'88888888-8888-4888-8888-888888888888').replace(",1,'PASSWORD'",",2,'API_KEY'"),'SECRET_PARENT_TYPE_MISMATCH')
test('byte-import-digest-immutable',f"UPDATE kcml_secret_v1.secret_version SET original_import_bytes_digest=decode(repeat('ff',32),'hex')WHERE id='{V}';",'SECRET_VERSION_CRYPTO_IMMUTABLE')
test('semantic-digest-immutable',f"UPDATE kcml_secret_v1.secret_version SET canonical_value_digest=decode(repeat('ff',32),'hex')WHERE id='{V}';",'SECRET_VERSION_CRYPTO_IMMUTABLE')
test('created-cannot-skip-to-retired',f"UPDATE kcml_secret_v1.secret_version SET lifecycle='RETIRED',activated_at=clock_timestamp(),retired_at=clock_timestamp(),activation_logical_operation_id='99999999-9999-4999-8999-999999999999'WHERE id='{V}';",'SECRET_VERSION_TRANSITION_INVALID')
q=run(f"BEGIN;UPDATE kcml_secret_v1.secret_record SET secret_type='API_KEY' WHERE id='{S}';DO $$BEGIN IF NOT EXISTS(SELECT 1 FROM kcml_secret_v1.secret_version WHERE id='{V}' AND secret_type='PASSWORD' AND lifecycle='CREATED') THEN RAISE EXCEPTION 'VERSION_TYPE_REINTERPRETED';END IF;END$$;ROLLBACK;")
cases.append({'id':'inactive-metadata-change-retains-old-version-type','accepted':q.returncode==0,'passed':q.returncode==0,'authority':'8.3/8.5 metadata editing;25.6 existing immutableversion keepsfrozeninterpretation. No blanketroot-typeimmutableguard.'})
active=f"UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=clock_timestamp(),activation_logical_operation_id='99999999-9999-4999-8999-999999999999'WHERE id='{V}';UPDATE kcml_secret_v1.secret_record SET active_version_id='{V}',state_version=1,secret_activation_epoch=1 WHERE id='{S}';SET CONSTRAINTS ALL IMMEDIATE;"
test('active-pointer-type-cannot-silently-reclassify-version',active+f"UPDATE kcml_secret_v1.secret_record SET secret_type='API_KEY',state_version=2,secret_activation_epoch=2 WHERE id='{S}';",'secret_active_version_owns_parent')
report={'scope':'Independent actual fresh Secret DDL executed in own disposable DB. Opaque crypto bytes intentionally test SQL relations only, not crypto acceptance. Accepted mutations are findings, not PASS.','version':run('SELECT version();').stdout.strip(),'sourceDDLsha256':hashlib.sha256(ddl.encode()).hexdigest(),'cases':cases,'checks':len(cases),'failed':sum(c['passed']is False for c in cases),'runtimeAcceptance':'NOT_EVALUATED'}
(HERE/'secret-sql-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(cases),'failed':report['failed']}))
