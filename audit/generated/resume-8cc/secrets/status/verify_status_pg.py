from pathlib import Path
import sys,json,hashlib,threading,time,uuid
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'audit/generated/resume-34d/auth-crypto')]
from ssot_sources import SSOT,resource_index
from libpq_fixture import DB,lit
source=SSOT.read_bytes();r=resource_index();base=r['database/secret-profile-roots.sql']['raw'];candidate=(OUT/'secret-record-status.sql').read_bytes();name='secret_status_8cc'
a=DB('postgres')
if not a.query('SELECT 1 FROM pg_database WHERE datname='+lit(name)):a.query('CREATE DATABASE '+name)
a.close();db=DB(name);db.query('SET client_min_messages=warning;DROP SCHEMA IF EXISTS kcml_secret_v1 CASCADE;');db.query(base.decode())
sid=str(uuid.uuid4());other=str(uuid.uuid4());v1=str(uuid.uuid4());v2=str(uuid.uuid4());v3=str(uuid.uuid4());checks=[]
def rec(i,ok,diag=None):checks.append({'id':i,'status':'PASS'if ok else'FAIL','actualDiagnostic':diag})
def root(sid,name):return "INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,state_version,secret_activation_epoch,created_at,updated_at) VALUES("+lit(sid)+','+lit(name)+",'Synthetic','PASSWORD','LEGACY_UNREVIEWED_STATUS',0,0,now(),now());"
def version(vid,sid,num):return "INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,creator_context_id) VALUES("+lit(vid)+','+lit(sid)+','+str(num)+",'PASSWORD','RAW_UTF8','EXACT_SECRET_BYTES_V1',5,decode('010203','hex'),decode('040506','hex'),'FIXTURE_OPAQUE_NOT_CRYPTO_PROOF','FIXTURE_KEY','FIXTURE_FINGERPRINT',decode(repeat('00',32),'hex'),decode(repeat('00',32),'hex'),'CREATED',now(),'dddddddd-dddd-4ddd-8ddd-dddddddddddd');"
db.query(root(sid,'SYNTHETIC_STATUS')+root(other,'SYNTHETIC_OTHER'));db.query(version(v1,sid,1)+version(v2,sid,2)+version(v3,other,1));db.query(candidate.decode())
def get(s=sid):return db.query('SELECT status,kcml_secret_v1.record_status_v1(id) FROM kcml_secret_v1.secret_record WHERE id='+lit(s))[0]
rec('legacy-status-only-materialized-immutable-RAW-preserved',get()==['INACTIVE','INACTIVE']and db.query('SELECT value_representation,encode(ciphertext,\'hex\')FROM kcml_secret_v1.secret_version WHERE id='+lit(v1))[0]==['RAW_UTF8','010203'])
def activate(v):return "UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=now(),retired_at=NULL,activation_logical_operation_id='ffffffff-ffff-4fff-8fff-ffffffffffff' WHERE id="+lit(v)+';'
def pointer(v):return 'UPDATE kcml_secret_v1.secret_record SET active_version_id='+('NULL'if v is None else lit(v))+',state_version=state_version+1,secret_activation_epoch=secret_activation_epoch+1 WHERE id='+lit(sid)+';'
def transaction(sql):db.query('BEGIN;SELECT id FROM kcml_secret_v1.secret_record WHERE id='+lit(sid)+' FOR UPDATE;'+sql+'COMMIT;')
transaction(activate(v1)+pointer(v1));rec('atomic-activation-derived-ACTIVE',get()==['ACTIVE','ACTIVE'])
transaction("UPDATE kcml_secret_v1.secret_version SET lifecycle='RETIRED',retired_at=now()WHERE id="+lit(v1)+';'+activate(v2)+pointer(v2));rec('retire-before-activation-rotation-derived-ACTIVE',get()==['ACTIVE','ACTIVE'])
def negative(i,sql,expected):
 db.query('BEGIN')
 try:db.query(sql);db.query('COMMIT');rec(i,False)
 except RuntimeError as ex:rec(i,expected in str(ex),str(ex).splitlines()[0])
 finally:
  if db.transaction_status()!=0:db.query('ROLLBACK')
