"""Actual isolated PostgreSQL 18.6 fixtures. Does not claim broker/crypto runtime."""
import hashlib,json,subprocess
from pathlib import Path
from secret_profile_reference import SCHEMA,schema_digest,compiled_schema_bytes
D=Path(__file__).resolve().parent
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-d','sc116_secretpg_secret_pg_integrated','-v','ON_ERROR_STOP=1','-At']
def quote(v):return "'"+v.replace("'","''")+"'"
def run(sql):return subprocess.run(PSQL+['-c',sql],text=True,capture_output=True)
checks=[]
def positive(id_,sql):
 r=run(sql);checks.append({'id':id_,'passed':r.returncode==0,'kind':'ACTUAL_POSTGRES_SQL','returnCode':r.returncode})
 if r.returncode:print(id_,r.stderr[:150])
def negative(id_,sql,state,constraint):
 # SQL executes in its own subtransaction, captures precise SQLSTATE and
 # constraint name, and fails on acceptance or any unrelated exception.
 block="""DO $test$ DECLARE actual_state text;actual_constraint text; BEGIN BEGIN %s; RAISE EXCEPTION 'UNEXPECTED_ACCEPTANCE'; EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS actual_state=RETURNED_SQLSTATE,actual_constraint=CONSTRAINT_NAME; IF actual_state<>%s OR actual_constraint<>%s THEN RAISE EXCEPTION 'WRONG_DIAGNOSTIC: %% %%',actual_state,actual_constraint; END IF; END; END $test$;"""%(sql,quote(state),quote(constraint))
 r=run(block);checks.append({'id':id_,'passed':r.returncode==0,'kind':'ACTUAL_POSTGRES_SPECIFIC_REJECTION','expectedSQLState':state,'expectedConstraint':constraint,'returnCode':r.returncode})
 if r.returncode:print(id_,r.stderr[:200])
# Reset only this task's explicitly created private fixture schema.
setup=run('DROP SCHEMA IF EXISTS kcml_secret_v1 CASCADE');assert setup.returncode==0
setup=subprocess.run(PSQL,input=canonical_sql.decode(),text=True,capture_output=True);assert setup.returncode==0,setup.stderr
# Database and DDL are intentionally created by the parent-shell once. This
# fixture resets only its OWN private schema through a new database, never main.
positive('server-version-is-18.6',"DO $$BEGIN IF current_setting('server_version') NOT LIKE '18.6%' THEN RAISE EXCEPTION 'VERSION';END IF;END$$")
for p in SCHEMA['x-profileInventory']:
 if p['profileId']=='BROWSER_AUTH_STATE_GRAPH_V1':continue
 name=p['profileId'];raw=compiled_schema_bytes(name);digest=hashlib.sha256(raw).hexdigest()
 positive(name+'/real-registry-schema-bytes-digest',f"INSERT INTO kcml_secret_v1.secret_value_profile_registry VALUES ({quote(p['secretType'])},{quote(name)},{quote('urn:kcml:secret-profile-handoffs:1#/$defs/'+name)},decode('{digest}','hex'),decode('{raw.hex()}','hex'),'ACTIVE',decode('{SCHEMA['x-sourceSha256']}','hex'),decode('{hashlib.sha256(b'SYNTHETIC_REFERENCE_REVIEW_ONLY').hexdigest()}','hex'),now())")
