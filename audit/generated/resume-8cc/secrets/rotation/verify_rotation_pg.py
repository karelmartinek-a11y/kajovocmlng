from pathlib import Path
import sys,json,hashlib,secrets,copy,threading,time,re
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'audit/generated/resume-34d/auth-crypto'),str(OUT),str(OUT.parent/'credential-eligibility')]
from ssot_sources import SSOT,resource_index
from libpq_fixture import DB
from secret_command_chain_eligible import fixture_create_secret,create_secret,authenticate_api,lit,b,uid
from generation_auth_crypto import verifier_hash,fingerprint,canonical,sha,open_snapshot
class TraceDB:
 def __init__(self,actual):self.actual=actual;self.trace=[]
 def query(self,sql):self.trace.append(sql);return self.actual.query(sql)
 def __getattr__(self,name):return getattr(self.actual,name)
source=SSOT.read_bytes();rs=resource_index();name='owner_rotate_projection_8cc'
a=DB('postgres')
if not a.query('SELECT 1 FROM pg_database WHERE datname='+lit(name)):a.query('CREATE DATABASE '+name)
a.close();db=TraceDB(DB(name));db.query('SET client_min_messages=warning;DROP SCHEMA public CASCADE;CREATE SCHEMA public;');db.query('DROP SCHEMA IF EXISTS kcml_secret_v1 CASCADE')
resources=['database/generation-create-foundations.sql','database/secret-profile-roots.sql','database/secret-owner-binding.sql','database/secret-profile-publication.sql']
for p in resources:db.query(rs[p]['raw'].decode())
encoder_source=rs['database/generation-protected-registry-link.sql']['raw'];start=encoder_source.index(b'CREATE FUNCTION kcml_crypto_compact_sorted_json_v1(');end=encoder_source.index(b'END $$;',start)+len(b'END $$;');encoder=encoder_source[start:end];db.query(encoder.decode())
sql=(OUT.parent/'credential-eligibility/secret-command-chain-eligible.sql').read_bytes();db.query(sql.decode())
owner=uid();inc=uid();sid=uid();vid=uid();token=secrets.token_urlsafe(32).encode();newtoken=secrets.token_urlsafe(32).encode();key=secrets.token_bytes(32);checks=[]
def rec(i,ok,diag=None):checks.append({'id':i,'status':'PASS'if ok else'FAIL','actualDiagnostic':diag})
db.query("INSERT INTO owner_identity VALUES("+lit(owner)+",1,'KRMAR78','FIXTURE_PASSWORD_HASH',now(),false,NULL,true,0,0,0,now(),now(),'GITHUB_ACTIONS_PASS');")
db.query('INSERT INTO platform_incarnation VALUES(1,'+lit(inc)+",1,now(),'ISOLATED_FIXTURE',NULL,NULL);")
db.query('INSERT INTO application_deployment_head VALUES(1,1,'+lit(uid())+','+b(sha(b'fixturemanifest'))+','+lit(inc)+',0,now());')
db.query('BEGIN; INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,state_version,secret_activation_epoch,created_at,updated_at)VALUES('+lit(sid)+",'KCML_OWNER_API_KEY','Synthetic','API_KEY','FIXTURE_STATUS_UNREVIEWED',0,0,now(),now());")
db.query('INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,creator_context_id)VALUES('+','.join([lit(vid),lit(sid),'1',"'API_KEY'","'RAW_UTF8'","'EXACT_SECRET_BYTES_V1'",str(len(token)),b(b'opaque'),' '+b(b'opaque'),"'FIXTURE_PREREQUISITE_NOT_CRYPTO_PROOF'","'FIXTURE_OWNER_KEY'",lit(fingerprint(token)),b(sha(token)),b(sha(token)),"'CREATED'",'now()',lit(uid())])+');')
db.query("UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=now(),activation_logical_operation_id="+lit(uid())+' WHERE id='+lit(vid)+'; UPDATE kcml_secret_v1.secret_record SET active_version_id='+lit(vid)+',state_version=1,secret_activation_epoch=1 WHERE id='+lit(sid)+';')
db.query('INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,credential_activation_epoch,created_at)VALUES('+','.join(['1',lit(sid),lit(vid),lit(verifier_hash(token)),lit(fingerprint(token)),'1','1','now()'])+');COMMIT;')
status_sql=(OUT.parent/'status/secret-record-status.sql').read_bytes();db.query(status_sql.decode())
schema=rs['contracts/secrets/import.schema.json']['raw']
db.query('INSERT INTO kcml_secret_v1.operation_contract_publication VALUES('+','.join(["'secret.create'",'1',lit('sha256:'+sha(schema).hex()),b(schema),b(sha(schema)),b(sha(source))])+');')
body={'stableName':'SYNTHETIC_CHAIN','displayName':'Synthetic','type':'PASSWORD','value':{'encoding':'UTF8','text':'synthetic\u0001secret exact α'}}
def create(body_,client='case-main',omit=()):return fixture_create_secret(db,token,canonical(body_),client,key,'fixture-shared-master-key','INACTIVE','2099-01-01T00:00:00Z',omit=omit)
from owner_rotation_projection import fixture_rotate_projection,rotate_owner_api_key
rotation_sql=(OUT/'rotation-projection.sql').read_bytes();db.query(rotation_sql.decode())
rotation_schema=(OUT/'rotation-request-proposal.schema.json').read_bytes()
db.query('INSERT INTO kcml_secret_v1.operation_contract_publication VALUES('+','.join(["'ownerApiKey.rotate'",'1',lit('sha256:'+sha(rotation_schema).hex()),b(rotation_schema),b(sha(rotation_schema)),b(sha(source))])+')')
def states(c=db):return c.query('SELECT c.credential_version,c.state_version,c.credential_activation_epoch,r.state_version,r.secret_activation_epoch,c.secret_version_id FROM owner_api_credential c JOIN kcml_secret_v1.secret_record r ON r.id=c.secret_id')[0]
def request(c=db):
 r=states(c);return canonical({'expectedCredentialStateVersion':r[1],'expectedSecretStateVersion':r[3]})
