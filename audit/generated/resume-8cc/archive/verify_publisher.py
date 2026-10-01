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
program=program.replace("database='auth_crypto_full_34d'","database='archive_publisher_8cc'").replace('from auth_crypto_reference import *','from generation_auth_crypto import *').replace('from acceptance_reference import authenticate_owner_api','from generation_auth_acceptance import authenticate_owner_api')
ns={'__file__':str(original)};exec(compile(program,'reviewed-existing-auth-chain-positive-factory','exec'),ns)
db=ns['db'];rs=resource_index()
for name in ['database/generation-create-preroot.sql','database/canonical-crypto-registry.sql']:db.query(rs[name]['raw'].decode())
candidate=rs['database/generation-protected-registry-link.sql']['raw'];db.query(candidate.decode())
for n in ['database/generation-frozen-archive.sql','database/generation-preroot-frozen-archive.sql','database/generation-create-read.sql']:db.query(rs[n]['raw'].decode())
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

sys.path.insert(0,str(HERE))
from generation_policy_package import *
package,blobs=build_package(rs,schema_raw,policy,authority)
candidate=(HERE/'generation-trusted-policy-publisher.sql').read_bytes();db.query(candidate.decode())
# Trusted deployment installer only. No endpoint/model registration API.
def release_sql(raw=package,omit=None):
 sql='SET LOCAL ROLE kcml_generation_policy_installer;INSERT INTO generation_policy_release_v1(application_deployment_epoch,operation_contract_digest,package_id,package_digest,package_bytes,request_schema_id,request_schema_digest,request_policy_id,request_policy_digest)VALUES('+','.join(['1',b(pinned['contractDigest']),lit(PACKAGE_ID),b(sha(raw)),b(raw),lit(schema_id),b(sha(schema_raw)),lit(POLICY_ID),b(sha(policy))])+');'
 for (kind,id,d),raw in blobs.items():
  if id==omit:continue
  sql+='INSERT INTO generation_policy_release_blob_v1 VALUES('+','.join(['1',lit(kind),lit(id),b(sha(raw)),b(raw),lit('trusted-fixture-deployment/source'),b(sha(raw))])+');'
 return sql+'RESET ROLE;'
def error(name,sql,code):
 db.query('SAVEPOINT negative')
 try:db.query(sql);rec(name,False,code)
 except Exception as e:rec(name,code in str(e),code,str(e))
 finally:db.query('ROLLBACK TO SAVEPOINT negative')
