from pathlib import Path
import sys,json,hashlib,secrets,copy,threading,time,re
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'audit/generated/resume-34d/auth-crypto'),str(OUT)]
from ssot_sources import SSOT,resource_index
from libpq_fixture import DB
from secret_command_chain_eligible import fixture_create_secret,create_secret,authenticate_api,lit,b,uid
from generation_auth_crypto import verifier_hash,fingerprint,canonical,sha,open_snapshot
class TraceDB:
 def __init__(self,actual):self.actual=actual;self.trace=[]
 def query(self,sql):self.trace.append(sql);return self.actual.query(sql)
 def __getattr__(self,name):return getattr(self.actual,name)
source=SSOT.read_bytes();rs=resource_index();name='key_secret_eligibility_peer_8cc'
a=DB('postgres')
if not a.query('SELECT 1 FROM pg_database WHERE datname='+lit(name)):a.query('CREATE DATABASE '+name)
a.close();db=TraceDB(DB(name));db.query('SET client_min_messages=warning;DROP SCHEMA public CASCADE;CREATE SCHEMA public;');db.query('DROP SCHEMA IF EXISTS kcml_secret_v1 CASCADE')
resources=['database/generation-create-foundations.sql','database/secret-profile-roots.sql','database/secret-owner-binding.sql','database/secret-profile-publication.sql']
for p in resources:db.query(rs[p]['raw'].decode())
encoder_source=rs['database/generation-protected-registry-link.sql']['raw'];start=encoder_source.index(b'CREATE FUNCTION kcml_crypto_compact_sorted_json_v1(');end=encoder_source.index(b'END $$;',start)+len(b'END $$;');encoder=encoder_source[start:end];db.query(encoder.decode())
sql=(OUT/'secret-command-chain-eligible.sql').read_bytes();db.query(sql.decode())
owner=uid();inc=uid();sid=uid();vid=uid();token=secrets.token_urlsafe(32).encode();newtoken=secrets.token_urlsafe(32).encode();key=secrets.token_bytes(32);checks=[]
def rec(i,ok,diag=None):checks.append({'id':i,'status':'PASS'if ok else'FAIL','actualDiagnostic':diag})
db.query("INSERT INTO owner_identity VALUES("+lit(owner)+",1,'KRMAR78','FIXTURE_PASSWORD_HASH',now(),false,NULL,true,0,0,0,now(),now(),'GITHUB_ACTIONS_PASS');")
db.query('INSERT INTO platform_incarnation VALUES(1,'+lit(inc)+",1,now(),'ISOLATED_FIXTURE',NULL,NULL);")
db.query('INSERT INTO application_deployment_head VALUES(1,1,'+lit(uid())+','+b(sha(b'fixturemanifest'))+','+lit(inc)+',0,now());')
db.query('BEGIN; INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,state_version,secret_activation_epoch,created_at,updated_at)VALUES('+lit(sid)+",'KCML_OWNER_API_KEY','Synthetic','API_KEY','FIXTURE_STATUS_UNREVIEWED',0,0,now(),now());")
db.query('INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,creator_context_id)VALUES('+','.join([lit(vid),lit(sid),'1',"'API_KEY'","'RAW_UTF8'","'EXACT_SECRET_BYTES_V1'",str(len(token)),b(b'opaque'),' '+b(b'opaque'),"'FIXTURE_PREREQUISITE_NOT_CRYPTO_PROOF'","'FIXTURE_OWNER_KEY'",lit(fingerprint(token)),b(sha(token)),b(sha(token)),"'CREATED'",'now()',lit(uid())])+');')
db.query("UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=now(),activation_logical_operation_id="+lit(uid())+' WHERE id='+lit(vid)+'; UPDATE kcml_secret_v1.secret_record SET active_version_id='+lit(vid)+',state_version=1,secret_activation_epoch=1 WHERE id='+lit(sid)+';')
db.query('INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,credential_activation_epoch,created_at)VALUES('+','.join(['1',lit(sid),lit(vid),lit(verifier_hash(token)),lit(fingerprint(token)),'1','1','now()'])+');COMMIT;')
status_sql=(OUT/'status/secret-record-status.sql').read_bytes();db.query(status_sql.decode())
schema=rs['contracts/secrets/import.schema.json']['raw']
db.query('INSERT INTO kcml_secret_v1.operation_contract_publication VALUES('+','.join(["'secret.create'",'1',lit('sha256:'+sha(schema).hex()),b(schema),b(sha(schema)),b(sha(source))])+');')
body={'stableName':'SYNTHETIC_CHAIN','displayName':'Synthetic','type':'PASSWORD','value':{'encoding':'UTF8','text':'synthetic\u0001secret exact α'}}
def create(body_,client='case-main',omit=()):return fixture_create_secret(db,token,canonical(body_),client,key,'fixture-shared-master-key','INACTIVE','2099-01-01T00:00:00Z',omit=omit)
trace_start=len(db.trace);db.query('BEGIN'); result=create(body);db.query('SET CONSTRAINTS ALL IMMEDIATE');positive_trace=db.trace[trace_start:]
observer=DB(name)
rec('command-root-event-outbox-audit-invisible-before-commit',observer.query("SELECT (SELECT count(*)FROM domain_command),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM transactional_outbox),(SELECT count(*)FROM audit_event)")[0]==['0']*4)
db.query('COMMIT')
rec('actual-secret-command-chain-committed',observer.query("SELECT (SELECT count(*)FROM domain_command),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM transactional_outbox),(SELECT count(*)FROM audit_event)")[0]==['1']*4)
rec('secret-specific-context-not-generation-substitute',db.query('SELECT count(*) FROM generation_create_trusted_context')[0][0]=='0')
rec('created-candidate-inactive',db.query('SELECT lifecycle,active_version_id FROM kcml_secret_v1.secret_version v JOIN kcml_secret_v1.secret_record r ON r.id=v.secret_id WHERE v.id='+lit(result['output']['versionId']))[0]==['CREATED',None])
# Authenticated open uses actual joined persisted identities and ciphertext.
row=db.query("SELECT c.owner_id,v.secret_id,v.id,v.secret_type,v.value_representation,v.profile_id,v.value_schema_id,encode(v.value_schema_digest,'hex'),v.plaintext_byte_length,encode(v.original_import_bytes_digest,'hex'),encode(v.canonical_value_digest,'hex'),c.id,x.logical_operation_id,v.algorithm,v.key_id,encode(v.nonce,'hex'),encode(v.ciphertext,'hex') FROM kcml_secret_v1.create_completion x JOIN kcml_secret_v1.owner_api_context c ON c.id=x.trusted_context_id JOIN kcml_secret_v1.secret_version v ON v.id=x.version_id WHERE x.logical_operation_id="+lit(result['logicalOperationId']))[0]
names=['ownerId','secretId','secretVersionId','secretType','representation','profileId','schemaId','schemaDigest','plaintextByteLength','originalImportBytesDigest','canonicalValueDigest','trustedContextId','logicalOperationId'];metadata=dict(zip(names,row[:13]));metadata['plaintextByteLength']=int(metadata['plaintextByteLength'])
for k in ['schemaDigest','originalImportBytesDigest','canonicalValueDigest']:
 if metadata[k] is not None:metadata[k]='sha256:'+metadata[k]
