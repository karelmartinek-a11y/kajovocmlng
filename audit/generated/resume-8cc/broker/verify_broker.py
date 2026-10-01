import sys,subprocess,json,hashlib,os,copy,uuid,concurrent.futures,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
from generation_auth_crypto import seal,aad,profile_bytes,profile_digest,sha
from secret_profile_import import candidate_from_http
from secret_profile_reference import schema_digest,canonical_value_digest,compiled_schema_bytes,SCHEMA
from secret_broker_open import open_for_consumer
source=SSOT.read_bytes();r=resource_index();candidate=(OUT/'secret-broker-boundary.sql').read_bytes()
P=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-v','ON_ERROR_STOP=1','-qAt']
DB='secret_broker_8cc'
def run(sql,db=DB):return subprocess.run(P+['-d',db],input=sql,text=True,capture_output=True)
if not run(f"SELECT 1 FROM pg_database WHERE datname='{DB}'",'postgres').stdout.strip():assert run('CREATE DATABASE '+DB,'postgres').returncode==0
foundation=r['database/generation-create-foundations.sql']['raw'];a=foundation.index(b'CREATE TABLE domain_command (');z=foundation.index(b'\n);',a)+3;command=foundation[a:z]
q=run('DROP SCHEMA IF EXISTS kcml_secret_v1 CASCADE;DROP TABLE IF EXISTS domain_command CASCADE;DROP TABLE IF EXISTS canonical_protected_nonce_reservation,canonical_master_key_generation,canonical_authenticated_crypto_profile CASCADE;DROP FUNCTION IF EXISTS kcml_canonical_crypto_registry_immutable_v1() CASCADE;'+command.decode()+r['database/secret-profile-roots.sql']['raw'].decode()+r['database/canonical-crypto-registry.sql']['raw'].decode()+candidate.decode());assert q.returncode==0,q.stderr
ids={k:str(uuid.uuid4())for k in ['owner','secret','version','creationctx','creationop','ctx','op','scope','binding','source','target','sourceRev','targetRev','activation','pending','correlation']}
id=lambda k:"'"+ids[k]+"'"
def b(x):return "decode('"+x.hex()+"','hex')"
def j(x):return b(json.dumps(x,sort_keys=True,separators=(',',':')).encode())
key=os.urandom(32);KEYID='ISOLATED_BROKER_FIXTURE_KEY_NOT_SYSTEMD';profile='TOTP_BASE32_V1'
raw_http=json.dumps({'stableName':'SYNTHETIC_TOTP','displayName':'Synthetic','type':'TOTP_SEED','value':{'representation':'PROFILE_JSON_V1','profileId':profile,'profile':{'variant':profile,'seedBase32':'JBSWY3DPEHPK3PXP','algorithm':'SHA1','digits':6,'periodSeconds':30}}},separators=(',',':')).encode();imported=candidate_from_http(raw_http)
meta={'ownerId':ids['owner'],'secretId':ids['secret'],'secretVersionId':ids['version'],'secretType':'TOTP_SEED','representation':'PROFILE_JSON_V1','profileId':profile,'schemaId':SCHEMA['$id']+'#/$defs/'+profile,'schemaDigest':schema_digest(profile),'plaintextByteLength':len(imported['bytes']),'originalImportBytesDigest':'sha256:'+sha(imported['bytes']).hex(),'canonicalValueDigest':canonical_value_digest(imported),'trustedContextId':ids['creationctx'],'logicalOperationId':ids['creationop']}
env=seal(imported['bytes'],key,KEYID,meta,'SECRET_IMMUTABLE_VERSION')
consumer={'consumerId':'SYNTHETIC_TOTP_ADAPTER','consumerRevision':'1','purposeKind':'REFERENCE_TEST','profiles':[{'secretType':'TOTP_SEED','profileId':profile,'schemaDigest':schema_digest(profile)}],'allowedOrigins':[],'cookieHosts':[],'tokenEndpoint':None,'database':None,'keyAlgorithms':[],'browserMembers':[],'serializerIds':[],'engineBuild':'ISOLATED_FIXTURE','keyAlgorithmPolicies':[],'totpPolicies':[{'algorithm':'SHA1','digits':6,'minimumSeedBytes':10,'minimumPeriodSeconds':30,'maximumPeriodSeconds':30}],'oauthClientId':None,'authorizedOAuthScopes':[]}
descriptor=b'EXACT_ISOLATED_RUNTIME_COMMAND_DESCRIPTOR';binding_bytes=json.dumps({'bindingId':ids['binding'],'bindingRevision':'1','secretId':ids['secret'],'sourceObjectId':ids['source'],'sourceRevisionId':ids['sourceRev'],'targetObjectId':ids['target'],'targetRevisionId':ids['targetRev'],'activationSetRevision':ids['activation'],'purpose':'REFERENCE_TEST','consumerStep':'STEP_1','placementPath':'/secret'},sort_keys=True,separators=(',',':')).encode()
# Exact canonical table statement; no scope fixture is represented as real API
# or gateway authority. It is a privileged typed-consuming-boundary witness.
cmd={'logical_operation_id':ids['op'],'operation_id':'runtime.handler.invoke','owner_id':ids['owner'],'request_digest':b'R'*32,'execution_descriptor_bytes':descriptor,'execution_descriptor_digest':sha(descriptor),'state':'ACCEPTED','terminal':False,'platform_incarnation_id':str(uuid.uuid4()),'application_deployment_epoch':1,'created_at':'2026-10-01T00:00:00Z','updated_at':'2026-10-01T00:00:00Z','command_id':str(uuid.uuid4()),'operation_contract_revision':'FIXTURE','caller_channel':'TRUSTED_RUNTIME_FIXTURE','execution_context_id':ids['ctx'],'target_aggregate_kind':'FIXTURE_TARGET','target_aggregate_id':ids['target'],'canonical_arguments_snapshot_id':str(uuid.uuid4()),'scope_digest':b'S'*32,'client_key_digest':b'I'*32,'correlation_id':ids['correlation'],'accepted_at':'2026-10-01T00:00:00Z'}
def lit(v):
 if isinstance(v,bytes):return b(v)
 if v is None:return 'NULL'
 if isinstance(v,bool):return 'true'if v else'false'
 if isinstance(v,int):return str(v)
 return "'"+v.replace("'","''")+"'"
