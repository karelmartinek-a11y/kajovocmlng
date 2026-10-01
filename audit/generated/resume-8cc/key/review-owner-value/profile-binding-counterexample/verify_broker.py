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
DB='key_owner_profile_counterexample_8cc'
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
alternate_profile=b'{"profileId":"ISOLATED_DIFFERENT_DECLARED_PROFILE"}';alternate_digest=sha(alternate_profile)
sql+="INSERT INTO canonical_authenticated_crypto_profile VALUES('ISOLATED_DIFFERENT_DECLARED_PROFILE',"+b(alternate_profile)+','+b(alternate_digest)+",'AES_256_GCM');"
sql+="INSERT INTO canonical_master_key_generation VALUES('"+KEYID+"',"+b(sha(key))+",1,'ISOLATED_NOT_SYSTEMD','ISOLATED_NOT_SERVICE',"+b(alternate_digest)+",now());"
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
