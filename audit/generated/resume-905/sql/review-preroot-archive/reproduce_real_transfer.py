"""Bounded real PG chain: actual auth/context/root + candidate typed nonce link.
Random fixture keys are not systemd evidence. No secret/key bytes in report.
"""
from pathlib import Path
import sys,json,copy
HERE=Path(__file__).parent;ROOT=Path('/workspace/kajovocmlng')
for p in [ROOT/'scripts',ROOT/'audit/generated/resume-34d/auth-crypto',ROOT/'audit/generated/resume-d362/persistence']:sys.path.insert(0,str(p))
from ssot_sources import SSOT,resource_index
from generation_auth_crypto import canonical,sha,aad,open_snapshot
from libpq_fixture import DB,lit
original=ROOT/'audit/generated/resume-34d/auth-crypto/verify_authenticated_full_chain.py'
program=original.read_text().split('# Full positive')[0]
program=program.replace("database='auth_crypto_full_34d'","database='independent_crypto_preroot_archive905'").replace('from auth_crypto_reference import *','from generation_auth_crypto import *').replace('from acceptance_reference import authenticate_owner_api','from generation_auth_acceptance import authenticate_owner_api')
ns={'__file__':str(original)};exec(compile(program,'reviewed-existing-auth-chain-positive-factory','exec'),ns)
db=ns['db'];rs=resource_index()
for name in ['database/generation-create-preroot.sql','database/canonical-crypto-registry.sql']:db.query(rs[name]['raw'].decode())
candidate=rs['database/generation-protected-registry-link.sql']['raw'];db.query(candidate.decode())
for n in ['database/generation-frozen-archive.sql','database/generation-create-read.sql']:db.query(rs[n]['raw'].decode())
import hashlib,subprocess
from generation_frozen_archive import policy_bytes,DOMAIN_IMPLEMENTATION,POLICY_ID,compile_archived_request
from generation_read_hydration_archive import hydrate_storage
import generation_frozen_archive,generation_read_hydration_archive,generation_create_consumer_archive
from create_operation_contracts import ContractFailure
assert Path(generation_frozen_archive.__file__).resolve()==ROOT/'scripts/generation_frozen_archive.py'
assert Path(generation_read_hydration_archive.__file__).resolve()==ROOT/'scripts/generation_read_hydration_archive.py'
assert Path(generation_create_consumer_archive.__file__).resolve()==ROOT/'scripts/generation_create_consumer_archive.py'
source=SSOT.read_bytes();checks=[]
extension=rs['database/generation-preroot-frozen-archive.sql']['raw'];assert extension==(HERE/'generation-preroot-frozen-archive.sql').read_bytes(),'CANONICAL_PREROOT_ARCHIVE_BYTES_DIFFER';db.query(extension.decode())
pinned=ns['pin']();ns['pin']=lambda:pinned
schema_raw=pinned['domainSchemaBytes'];mask=json.loads(schema_raw);schema_id=mask['$id']
authority=source[source.index(b'### 12.47'):source.index(b'### 12.48')]+source[source.index(b'### 12.54'):source.index(b'## 13.',source.index(b'### 12.54'))]
policy=policy_bytes(authority,DOMAIN_IMPLEMENTATION)
def digest(raw):return 'sha256:'+sha(raw).hex()
def rec(name,ok,expected=None,actual=None):
 checks.append({'id':name,'passed':bool(ok),'expectedDiagnostic':expected,'actualDiagnostic':actual});assert ok,(name,actual)