envelope={'algorithm':row[13],'keyId':row[14],'cryptoProfileDigest':__import__('generation_auth_crypto').profile_digest(),'nonce':bytes.fromhex(row[15]),'ciphertext':bytes.fromhex(row[16])}
with open_snapshot(envelope,key,row[14],metadata,lambda raw:raw.decode('utf8'),purpose='SECRET_IMMUTABLE_VERSION')as plain:rec('actual-secret-rows-authenticated-original-byte-hydration',bytes(plain)==body['value']['text'].encode())
db.query('BEGIN');replayed=create(body);db.query('COMMIT');rec('idempotent-replay-original-receipt-no-new-event',replayed['replay']and replayed['output']==result['output']and db.query('SELECT count(*)FROM domain_event')[0][0]=='1')
wrong=copy.deepcopy(body);wrong['displayName']='different'
db.query('BEGIN')
try:create(wrong);rec('same-key-changed-request-conflict',False)
except ValueError as e:rec('same-key-changed-request-conflict',str(e)=='IDEMPOTENCY_CONFLICT')
finally:db.query('ROLLBACK')
for component in ['completion','outbox','audit','idempotency','locator']:
 changed={**body,'stableName':'SYNTHETIC_MISSING_'+component};db.query('BEGIN')
 try:create(changed,'missing-'+component,omit=(component,));db.query('COMMIT');rec('missing-'+component+'-rolls-back-entire-chain',False)
 except RuntimeError as e:rec('missing-'+component+'-rolls-back-entire-chain','SECRET_CREATE_COMPLETION_REQUIRED' in str(e)if component=='completion'else'SECRET_CREATE_ATOMIC_CLOSURE_INCOMPLETE'in str(e))
 finally:
  if db.transaction_status()!=0:db.query('ROLLBACK')
 rec('no-leaked-'+component+'-artifacts',db.query('SELECT count(*)FROM domain_command')[0][0]=='1')
