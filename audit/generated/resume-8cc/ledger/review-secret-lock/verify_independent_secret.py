from pathlib import Path
import sys,json,hashlib,secrets,copy,threading,time
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'audit/generated/resume-34d/auth-crypto'),str(OUT)]
from ssot_sources import SSOT,resource_index
from libpq_fixture import DB
from secret_command_chain import fixture_create_secret,create_secret,authenticate_api,lit,b,uid
from generation_auth_crypto import verifier_hash,fingerprint,canonical,sha,open_snapshot
class TraceDB:
 def __init__(self,actual):self.actual=actual;self.trace=[]
 def query(self,sql):self.trace.append(sql);return self.actual.query(sql)
 def __getattr__(self,name):return getattr(self.actual,name)
source=SSOT.read_bytes();rs=resource_index();name='secret_lock_review_8cc'
a=DB('postgres')
if not a.query('SELECT 1 FROM pg_database WHERE datname='+lit(name)):a.query('CREATE DATABASE '+name)
a.close();db=TraceDB(DB(name));db.query('SET client_min_messages=warning;DROP SCHEMA public CASCADE;CREATE SCHEMA public;');db.query('DROP SCHEMA IF EXISTS kcml_secret_v1 CASCADE')
resources=['database/generation-create-foundations.sql','database/secret-profile-roots.sql','database/secret-owner-binding.sql','database/secret-profile-publication.sql']
for p in resources:db.query(rs[p]['raw'].decode())
sql=(OUT/'secret-command-chain.sql').read_bytes();db.query(sql.decode())
owner=uid();inc=uid();sid=uid();vid=uid();token=secrets.token_urlsafe(32).encode();newtoken=secrets.token_urlsafe(32).encode();key=secrets.token_bytes(32);checks=[]
def rec(i,ok,diag=None):checks.append({'id':i,'status':'PASS'if ok else'FAIL','actualDiagnostic':diag})
db.query("INSERT INTO owner_identity VALUES("+lit(owner)+",1,'KRMAR78','FIXTURE_PASSWORD_HASH',now(),false,NULL,true,0,0,0,now(),now(),'GITHUB_ACTIONS_PASS');")
db.query('INSERT INTO platform_incarnation VALUES(1,'+lit(inc)+",1,now(),'ISOLATED_FIXTURE',NULL,NULL);")
db.query('INSERT INTO application_deployment_head VALUES(1,1,'+lit(uid())+','+b(sha(b'fixturemanifest'))+','+lit(inc)+',0,now());')
db.query('BEGIN; INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,state_version,secret_activation_epoch,created_at,updated_at)VALUES('+lit(sid)+",'KCML_OWNER_API_KEY','Synthetic','API_KEY','FIXTURE_STATUS_UNREVIEWED',0,0,now(),now());")
db.query('INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,creator_context_id)VALUES('+','.join([lit(vid),lit(sid),'1',"'API_KEY'","'RAW_UTF8'","'EXACT_SECRET_BYTES_V1'",str(len(token)),b(b'opaque'),' '+b(b'opaque'),"'FIXTURE_PREREQUISITE_NOT_CRYPTO_PROOF'","'FIXTURE_OWNER_KEY'",lit(fingerprint(token)),b(sha(token)),b(sha(token)),"'CREATED'",'now()',lit(uid())])+');')
db.query("UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=now(),activation_logical_operation_id="+lit(uid())+' WHERE id='+lit(vid)+'; UPDATE kcml_secret_v1.secret_record SET active_version_id='+lit(vid)+',state_version=1,secret_activation_epoch=1 WHERE id='+lit(sid)+';')
db.query('INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,credential_activation_epoch,created_at)VALUES('+','.join(['1',lit(sid),lit(vid),lit(verifier_hash(token)),lit(fingerprint(token)),'1','1','now()'])+');COMMIT;')
schema=rs['contracts/secrets/import.schema.json']['raw']
db.query('INSERT INTO kcml_secret_v1.operation_contract_publication VALUES('+','.join(["'secret.create'",'1',lit('sha256:'+sha(schema).hex()),b(schema),b(sha(schema)),b(sha(source))])+');')
body={'stableName':'SYNTHETIC_CHAIN','displayName':'Synthetic','type':'PASSWORD','value':{'encoding':'UTF8','text':'synthetic\u0001secret exact α'}}
def create(body_,client='case-main',omit=()):return fixture_create_secret(db,token,canonical(body_),client,key,'fixture-shared-master-key','FIXTURE_STATUS_UNREVIEWED','2099-01-01T00:00:00Z',omit=omit)
import re
class Inject:
 def __init__(self,db,transform):self.db=db;self.transform=transform;self.trace=[]
 def query(self,sql):self.trace.append(sql);return self.db.query(self.transform(sql))
 def __getattr__(self,n):return getattr(self.db,n)