def b(raw):return "decode('"+raw.hex()+"','hex')"
def publish(kind,id,raw):return 'SELECT kcml_archive_publish_v1('+','.join([lit(kind),lit(id),b(sha(raw)),b(raw),"'SSOT#12.47+12.54'",b(sha(authority))])+');'
publication=publish('SCHEMA',schema_id,schema_raw)+publish('DOMAIN_POLICY',POLICY_ID,policy)+publish('AUTHORITY','SSOT#12.47+12.54',authority)+publish('POLICY_IMPLEMENTATION','GENERATION_CREATE_REQUEST_SEMANTICS_V1',DOMAIN_IMPLEMENTATION)
def install_protected(parts,meta):
 db.query(''.join(parts.values()))
 row=db.query("SELECT encode(ciphertext,'hex'),encode(nonce,'hex')FROM generation_job_initial_request_snapshot")[0]
 cipher=bytes.fromhex(row[0]);nonce=bytes.fromhex(row[1]);keyid='fixture-systemd-key-generation-1';metadata=aad(meta,key_id=keyid)
 db.query("INSERT INTO canonical_authenticated_crypto_profile VALUES('KCML_PROTECTED_INPUT_AES256_GCM_V1',"+b(ns['profile_bytes']())+','+b(ns['profile_digest']())+",'AES_256_GCM');")
 db.query('INSERT INTO canonical_master_key_generation VALUES('+lit(keyid)+','+b(sha(ns['key']))+",1,'kcml-master-key','isolated-fixture.service',"+b(ns['profile_digest']())+',clock_timestamp());')
 db.query('INSERT INTO canonical_protected_nonce_reservation VALUES('+','.join([lit(keyid),b(nonce),"'GENERATION_INITIAL_REQUEST'",lit(meta['snapshotId']),lit(meta['logicalOperationId']),b(metadata),b(sha(metadata)),b(sha(cipher))])+');')
 return {'algorithm':'AES_256_GCM','keyId':keyid,'cryptoProfileDigest':ns['profile_digest'](),'nonce':nonce,'ciphertext':cipher}
def archive_bind(meta):
 return 'INSERT INTO generation_frozen_policy_binding_v1(snapshot_id,logical_operation_id,schema_id,schema_digest,policy_id,policy_digest,dependency_closure)VALUES('+','.join([lit(meta['snapshotId']),lit(meta['logicalOperationId']),lit(schema_id),b(sha(schema_raw)),lit(POLICY_ID),b(sha(policy)),"'[]'"])+');'
import re,struct
# Reuse only pure retained outcome producer, not its old setup/proposal SQL.
original_failure=ROOT/'audit/generated/resume-34d/failure-sql/verify_failure_before_root.py'
failure_source=original_failure.read_text()
failure_function=failure_source[failure_source.index('def parts('):failure_source.index('checks=[]',failure_source.index('def parts('))]
inner=ns['ns'];inner['pinned']=pinned

def pending_parts(positive,meta):
 env={'ns':inner,'owner':meta['ownerId'],'op':meta['logicalOperationId'],'job':meta['jobId'],'snap':meta['snapshotId'],'context':lit(meta['trustedContextId']),'audit':inner['audit'],'authsql':'','contextsql':'','copy':copy,'json':json,'hashlib':hashlib,'struct':struct,'b':b}
 exec(compile(failure_function,'unchanged-pure-native-retained-outcome-factory','exec'),env)
 ps=env['parts']('ACCEPTED',False);ps.pop('auth');ps.pop('context')
 hexes=re.findall(r"decode\('([0-9a-f]+)','hex'\)",positive['snapshot']);assert len(hexes)==5
 env_cipher={'algorithm':'AES_256_GCM','keyId':'fixture-systemd-key-generation-1','cryptoProfileDigest':bytes.fromhex(hexes[4]),'nonce':bytes.fromhex(hexes[3]),'ciphertext':bytes.fromhex(hexes[2])}
 ps['snapshot']='INSERT INTO generation_create_preroot_snapshot VALUES('+','.join([lit(meta['snapshotId']),lit(meta['logicalOperationId']),lit(meta['jobId']),lit(meta['trustedContextId']),lit(meta['requestSchemaId']),b(bytes.fromhex(hexes[0])),b(bytes.fromhex(hexes[1])),b(env_cipher['ciphertext']),b(env_cipher['nonce']),lit(env_cipher['algorithm']),lit(env_cipher['keyId']),b(env_cipher['cryptoProfileDigest']),'clock_timestamp()'])+');'
 return ps,env_cipher