def rotate(c,t,raw,client):return fixture_rotate_projection(c,t,raw,client,key,'fixture-shared-master-key','2099-01-01T00:00:00Z')
from jsonschema import Draft202012Validator,FormatChecker
request_validator=Draft202012Validator(json.loads(rotation_schema),format_checker=FormatChecker());request_validator.check_schema(json.loads(rotation_schema))
output_validator=Draft202012Validator(json.loads((OUT/'rotation-output-proposal.schema.json').read_bytes()),format_checker=FormatChecker())
initial=states();initial_request=request();db.query('BEGIN');mark=len(db.trace);first=rotate(db,token,initial_request,'rotate-first');trace=db.trace[mark:]
observer=DB(name);rec('rotation-all-heads-unpublished-before-commit',states(observer)==initial);db.query('COMMIT')
now=states();rec('independent-JSON-schema-positive-request-output-valid',not list(request_validator.iter_errors(json.loads(initial_request)))and not list(output_validator.iter_errors(first['output'])));rec('atomic-credential-and-secret-exact-monotonic-epochs',now[:5]==['2','1','2','2','2'])
rec('one-ACTIVE-previous-RETIRED-no-immutable-copy',db.query('SELECT lifecycle,count(*)FROM kcml_secret_v1.secret_version WHERE secret_id='+lit(sid)+'GROUP BY lifecycle ORDER BY lifecycle')==[['ACTIVE','1'],['RETIRED','1']])
rec('rotated-output-no-secret-values',set(first['output'])=={'secretId','activeVersionId','versionNumber','recordStatus','secretStateVersion','secretActivationEpoch','credentialVersion','credentialStateVersion','credentialActivationEpoch','fingerprint','rotatedAt'}and not any(first['fixtureGeneratedToken'].decode()in statement for statement in db.trace))
row=db.query("SELECT encode(ciphertext,'hex'),encode(nonce,'hex'),algorithm,key_id FROM kcml_secret_v1.secret_version WHERE id="+lit(first['output']['activeVersionId']))[0]
envelope={'ciphertext':bytes.fromhex(row[0]),'nonce':bytes.fromhex(row[1]),'algorithm':row[2],'keyId':row[3],'cryptoProfileDigest':__import__('generation_auth_crypto').profile_digest()}
with open_snapshot(envelope,key,row[3],first['metadata'],lambda raw:raw.decode('ascii'),purpose='SECRET_IMMUTABLE_VERSION')as plain:rec('actual-persisted-cipher-opens-exact-generated-synthetic-bytes',bytes(plain)==first['fixtureGeneratedToken'])
newtoken=first['fixtureGeneratedToken']
def reject(name,call,expected):
 before=states();db.query('BEGIN')
 try:call();db.query('COMMIT');rec(name,False)
 except (ValueError,RuntimeError)as ex:rec(name,expected in str(ex),str(ex).splitlines()[0])
 finally:
  if db.transaction_status()!=0:db.query('ROLLBACK')
 rec(name+'-no-published-head-mutation',states()==before)