db.query('BEGIN')
try:authenticate_api(db,b'wrong-token',sha(b'actualrequest'));rec('actual-wrong-token-before-root-rejected',False)
except ValueError as e:rec('actual-wrong-token-before-root-rejected',str(e)=='OWNER_API_AUTHENTICATION_FAILED')
finally:db.query('ROLLBACK')
rec('failed-auth-no-context-or-command-leak',db.query('SELECT count(*)FROM kcml_secret_v1.owner_api_context')[0][0]=='1')
# Two same-key requests: unique C0 first claim makes the second wait for
# actual first COMMIT, then replay exact receipt without another event.
concurrent_body={**body,'stableName':'SYNTHETIC_CONCURRENT'}
db.query('BEGIN');first=create(concurrent_body,'same-concurrent-key')
started=threading.Event();finished=threading.Event();race=[]
def contender():
 c=DB(name)
 try:
  c.query('BEGIN');started.set()
  value=fixture_create_secret(c,token,canonical(concurrent_body),'same-concurrent-key',key,'fixture-shared-master-key','INACTIVE','2099-01-01T00:00:00Z')
  c.query('COMMIT');race.append(value)
 except Exception as ex:race.append(str(ex))
 finally:finished.set();c.close()
t=threading.Thread(target=contender);t.start();started.wait(3);time.sleep(.15)
rec('second-same-key-waits-for-real-first-commit',not finished.is_set())
db.query('COMMIT');t.join(10)
rec('two-requests-one-root-and-canonical-replay',len(race)==1 and isinstance(race[0],dict)and race[0]['replay']and race[0]['output']==first['output']and db.query('SELECT count(*)FROM domain_event')[0][0]=='2')
# Exact body byte metadata survives native import and physical root projection.
extra={**body,'stableName':'SYNTHETIC_METADATA','description':'exact α','purposeKind':'SYNTHETIC_PURPOSE','tags':['one','two'],'group':'a','url':'https://synthetic.invalid','username':'u','notes':'  exact  ','expiration':'2099-01-01T00:00:00Z'}
db.query('BEGIN');x=create(extra,'metadata-key');db.query('COMMIT')
rec('all-supplied-optional-metadata-persisted',db.query("SELECT description,purpose_kind,tags::text,group_name,url,username,notes,expires_at IS NOT NULL FROM kcml_secret_v1.secret_record WHERE id="+lit(x['output']['secretId']))[0]==['exact α','SYNTHETIC_PURPOSE','{one,two}','a','https://synthetic.invalid','u','  exact  ','t'])
# Domain writer may consume exact context but cannot mint an auth receipt.
db.query('BEGIN');db.query('SET LOCAL ROLE kcml_secret_domain_writer')
try:db.query('INSERT INTO kcml_secret_v1.owner_api_context SELECT * FROM kcml_secret_v1.owner_api_context LIMIT 1');rec('domain-writer-direct-auth-context-insert-denied',False)
except RuntimeError as ex:rec('domain-writer-direct-auth-context-insert-denied','permission denied'in str(ex))
finally:db.query('ROLLBACK')
try:create_secret();rec('real-adapter-retention-unresolved-fails-closed',False)
except ValueError as ex:rec('real-adapter-retention-unresolved-fails-closed',str(ex)=='SECRET_RETENTION_AUTHORITY_UNRESOLVED')
def first(marker):return next(i for i,stmt in enumerate(positive_trace)if marker in stmt)
ordered_markers=['FROM platform_incarnation','FROM application_deployment_head','FROM owner_api_credential','INSERT INTO idempotency_locator','INSERT INTO domain_idempotency_record','AND id='+lit(owner)+' FOR UPDATE','INSERT INTO kcml_secret_v1.secret_record','INSERT INTO kcml_secret_v1.owner_api_context','INSERT INTO kcml_secret_v1.secret_version','INSERT INTO domain_command','INSERT INTO domain_event','INSERT INTO kcml_secret_v1.create_completion','INSERT INTO transactional_outbox','FROM audit_head']
positions=[first(marker)for marker in ordered_markers]
rec('actual-native-query-stage-order-B-C-E-H-I',positions==sorted(positions))
audit_position=first('FROM audit_head')
post_audit=[x for x in positive_trace[audit_position+1:]if not x.startswith('SET CONSTRAINTS')]
rec('no-A-through-H-write-after-I-audit-head',len(post_audit)==1 and post_audit[0].startswith('INSERT INTO audit_event')and 'UPDATE audit_head'in post_audit[0])
fk=db.query("SELECT conrelid::regclass::text,confrelid::regclass::text,condeferrable,condeferred FROM pg_constraint WHERE contype='f' AND conrelid IN('idempotency_locator'::regclass,'domain_idempotency_record'::regclass)")
rec('catalog-C-claims-only-deferred-command-FKs-no-early-owner-lock',len(fk)==2 and all(x[1]=='domain_command' and x[2:] ==['t','t']for x in fk))
# Preserve the reviewer's exact counterexample: forge all three persisted
# result digests consistently, while plaintext/receipt/context remain valid.
class ForgeDB:
 def __init__(self,actual):self.actual=actual;self.result=None
 def query(self,sql):
  if sql.startswith('INSERT INTO domain_command('):
   encoded=list(re.finditer(r"decode\('([0-9a-f]+)','hex'\)",sql));self.result=bytes.fromhex(encoded[3][1])
  if self.result is not None and (sql.startswith('INSERT INTO domain_command(')or sql.startswith('INSERT INTO kcml_secret_v1.create_completion VALUES(')or sql.startswith('UPDATE domain_idempotency_record')):
   sql=sql.replace(b(self.result),b(bytes(32)))
  return self.actual.query(sql)
 def transaction_status(self):return self.actual.transaction_status()