def reserve(meta,envelope):
 metadata=aad(meta,key_id=envelope['keyId'])
 db.query("INSERT INTO canonical_authenticated_crypto_profile VALUES('KCML_PROTECTED_INPUT_AES256_GCM_V1',"+b(ns['profile_bytes']())+','+b(ns['profile_digest']())+",'AES_256_GCM');")
 db.query('INSERT INTO canonical_master_key_generation VALUES('+lit(envelope['keyId'])+','+b(sha(ns['key']))+",1,'kcml-master-key','isolated-fixture.service',"+b(ns['profile_digest']())+',clock_timestamp());')
 db.query('INSERT INTO canonical_protected_nonce_reservation VALUES('+','.join([lit(envelope['keyId']),b(envelope['nonce']),"'GENERATION_INITIAL_REQUEST'",lit(meta['snapshotId']),lit(meta['logicalOperationId']),b(metadata),b(sha(metadata)),b(sha(envelope['ciphertext']))])+');')

def bind_preroot(meta):return archive_bind(meta).replace('generation_frozen_policy_binding_v1','generation_preroot_frozen_policy_binding_v1')
def zero():return db.query('SELECT(SELECT count(*)FROM domain_command),(SELECT count(*)FROM generation_create_preroot_snapshot),(SELECT count(*)FROM generation_preroot_frozen_policy_binding_v1),(SELECT count(*)FROM canonical_protected_nonce_reservation)')[0]==['0']*4

def pending_negative(name,mutation,expected):
 db.query('BEGIN')
 try:
  positive,meta,plain=ns['build']();pending,envelope=pending_parts(positive,meta);db.query(''.join(pending.values()));reserve(meta,envelope)
  pub=publication;binding=bind_preroot(meta)
  if mutation=='missing-binding':binding=''
  if mutation=='missing-bytes':pub=''
  if mutation=='wrong-schema':
   alternate=schema_raw+b' ';pub+=publish('SCHEMA',schema_id,alternate);binding=binding.replace(b(sha(schema_raw)),b(sha(alternate)))
  if mutation=='missing-dependency':binding=binding.replace("'[]'",lit(json.dumps([{'schemaId':'urn:missing:dependency','bundleDigest':'sha256:'+'00'*32}])))
  db.query(pub+binding);db.query('COMMIT');rec(name,False,expected,'ACCEPTED_UNEXPECTEDLY')
 except Exception as e:
  db.query('ROLLBACK');rec(name,expected in str(e),expected,str(e))
 rec(name+'-whole-chain-rolled-back',zero())

pending_negative('accepted-preroot-missing-archive-binding','missing-binding','FROZEN_PREROOT_ARCHIVE_REQUIRED')
pending_negative('accepted-preroot-missing-schema-bytes','missing-bytes','preroot_archive_schema_fk')
pending_negative('accepted-preroot-available-wrong-schema-digest','wrong-schema','FROZEN_PREROOT_ARCHIVE_SNAPSHOT_BINDING_MISMATCH')
pending_negative('accepted-preroot-missing-closure-bytes','missing-dependency','FROZEN_ARCHIVE_DEPENDENCY_UNAVAILABLE')