def ticket(meta):return 'SET LOCAL ROLE kcml_domain_writer;SELECT kcml_pin_policy_acceptance_v1('+lit(meta['trustedContextId'])+','+lit(meta['logicalOperationId'])+');RESET ROLE;'
def accepted(meta):return 'SET LOCAL ROLE kcml_domain_writer;SELECT kcml_publish_accepted_policy_package_v1('+','.join(lit(meta[k])for k in ['trustedContextId','logicalOperationId','snapshotId'])+');RESET ROLE;'
# Closed masks reject bare/null packages using a valid deployed pin.
db.query('BEGIN');parts,meta,plain=ns['build']()
error('bare-package-mask',release_sql(canonical({'packageId':PACKAGE_ID})), 'generation_policy_package_mask')
error('null-package-members',release_sql(canonical({**json.loads(package),'members':None})), 'generation_policy_package_mask')
db.query('ROLLBACK')
# A shaped package with a different request identity cannot bind a real snapshot.
db.query('BEGIN');parts,meta,plain=ns['build']();wrong_package=json.loads(package);wrong_package['requestSchema']['schemaId']='urn:kcml:foreign:request';db.query(release_sql(canonical(wrong_package)));db.query(ticket(meta));install_protected(parts,meta)
error('full-package-wrong-request-identity',accepted(meta),'GENERATION_ARCHIVE_PACKAGE_REQUEST_IDENTITY_MISMATCH');db.query('ROLLBACK')
# Missing code archive is detected before commit, removing whole chain.
db.query('BEGIN');parts,meta,plain=ns['build']();db.query(release_sql(omit='urn:kcml:policy-source:generation_own_kind_policy_v1.py'));db.query(ticket(meta));install_protected(parts,meta)
error('actual-release-missing-code-member',accepted(meta),'GENERATION_ARCHIVE_PACKAGE_MEMBER_UNAVAILABLE');db.query('ROLLBACK')
rec('failed-publication-full-rollback',db.query('SELECT (SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_command),(SELECT count(*)FROM generation_policy_release_v1),(SELECT count(*)FROM generation_policy_acceptance_ticket_v1)')[0]==['0']*4)
# A legacy request-only archive does not satisfy installed full-package gate.
db.query('BEGIN');parts,meta,plain=ns['build']();db.query(release_sql());db.query(ticket(meta));install_protected(parts,meta);db.query(publication+archive_bind(meta))
try:db.query('COMMIT');rec('request-only-archive-package-omission',False)
except Exception as e:rec('request-only-archive-package-omission','GENERATION_ARCHIVE_ACCEPTED_PACKAGE_REQUIRED'in str(e),'GENERATION_ARCHIVE_ACCEPTED_PACKAGE_REQUIRED',str(e));db.query('ROLLBACK')
rec('omitted-package-root-event-rollback',db.query('SELECT(SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM generation_accepted_policy_package_v1)')[0]==['0']*3)
# Correct actual token/context -> pre-H B authority ticket -> H root -> publisher.
db.query('BEGIN');parts,meta,plain=ns['build']();foreign_parts,foreign_meta,foreign_plain=ns['build']();db.query(release_sql())
error('domain-cannot-install-policy','SET LOCAL ROLE kcml_domain_writer;INSERT INTO generation_policy_release_v1 SELECT * FROM generation_policy_release_v1','permission denied')
db.query(ticket(meta));envelope=install_protected(parts,meta)
error('late-lower-lock-ticket-denied',ticket(meta),'GENERATION_ARCHIVE_ACCEPTANCE_LOCK_ORDER')
error('publisher-wrong-context',accepted({**meta,'trustedContextId':foreign_meta['trustedContextId']}),'GENERATION_ARCHIVE_ACCEPTED_CONTEXT_MISMATCH')
error('unscoped-publisher-role','SET LOCAL ROLE kcml_authentication_writer;SELECT kcml_publish_accepted_policy_package_v1('+','.join(lit(meta[k])for k in ['trustedContextId','logicalOperationId','snapshotId'])+');','permission denied')
db.query(accepted(meta));db.query('SET LOCAL ROLE kcml_domain_writer');replay=db.query('SELECT encode(kcml_publish_accepted_policy_package_v1('+','.join(lit(meta[k])for k in ['trustedContextId','logicalOperationId','snapshotId'])+'),\'hex\')')[0][0];db.query('RESET ROLE');rec('same-tx-replay-identical-package',replay==sha(package).hex())
db.query('COMMIT');rec('trusted-token-package-root-atomic-commit',True)
observer=DB('archive_publisher_8cc')
counts=observer.query('SELECT (SELECT count(*)FROM generation_accepted_policy_package_v1),(SELECT count(*)FROM generation_frozen_policy_binding_v1),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM transactional_outbox),(SELECT count(*)FROM audit_event)')[0]
rec('fresh-observer-package-event-audit-available',counts==['1']*5)
# Persisted acceptance ticket cannot authorize a later transaction.
observer.query('BEGIN')
try:observer.query(accepted(meta));rec('cross-tx-ticket-replay-denied',False)
except Exception as e:rec('cross-tx-ticket-replay-denied','GENERATION_ARCHIVE_ACCEPTANCE_PHASE_REQUIRED'in str(e),'GENERATION_ARCHIVE_ACCEPTANCE_PHASE_REQUIRED',str(e))
finally:observer.query('ROLLBACK')
# Retained package comes from SQL available bytes, not current specification.
stored_package=bytes.fromhex(observer.query("SELECT encode(package_bytes,'hex')FROM generation_policy_release_v1")[0][0])
stored_blobs={}
for kind,id,d,raw in observer.query("SELECT bundle_kind,bundle_id,'sha256:'||encode(bundle_digest,'hex'),encode(exact_bytes,'hex') FROM generation_frozen_bundle_v1"):
 stored_blobs[(kind,id,d)]=bytes.fromhex(raw)
rec('actual-persisted-exact-policy-source-closure',load_package(stored_package,digest(package),stored_blobs)[0]==json.loads(package))
# Actual own-kind record bytes and current authority-native schemas, not valid flags.
import generation_admission_contracts as g
sys.modules['generation_admission_reference']=g
sys.path.insert(0,str(ROOT/'audit/generated/resume-d362/admission'))
import generation_admission_fixtures as f
records=copy.deepcopy(f.records);new_lb=digest(rs['contracts/generation/admission-basis.schema.json']['raw'])
def replace(v,mapping):
 if isinstance(v,str):return mapping.get(v,v)
 if isinstance(v,list):return [replace(x,mapping)for x in v]
 if isinstance(v,dict):return {k:replace(x,mapping)for k,x in v.items()}
 return v