reject('old-verifier-rejected-after-real-rotation-commit',lambda:rotate(db,token,request(),'old-token'),'OWNER_API_AUTHENTICATION_FAILED')
reject('credential-CAS-conflict',lambda:rotate(db,newtoken,canonical({'expectedCredentialStateVersion':'0','expectedSecretStateVersion':'2'}),'bad-credential-CAS'),'OWNER_ROTATION_CREDENTIAL_STATE_CAS_CONFLICT')
reject('Secret-CAS-conflict',lambda:rotate(db,newtoken,canonical({'expectedCredentialStateVersion':'1','expectedSecretStateVersion':'1'}),'bad-secret-CAS'),'OWNER_ROTATION_SECRET_STATE_CAS_CONFLICT')
db.query('BEGIN');again=rotate(db,newtoken,initial_request,'rotate-first');db.query('COMMIT');rec('current-authenticated-replay-original-outcome-no-second-key',again['replay']and again['output']==first['output']and states()==now)
class MutationDB:
 def __init__(self,actual,kind):self.actual=actual;self.kind=kind
 def query(self,sql):
  if self.kind=='omit-outbox'and sql.startswith('INSERT INTO transactional_outbox'):return self.actual.query('SELECT 1')
  if self.kind=='epoch-jump'and sql.startswith('UPDATE owner_api_credential SET'):sql=sql.replace('credential_activation_epoch=credential_activation_epoch+1','credential_activation_epoch=credential_activation_epoch+2')
  return self.actual.query(sql)
 def transaction_status(self):return self.actual.transaction_status()
for mutation in ['omit-outbox','epoch-jump']:
 reject(mutation+'-actual-COMMIT-closure-rejected',lambda m=mutation:rotate(MutationDB(db,m),newtoken,request(),m),'OWNER_ROTATION_PROJECTION_ATOMIC_CLOSURE_INVALID')
# Real acceptance SHARE survives until commit, fencing an UPDATE rotation.
db.query('BEGIN');accepted=fixture_create_secret(db,newtoken,canonical({**body,'stableName':'SYNTHETIC_PRE_ROTATION_ACCEPTED'}),'accepted-before-rotation',key,'fixture-shared-master-key','INACTIVE','2099-01-01T00:00:00Z')
started=threading.Event();finished=threading.Event();seen=[];raw=request();
def pending_rotation():
 c=DB(name)
 try:c.query('BEGIN');started.set();seen.append(rotate(c,newtoken,raw,'rotate-after-acceptance'));c.query('COMMIT')
 except Exception as ex:seen.append({'error':str(ex)})
 finally:
  if c.transaction_status()!=0:c.query('ROLLBACK')
  c.close();finished.set()