sql='INSERT INTO domain_command('+','.join(cmd)+') VALUES('+','.join(lit(v)for v in cmd.values())+');'
sql+="INSERT INTO canonical_authenticated_crypto_profile VALUES('KCML_PROTECTED_INPUT_AES256_GCM_V1',"+b(profile_bytes())+','+b(profile_digest())+",'AES_256_GCM');"
sql+="INSERT INTO canonical_master_key_generation VALUES('"+KEYID+"',"+b(sha(key))+",1,'ISOLATED_NOT_SYSTEMD','ISOLATED_NOT_SERVICE',"+b(profile_digest())+",now());"
sql+="INSERT INTO canonical_protected_nonce_reservation VALUES('"+KEYID+"',"+b(env['nonce'])+",'SECRET_IMMUTABLE_VERSION',"+id('version')+','+id('creationop')+','+b(aad(meta,'SECRET_IMMUTABLE_VERSION',KEYID))+','+b(sha(aad(meta,'SECRET_IMMUTABLE_VERSION',KEYID)))+','+b(sha(env['ciphertext']))+');'
schema=compiled_schema_bytes(profile)
sql+="INSERT INTO kcml_secret_v1.secret_value_profile_registry VALUES('TOTP_SEED','"+profile+"','"+meta['schemaId']+"',"+b(sha(schema))+','+b(schema)+",'ACTIVE',"+b(sha(source))+','+b(sha(b'ISOLATED_NOT_REVIEW_APPROVAL'))+",now());"
sql+='INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,state_version,secret_activation_epoch,created_at,updated_at)VALUES('+id('secret')+",'SYNTHETIC_TOTP','Synthetic','TOTP_SEED','ISOLATED_STATUS_NOT_POLICY',0,0,now(),now());"
cols={'id':ids['version'],'secret_id':ids['secret'],'version_number':1,'secret_type':'TOTP_SEED','value_representation':'PROFILE_JSON_V1','profile_id':profile,'value_schema_id':meta['schemaId'],'value_schema_digest':sha(schema),'payload_format':'EXACT_SECRET_BYTES_V1','plaintext_byte_length':len(imported['bytes']),'ciphertext':env['ciphertext'],'nonce':env['nonce'],'algorithm':env['algorithm'],'key_id':KEYID,'fingerprint':sha(imported['bytes']).hex()[:16],'original_import_bytes_digest':sha(imported['bytes']),'canonical_value_digest':bytes.fromhex(meta['canonicalValueDigest'][7:]),'lifecycle':'CREATED','created_at':'2026-10-01T00:00:00Z','creator_context_id':ids['creationctx']}
sql+='BEGIN;INSERT INTO kcml_secret_v1.secret_version('+','.join(cols)+')VALUES('+','.join(lit(v)for v in cols.values())+');UPDATE kcml_secret_v1.secret_version SET lifecycle=\'ACTIVE\',activated_at=now(),activation_logical_operation_id='+id('creationop')+';UPDATE kcml_secret_v1.secret_record SET active_version_id='+id('version')+',state_version=1,secret_activation_epoch=1;COMMIT;'
sql+='INSERT INTO kcml_secret_v1.broker_subject_head VALUES('+id('source')+','+id('sourceRev')+','+id('activation')+',0,0),('+id('target')+','+id('targetRev')+','+id('activation')+',0,0);'
sql+='INSERT INTO kcml_secret_v1.broker_binding VALUES('+id('binding')+',1,'+id('secret')+','+id('source')+','+id('sourceRev')+','+id('target')+','+id('targetRev')+','+id('activation')+",'REFERENCE_TEST','STEP_1','/secret',"+b(binding_bytes)+','+b(sha(binding_bytes))+",now(),now()+interval '1 hour',NULL);"
sql+='INSERT INTO kcml_secret_v1.broker_use_scope VALUES('+id('scope')+','+id('op')+','+id('ctx')+','+b(sha(descriptor))+','+id('binding')+',1,'+b(sha(binding_bytes))+",'SYNTHETIC_TOTP',"+id('source')+','+id('sourceRev')+','+id('target')+','+id('targetRev')+','+id('activation')+",'REFERENCE_TEST','STEP_1','/secret',"+j(consumer)+','+b(sha(json.dumps(consumer,sort_keys=True,separators=(',',':')).encode()))+','+id('pending')+','+id('correlation')+",now()+interval '1 hour',NULL);"
q=run(sql);assert q.returncode==0,q.stderr
cases=[]
select='SELECT row_to_json(x) FROM kcml_secret_v1.broker_resolve_v1('+id('scope')+','+id('pending')+','+id('correlation')+') x;'
def result(sql=select):
 q=run(sql);assert q.returncode==0,q.stderr
 rows=[json.loads(x) for x in q.stdout.splitlines()if x.startswith('{')];return rows[-1]
