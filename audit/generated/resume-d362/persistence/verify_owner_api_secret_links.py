#!/usr/bin/env python3
from pathlib import Path
import subprocess,json,hashlib,sys,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'));from ssot_sources import SSOT
source_document_bytes=SSOT.read_bytes();source_self_bytes=Path(__file__).read_bytes()
base=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-X','-A','-t','-q','-v','ON_ERROR_STOP=1','--set=VERBOSITY=verbose']
r=subprocess.run(base+['-d','postgres','-c','CREATE DATABASE generation_auth_secret_fixture;'],capture_output=True,text=True);assert r.returncode==0 or 'already exists' in r.stderr
p=base+['-d','generation_auth_secret_fixture']
def sql(s):return subprocess.run(p,input=s,capture_output=True,text=True)
setup='DROP SCHEMA public CASCADE;CREATE SCHEMA public;DROP SCHEMA IF EXISTS kcml_secret_v1 CASCADE;SET search_path=public,pg_catalog;'+HERE.joinpath('authentication-roots-proposed.sql').read_text()+ROOT.joinpath('audit/generated/resume-d362/secrets/secret-profile-roots.sql').read_text()+HERE.joinpath('owner-api-secret-links-proposed.sql').read_text()
r=sql(setup);assert r.returncode==0,r.stderr
S='10000000-0000-4000-8000-000000000001';V='20000000-0000-4000-8000-000000000001'
# Opaque encrypted-field carriers establish only physical guard/FK semantics.
# This witness is not a cryptographic/token-verifier or creator-context proof.
w=f"""INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,active_version_id,state_version,secret_activation_epoch,created_at,updated_at)
VALUES('{S}','KCML_OWNER_API_KEY','Synthetic reserved credential','API_KEY','SYNTHETIC_STATUS_NOT_LIFECYCLE_PROOF',NULL,0,0,clock_timestamp(),clock_timestamp());
INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,activated_at,creator_context_id,activation_logical_operation_id)
VALUES('{V}','{S}',1,'API_KEY','RAW_UTF8','EXACT_SECRET_BYTES_V1',1,decode('01','hex'),decode('02','hex'),'OPAQUE_FIXTURE_NOT_CRYPTO','SYNTHETIC_KEY','synthetic-fingerprint',decode(repeat('03',32),'hex'),decode(repeat('04',32),'hex'),'CREATED',clock_timestamp()-interval '1s',NULL,'30000000-0000-4000-8000-000000000001',NULL);
UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=clock_timestamp(),activation_logical_operation_id='40000000-0000-4000-8000-000000000001' WHERE id='{V}';
UPDATE kcml_secret_v1.secret_record SET active_version_id='{V}',state_version=1,secret_activation_epoch=1 WHERE id='{S}';
INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,state_version,credential_activation_epoch,created_at)
VALUES(1,'{S}','{V}','SYNTHETIC_HASH_NOT_VERIFIER','synthetic-fingerprint',1,1,1,clock_timestamp());"""
checks=[]
def test(name,change='',expected=None):
 r=sql('BEGIN;'+w+change+'SET CONSTRAINTS ALL IMMEDIATE;ROLLBACK;');m=re.search(r'ERROR:\s+(\w+):',r.stderr);a=m[1] if m else None;ok=r.returncode==0 if expected is None else r.returncode!=0 and a==expected
 checks.append({'id':name,'status':'PASS' if ok else 'FAIL','expectedSqlstate':expected,'actualSqlstate':a,'positiveWitness':'actualfullcandidateSecret/APIrootmetadata+oneACTIVEreservedversion','plaintextOrVerifierValuesRecorded':False});assert ok,(name,r.stderr)
test('reserved-api-exact-version-parent-active-fingerprint')
test('reserved-api-pointer-null-disagreement',"UPDATE kcml_secret_v1.secret_record SET active_version_id=NULL;",'23514')
test('credential-fingerprint-differs-from-active-version',"UPDATE owner_api_credential SET fingerprint='other-synthetic-fingerprint';",'23514')
test('reserved-secret-name-changed',"UPDATE kcml_secret_v1.secret_record SET stable_name='OTHER_SYNTHETIC_SECRET';",'23514')
test('credential-singleton-identity-immutable',"UPDATE owner_api_credential SET singleton_key=2;",'55000')
test('credential-singleton-delete-forbidden','DELETE FROM owner_api_credential;','55000')
r=sql('SHOW server_version;');assert r.stdout.strip()=='18.6'
report={'format':'KCML-PG-OWNER-API-SECRET-LINKS/1','sourceDocumentSha256':hashlib.sha256(source_document_bytes).hexdigest(),'postgresVersion':'18.6','sourcePointers':['§25.3','§51.11','§51.20'],'consumedSqlSha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [HERE/'authentication-roots-proposed.sql',ROOT/'audit/generated/resume-d362/secrets/secret-profile-roots.sql',HERE/'owner-api-secret-links-proposed.sql']},'verifierSha256':hashlib.sha256(source_self_bytes).hexdigest(),'checks':checks,'summary':{'checks':len(checks),'failed':sum(c['status']!='PASS' for c in checks)},'notProven':['actual API material constant-time verifier under credential lock','full rotate/idempotency/command/outbox/audit transaction','credential version/epoch own CAS monotonic writes','cryptographic ciphertext/master-key material','Secret creator-context external FK and Secret record lifecycle'],'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'};assert SSOT.read_bytes()==source_document_bytes, 'SOURCE_DOCUMENT_CHANGED_DURING_PROOF'
assert Path(__file__).read_bytes()==source_self_bytes, 'VERIFIER_CHANGED_DURING_PROOF'
HERE.joinpath('owner-api-secret-links-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))