forged={**body,'stableName':'SYNTHETIC_FORGED_RESULT'}
db.query('BEGIN')
try:
 fixture_create_secret(ForgeDB(db),token,canonical(forged),'forged-result',key,'fixture-shared-master-key','INACTIVE','2099-01-01T00:00:00Z');db.query('COMMIT');rec('independent-crossrow-equal-forged-result-digest-rejected',False)
except RuntimeError as ex:rec('independent-crossrow-equal-forged-result-digest-rejected','secret_semantic_result_digest'in str(ex))
finally:
 if db.transaction_status()!=0:db.query('ROLLBACK')
# Stronger mutation: replace semantic bytes AND all matching digests with a
# valid SHA-256 of the wrong finite response. Table hash equality alone passes;
# deferred recomputation from immutable receipt/command must reject at COMMIT.
class ForgeSemanticDB:
 def __init__(self,actual):self.actual=actual;self.result=None;self.wrong=None
 def query(self,sql):
  if sql.startswith('INSERT INTO domain_command('):
   encoded=list(re.finditer(r"decode\('([0-9a-f]+)','hex'\)",sql));self.result=bytes.fromhex(encoded[3][1]);self.wrong=canonical({'status':'SUCCEEDED','output':{'forged':True}})
  if self.result is not None and (sql.startswith('INSERT INTO domain_command(')or sql.startswith('INSERT INTO kcml_secret_v1.create_completion VALUES(')or sql.startswith('UPDATE domain_idempotency_record')):
   if sql.startswith('INSERT INTO kcml_secret_v1.create_completion VALUES('):
    encoded=list(re.finditer(r"decode\('([0-9a-f]+)','hex'\)",sql));sql=sql.replace(encoded[4][0],b(self.wrong))
   sql=sql.replace(b(self.result),b(sha(self.wrong)))
  return self.actual.query(sql)
 def transaction_status(self):return self.actual.transaction_status()
db.query('BEGIN')
try:
 fixture_create_secret(ForgeSemanticDB(db),token,canonical({**body,'stableName':'SYNTHETIC_FORGED_SEMANTIC'}),'forged-semantic-result',key,'fixture-shared-master-key','INACTIVE','2099-01-01T00:00:00Z');db.query('COMMIT');rec('coupled-valid-hash-wrong-semantic-bytes-rejected-at-commit',False)
except RuntimeError as ex:rec('coupled-valid-hash-wrong-semantic-bytes-rejected-at-commit','SECRET_CREATE_SEMANTIC_RESULT_MISMATCH'in str(ex))
finally:
 if db.transaction_status()!=0:db.query('ROLLBACK')