mapping={f.lb:new_lb}
for _ in range(4):
 next_map={}
 for r in records.values():
  r['schema']=replace(r['schema'],mapping);old=r['contentDigest'];r['bytes']=g.canonical(replace(g.source_json(r['bytes']),mapping));r['contentDigest']=g.digest(r['bytes'])
  if old!=r['contentDigest']:next_map[old]=r['contentDigest']
 mapping.update(next_map)
bodies=replace(copy.deepcopy(f.bodies),mapping);heads={f.TARGET:{'snapshotId':f.SNAP,'contentDigest':records[f.SNAP]['contentDigest']}}
for kind,body in bodies.items():
 result=dispatch_own_kind(stored_package,digest(package),stored_blobs,body,records,'synthetic-owner',heads)
 rec(kind+'/archived-own-kind-real-record-byte-admission',result['decision']=='ADMIT_DISCUSSION')
 bad=copy.deepcopy(body);bad['generationBasis']['expectedDigest']='sha256:'+'0'*64
 try:dispatch_own_kind(stored_package,digest(package),stored_blobs,bad,records,'synthetic-owner',heads);rec(kind+'/wrong-basis-digest',False)
 except ContractFailure as e:rec(kind+'/wrong-basis-digest','GENERATION_BASIS_DIGEST_CONFLICT' in str(e),'GENERATION_BASIS_DIGEST_CONFLICT',str(e))
for label,changed,expected in [('blank-intent',{**bodies['UPDATE'],'intent':'   '},'EMPTY_INTENT'),('duplicate-artifact',{**bodies['UPDATE'],'sources':[{'kind':'FILE','artifactId':f.SPEC},{'kind':'IMAGE','artifactId':f.SPEC}]},'DUPLICATE_ARTIFACT_REFERENCE')]:
 try:dispatch_own_kind(stored_package,digest(package),stored_blobs,changed,records,'synthetic-owner',heads);rec(label+'/archived-request-policy',False)
 except ContractFailure as e:rec(label+'/archived-request-policy',expected in str(e),expected,str(e))
missing=dict(stored_blobs);missing.pop(next(k for k in missing if k[1]=='urn:kcml:policy-source:generation_own_kind_policy_v1.py'))
try:dispatch_own_kind(stored_package,digest(package),missing,bodies['UPDATE'],records,'synthetic-owner',heads);rec('historical-required-source-unavailable',False)
except ContractFailure as e:rec('historical-required-source-unavailable','MEMBER_UNAVAILABLE'in str(e),'GENERATION_POLICY_PACKAGE_MEMBER_UNAVAILABLE',str(e))
# SQL archived identity substitution still requires digest of exact selected bytes.
try:load_package(stored_package,'sha256:'+'0'*64,stored_blobs);rec('package-identity-swap',False)
except ContractFailure as e:rec('package-identity-swap','PACKAGE_DIGEST_MISMATCH'in str(e),'GENERATION_POLICY_PACKAGE_DIGEST_MISMATCH',str(e))
# Same schema ID, distinct authentic stored revisions: explicit archived mask wins.
historical_schema=json.loads(schema_raw);historical_schema['properties']['intent']['const']=bodies['UPDATE']['intent'];historical_schema_raw=canonical(historical_schema)
historical_package,historical_blobs=build_package(rs,historical_schema_raw,policy,authority)
db.query('BEGIN')
for (kind,id,d),raw in historical_blobs.items():
 if (kind,id,d)not in stored_blobs:db.query(publish(kind,id,raw))