negative('readonly-status-edit','UPDATE kcml_secret_v1.secret_record SET status=\'INACTIVE\'WHERE id='+lit(sid),'SECRET_STATUS_NOT_EDITABLE')
negative('null-status-edit','UPDATE kcml_secret_v1.secret_record SET status=NULL WHERE id='+lit(sid),'SECRET_STATUS_NOT_EDITABLE')
negative('foreign-pointer-integrity','UPDATE kcml_secret_v1.secret_record SET active_version_id='+lit(v3)+' WHERE id='+lit(sid),'SECRET_STATUS_POINTER_IDENTITY_MISMATCH')
negative('unavailable-pointer-integrity','UPDATE kcml_secret_v1.secret_record SET active_version_id='+lit(str(uuid.uuid4()))+' WHERE id='+lit(sid),'SECRET_STATUS_POINTER_UNAVAILABLE')
negative('retired-pointer-integrity','UPDATE kcml_secret_v1.secret_record SET active_version_id='+lit(v1)+' WHERE id='+lit(sid),'SECRET_STATUS_POINTER_NOT_ACTIVE')
negative('active-without-pointer-integrity','UPDATE kcml_secret_v1.secret_record SET active_version_id=NULL WHERE id='+lit(sid),'SECRET_STATUS_ACTIVE_WITHOUT_POINTER')
negative('wrong-active-kind-integrity','UPDATE kcml_secret_v1.secret_record SET secret_type=\'API_KEY\' WHERE id='+lit(sid),'SECRET_STATUS_POINTER_IDENTITY_MISMATCH')
negative('absent-record-integrity','SELECT kcml_secret_v1.record_status_v1('+lit(str(uuid.uuid4()))+')','SECRET_STATUS_RECORD_UNAVAILABLE')
# Controlled corruption probes remove only private fixture enforcement inside
# rolled-back transactions. Canonical constraints are never weakened in output.
negative('multiple-active-diagnostic-not-silent-status',"DROP INDEX kcml_secret_v1.secret_one_active_version;"+activate(v1)+'SELECT kcml_secret_v1.record_status_v1('+lit(sid)+');','SECRET_STATUS_MULTIPLE_ACTIVE')
negative('stale-projection-diagnostic-not-silent-repair',"ALTER TABLE kcml_secret_v1.secret_record DISABLE TRIGGER secret_status_projection_before; UPDATE kcml_secret_v1.secret_record SET status='INACTIVE' WHERE id="+lit(sid)+';SELECT kcml_secret_v1.record_status_v1('+lit(sid)+');','SECRET_STATUS_PROJECTION_MISMATCH')
rec('counterexamples-rollback-restores-valid-state',get()==['ACTIVE','ACTIVE'])
transaction("UPDATE kcml_secret_v1.secret_version SET lifecycle='RETIRED',retired_at=now()WHERE id="+lit(v2)+';'+pointer(None));rec('atomic-deactivation-derived-INACTIVE',get()==['INACTIVE','INACTIVE'])
transaction(activate(v1)+pointer(v1));rec('historical-exact-RAW-reactivation-no-copy',get()==['ACTIVE','ACTIVE']and db.query('SELECT count(*)FROM kcml_secret_v1.secret_version WHERE secret_id='+lit(sid))[0][0]=='2')
before=db.query('SELECT state_version,secret_activation_epoch FROM kcml_secret_v1.secret_record WHERE id='+lit(sid))[0]
rec('read-replay-no-projection-state-epoch-mutation',get()==['ACTIVE','ACTIVE']and db.query('SELECT state_version,secret_activation_epoch FROM kcml_secret_v1.secret_record WHERE id='+lit(sid))[0]==before)
db.query('BEGIN;SELECT id FROM kcml_secret_v1.secret_record WHERE id='+lit(sid)+' FOR UPDATE;UPDATE kcml_secret_v1.secret_version SET lifecycle=\'RETIRED\',retired_at=now()WHERE id='+lit(v1)+';'+pointer(None))
started=threading.Event();finished=threading.Event();seen=[]
def waiter():
 c=DB(name)
 try:
  c.query('BEGIN');started.set();c.query('SELECT id FROM kcml_secret_v1.secret_record WHERE id='+lit(sid)+' FOR UPDATE')
  seen.append(c.query('SELECT status,kcml_secret_v1.record_status_v1(id) FROM kcml_secret_v1.secret_record WHERE id='+lit(sid))[0]);c.query('COMMIT')
 finally:finished.set();c.close()
t=threading.Thread(target=waiter);t.start();started.wait(3);time.sleep(.15);rec('concurrent-namespace-consumer-waits-for-projection-commit',not finished.is_set());db.query('COMMIT');t.join(10)
rec('concurrent-consumer-sees-one-committed-INACTIVE',seen==[['INACTIVE','INACTIVE']])
transaction('UPDATE kcml_secret_v1.secret_record SET deleted_at=now(),updated_at=now(),state_version=state_version+1 WHERE id='+lit(sid)+';');rec('deletion-derived-DELETED',get()==['DELETED','DELETED'])
negative('deletion-does-not-mask-foreign-pointer','UPDATE kcml_secret_v1.secret_record SET active_version_id='+lit(v3)+'WHERE id='+lit(sid),'SECRET_STATUS_POINTER_IDENTITY_MISMATCH')
rec('no-automatic-activation-or-version-rewrite-on-deletion',db.query('SELECT lifecycle,encode(ciphertext,\'hex\')FROM kcml_secret_v1.secret_version WHERE id='+lit(v1))[0]==['RETIRED','010203'])
report={'status':'PASS'if all(c['status']=='PASS'for c in checks)else'BLOCKED','checked':len(checks),'failed':sum(c['status']!='PASS'for c in checks),'checks':checks,'sourceSha256':hashlib.sha256(source).hexdigest(),'sourceUnchangedDuringRun':source==SSOT.read_bytes(),'canonicalSecretRootsSha256':hashlib.sha256(base).hexdigest(),'candidateStatusSqlSha256':hashlib.sha256(candidate).hexdigest(),'postgresVersion':db.query('SHOW server_version')[0][0],'approvedDecisionFile':'audit/OWNER_SECRET_ROOT_STATUS_DECISION.json','approvedDecisionFileSha256':hashlib.sha256((ROOT/'audit/OWNER_SECRET_ROOT_STATUS_DECISION.json').read_bytes()).hexdigest(),'proofScope':'Actual persisted derived status/immutable versions/integrity/deferred-finalchecks and concurrency; not full activation command/outbox/rotation verifier nor real master-key evidence','wholeOperationClosed':False,'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
(OUT/'status-postgres-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));db.close()
