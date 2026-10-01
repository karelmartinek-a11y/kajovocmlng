"""Bounded real PG chain: actual auth/context/root + candidate typed nonce link.
Random fixture keys are not systemd evidence. No secret/key bytes in report.
"""
from pathlib import Path
import sys,json,copy
HERE=Path(__file__).parent;ROOT=HERE.parents[4]
for p in [ROOT/'scripts',ROOT/'audit/generated/resume-34d/auth-crypto',ROOT/'audit/generated/resume-d362/persistence']:sys.path.insert(0,str(p))
from ssot_sources import SSOT,resource_index
from generation_auth_crypto import canonical,sha,aad,open_snapshot
from libpq_fixture import DB,lit
original=ROOT/'audit/generated/resume-34d/auth-crypto/verify_authenticated_full_chain.py'
program=original.read_text().split('# Full positive')[0]
program=program.replace("database='auth_crypto_full_34d'","database='archive_joined_905'").replace('from auth_crypto_reference import *','from generation_auth_crypto import *').replace('from acceptance_reference import authenticate_owner_api','from generation_auth_acceptance import authenticate_owner_api')
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
# Correct auth, crypto and all root/event joins; only required archive missing.
db.query('BEGIN');parts,meta,plain=ns['build']();envelope=install_protected(parts,meta)
try:db.query('COMMIT');rec('missing-archive-full-auth-crypto-chain-rejected',False)
except Exception as e:
 rec('missing-archive-full-auth-crypto-chain-rejected','FROZEN_ARCHIVE_REQUIRED'in str(e),'FROZEN_ARCHIVE_REQUIRED',str(e));db.query('ROLLBACK')
counts=db.query('SELECT(SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_command),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM canonical_protected_nonce_reservation),(SELECT count(*)FROM generation_create_authentication_acceptance)')[0]
rec('missing-archive-rollback-removes-whole-connected-chain',counts==['0']*5)
# ONE real transaction: verified token lock/context, real plaintext encryption,
# protected row/global nonce, archive, root/event/outbox/audit/locator COMMIT.
db.query('BEGIN');parts,meta,plain=ns['build']();envelope=install_protected(parts,meta);db.query(publication+archive_bind(meta));db.query('COMMIT');rec('one-auth-protected-archive-root-event-commit',True)
observer=DB('archive_joined_905')
counts=observer.query('SELECT(SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_command),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM transactional_outbox),(SELECT count(*)FROM audit_event),(SELECT count(*)FROM idempotency_locator),(SELECT count(*)FROM canonical_protected_nonce_reservation),(SELECT count(*)FROM generation_frozen_policy_binding_v1)')[0]
rec('independent-observer-sees-entire-committed-chain',counts==['1']*8)
row=json.loads(observer.query('SELECT kcml_generation_create_read_storage_v1('+lit(meta['ownerId'])+','+lit(meta['jobId'])+');')[0][0])
archive=json.loads(observer.query('SELECT kcml_archive_read_v1('+lit(meta['snapshotId'])+','+lit(meta['logicalOperationId'])+');')[0][0])
bundles={d:bytes.fromhex(raw)for d,raw in archive['bundles'].items()};implementations={digest(DOMAIN_IMPLEMENTATION):DOMAIN_IMPLEMENTATION}
# Hydrate actual typed persisted metadata rather than return a plaintext flag.
stored=observer.query("SELECT c.owner_id,j.id,s.snapshot_id,s.logical_operation_id,s.request_schema_id,encode(s.request_schema_digest,'hex'),encode(s.content_digest,'hex'),c.id,c.platform_incarnation_id,c.application_deployment_epoch,encode(c.execution_descriptor_digest,'hex'),c.initiating_access_channel,s.algorithm,s.key_id,encode(s.crypto_profile_digest,'hex'),encode(s.nonce,'hex'),encode(s.ciphertext,'hex') FROM generation_job j JOIN generation_job_initial_request_snapshot s ON s.job_id=j.id JOIN domain_command d ON d.logical_operation_id=s.logical_operation_id JOIN generation_create_trusted_context c ON c.id=d.execution_context_id WHERE j.id="+lit(meta['jobId']))[0]
fields=('ownerId','jobId','snapshotId','logicalOperationId','requestSchemaId','requestSchemaDigest','contentDigest','trustedContextId','platformIncarnationId','applicationDeploymentEpoch','executionDescriptorDigest','initiatingAccessChannel')
persisted_meta=dict(zip(fields,stored[:12]));persisted_meta['applicationDeploymentEpoch']=int(persisted_meta['applicationDeploymentEpoch'])
for k in ['requestSchemaDigest','contentDigest','executionDescriptorDigest']:persisted_meta[k]='sha256:'+persisted_meta[k]
persisted_envelope={'algorithm':stored[12],'keyId':stored[13],'cryptoProfileDigest':bytes.fromhex(stored[14]),'nonce':bytes.fromhex(stored[15]),'ciphertext':bytes.fromhex(stored[16])}
validator=compile_archived_request(archive['binding'],bundles,policy_implementations=implementations)
opened=[]
def opener(snapshot_id,expected):
 assert snapshot_id==persisted_meta['snapshotId'] and expected['jobId']==persisted_meta['jobId']
 with open_snapshot(persisted_envelope,ns['key'],stored[13],persisted_meta,lambda raw:validator(ns['strict_json'](raw)))as view:
  raw=bytes(view);opened.append(True);return raw