def run_create(proxy,bdy,key_):return fixture_create_secret(proxy,token,canonical(bdy),key_,key,'fixture-shared-master-key','FIXTURE_STATUS_UNREVIEWED','2099-01-01T00:00:00Z')
def counts():return db.query("SELECT (SELECT count(*)FROM domain_command),(SELECT count(*)FROM kcml_secret_v1.secret_record),(SELECT count(*)FROM kcml_secret_v1.owner_api_context),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM audit_event)")[0]
trace_start=len(db.trace);db.query('BEGIN');positive=run_create(db,body,'review-positive');db.query('SET CONSTRAINTS ALL IMMEDIATE');trace=db.trace[trace_start:];db.query('COMMIT')
rec('actual-owner-token-native-positive-root-to-audit-commit',True)
foreignctx=db.query('SELECT trusted_context_id FROM kcml_secret_v1.create_completion WHERE logical_operation_id='+lit(positive['logicalOperationId']))[0][0]

def positive_then_negative(label,transform,diagnostic):
 bdy={**body,'stableName':'SYNTHETIC_REVIEW_'+label.upper()};client='review-'+label
 db.query('BEGIN');run_create(db,bdy,client);db.query('SET CONSTRAINTS ALL IMMEDIATE');db.query('ROLLBACK')
 before=counts();db.query('BEGIN')
 try:run_create(Inject(db,transform),bdy,client);db.query('SET CONSTRAINTS ALL IMMEDIATE');db.query('COMMIT');rec(label,False,'UNEXPECTED_COMMIT')
 except (RuntimeError,ValueError)as ex:rec(label,diagnostic in str(ex),str(ex)[-700:])
 finally:
  if db.transaction_status()!=0:db.query('ROLLBACK')
 rec(label+'/no-partial-artifacts',counts()==before)

def foreign(sql):
 if sql.startswith('INSERT INTO domain_command('):
  sql=re.sub(r"'OWNER_API_KEY','[0-9a-f-]{36}','SECRET_RECORD'", "'OWNER_API_KEY',"+lit(foreignctx)+",'SECRET_RECORD'",sql)
 return sql
positive_then_negative('foreign-context',foreign,'SECRET_CONTEXT_SINGLE_COMMAND_REQUIRED')

def receipt(sql):
 if sql.startswith('INSERT INTO domain_event VALUES(')or sql.startswith('INSERT INTO kcml_secret_v1.create_completion VALUES('):
  encoded=list(re.finditer(r"decode\('([0-9a-f]+)','hex'\)",sql))
  index=1 if sql.startswith('INSERT INTO domain_event')else 2
  old=bytes.fromhex(encoded[index][1]);doc=json.loads(old);doc['versionState']='ACTIVE';new=canonical(doc)
  sql=sql.replace(b(old),b(new)).replace(b(sha(old)),b(sha(new)))
 return sql