# Real verified-token acceptance+protected byte producer+archive BEFORE any root.
db.query('BEGIN');positive,meta,plain=ns['build']();pending,envelope=pending_parts(positive,meta);db.query(''.join(pending.values()));reserve(meta,envelope);db.query(publication+bind_preroot(meta));db.query('COMMIT')
rec('accepted-preroot-actual-auth-crypto-archive-outcome-commit',True)
counts=db.query('SELECT(SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM transactional_outbox),(SELECT count(*)FROM generation_create_preroot_snapshot),(SELECT count(*)FROM generation_create_preroot_outcome),(SELECT count(*)FROM generation_preroot_frozen_policy_binding_v1)')[0]
rec('accepted-preroot-no-fabricated-root-or-created-event',counts==['0','0','0','1','1','1'])
previous=db.query("SELECT encode(event_hash,'hex')FROM audit_event")[0][0]
retained_before=db.query("SELECT encode(canonical_bytes,'hex')FROM generation_create_preroot_outcome")[0][0]
archive_before=json.loads(db.query('SELECT kcml_preroot_archive_read_v1('+lit(meta['snapshotId'])+','+lit(meta['logicalOperationId'])+');')[0][0])
rec('actual-preroot-archive-read-available-without-root',archive_before['binding']['schemaDigest']==digest(schema_raw) and bytes.fromhex(archive_before['bundles'][digest(policy)])==policy)
# Preserve exact real ciphertext from accepted snapshot during later successful
# progression; never obtain a new identity, encrypt anew or select current policy.
transfer={k:positive[k]for k in ['root','snapshot','event','outbox','completion','typed-binding']}
transfer['command']=f"UPDATE domain_command SET state='SUCCEEDED',terminal=true,state_version=state_version+1,result_digest={b(inner['rd'])},terminal_at=clock_timestamp(),updated_at=clock_timestamp() WHERE logical_operation_id='{meta['logicalOperationId']}' AND state='ACCEPTED' AND state_version=1;"
transfer['idempotency']=f"UPDATE domain_idempotency_record SET state='SUCCEEDED',state_version=state_version+1,canonical_outcome_digest={b(inner['rd'])} WHERE logical_operation_id='{meta['logicalOperationId']}' AND state='EXECUTING' AND state_version=1;"
abody=inner['auditbody'].copy();abody.update(chainSequence='2',previousHash='sha256:'+previous)
ab=inner['canonical_bytes'](abody);ah=hashlib.sha256(b'KCML-AUDIT-CHAIN'+struct.pack('>I',1)+bytes.fromhex(previous)+struct.pack('>q',2)+struct.pack('>q',len(ab))+ab).digest();newaudit='00000000-0000-4000-8000-000000000012'
transfer['audit']=f"SELECT *FROM audit_head WHERE singleton_key=1 FOR UPDATE;INSERT INTO audit_event VALUES('{newaudit}',2,{b(bytes.fromhex(previous))},{b(ah)},1,'{meta['logicalOperationId']}','{inner['eventid']}',{b(ab)},false);UPDATE audit_head SET last_sequence=2,last_hash={b(ah)},state_version=state_version+1 WHERE singleton_key=1 AND last_sequence=1;"
transfer['archive-binding']=archive_bind(meta)

def transfer_negative(name,change,code):
 values=transfer.copy();extra=''
 if change=='missing-binding':values.pop('archive-binding')
 if change=='different-policy':
  other_policy=json.loads(policy);other_policy['revision']='DIFFERENT_RETAINED_REVISION';other=canonical(other_policy);extra=publish('DOMAIN_POLICY',POLICY_ID,other);values['archive-binding']=values['archive-binding'].replace(b(sha(policy)),b(sha(other)))
 if change=='different-closure':
  dep=b'{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:fixture:dependency","type":"string"}';extra=publish('SCHEMA','urn:fixture:dependency',dep);values['archive-binding']=values['archive-binding'].replace("'[]'",lit(json.dumps([{'schemaId':'urn:fixture:dependency','bundleDigest':digest(dep)}])))
 if change=='ciphertext':values['snapshot']=values['snapshot'].replace(b(envelope['ciphertext']),b(envelope['ciphertext'][:-1]+bytes([envelope['ciphertext'][-1]^1])))
 db.query('BEGIN')
 try:db.query(extra+''.join(values.values()));db.query('COMMIT');rec(name,False,code,'ACCEPTED_UNEXPECTEDLY')
 except Exception as e:db.query('ROLLBACK');rec(name,code in str(e),code,str(e))
 counts=db.query('SELECT(SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM generation_frozen_policy_binding_v1),(SELECT state FROM domain_command)')[0]
 retained_archive=json.loads(db.query('SELECT kcml_preroot_archive_read_v1('+lit(meta['snapshotId'])+','+lit(meta['logicalOperationId'])+');')[0][0])
 retained_outcome=db.query("SELECT encode(canonical_bytes,'hex')FROM generation_create_preroot_outcome")[0][0]
 rec(name+'-keeps-existing-accepted-history-only',counts==['0','0','0','ACCEPTED'] and retained_archive==archive_before and retained_outcome==retained_before)

