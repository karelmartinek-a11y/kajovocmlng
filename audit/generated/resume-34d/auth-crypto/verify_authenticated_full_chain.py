"""Real OWNER API material -> canonical joined PG root/event/outbox/audit COMMIT.
Uses current embedded foundation SQL unchanged, plus explicitly named technical
request-auth binding extension; real AES profile reference protects native input.
"""
from pathlib import Path
import sys,json,re,secrets,hashlib,copy,threading,time
HERE=Path(__file__).parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'audit/generated/resume-d362/persistence'))
from ssot_sources import SSOT,resource_index
from auth_crypto_reference import *
from acceptance_reference import authenticate_owner_api
from libpq_fixture import DB,lit
from generation_descriptor_registry import pin,descriptor as make_descriptor
from context_fixture_exports import common,call
from create_operation_contracts import validate_body,strict_json
raw=SSOT.read_bytes();rs=resource_index();foundation=rs['database/generation-create-foundations.sql']['raw'].decode();database='auth_crypto_full_34d'
admin=DB('postgres')
if not admin.query('SELECT 1 FROM pg_database WHERE datname='+lit(database)):admin.query('CREATE DATABASE '+database)
admin.close();db=DB(database);db.query('DROP SCHEMA public CASCADE;CREATE SCHEMA public;');db.query(foundation);auth_sql=rs.get('database/generation-create-authentication.sql',{}).get('raw',(HERE/'authentication-request-binding-proposed.sql').read_bytes())
assert auth_sql==(HERE/'authentication-request-binding-proposed.sql').read_bytes(),'AUTH_EXTENSION_EMBEDDED_BYTES_DIFFER_FROM_REVIEWED_CANDIDATE'
db.query(auth_sql.decode());db.query('ALTER TABLE generation_job_initial_request_snapshot ADD CONSTRAINT unique_generation_crypto_nonce UNIQUE(key_id,nonce)')
# Reuse historical independent exact success/event/audit fixture algebra without
# executing its proposal SQL, setup, report writes or historical auth fixture.
original=(ROOT/'audit/generated/resume-d362/events/verify_combined_generation.py').read_text()
program=original[:original.index('modulefile=')]+original[original.index('context='):original.index('# All negatives mutate')]
program=program.replace("descriptor=canonical_bytes(freeze_descriptor(native,{'owner':owner},'fixture-pinned-v1'));","descriptor=make_descriptor(owner,'sha256:'+key.hex(),pin());")
ns={'__file__':str(ROOT/'audit/generated/resume-d362/events/verify_combined_generation.py'),'make_descriptor':make_descriptor,'pin':pin};exec(compile(program,'read-only-reused-canonical-positive-factory','exec'),ns)
base=ns['base'];owner=ns['owner'];key=secrets.token_bytes(32);token=secrets.token_urlsafe(32).encode('ascii');new_token=secrets.token_urlsafe(32).encode('ascii');checks=[]
def rec(n,ok,code=None):checks.append({'case':n,'passed':bool(ok),'actualDiagnostic':code})
def setup():
 db.query(common(owner,owner,1)+f"INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,state_version,credential_activation_epoch,created_at)VALUES(1,'90000000-0000-4000-8000-000000000001','90000000-0000-4000-8000-000000000002',{lit(verifier_hash(token))},{lit(fingerprint(token))},1,0,1,clock_timestamp());")
setup()
def build():
 a=authenticate_owner_api(db,extract_owner_api_token([('Authorization',b'Bearer '+token)],4096),ns['request_digest'],4096,ns['descriptor'])
 db.query(call(owner,a['authenticationAcceptanceId'],ns['request_digest'].hex(),'sha256:'+ns['key'].hex()))
 db.query('SAVEPOINT second_context')
 try:
  db.query(call(owner,a['authenticationAcceptanceId'],ns['request_digest'].hex(),'sha256:'+ns['key'].hex()));rec('single-use-receipt-no-second-context',False)
 except Exception as ex:rec('single-use-receipt-no-second-context','generation_auth_receipt_single_context'in str(ex))
 finally:db.query('ROLLBACK TO SAVEPOINT second_context')
 ctx=db.query('SELECT id FROM generation_create_trusted_context WHERE authentication_acceptance_id='+lit(a['authenticationAcceptanceId']))[0][0]
 plaintext=ns['canonical_bytes'](ns['body'])
 meta={'ownerId':owner,'jobId':ns['job'],'snapshotId':ns['snap'],'logicalOperationId':ns['op'],'requestSchemaId':'urn:kcml:r9:semantic:route.0215:body','requestSchemaDigest':'sha256:'+pin()['domainSchemaDigest'].hex(),'contentDigest':'sha256:'+sha(plaintext).hex(),'trustedContextId':ctx,'platformIncarnationId':owner,'applicationDeploymentEpoch':1,'executionDescriptorDigest':'sha256:'+sha(ns['descriptor']).hex(),'initiatingAccessChannel':'OWNER_API_KEY'}
 enc=seal(plaintext,key,'fixture-systemd-key-generation-1',meta)
 parts={k:v for k,v in base.items()if k not in ('auth','context')}
 parts['command']=parts['command'].replace('fixture-pinned-v1',pin()['operationRevision'])
 parts['typed-binding']=f"INSERT INTO generation_create_command_binding VALUES('{ns['op']}','{ctx}','{ns['snap']}');"
 parts['snapshot']=f"INSERT INTO generation_job_initial_request_snapshot VALUES('{ns['job']}','{ns['snap']}','{ns['op']}',{lit(meta['requestSchemaId'])},{ns['b'](pin()['domainSchemaDigest'])},{ns['b'](sha(plaintext))},{ns['b'](enc['ciphertext'])},{ns['b'](enc['nonce'])},{lit(enc['algorithm'])},{lit(enc['keyId'])},{ns['b'](enc['cryptoProfileDigest'])},clock_timestamp());"
 return parts,meta,plaintext