t=threading.Thread(target=pending_rotation);t.start();started.wait(3);time.sleep(.2);rec('rotation-UPDATE-waits-for-real-acceptance-SHARE-commit',not finished.is_set());db.query('COMMIT');t.join(10)
rec('accepted-old-context-remains-durable-after-following-rotation',len(seen)==1 and'error'not in seen[0]and db.query('SELECT count(*)FROM domain_command WHERE logical_operation_id='+lit(accepted['logicalOperationId']))[0][0]=='1')
currenttoken=seen[0]['fixtureGeneratedToken']if seen and'error'not in seen[0]else newtoken
# Reverse order: verifier lock waits, then tests the committed new verifier.
db.query('BEGIN');pending=rotate(db,currenttoken,request(),'rotate-before-acceptance');started=threading.Event();finished=threading.Event();observed=[]
def pending_acceptance():
 c=DB(name)
 try:
  c.query('BEGIN');started.set();fixture_create_secret(c,currenttoken,canonical({**body,'stableName':'SYNTHETIC_STALE_AFTER_WAIT'}),'stale-after-rotation',key,'fixture-shared-master-key','INACTIVE','2099-01-01T00:00:00Z');c.query('COMMIT');observed.append('UNSAFE_ACCEPTED')
 except (ValueError,RuntimeError)as ex:observed.append(str(ex))
 finally:
  if c.transaction_status()!=0:c.query('ROLLBACK')
  c.close();finished.set()
t=threading.Thread(target=pending_acceptance);t.start();started.wait(3);time.sleep(.2);rec('new-acceptance-SHARE-waits-for-rotation-UPDATE-commit',not finished.is_set());db.query('COMMIT');t.join(10)
rec('old-verifier-waiter-denied-before-new-command',len(observed)==1 and'OWNER_API_AUTHENTICATION_FAILED'in observed[0]and db.query("SELECT count(*)FROM kcml_secret_v1.secret_record WHERE stable_name='SYNTHETIC_STALE_AFTER_WAIT'")[0][0]=='0')
# Two same-key requests: second waits on B3, authenticates committed current
# credential, then returns retained outcome without another random key/version.
active_token=pending['fixtureGeneratedToken'];db.query('BEGIN');raw=request();duo=rotate(db,active_token,raw,'two-rotation-same-key');started=threading.Event();finished=threading.Event();seen=[]
def duplicate_rotation():
 c=DB(name)
 try:c.query('BEGIN');started.set();seen.append(rotate(c,duo['fixtureGeneratedToken'],raw,'two-rotation-same-key'));c.query('COMMIT')
 except (ValueError,RuntimeError)as ex:seen.append({'error':str(ex)})
 finally:
  if c.transaction_status()!=0:c.query('ROLLBACK')
  c.close();finished.set()
t=threading.Thread(target=duplicate_rotation);t.start();started.wait(3);time.sleep(.2);rec('two-rotation-same-key-second-waits-on-real-B3',not finished.is_set());db.query('COMMIT');t.join(10)
rec('two-rotation-same-key-only-one-outcome-and-new-version',len(seen)==1 and seen[0].get('replay')and seen[0]['output']==duo['output']and states()[0]==duo['output']['credentialVersion'])
# A rolled-back key cannot become current; waiting old credential remains valid.
active_token=duo['fixtureGeneratedToken'];before=states();raw=request();db.query('BEGIN');uncommitted=rotate(db,active_token,raw,'rollback-then-retry');started=threading.Event();finished=threading.Event();seen=[]
def after_rotation_rollback():
 c=DB(name)
 try:c.query('BEGIN');started.set();seen.append(rotate(c,active_token,raw,'rollback-then-retry'));c.query('COMMIT')
 except (ValueError,RuntimeError)as ex:seen.append({'error':str(ex)})
 finally:
  if c.transaction_status()!=0:c.query('ROLLBACK')
  c.close();finished.set()