# Actual root UUID order in both fresh allocation directions.
import secret_command_chain_eligible as eligible
original_uid=eligible.uid
for suffix,target in [('low','00000000-0000-4000-8000-000000000001'),('high','ffffffff-ffff-4fff-8fff-ffffffffffff')]:
 counter=[0]
 def allocating():
  counter[0]+=1
  return target if counter[0]==4 else original_uid()
 eligible.uid=allocating;mark=len(db.trace);db.query('BEGIN')
 ordered_result=create({**body,'stableName':'SYNTHETIC_ORDER_'+suffix},'ordered-'+suffix);db.query('COMMIT');eligible.uid=original_uid
 e20=[]
 for statement in db.trace[mark:]:
  if statement.startswith('INSERT INTO kcml_secret_v1.secret_record'):e20.append(target)
  elif statement.startswith('SELECT id FROM kcml_secret_v1.secret_record')and statement.endswith('FOR UPDATE'):e20.append(sid)
 rec('actual-fresh-E20-UUID-order-'+suffix,e20==sorted([sid,target]))
 rec('approved-INACTIVE-create-output-'+suffix,ordered_result['output']['recordStatus']=='INACTIVE')
# Valid ACTIVE -> DELETED transition can commit physically with the same historical
# ACTIVE pointer. Both a waiting fresh request and replay must reject it.
def deletion_race(replay):
 writer=DB(name);started=threading.Event();finished=threading.Event();observed=[]
 request_body=body if replay else {**body,'stableName':'SYNTHETIC_DELETED_WAIT'}
 client='case-main'if replay else'deleted-wait-fresh'
 before=db.query('SELECT count(*)FROM domain_command')[0][0]
 writer.query('BEGIN;SELECT id FROM owner_identity WHERE id='+lit(owner)+' FOR UPDATE;SELECT id FROM kcml_secret_v1.secret_record WHERE id='+lit(sid)+' FOR UPDATE;UPDATE kcml_secret_v1.secret_record SET deleted_at=clock_timestamp(),state_version=state_version+1 WHERE id='+lit(sid)+';')
 def waiting():
  c=DB(name)
  try:
   c.query('BEGIN');started.set();fixture_create_secret(c,token,canonical(request_body),client,key,'fixture-shared-master-key','INACTIVE','2099-01-01T00:00:00Z');c.query('COMMIT');observed.append('UNSAFE_ACCEPTED')
  except (RuntimeError,ValueError)as ex:observed.append(str(ex))
  finally:
   if c.transaction_status()!=0:c.query('ROLLBACK')
   c.close();finished.set()
 t=threading.Thread(target=waiting);t.start();started.wait(3);time.sleep(.2)
 rec(('replay'if replay else'fresh')+'-waits-before-current-root-result',not finished.is_set())
 writer.query('COMMIT');t.join(10)
 rec(('replay'if replay else'fresh')+'-rejects-committed-DELETED-current-credential',len(observed)==1 and'OWNER_API_CREDENTIAL_ROOT_NOT_ACTIVE'in observed[0],observed[0]if observed else'NO_RESULT')
 rec(('replay'if replay else'fresh')+'-denial-leaves-no-command',db.query('SELECT count(*)FROM domain_command')[0][0]==before)
 writer.query('BEGIN;SELECT id FROM owner_identity WHERE id='+lit(owner)+' FOR UPDATE;SELECT id FROM kcml_secret_v1.secret_record WHERE id='+lit(sid)+' FOR UPDATE;UPDATE kcml_secret_v1.secret_record SET deleted_at=NULL WHERE id='+lit(sid)+';COMMIT;');writer.close()
deletion_race(False);deletion_race(True)
# Canonical OWNER binding prevents an INACTIVE current credential from committing.
# A waiter observes the actual rollback, never an invented accepted source state.
writer=DB(name);writer.query('BEGIN;SELECT id FROM owner_identity WHERE id='+lit(owner)+' FOR UPDATE;SELECT id FROM kcml_secret_v1.secret_record WHERE id='+lit(sid)+' FOR UPDATE;UPDATE kcml_secret_v1.secret_version SET lifecycle=\'RETIRED\',retired_at=now()WHERE id='+lit(vid)+';UPDATE kcml_secret_v1.secret_record SET active_version_id=NULL WHERE id='+lit(sid)+';')
started=threading.Event();finished=threading.Event();observed=[]
def after_inactive():
 c=DB(name)
 try:
  c.query('BEGIN');started.set();observed.append(fixture_create_secret(c,token,canonical(body),'case-main',key,'fixture-shared-master-key','INACTIVE','2099-01-01T00:00:00Z')['replay']);c.query('COMMIT')
 finally:
  if c.transaction_status()!=0:c.query('ROLLBACK')
  c.close();finished.set()