# Full positive with actual credential SHARE held continuously through all artifacts.
db.query('BEGIN');parts,meta,plaintext=build();db.query(''.join(parts.values()));db.query('SET CONSTRAINTS ALL IMMEDIATE')
rotation=DB(database);started=threading.Event();finished=threading.Event();race=[]
def rotate():
 started.set()
 try:
  rotation.query('BEGIN');rotation.query('UPDATE owner_api_credential SET verifier_hash='+lit(verifier_hash(new_token))+',fingerprint='+lit(fingerprint(new_token))+',credential_version=credential_version+1,credential_activation_epoch=credential_activation_epoch+1,state_version=state_version+1');rotation.query('COMMIT');race.append('COMMITTED')
 except Exception as e:race.append(str(e))
 finally:finished.set()
t=threading.Thread(target=rotate);t.start();started.wait(3);time.sleep(.2);rec('rotation-cannot-cross-verified-token-to-full-command-commit',not finished.is_set())
# Observe actual invisibility from a third connection before commit.
observer=DB(database);counts=observer.query('SELECT (SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_command),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM transactional_outbox),(SELECT count(*)FROM audit_event)')[0]
rec('all-five-outcomes-invisible-before-commit',counts==['0']*5)
db.query('COMMIT');t.join(10);rec('rotation-after-full-canonical-acceptance-commit',race==['COMMITTED'])
counts=observer.query('SELECT (SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_command),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM transactional_outbox),(SELECT count(*)FROM audit_event)')[0];rec('all-five-outcomes-visible-atomically',counts==['1']*5)
# Hydration DERIVES authenticated metadata from actual joined persisted rows.
row=db.query("SELECT j.owner_id,j.id,s.snapshot_id,s.logical_operation_id,s.request_schema_id,encode(s.request_schema_digest,'hex'),encode(s.content_digest,'hex'),c.id,c.platform_incarnation_id,c.application_deployment_epoch,encode(c.execution_descriptor_digest,'hex'),c.initiating_access_channel,s.algorithm,s.key_id,encode(s.crypto_profile_digest,'hex'),encode(s.nonce,'hex'),encode(s.ciphertext,'hex')FROM generation_job j JOIN generation_job_initial_request_snapshot s ON s.job_id=j.id AND s.snapshot_id=j.initial_request_snapshot_id JOIN generation_create_command_binding cb ON cb.logical_operation_id=s.logical_operation_id AND cb.argument_snapshot_id=s.snapshot_id JOIN generation_create_trusted_context c ON c.id=cb.trusted_context_id AND c.id=j.initiating_execution_context_id")[0]
actual=dict(zip(IDENTITY_FIELDS,row[:12]));actual['applicationDeploymentEpoch']=int(actual['applicationDeploymentEpoch'])
for f in ('requestSchemaDigest','contentDigest','executionDescriptorDigest'):actual[f]='sha256:'+actual[f]
e={'algorithm':row[12],'keyId':row[13],'cryptoProfileDigest':bytes.fromhex(row[14]),'nonce':bytes.fromhex(row[15]),'ciphertext':bytes.fromhex(row[16])}
def consumer(v):validate_body('generation.job.create',strict_json(v))
with open_snapshot(e,key,'fixture-systemd-key-generation-1',actual,consumer) as view:rec('actual-persisted-bytes-hydrate-native-consumer',bytes(view)==plaintext)
# Immutable frozen context remains valid after key rotation, while new auth/replay
# with old key MUST authenticate again and fails, no retained receipt lookup.
db.query('BEGIN')
try:authenticate_owner_api(db,extract_owner_api_token([('Authorization',b'Bearer '+token)],4096),ns['request_digest'],4096,ns['descriptor']);rec('old-token-replay-denied-after-rotation',False)
except ValueError as ex:rec('old-token-replay-denied-after-rotation',str(ex)=='OWNER_API_AUTHENTICATION_FAILED')
finally:db.query('ROLLBACK')
version=db.query('SHOW server_version')[0][0]
report={'status':'PASS'if all(c['passed']for c in checks)else'BLOCKED','sourceDocumentSha256':sha(raw).hex(),'canonicalSqlSha256':rs['database/generation-create-foundations.sql']['sha256'],'postgresqlVersion':version,'checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'wholeOperationClosed':False,'proofScope':__doc__,'systemdKeyMaterialization':'BLOCKED_REQUIRED_PREGENERATION_FIXTURE','supportSha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()).hex()for p in [Path(__file__),HERE/'auth_crypto_reference.py',HERE/'acceptance_reference.py',HERE/'libpq_fixture.py',HERE/'authentication-request-binding-proposed.sql',ROOT/'audit/generated/resume-d362/events/verify_combined_generation.py']}}
(HERE/'authenticated-full-chain-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ('status','checked','failed')}));db.close();rotation.close();observer.close()