t=threading.Thread(target=after_rotation_rollback);t.start();started.wait(3);time.sleep(.2);rec('rollback-rotation-waiter-cannot-read-uncommitted-new-key',not finished.is_set());db.query('ROLLBACK');t.join(10)
rec('rollback-waiter-old-verifier-produces-one-committed-retry',len(seen)==1 and'error'not in seen[0]and not seen[0]['replay']and int(states()[0])==int(before[0])+1)
rec('rolled-back-new-version-and-outcome-absent',db.query('SELECT count(*)FROM kcml_secret_v1.secret_version WHERE id='+lit(uncommitted['output']['activeVersionId']))[0][0]=='0'and db.query('SELECT count(*)FROM domain_command WHERE logical_operation_id='+lit(uncommitted['logicalOperationId']))[0][0]=='0')
latest_token=seen[0]['fixtureGeneratedToken']
for case,raw_bad,expected in [
 ('missing-CAS-field',canonical({'expectedCredentialStateVersion':'0'}),'OWNER_ROTATION_REQUEST_FIELDS_INVALID'),
 ('extra-client-key',canonical({'expectedCredentialStateVersion':'0','expectedSecretStateVersion':'0','newToken':'synthetic'}),'OWNER_ROTATION_REQUEST_FIELDS_INVALID'),
 ('null-CAS',canonical({'expectedCredentialStateVersion':None,'expectedSecretStateVersion':'0'}),'OWNER_ROTATION_EXPECTED_VERSION_INVALID'),
 ('numeric-CAS',canonical({'expectedCredentialStateVersion':0,'expectedSecretStateVersion':'0'}),'OWNER_ROTATION_EXPECTED_VERSION_INVALID'),
 ('leading-zero-CAS',canonical({'expectedCredentialStateVersion':'00','expectedSecretStateVersion':'0'}),'OWNER_ROTATION_EXPECTED_VERSION_INVALID'),
 ('bigint-overflow',canonical({'expectedCredentialStateVersion':'9223372036854775808','expectedSecretStateVersion':'0'}),'OWNER_ROTATION_EXPECTED_VERSION_INVALID'),
 ('duplicate-JSON-CAS',b'{"expectedCredentialStateVersion":"0","expectedCredentialStateVersion":"0","expectedSecretStateVersion":"0"}','DUPLICATE_JSON_KEY'),
 ('invalid-JSON-encoding',b'\xff','INVALID_UTF8')]:
 reject(case,lambda raw_bad=raw_bad:rotate(db,latest_token,raw_bad,case),expected)
 if case not in ['duplicate-JSON-CAS','invalid-JSON-encoding']:rec(case+'-also-rejected-by-independent-request-mask',bool(list(request_validator.iter_errors(json.loads(raw_bad)))))
try:rotate_owner_api_key();rec('real-adapter-does-not-claim-empty-invalidation-inventory',False)
except ValueError as ex:rec('real-adapter-does-not-claim-empty-invalidation-inventory',str(ex)=='OWNER_ROTATION_EFFECTIVE_INVALIDATION_INVENTORY_UNRESOLVED')
report={'status':'PASS'if all(x['status']=='PASS'for x in checks)else'BLOCKED','checked':len(checks),'failed':sum(x['status']!='PASS'for x in checks),'checks':checks,'sourceSha256':sha(source).hex(),'sourceUnchangedDuringRun':source==SSOT.read_bytes(),'canonicalEmbeddedResourceSha256':{p:rs[p]['sha256']for p in resources},'statusSqlSha256':sha(status_sql).hex(),'createSqlSha256':sha(sql).hex(),'rotationSqlSha256':sha(rotation_sql).hex(),'rotationHelperSha256':sha((OUT/'owner_rotation_projection.py').read_bytes()).hex(),'proposedRequestSchemaBytesSha256':sha(rotation_schema).hex(),'rotationOutputMaskSha256':sha((OUT/'rotation-output-proposal.schema.json').read_bytes()).hex(),'postgresVersion':db.query('SHOW server_version')[0][0],'scope':'Bounded actual credential/root mutation, native verifier, CAS, canonical fixture-key AEAD, atomic outcome and acceptance locking. Not complete rotation/invalidation inventory, issuance/key authority or runtime acceptance.','OWNERPrerequisiteCipher':'OPAQUE_EXISTING_CREDENTIAL_STATE_NOT_PROVISIONING_PROOF','wholeOperationClosed':False,'effectiveInvalidationInventory':'OPEN_NOT_ASSUMED_EMPTY','systemdCredentialSource':'NOT_EVALUATED_SYNTHETIC_FIXTURE_KEY_ONLY','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
(OUT/'rotation-projection-postgres-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));db.close();observer.close()