S1='11111111-1111-4111-8111-111111111111';S2='22222222-2222-4222-8222-222222222222';V1='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';V2='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';V3='cccccccc-cccc-4ccc-8ccc-cccccccccccc'
record=lambda sid,name:f"INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,state_version,secret_activation_epoch,created_at,updated_at) VALUES('{sid}',{quote(name)},'SYNTHETIC','PASSWORD','FIXTURE_RECORD_STATUS_UNREVIEWED',0,0,now(),now())"
positive('record-roots-insert',record(S1,'SYNTHETIC_ONE')+';'+record(S2,'SYNTHETIC_TWO'))
version=lambda vid,sid,number:f"INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,creator_context_id) VALUES('{vid}','{sid}',{number},'PASSWORD','RAW_UTF8','EXACT_SECRET_BYTES_V1',9,decode('010203','hex'),decode('040506','hex'),'FIXTURE_BYTES_ONLY_NOT_CRYPTO_EVIDENCE','FIXTURE_KEY','FIXTURE_FINGERPRINT',decode(repeat('00',32),'hex'),decode(repeat('00',32),'hex'),'CREATED',now(),'dddddddd-dddd-4ddd-8ddd-dddddddddddd')"
positive('candidate-create-is-not-active',version(V1,S1,1)+';'+version(V2,S1,2)+';'+version(V3,S2,1))
negative('same-secret-version-number-unique',version('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',S1,1),'23505','secret_version_secret_id_version_number_key')
negative('ciphertext-immutable',f"UPDATE kcml_secret_v1.secret_version SET ciphertext=decode('ff','hex')WHERE id='{V1}'",'23514','secret_version_crypto_immutable')
negative('version-delete-forbidden',f"DELETE FROM kcml_secret_v1.secret_version WHERE id='{V1}'",'23514','secret_version_immutable')
negative('parent-selected-version-composite-FK',f"UPDATE kcml_secret_v1.secret_record SET active_version_id='{V3}'WHERE id='{S1}';SET CONSTRAINTS kcml_secret_v1.secret_active_version_owns_parent IMMEDIATE",'23503','secret_active_version_owns_parent')
negative('pointer-without-ACTIVE-version',f"UPDATE kcml_secret_v1.secret_record SET active_version_id='{V1}'WHERE id='{S1}';SET CONSTRAINTS ALL IMMEDIATE",'23514','secret_active_pointer_consistency')
activate=lambda vid:f"UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=now(),activation_logical_operation_id='ffffffff-ffff-4fff-8fff-ffffffffffff'WHERE id='{vid}'"
positive('atomic-activation-version-and-pointer',f"BEGIN;SELECT id FROM kcml_secret_v1.secret_record WHERE id='{S1}'FOR UPDATE;{activate(V1)};UPDATE kcml_secret_v1.secret_record SET active_version_id='{V1}',state_version=1,secret_activation_epoch=1 WHERE id='{S1}';COMMIT")
negative('ACTIVE-root-type-must-match-selected-version',f"UPDATE kcml_secret_v1.secret_record SET secret_type='API_KEY' WHERE id='{S1}';SET CONSTRAINTS kcml_secret_v1.secret_active_version_owns_parent IMMEDIATE",'23503','secret_active_version_owns_parent')
positive('inactive-root-metadata-edit-keeps-historic-version-type',f"BEGIN;UPDATE kcml_secret_v1.secret_record SET secret_type='API_KEY' WHERE id='{S2}';DO $$$$BEGIN IF (SELECT secret_type FROM kcml_secret_v1.secret_version WHERE id='{V3}')<>'PASSWORD' THEN RAISE EXCEPTION 'HISTORIC_TYPE_CHANGED';END IF;END$$$$;COMMIT".replace('$$$$','$$'))
negative('second-ACTIVE-partial-unique',activate(V2),'23505','secret_one_active_version')
positive('atomic-retire-before-next-activate',f"BEGIN;SELECT id FROM kcml_secret_v1.secret_record WHERE id='{S1}'FOR UPDATE;UPDATE kcml_secret_v1.secret_version SET lifecycle='RETIRED',retired_at=now()WHERE id='{V1}';{activate(V2)};UPDATE kcml_secret_v1.secret_record SET active_version_id='{V2}',state_version=2,secret_activation_epoch=2 WHERE id='{S1}';COMMIT")
positive('historical-reactivation-allowed',f"BEGIN;SELECT id FROM kcml_secret_v1.secret_record WHERE id='{S1}'FOR UPDATE;UPDATE kcml_secret_v1.secret_version SET lifecycle='RETIRED',retired_at=now()WHERE id='{V2}';UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=now(),retired_at=NULL WHERE id='{V1}';UPDATE kcml_secret_v1.secret_record SET active_version_id='{V1}',state_version=3,secret_activation_epoch=3 WHERE id='{S1}';COMMIT")
positive('soft-delete-retains-stable-name',f"UPDATE kcml_secret_v1.secret_record SET deleted_at=now(),updated_at=now()WHERE id='{S2}'")
negative('stable-name-no-soft-delete-reuse',record('99999999-9999-4999-8999-999999999999','SYNTHETIC_TWO'),'23505','secret_record_stable_name_key')
negative('profile-definition-immutable',"UPDATE kcml_secret_v1.secret_value_profile_registry SET schema_id='forged'WHERE profile_id='TOTP_BASE32_V1'",'23514','secret_profile_definition_immutable')
# Actual synthetic AES-GCM ciphertext is persisted in PostgreSQL and rehydrated
# from database bytes, rather than only an in-memory encryption roundtrip.
# The fixture key remains ephemeral; this is not the canonical systemd source.
from secret_profile_reference import import_body,store_reference,load_reference
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import uuid
proposal=json.loads(subprocess.check_output(['git','show',SCHEMA['x-inputCommit']+':audit/generated/create-review-authority/secret-variant-proposals.json']))
for contract in proposal['contracts']:
 for branch in contract['schema']['oneOf']:
  profile=branch['properties']['variant']['const'];value=next(x['value']for x in contract['syntheticCases']if x['expected']=='SCHEMA_ACCEPT'and x['value']['variant']==profile)
  raw=json.dumps({'stableName':'SYNTHETIC_'+profile,'displayName':'Synthetic','type':contract['secretType'],'value':{'representation':'PROFILE_JSON_V1','profileId':profile,'profile':value}},ensure_ascii=True,indent=2).encode()
  candidate=import_body(raw);sid=str(uuid.uuid4());vid=str(uuid.uuid4());key=AESGCM.generate_key(bit_length=256);sealed=store_reference(candidate,sid,vid,key);m=sealed['metadata']
  sql=f"INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,state_version,secret_activation_epoch,created_at,updated_at) VALUES('{sid}',{quote('SYNTHETIC_'+profile)},'SYNTHETIC',{quote(contract['secretType'])},'FIXTURE_RECORD_STATUS_UNREVIEWED',0,0,now(),now());"
  sql+=f"INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,profile_id,value_schema_id,value_schema_digest,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,creator_context_id) VALUES('{vid}','{sid}',1,{quote(m['type'])},'PROFILE_JSON_V1',{quote(profile)},{quote(m['schemaId'])},decode('{m['schemaDigest'][7:]}','hex'),'EXACT_SECRET_BYTES_V1',{m['plaintextByteLength']},decode('{sealed['ciphertext'].hex()}','hex'),decode('{sealed['nonce'].hex()}','hex'),'SYNTHETIC_AESGCM_256_NOT_PRODUCTION_PROFILE','EPHEMERAL_FIXTURE_KEY','SYNTHETIC_PRIVATE_FINGERPRINT',decode('{m['valueDigest'][7:]}','hex'),decode('{m['canonicalValueDigest'][7:]}','hex'),'CREATED',now(),'dddddddd-dddd-4ddd-8ddd-dddddddddddd');"
  result=run(sql);okay=result.returncode==0
  if okay:
   result=run(f"SELECT json_build_object('secretId',secret_id,'versionId',id,'type',secret_type,'representation',value_representation,'profileId',profile_id,'schemaId',value_schema_id,'schemaDigest','sha256:'||encode(value_schema_digest,'hex'),'plaintextByteLength',plaintext_byte_length,'valueDigest','sha256:'||encode(original_import_bytes_digest,'hex'),'canonicalValueDigest','sha256:'||encode(canonical_value_digest,'hex'),'payloadFormat',payload_format,'ciphertext',encode(ciphertext,'hex'),'nonce',encode(nonce,'hex')) FROM kcml_secret_v1.secret_version WHERE id='{vid}'")
   selected=json.loads(result.stdout);cipher=bytes.fromhex(selected.pop('ciphertext'));nonce=bytes.fromhex(selected.pop('nonce'));selected_aad=json.dumps(selected,sort_keys=True,separators=(',',':')).encode()
   hydrated=load_reference({'metadata':selected,'aad':selected_aad,'ciphertext':cipher,'nonce':nonce},key,sid,vid);okay=hydrated==candidate['bytes']
  checks.append({'id':profile+'/actual-PG-encrypted-original-bytes-hydration','passed':okay,'kind':'ACTUAL_POSTGRES_AND_SYNTHETIC_AEAD','productionMasterKeyEvidence':False})