positive_then_negative('changed-public-receipt',receipt,'SECRET_CREATE_ATOMIC_CLOSURE_INCOMPLETE')
# Scoped replay selects frozen original scope even after current publication revision changes.
# Actual new release is independent B head/contract publication fixture, preserving old row.
before=counts();db.query('BEGIN');replay=run_create(db,body,'review-positive');db.query('COMMIT')
rec('scoped-frozen-replay-original-output-no-new-write',replay['replay']and replay['output']==positive['output']and counts()==before)
changed={**body,'displayName':'changed typed metadata'};db.query('BEGIN')
try:run_create(db,changed,'review-positive');rec('scoped-replay-different-native-request-conflict',False)
except ValueError as ex:rec('scoped-replay-different-native-request-conflict',str(ex)=='IDEMPOTENCY_CONFLICT')
finally:db.query('ROLLBACK')
# Actual isolated release epoch changes current B publication/revision while
# retained C0/C1 must keep original descriptor scope. No production deployment.
old_revision=db.query("SELECT operation_revision FROM kcml_secret_v1.operation_contract_publication WHERE operation_id='secret.create' AND application_deployment_epoch=1")[0][0]
db.query('BEGIN;SELECT pg_advisory_xact_lock(1000,0);')
db.query('UPDATE application_deployment_head SET application_deployment_epoch=2,state_version=state_version+1,updated_at=clock_timestamp() WHERE singleton_key=1;')
db.query('INSERT INTO kcml_secret_v1.operation_contract_publication VALUES('+','.join(["'secret.create'",'2',lit(old_revision+'-synthetic-release-2'),b(schema),b(sha(schema)),b(sha(source))])+');')
db.query('COMMIT');before=counts();db.query('BEGIN');revision_replay=run_create(db,body,'review-positive');db.query('COMMIT')
rec('current-release-changes-retained-replay-keeps-original-scope',revision_replay['replay']and revision_replay['output']==positive['output']and counts()==before and db.query('SELECT application_deployment_epoch FROM domain_command WHERE logical_operation_id='+lit(positive['logicalOperationId']))[0][0]=='1')
# Independently probe forged-but-crossrow-equal canonical result digests.
# No plaintext/cipher/request mutation: all unchanged positive domain bytes.
bdy={**body,'stableName':'SYNTHETIC_REVIEW_RESULT_DIGEST'};client='review-result-digest'
db.query('BEGIN');run_create(db,bdy,client);db.query('SET CONSTRAINTS ALL IMMEDIATE');db.query('ROLLBACK')
seen=[]
def forged_digest(sql):
 if sql.startswith('INSERT INTO domain_command('):
  encoded=list(re.finditer(r"decode\('([0-9a-f]+)','hex'\)",sql));seen.append(bytes.fromhex(encoded[3][1]))
 if seen and (sql.startswith('INSERT INTO domain_command(')or sql.startswith('INSERT INTO kcml_secret_v1.create_completion VALUES(')or sql.startswith('UPDATE domain_idempotency_record')):sql=sql.replace(b(seen[0]),b(bytes(32)))
 return sql
before=counts();db.query('BEGIN')
try:
 proposed=run_create(Inject(db,forged_digest),bdy,client);db.query('SET CONSTRAINTS ALL IMMEDIATE')
 got=db.query('SELECT encode(result_digest,\'hex\') FROM kcml_secret_v1.create_completion WHERE logical_operation_id='+lit(proposed['logicalOperationId']))[0][0]
 rec('forged-canonical-result-digest-rejected',False,{'actualAcceptedDigest':got,'expectedProducerResultDigest':proposed['response']['resultDigest'],'violation':'crossrow-equal arbitrary digest accepted although it is not hash of semantic result'})
except RuntimeError as ex:rec('forged-canonical-result-digest-rejected',True,str(ex)[-700:])
finally:db.query('ROLLBACK')
rec('review-counterexample-rolled-back-no-persistent-change',counts()==before)
# Lock-plan counterprobe pauses immediately before E10 and asks another real
# session for OWNER FOR UPDATE: an early FK KEY SHARE would make this timeout.
owner_probe=[]
def probe_before_e(sql):
 if sql.startswith('SELECT id FROM owner_identity')and'FOR UPDATE'in sql:
  probe=DB(name)
  try:probe.query("BEGIN;SET LOCAL lock_timeout='100ms';");probe.query('SELECT id FROM owner_identity WHERE id='+lit(owner)+' FOR UPDATE');owner_probe.append(True)
  except RuntimeError as ex:owner_probe.append(False)
  finally:probe.query('ROLLBACK');probe.close()
 return sql