row=result();assert row['diagnostic']=='RESOLVED';assert open_for_consumer(row['protected_row'],key,KEYID,datetime.now(timezone.utc))==imported['bytes'];cases.append({'id':'actual-PG-protected-row-canonical-open-native-TOTP-byteexact','status':'PASS'})
old=row['resolution_id'];row2=result();assert row2['resolution_id']==old;cases.append({'id':'stable-logical-pending-resolution-replay','status':'PASS'})
def deny(name,mut,code):
 x=result('BEGIN;'+mut+select+'ROLLBACK;');assert x['diagnostic']==code and x['protected_row']is None,(name,x['diagnostic']);cases.append({'id':name,'status':'PASS','diagnostic':code})
deny('wrong-target-revision',"UPDATE kcml_secret_v1.broker_use_scope SET target_revision_id='"+str(uuid.uuid4())+"';",'SECRET_SOURCE_TARGET_REVISION_STALE')
deny('wrong-source-revision',"UPDATE kcml_secret_v1.broker_use_scope SET source_revision_id='"+str(uuid.uuid4())+"';",'SECRET_SOURCE_TARGET_REVISION_STALE')
deny('wrong-purpose',"UPDATE kcml_secret_v1.broker_use_scope SET purpose='WRONG';",'SECRET_BINDING_SCOPE_MISMATCH')
deny('wrong-placement',"UPDATE kcml_secret_v1.broker_use_scope SET placement_path='/other';",'SECRET_BINDING_SCOPE_MISMATCH')
deny('expired-binding',"UPDATE kcml_secret_v1.broker_binding SET activated_at=now()-interval '2 hours',expires_at=now()-interval '1 hour';",'SECRET_BINDING_STALE')
deny('expired-use-scope',"UPDATE kcml_secret_v1.broker_use_scope SET expires_at=now()-interval '1 hour';",'SECRET_USE_CONTEXT_EXPIRED')
deny('stale-activation',"UPDATE kcml_secret_v1.broker_use_scope SET activation_set_revision='"+str(uuid.uuid4())+"';",'SECRET_SOURCE_TARGET_REVISION_STALE')
deny('stale-invalidation-barrier',"UPDATE kcml_secret_v1.broker_subject_head SET invalidation_epoch=1;",'SECRET_INVALIDATION_BARRIER_PENDING')
deny('secret-expired',"UPDATE kcml_secret_v1.secret_record SET expires_at=now()-interval '1 hour';",'SECRET_EXPIRED')
deny('cancelled-parent',"UPDATE domain_command SET state='CANCELLED';",'SECRET_USE_COMMAND_SCOPE_MISMATCH')
deny('create-is-not-runtime-authority',"UPDATE domain_command SET operation_id='secret.create';",'SECRET_CREATE_CONTEXT_NOT_RUNTIME_USE')
# Native negative uses valid protected row; only declaration differs.
bad=copy.deepcopy(row['protected_row']);c=copy.deepcopy(consumer);c['profiles']=[];bad['consumerDeclarationHex']=json.dumps(c).encode().hex()
try:open_for_consumer(bad,key,KEYID,datetime.now(timezone.utc));raise AssertionError('unsupported profile accepted')
except Exception as e:
 assert getattr(e,'code',None)=='SECRET_VARIANT_UNSUPPORTED',repr(e);cases.append({'id':'native-profile-unsupported-consumer','status':'PASS','diagnostic':e.code})