kwargs={'selected_job_id':meta['jobId'],'authenticated_owner_id':meta['ownerId'],'open_snapshot':opener,'archive_binding':archive['binding'],'archive_bundles':bundles,'policy_implementations':implementations}
result=hydrate_storage(row,**kwargs)
rec('actual-postcommit-protected-open-archive-hydration-domain-consumer',len(opened)==1 and result['jobId']==meta['jobId'] and result['executionApproved']is False)
rec('consumer-output-no-plaintext-credential-key-or-authority',set(result)=={'jobId','state','stateVersion','eventSequence','nextAction','executionApproved','activationAuthorized'})
changed=copy.deepcopy(persisted_meta);changed['trustedContextId']='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
def bad_opener(sid,expected):
 with open_snapshot(persisted_envelope,ns['key'],stored[13],changed,lambda raw:validator(ns['strict_json'](raw)))as view:return bytes(view)
try:hydrate_storage(row,**{**kwargs,'open_snapshot':bad_opener});rec('protected-context-swap-rejected-after-valid-archive',False)
except ValueError as e:rec('protected-context-swap-rejected-after-valid-archive',str(e)=='PROTECTED_INPUT_AUTHENTICATION_FAILED','PROTECTED_INPUT_AUTHENTICATION_FAILED',str(e))
from ssot_sources import resources
oldsource=subprocess.run(['git','show','d362487999bd795d4723c2a930e93fc7aa8aa295:00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT,capture_output=True,check=True).stdout
oldrs=resource_index(resources(oldsource.decode()))
oldmask=next(r['requestSchema']['properties']['body']for r in json.loads(oldrs['contracts/payload-contracts.json']['raw'])['records']if r['operationId']=='generation.job.create')
oldraw=canonical(oldmask);badbinding={**archive['binding'],'schemaDigest':digest(oldraw)};badbundles={**bundles,digest(oldraw):oldraw}
try:hydrate_storage(row,**{**kwargs,'archive_binding':badbinding,'archive_bundles':badbundles});rec('available-historical-mask-cannot-replace-root-frozen-pin',False)
except ContractFailure as e:rec('available-historical-mask-cannot-replace-root-frozen-pin',e.code=='FROZEN_POLICY_SNAPSHOT_BINDING_MISMATCH','FROZEN_POLICY_SNAPSHOT_BINDING_MISMATCH',e.code)
assert SSOT.read_bytes()==source,'SOURCE_CHANGED_DURING_JOINED_PROOF'
report={'status':'PASS','checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'sourceDocumentSha256':sha(source).hex(),'postgresqlVersion':observer.query('SHOW server_version')[0][0],'canonicalInputs':{n:rs[n]['sha256']for n in ['database/generation-create-foundations.sql','database/generation-create-authentication.sql','database/generation-create-preroot.sql','database/canonical-crypto-registry.sql','database/generation-protected-registry-link.sql','database/generation-frozen-archive.sql','database/generation-create-read.sql']},'supportSha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()).hex()for p in [Path(__file__),ROOT/'scripts/generation_auth_crypto.py',ROOT/'scripts/generation_auth_acceptance.py',ROOT/'scripts/generation_frozen_archive.py',ROOT/'scripts/generation_request_policy_v1.py',ROOT/'scripts/generation_read_hydration_archive.py',ROOT/'scripts/generation_create_consumer_archive.py']},'systemdSourceProof':'BLOCKED_ENVIRONMENT','scope':'Connected successful CREATE and missing-archive rollback chain with real token verification and real canonical crypto primitive; key issuance/provisioning isolated synthetic, not authentic systemd source','limitations':['Archived request-hydration policy only; full kind admission/execution policies independent','Pre-root retained failure/pending archive still separate','Public endpoint/read authentication and UI dispatch runtime acceptance NOT_EVALUATED'],'wholeOperationClosed':False,'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
(HERE/'joined-chain-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));observer.close();db.close()