db.query(publish('POLICY_IMPLEMENTATION',PACKAGE_ID,historical_package));db.query('COMMIT')
historical_stored=bytes.fromhex(db.query("SELECT encode(exact_bytes,'hex')FROM generation_frozen_bundle_v1 WHERE bundle_id="+lit(PACKAGE_ID)+" AND bundle_digest="+b(sha(historical_package)))[0][0])
all_stored={(kind,id,d):bytes.fromhex(raw)for kind,id,d,raw in observer.query("SELECT bundle_kind,bundle_id,'sha256:'||encode(bundle_digest,'hex'),encode(exact_bytes,'hex')FROM generation_frozen_bundle_v1")}
rec('same-id-different-revision-available',schema_id==historical_schema['$id'] and sha(schema_raw)!=sha(historical_schema_raw))
rec('stored-historical-own-kind-mask-accept',dispatch_own_kind(historical_stored,digest(historical_package),all_stored,bodies['UPDATE'],records,'synthetic-owner',heads)['decision']=='ADMIT_DISCUSSION')
historical_bad=copy.deepcopy(bodies['UPDATE']);historical_bad['intent']='Other valid current request intent'
rec('same-body-current-policy-admits',dispatch_own_kind(stored_package,digest(package),all_stored,historical_bad,records,'synthetic-owner',heads)['decision']=='ADMIT_DISCUSSION')
try:dispatch_own_kind(historical_stored,digest(historical_package),all_stored,historical_bad,records,'synthetic-owner',heads);rec('historical-selected-mask-rejects-not-current-fallback',False)
except ContractFailure as e:rec('historical-selected-mask-rejects-not-current-fallback','FROZEN_SCHEMA_CONTENT_INVALID'in str(e),'FROZEN_SCHEMA_CONTENT_INVALID',str(e))
# Root independently identified type/availability defects: store actual variant bytes.
mutations=[]
v=copy.deepcopy(json.loads(stored_package));v['version']=True;mutations.append(('version-boolean',v,'GENERATION_POLICY_PACKAGE_INVALID'))
v=copy.deepcopy(json.loads(stored_package));v['requestSchema']['schemaId']=[];mutations.append(('request-schema-id-array',v,'GENERATION_POLICY_PACKAGE_INVALID'))
v=copy.deepcopy(json.loads(stored_package));v['requestPolicy']['policyDigest']=None;mutations.append(('request-policy-digest-null',v,'GENERATION_POLICY_PACKAGE_INVALID'))
v=copy.deepcopy(json.loads(stored_package));v['members']=[m for m in v['members']if m['id']!='contracts/generation/artifact-schema-map.json'];mutations.append(('required-artifact-authority-omitted',v,'GENERATION_POLICY_AUTHORITY_MEMBER_UNAVAILABLE'))
list_schema=canonical([]);db.query('BEGIN');db.query(publish('SCHEMA',schema_id,list_schema));db.query('COMMIT')
v=copy.deepcopy(json.loads(stored_package));v['requestSchema']['bundleDigest']=digest(list_schema)
for member in v['members']:
 if member['kind']=='SCHEMA'and member['id']==schema_id:member['digest']=digest(list_schema)
mutations.append(('schema-list-instead-object',v,'GENERATION_POLICY_PACKAGE_SCHEMA_IDENTITY_MISMATCH'))
for label,variant,expected in mutations:
 raw=canonical(variant);db.query('BEGIN');db.query(publish('POLICY_IMPLEMENTATION','urn:kcml:fixture:invalid-package:'+label,raw));db.query('COMMIT')
 retrieved=bytes.fromhex(observer.query("SELECT encode(exact_bytes,'hex')FROM generation_frozen_bundle_v1 WHERE bundle_id="+lit('urn:kcml:fixture:invalid-package:'+label)+" AND bundle_digest="+b(sha(raw)))[0][0])
 all_stored={(kind,id,d):bytes.fromhex(blob)for kind,id,d,blob in observer.query("SELECT bundle_kind,bundle_id,'sha256:'||encode(bundle_digest,'hex'),encode(exact_bytes,'hex')FROM generation_frozen_bundle_v1")}
 try:dispatch_own_kind(retrieved,digest(raw),all_stored,bodies['UPDATE'],records,'synthetic-owner',heads);rec(label+'/stored-package-specific-rejection',False)
 except ContractFailure as e:rec(label+'/stored-package-specific-rejection',expected in str(e),expected,str(e))
report={'sourceDigest':digest(source),'canonicalInputsExecuted':True,'candidateSqlDigest':digest(candidate),'packageDigest':digest(package),'proofKind':'ISOLATED_POSTGRESQL18_6_TRUSTED_PACKAGE_OWN_KIND_DISCUSSION','checks':checks,'pass':sum(c['passed']for c in checks),'fail':sum(not c['passed']for c in checks),'limitations':['Deployment bootstrap installer exercised as isolated role, not production service installer attestation.','Static dispatcher covers UPDATE/RETRY/REPAIR discussion; ledger CAS classifier and other fullkind execution policies not claimed.','Actual systemd encrypted credential remains separately environment blocked.']}
(HERE/'publisher-proof.json').write_text(json.dumps(report,indent=2)+'\n');(HERE/'package.json').write_bytes(package)
print(json.dumps({'PASS':report['pass'],'FAIL':report['fail'],'source':report['sourceDigest']}))