bad=copy.deepcopy(row['protected_row']);bad['version']['id']=str(uuid.uuid4())
try:open_for_consumer(bad,key,KEYID,datetime.now(timezone.utc));raise AssertionError('wrong immutableversion accepted')
except ValueError as e:assert str(e)=='SECRET_PROTECTED_CREATOR_BINDING_MISMATCH';cases.append({'id':'wrong-immutable-version','status':'PASS','diagnostic':str(e)})
bad=copy.deepcopy(row['protected_row']);c=copy.deepcopy(consumer);c['purposeKind']='WRONG';bad['consumerDeclarationHex']=json.dumps(c).encode().hex()
try:open_for_consumer(bad,key,KEYID,datetime.now(timezone.utc));raise AssertionError('wrong consumer purpose accepted')
except ValueError as e:assert str(e)=='SECRET_CONSUMER_PURPOSE_MISMATCH';cases.append({'id':'wrong-consumer-declared-purpose','status':'PASS','diagnostic':str(e)})
try:open_for_consumer(row['protected_row'],os.urandom(32),KEYID,datetime.now(timezone.utc));raise AssertionError('wrong key accepted')
except ValueError as e:assert str(e)=='SECRET_INVOCATION_KEY_FINGERPRINT_MISMATCH';cases.append({'id':'wrong-key-source-identity','status':'PASS','diagnostic':str(e)})
bad=copy.deepcopy(row['protected_row']);raw=bytearray(bytes.fromhex(bad['version']['ciphertext'][2:]));raw[-1]^=1;bad['version']['ciphertext']='\\x'+raw.hex();bad['protectedAuthority']['ciphertextDigestHex']=sha(raw).hex()
try:open_for_consumer(bad,key,KEYID,datetime.now(timezone.utc));raise AssertionError('digest-valid ciphertext corruption accepted')
except ValueError as e:assert str(e)=='PROTECTED_INPUT_AUTHENTICATION_FAILED';cases.append({'id':'actual-canonical-AEAD-invalid-tag-with-resigned-cipher-digest','status':'PASS','diagnostic':str(e)})
# Audit denies are actual committed immutable evidence, not rollback exceptions.
x=result("UPDATE kcml_secret_v1.broker_subject_head SET invalidation_epoch=1;"+select);assert x['diagnostic']=='SECRET_INVALIDATION_BARRIER_PENDING'
q=run("SELECT count(*) FROM kcml_secret_v1.broker_resolution_audit WHERE diagnostic='SECRET_INVALIDATION_BARRIER_PENDING';");assert q.stdout.strip()=='1';run('UPDATE kcml_secret_v1.broker_subject_head SET completed_invalidation_epoch=invalidation_epoch;');cases.append({'id':'denial-immutable-audit-committed-without-plaintext','status':'PASS'})
q=run('UPDATE kcml_secret_v1.broker_resolution SET purpose=\'WRONG\';');assert q.returncode!=0 and 'SECRET_BROKER_EVIDENCE_IMMUTABLE'in q.stderr;cases.append({'id':'resolution-immutable','status':'PASS'})
# Expiry is sampled AFTER waiting for the actual Secret root lock.
lock_conn=subprocess.Popen(P+['-d',DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
def lock_query(sql):
 lock_conn.stdin.write(sql+'\n\\echo LOCK_END\n');lock_conn.stdin.flush();lines=[]
 while True:
  line=lock_conn.stdout.readline()
  if not line:raise AssertionError(lock_conn.stderr.read())
  if line.strip()=='LOCK_END':return lines
  lines.append(line.strip())
lock_query('BEGIN;SELECT 1 FROM kcml_secret_v1.secret_record WHERE id='+id('secret')+' FOR UPDATE;UPDATE kcml_secret_v1.broker_use_scope SET expires_at=clock_timestamp()+interval \'0.2 seconds\';')
waiter=subprocess.Popen(P+['-d',DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1);waiter.stdin.write('SELECT pg_backend_pid();BEGIN;'+select+'COMMIT;\n');waiter.stdin.close();pid=int(waiter.stdout.readline().strip());deadline=time.monotonic()+3
while time.monotonic()<deadline:
 if run('SELECT wait_event_type FROM pg_stat_activity WHERE pid='+str(pid)).stdout.strip()=='Lock':break
 time.sleep(.01)
else:raise AssertionError('expiry test failed to block on real root')
time.sleep(.3);lock_query('COMMIT;');lock_conn.stdin.close();assert lock_conn.wait(timeout=5)==0
rows=waiter.stdout.read();assert waiter.wait(timeout=5)==0,waiter.stderr.read();expired=json.loads(next(x for x in rows.splitlines()if x.startswith('{')));assert expired['diagnostic']=='SECRET_USE_CONTEXT_EXPIRED' and expired['protected_row']is None
run("UPDATE kcml_secret_v1.broker_use_scope SET expires_at=now()+interval '1 hour';");cases.append({'id':'lease-expired-during-lock-wait-fresh-postlock-clock-rejects','status':'PASS','diagnostic':'SECRET_USE_CONTEXT_EXPIRED'})
# Actual held PostgreSQL transaction encloses row → authenticated open →
# native use. Concurrent rotation waits on the real secret root UPDATE lock.
conn=subprocess.Popen(P+['-d',DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
def txquery(sql):
 conn.stdin.write(sql+'\n\\echo TX_END\n');conn.stdin.flush();lines=[]
 while True:
  line=conn.stdout.readline()
  if not line:raise AssertionError('transaction terminated:'+conn.stderr.read())
  if line.strip()=='TX_END':return lines
  lines.append(line.strip())
lines=txquery('BEGIN;'+select);held=json.loads(next(x for x in lines if x.startswith('{')));assert held['diagnostic']=='RESOLVED'
assert open_for_consumer(held['protected_row'],key,KEYID,datetime.now(timezone.utc))==imported['bytes']
issue_sql="SELECT kcml_secret_v1.broker_record_issuance_v1('"+held['resolution_id']+"',"+id('scope')+','+id('pending')+','+id('correlation')+');'
assert txquery(issue_sql)==[held['resolution_id']]
assert txquery(issue_sql)==[held['resolution_id']]
cases.append({'id':'canonical-open-native-validation-then-exact-pending-issuance-same-held-TX-replay','status':'PASS'})
rot=subprocess.Popen(P+['-d',DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
rot.stdin.write('SELECT pg_backend_pid();BEGIN;UPDATE kcml_secret_v1.secret_record SET secret_activation_epoch=secret_activation_epoch+1;COMMIT;\n');rot.stdin.close();pid=int(rot.stdout.readline().strip())
deadline=time.monotonic()+3
while time.monotonic()<deadline:
 if run("SELECT wait_event_type FROM pg_stat_activity WHERE pid="+str(pid)).stdout.strip()=='Lock':break
 time.sleep(.01)
else:raise AssertionError('rotation did not wait on actual lock')
cases.append({'id':'actual-root-UPDATE-held-through-authenticated-open-native-consumer','status':'PASS'})
txquery('COMMIT;');conn.stdin.close();assert conn.wait(timeout=5)==0,conn.stderr.read();assert rot.wait(timeout=5)==0,rot.stderr.read()
cases.append({'id':'rotation-commits-only-after-protected-use-transaction','status':'PASS'})
x=result();assert x['diagnostic']=='SECRET_OPERATION_VERSION_PIN_CONFLICT'and x['protected_row']is None
cases.append({'id':'post-rotation-same-operation-never-rebinds-version-or-epoch','status':'PASS','diagnostic':x['diagnostic']})
# SQL accepts no partial evidence on explicit rollback.
before=run('SELECT count(*) FROM kcml_secret_v1.broker_resolution_audit;').stdout.strip()
result('BEGIN;'+select+'ROLLBACK;');after=run('SELECT count(*) FROM kcml_secret_v1.broker_resolution_audit;').stdout.strip();assert before==after
cases.append({'id':'rollback-no-partial-resolution-audit','status':'PASS'})
q=run('SELECT count(*) FROM kcml_secret_v1.broker_issuance;');assert q.stdout.strip()=='1';cases.append({'id':'single-retained-issuance-under-replay','status':'PASS'})
run("DO $$BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_broker_untrusted_fixture') THEN CREATE ROLE kcml_broker_untrusted_fixture NOLOGIN;END IF;END$$;GRANT USAGE ON SCHEMA kcml_secret_v1 TO kcml_broker_untrusted_fixture;")
q=run('SET SESSION AUTHORIZATION kcml_broker_untrusted_fixture;'+select);assert q.returncode!=0 and 'permission denied for function'in q.stderr;cases.append({'id':'handler-untrusted-role-cannot-call-broker','status':'PASS'})
q=run('SET SESSION AUTHORIZATION kcml_broker_untrusted_fixture;SELECT ciphertext FROM kcml_secret_v1.secret_version;');assert q.returncode!=0 and 'permission denied for table'in q.stderr;cases.append({'id':'handler-untrusted-role-cannot-read-encrypted-store','status':'PASS'})
report={'checked':len(cases),'failed':0,'cases':cases,'sourceSha256':hashlib.sha256(source).hexdigest(),'sourceUnchanged':source==SSOT.read_bytes(),'canonicalInputs':{k:hashlib.sha256(r[k]['raw']).hexdigest()for k in ['database/secret-profile-roots.sql','database/generation-create-foundations.sql','database/canonical-crypto-registry.sql']},'candidateSqlSha256':hashlib.sha256(candidate).hexdigest(),'postgresVersion':run('SHOW server_version;').stdout.strip(),'fixtureCrypto':'ACTUAL_CANONICAL_AES256GCM_NOT_SYSTEMD_SOURCE','trustedRuntimeGatewayProducer':'NOT_EVALUATED_PRIVILEGED_SCOPE_AND_HEAD_FIXTURE','wholeOperationClosed':False,'plaintextInReport':False,'implementationAcceptance':'NOT_EVALUATED'}
(OUT/'broker-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'PASS')