db.query('BEGIN');run_create(Inject(db,probe_before_e),{**body,'stableName':'SYNTHETIC_REVIEW_NO_EARLY_OWNER'},'review-owner-lock');db.query('SET CONSTRAINTS ALL IMMEDIATE');db.query('COMMIT')
rec('actual-no-implicit-owner-keyshare-before-E10',owner_probe==[True])
# Continuous credential SHARE through the actual caller transaction conflicts
# with a real rotation writer, rather a declaration about lock ownership.
db.query('BEGIN');authenticate_api(db,token,sha(canonical(body)));contender=DB(name)
try:contender.query("BEGIN;SET LOCAL lock_timeout='100ms';");contender.query('UPDATE owner_api_credential SET state_version=state_version+1 WHERE singleton_key=1');rec('actual-credential-rotation-writer-blocked-through-acceptance',False)
except RuntimeError as ex:rec('actual-credential-rotation-writer-blocked-through-acceptance','lock timeout'in str(ex))
finally:contender.query('ROLLBACK');contender.close();db.query('ROLLBACK')
# Inspect every actual FK parent relation on C claims, not just SQL comments.
fk=db.query("SELECT conrelid::regclass::text,confrelid::regclass::text,condeferrable,condeferred FROM pg_constraint WHERE contype='f' AND conrelid IN('idempotency_locator'::regclass,'domain_idempotency_record'::regclass)")
rec('catalog-C0-C1-only-deferred-command-no-owner-FK',len(fk)==2 and all(v[1]=='domain_command'and v[2:]==['t','t']for v in fk))
markers=['FROM owner_api_credential','INSERT INTO idempotency_locator','INSERT INTO domain_idempotency_record','AND id='+lit(owner)+' FOR UPDATE','INSERT INTO kcml_secret_v1.secret_record','INSERT INTO kcml_secret_v1.owner_api_context','INSERT INTO kcml_secret_v1.secret_version','INSERT INTO domain_command','INSERT INTO domain_event','INSERT INTO kcml_secret_v1.create_completion','INSERT INTO transactional_outbox','FROM audit_head']
positions=[next(i for i,x in enumerate(trace)if marker in x)for marker in markers]
rec('independently-reproduced-B-C0-C1-E10-E20-H-I-order',positions==sorted(positions))
I=positions[-1];later=[v for v in trace[I+1:]if not v.startswith('SET CONSTRAINTS')]
rec('after-I-only-owned-audit-write-head-append',len(later)==1 and later[0].startswith('INSERT INTO audit_event')and'UPDATE audit_head'in later[0])
report={'inputCommit':'451b556067cb7cdd4f411cd742ab8fcaec8a379a','sourceSha256':sha(source).hex(),'sourceUnchangedDuringRun':source==SSOT.read_bytes(),'candidateSqlSha256':sha(sql).hex(),'candidateHelperSha256':sha((OUT/'secret_command_chain.py').read_bytes()).hex(),'postgresVersion':db.query('SHOW server_version')[0][0],'checks':checks,'checkCount':len(checks),'failedCount':sum(c['status']!='PASS'for c in checks),'fkCatalog':fk,'actualQueryFingerprints':[sha(v.encode()).hex()for v in trace],'wholeOperationClosed':False,'proofScope':'Independent current candidate actual owner-token verification/native acceptance/AES Secret row producer and PG lock/crossrow guards. Fixture master key is not systemd authority; existing credential cipher remains opaque.','remaining':['Actual OWNER_SESSION channel','Retention policy authoritative producer','Final installer/dispatcher roles','Target activation/provider/broker','Actual credential/master-key producers','Root status authoritative currentproducer']}
(OUT/'independent-secret-lock-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(checks),'failed':report['failedCount']}));db.close()