t=threading.Thread(target=after_inactive);t.start();started.wait(3);time.sleep(.2);rec('INACTIVE-change-waiter-does-not-return-before-source-decision',not finished.is_set())
try:writer.query('COMMIT');rec('canonical-current-credential-INACTIVE-producer-commit-denied',False)
except RuntimeError as ex:rec('canonical-current-credential-INACTIVE-producer-commit-denied','OWNER_CREDENTIAL_SECRET_BINDING_MISMATCH'in str(ex),str(ex).splitlines()[0])
finally:
 if writer.transaction_status()!=0:writer.query('ROLLBACK')
t.join(10);writer.close();rec('INACTIVE-rejected-source-rollback-waiter-replays-valid-ACTIVE',observed==[True])
# Independent positive-derived exact-binding negatives after real API verification.
from secret_command_chain_eligible import validate_locked_credential_root,lock_replay_roots_and_validate
for label,field,value,code in [('selected-version','credentialSecretVersionId',uid(),'OWNER_API_CREDENTIAL_ROOT_BINDING_MISMATCH'),('selected-root','credentialSecretId',uid(),'OWNER_API_CREDENTIAL_ROOT_UNAVAILABLE'),('owner-identity','owner',uid(),'SECRET_OWNER_IDENTITY_CHANGED')]:
 db.query('BEGIN');valid=authenticate_api(db,token,sha(b'peer exact binding'))
 db.query('SELECT id FROM owner_identity WHERE id='+lit(owner)+' FOR UPDATE;SELECT id FROM kcml_secret_v1.secret_record WHERE id='+lit(sid)+' FOR UPDATE;')
 validate_locked_credential_root(db,valid)
 changed=dict(valid);changed[field]=value
 try:
  if field=='owner':lock_replay_roots_and_validate(db,changed,result['output']['secretId'])
  else:validate_locked_credential_root(db,changed)
  rec('peer-positive-derived-'+label+'-binding',False)
 except ValueError as ex:rec('peer-positive-derived-'+label+'-binding',str(ex)==code,str(ex))
 finally:db.query('ROLLBACK')
report={'status':'PASS'if all(x['status']=='PASS'for x in checks)else'BLOCKED','checked':len(checks),'failed':sum(x['status']!='PASS'for x in checks),'checks':checks,'sourceSha256':sha(source).hex(),'sourceUnchangedDuringRun':source==SSOT.read_bytes(),'canonicalEmbeddedResourceSha256':{p:rs[p]['sha256']for p in resources},'canonicalEmbeddedCompactEncoderStatementSha256':sha(encoder).hex(),'candidateSqlSha256':sha(sql).hex(),'candidateStatusSqlSha256':sha(status_sql).hex(),'candidateHelperSha256':sha((OUT/'secret_command_chain_eligible.py').read_bytes()).hex(),'lockPlanSha256':sha((OUT/'secret-create-lock-plan.json').read_bytes()).hex(),'actualQueryTraceSha256':[sha(x.encode()).hex()for x in positive_trace],'queryStageOrder':ordered_markers,'queryTraceScope':'Actual libpq statements with exact C FK catalog check; excludes internal server SQL and does not claim arbitrary writer compliance. New child ordinals must be explicitly integrated before ready.','postgresVersion':db.query('SHOW server_version')[0][0],'wholeOperationClosed':False,'systemdCredentialSource':'NOT_EVALUATED_FIXTURE_KEY_ONLY','rootStatusPolicy':'APPROVED_PROJECTOR_CONSUMED_INACTIVE','retentionPolicy':'OPEN_FIXTURE_SERVER_DATE_NOT_PRODUCT_LIMIT','OWNERPrerequisiteCipher':'OPAQUE_EXISTING_CREDENTIAL_STATE_NOT_PROVISIONING_PROOF','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
(OUT/'credential-eligibility-postgres-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));db.close();observer.close()