report={'inputCommit':SCHEMA['x-inputCommit'],'sourceSha256':SCHEMA['x-sourceSha256'],'currentWorkingRepairInput':json.loads((D/'input-source.json').read_text()),'serverVersion':run('SELECT version()').stdout.strip(),'database':'sc116_secretpg_secret_pg_integrated','schema':'kcml_secret_v1','ddlSha256':hashlib.sha256((D/'secret-profile-roots.sql').read_bytes()).hexdigest(),'schemaSha256':hashlib.sha256((D/'secret-profile-handoffs.schema.json').read_bytes()).hexdigest(),'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'supportSha256':{n:hashlib.sha256((D/n).read_bytes()).hexdigest()for n in ['profile_reference.py','secret_value_parsers.py','verify_reference.py','synthetic_profile_fixtures.py']},'checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'actualPostgresExecuted':True,'sensitiveValuesInReport':False,'cryptoEvidence':'TEN_ACTUAL_PG_AND_EPHEMERAL_AESGCM_ROUNDTRIPS_NOT_CANONICAL_SYSTEMD_PROVIDER' ,'excluded':['External exact creator_context/domain_command FKs pending coordinator integration','Atomic event/outbox/audit and reserved OWNER credential consistency','Production master-key/systemd/cipher fixture','Secret record status enum and metadata/rotation-policy projections','Full browser engine serializer']}
(canonical_output/'postgres-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':report['checked'],'failed':report['failed']}));raise SystemExit(bool(report['failed']))