transfer_negative('success-transfer-missing-success-archive','missing-binding','FROZEN_ARCHIVE_REQUIRED')
transfer_negative('success-transfer-same-schema-different-policy','different-policy','FROZEN_PREROOT_ARCHIVE_TRANSFER_MISMATCH')
transfer_negative('success-transfer-available-different-closure','different-closure','FROZEN_PREROOT_ARCHIVE_TRANSFER_MISMATCH')
transfer_negative('success-transfer-protected-byte-reservation-mismatch','ciphertext','GENERATION_PROTECTED_RESERVATION_BINDING_INVALID')
db.query('BEGIN');db.query(''.join(transfer.values()));db.query('COMMIT');rec('accepted-to-success-exact-archive-and-protected-bytes-commit',True)
archive_after=json.loads(db.query('SELECT kcml_archive_read_v1('+lit(meta['snapshotId'])+','+lit(meta['logicalOperationId'])+');')[0][0])
rec('successful-archive-identical-to-retained-preroot-archive',archive_before==archive_after)
rec('prior-pending-outcome-bytes-retained',db.query("SELECT encode(canonical_bytes,'hex')FROM generation_create_preroot_outcome")[0][0]==retained_before)
counts=db.query('SELECT(SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_command),(SELECT count(*)FROM generation_job_initial_request_snapshot),(SELECT count(*)FROM generation_create_preroot_snapshot),(SELECT count(*)FROM generation_create_preroot_outcome),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM transactional_outbox),(SELECT count(*)FROM audit_event)')[0]
rec('one-root-command-event-outbox-with-earlier-history-two-audits',counts==['1','1','1','1','1','1','1','2'])
try:db.query('UPDATE generation_preroot_frozen_policy_binding_v1 SET policy_digest=policy_digest;');rec('retained-preroot-binding-immutable',False)
except Exception as e:rec('retained-preroot-binding-immutable','FROZEN_ARCHIVE_IMMUTABLE'in str(e),'FROZEN_ARCHIVE_IMMUTABLE',str(e))
validator=compile_archived_request(archive_after['binding'],{d:bytes.fromhex(raw)for d,raw in archive_after['bundles'].items()},policy_implementations={digest(DOMAIN_IMPLEMENTATION):DOMAIN_IMPLEMENTATION})
with open_snapshot(envelope,ns['key'],envelope['keyId'],meta,lambda raw:validator(ns['strict_json'](raw)))as view:rec('same-transferred-real-ciphertext-opens-under-retained-policy',bytes(view)==plain)
assert source==SSOT.read_bytes(),'SOURCE_CHANGED_DURING_FIXTURE'
report={'status':'PASS','checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'inputHead':'32a63a9e3447bd4ed9a7dc4638cadc113071a8b7','sourceDocumentSha256':sha(source).hex(),'postgresqlVersion':db.query('SHOW server_version')[0][0],'candidateExtensionSha256':sha(extension).hex(),'canonicalExtensionBytesExecuted':True,'canonicalInputs':{n:rs[n]['sha256']for n in ['database/generation-create-foundations.sql','database/generation-create-authentication.sql','database/generation-create-preroot.sql','database/canonical-crypto-registry.sql','database/generation-protected-registry-link.sql','database/generation-frozen-archive.sql']},'supportSha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()).hex()for p in [Path(__file__),original_failure,ROOT/'scripts/generation_auth_crypto.py',ROOT/'scripts/generation_auth_acceptance.py',ROOT/'scripts/generation_frozen_archive.py']},'systemdSourceProof':'BLOCKED_ENVIRONMENT','wholeOperationClosed':False,'scope':'Exact archive retention before root and same binding/protected bytes pending-to-success; actual token and crypto primitives with isolated synthetic key/registry provisioning','limitations':['Exact current embedded pre-root extension executed with candidate-byte equality; independent fixture reproduction','Full retained failure/cancel/unknown decision producers and full kind/execution archive policy remain separate','Not actual systemd key-source or generated application runtime acceptance']}
report['canonicalExtensionExecuted']=True;report['canonicalInputs']['database/generation-preroot-frozen-archive.sql']=rs['database/generation-preroot-frozen-archive.sql']['sha256'];
(HERE/'preroot-archive-transfer-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));db.close()
