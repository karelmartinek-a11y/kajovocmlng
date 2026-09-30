#!/usr/bin/env python3
from pathlib import Path
import subprocess,json,hashlib,re,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'scripts'));from ssot_sources import SSOT
source_document_bytes=SSOT.read_bytes();source_self_bytes=Path(__file__).read_bytes()
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-d','postgres','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','--set=VERBOSITY=verbose']
def sql(s):return subprocess.run(PSQL,input=s,text=True,capture_output=True)
assert sql('SHOW server_version;').stdout.strip()=='18.6'
proposal=HERE.joinpath('trusted-generation-context-proposed.sql').read_text()
from generation_descriptor_registry import pin,descriptor,pin_insert_sql
pinned=pin()
setup='DROP SCHEMA IF EXISTS generation_context_fixture CASCADE;CREATE SCHEMA generation_context_fixture;SET search_path=generation_context_fixture,public,pg_catalog;'+HERE.joinpath('authentication-roots-proposed.sql').read_text()+'''CREATE FUNCTION kcml_reject_generation_create_snapshot_update_v1() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='GENERATION_CREATE_IMMUTABLE_SNAPSHOT';END;$$;'''+HERE.joinpath('generation-contract-pin-proposed.sql').read_text()+proposal
r=sql(setup+HERE.joinpath('generation-context-role-bindings.sql').read_text());assert r.returncode==0,r.stderr
O='10000000-0000-4000-8000-000000000001';S='20000000-0000-4000-8000-000000000001';A='30000000-0000-4000-8000-000000000001';I='40000000-0000-4000-8000-000000000001'
prefix='SET search_path=generation_context_fixture,pg_catalog;BEGIN;'
common=f"INSERT INTO owner_identity(id,username,password_hash,password_changed_at,mfa_enabled,deployment_managed,session_epoch,created_at,updated_at,password_source) VALUES('{O}','KRMAR78','SYNTHETIC_HASH_NOT_VERIFIER',clock_timestamp(),true,true,2,clock_timestamp(),clock_timestamp(),'GITHUB_ACTIONS_PASS');INSERT INTO platform_incarnation VALUES(1,'{I}',1,clock_timestamp(),'SYNTHETIC_BOOTSTRAP',NULL,NULL);INSERT INTO application_deployment_head VALUES(1,7,'80000000-0000-4000-8000-000000000001',decode(repeat('01',32),'hex'),'{I}',0,clock_timestamp());"
common+=pin_insert_sql()
session=common+f"INSERT INTO owner_session(id,owner_identity_id,lookup_digest,session_hash,created_at,last_seen_at,expires_at,session_epoch) VALUES('{S}','{O}',decode(repeat('01',32),'hex'),'SYNTHETIC_NOT_AUTH_IMPLEMENTATION',clock_timestamp()-interval '2hour',clock_timestamp()-interval '1min',clock_timestamp()+interval '1hour',2);INSERT INTO generation_create_authentication_acceptance(id,owner_id,access_channel,session_id,session_epoch,session_lookup_digest,accepted_at)VALUES('{A}','{O}','OWNER_SESSION','{S}',2,decode(repeat('01',32),'hex'),clock_timestamp());"
api=common+f"INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,state_version,credential_activation_epoch,created_at) VALUES(1,'90000000-0000-4000-8000-000000000001','90000000-0000-4000-8000-000000000002','SYNTHETIC_HASH_NOT_VERIFIER','synthetic-fingerprint',3,0,1,clock_timestamp());INSERT INTO generation_create_authentication_acceptance(id,owner_id,access_channel,api_credential_version,api_credential_fingerprint,accepted_at)VALUES('{A}','{O}','OWNER_API_KEY',3,'synthetic-fingerprint',clock_timestamp());"
desc=descriptor(O,'sha256:'+'05'*32,pinned)
call=f"SELECT kcml_generation_create_context_v1('{A}',decode(repeat('03',32),'hex'),decode('{pinned['contractDigest'].hex()}','hex'),decode('{desc.hex()}','hex'));"
checks=[]
def test(name,base,pre='',expected=None,invoke=call):
 r=sql(prefix+base+pre+invoke+'ROLLBACK;');m=re.search(r'ERROR:\s+(\w+):',r.stderr);actual=m[1] if m else None
 diagnostic=None
 if expected is not None:
  if name.startswith('descriptor-server-binding-') or name=='descriptor-extra-field-rejected':diagnostic='GENERATION_DESCRIPTOR_PIN_BINDING_MISMATCH'
  elif name in ['descriptor-duplicate-json-key-rejected','descriptor-invalid-json-encoding-rejected','descriptor-invalid-utf8-rejected']:diagnostic='GENERATION_DESCRIPTOR_ENCODING_INVALID'
  elif name=='descriptor-noncanonical-bytes-rejected':diagnostic='GENERATION_DESCRIPTOR_NONCANONICAL'
  elif name=='caller-contract-digest-cannot-override-registry':diagnostic='GENERATION_CONTRACT_PIN_MISMATCH'
  elif name=='unregistered-deployment-pin-blocked':diagnostic='GENERATION_CONTRACT_PIN_UNRESOLVED'
  elif name in ['no-fake-receipt-specific-reject','temporary-relation-cannot-forge-trusted-auth-receipt']:diagnostic='GENERATION_AUTH_RECEIPT_UNRESOLVED'
  elif name.startswith('physical-singleton-key-one-') or name=='owner-singleton-cannot-be-deleted':diagnostic='FIXED_SINGLETON_IDENTITY_IMMUTABLE'
  elif name in ['revoked-session-specific-reject','expired-session-specific-reject','session-owner-epoch-changed','session-record-epoch-changed','session-lookup-digest-changed']:diagnostic='GENERATION_SESSION_AUTH_STALE'
  elif name.startswith('rotated-api-'):diagnostic='GENERATION_API_AUTH_STALE'
  elif name=='incarnation-mismatch-specific-reject':diagnostic='GENERATION_CONTEXT_INCARNATION_MISMATCH'
  elif name in ['authentication-receipt-immutable','context-immutable','immutable-contract-pin-cannot-be-retargeted']:diagnostic='GENERATION_CREATE_IMMUTABLE_SNAPSHOT'
  elif name=='short-request-digest-specific-reject':diagnostic='GENERATION_CONTEXT_INPUT_INVALID'
  elif name in ['singleton-owner-exact-case','singleton-owner-no-trim']:diagnostic='owner_identity_username_check'
 ok=r.returncode==0 if expected is None else r.returncode!=0 and actual==expected and (diagnostic is None or diagnostic in r.stderr)
 checks.append({'id':name,'status':'PASS' if ok else 'FAIL','expectedSqlstate':expected,'actualSqlstate':actual,'expectedDiagnostic':diagnostic,'diagnosticMatched':diagnostic is None or diagnostic in r.stderr,'witness':'persisted synthetic server authentication acceptance +actual current-row values','secretValuesIncluded':False})
 assert ok,(name,r.stderr)
test('session-context-from-current-owned-receipt',session)
test('api-context-from-current-singleton-receipt',api)
for table in ['owner_identity','platform_incarnation','application_deployment_head']:
 test('physical-singleton-key-one-'+table,session,f'UPDATE {table} SET singleton_key=2;',expected='55000',invoke='')
test('physical-singleton-key-one-owner-api',api,'UPDATE owner_api_credential SET singleton_key=2;',expected='55000',invoke='')
test('domain-writer-executes-reviewed-constructor',session,'SET LOCAL ROLE kcml_domain_writer;')
test('domain-writer-cannot-forge-authentication-receipt',session,'SET LOCAL ROLE kcml_domain_writer;DELETE FROM generation_create_authentication_acceptance;',expected='42501',invoke='')
test('authentication-producer-only-issues-receipt',session,"SET LOCAL ROLE kcml_authentication_writer;INSERT INTO generation_create_authentication_acceptance SELECT '30000000-0000-4000-8000-000000000002'::uuid,owner_id,access_channel,session_id,session_epoch,session_lookup_digest,api_credential_version,api_credential_fingerprint,accepted_at FROM generation_create_authentication_acceptance;",invoke='')
test('domain-writer-cannot-issue-owner-session',session,f"SET LOCAL ROLE kcml_domain_writer;INSERT INTO owner_session(id,owner_identity_id,lookup_digest,session_hash,created_at,last_seen_at,expires_at,session_epoch)VALUES('20000000-0000-4000-8000-000000000002','{O}',decode(repeat('02',32),'hex'),'SYNTHETIC_NOT_AUTH_IMPLEMENTATION',clock_timestamp()-interval '2hour',clock_timestamp()-interval '1min',clock_timestamp()+interval '1hour',2);",expected='42501',invoke='')
test('domain-writer-cannot-forge-context-row',session,'SET LOCAL ROLE kcml_domain_writer;INSERT INTO generation_create_trusted_context SELECT * FROM generation_create_trusted_context;',expected='42501',invoke='')
test('domain-writer-cannot-set-builder-role',session,'SET SESSION AUTHORIZATION kcml_domain_writer;SET LOCAL ROLE kcml_generation_context_builder;',expected='42501',invoke='')
test('revoked-session-specific-reject',session,"UPDATE owner_session SET revoked_at=clock_timestamp();",'28000')
test('expired-session-specific-reject',session,"UPDATE owner_session SET expires_at=clock_timestamp()-interval '1s';",'28000')
test('session-owner-epoch-changed',session,"UPDATE owner_identity SET session_epoch=3;",'28000')
test('session-record-epoch-changed',session,"UPDATE owner_session SET session_epoch=3;",'28000')
test('session-lookup-digest-changed',session,"UPDATE owner_session SET lookup_digest=decode(repeat('ff',32),'hex');",'28000')
test('rotated-api-version-specific-reject',api,"UPDATE owner_api_credential SET credential_version=4;",'28000')
test('rotated-api-fingerprint-specific-reject',api,"UPDATE owner_api_credential SET fingerprint='another-synthetic-value';",'28000')
test('incarnation-mismatch-specific-reject',session,"UPDATE application_deployment_head SET platform_incarnation_id='40000000-0000-4000-8000-000000000002';",'40001')
test('authentication-receipt-immutable',session,"UPDATE generation_create_authentication_acceptance SET session_epoch=3;",'55000')
test('context-immutable',session,call+"UPDATE generation_create_trusted_context SET application_deployment_epoch=8;",'55000',invoke='')
test('short-request-digest-specific-reject',session,expected='22023',invoke=call.replace("decode(repeat('03',32),'hex')","decode('01','hex')"))
test('no-fake-receipt-specific-reject',session,expected='P0002',invoke=call.replace(A,'30000000-0000-4000-8000-000000000002'))
fake='30000000-0000-4000-8000-000000000002'
shadow="SET SESSION AUTHORIZATION kcml_domain_writer;CREATE TEMP TABLE generation_create_authentication_acceptance(id uuid,owner_id uuid,access_channel text,session_id uuid,session_epoch bigint,session_lookup_digest bytea,api_credential_version bigint,api_credential_fingerprint text,accepted_at timestamptz);"+f"INSERT INTO pg_temp.generation_create_authentication_acceptance VALUES('{fake}','{O}','OWNER_SESSION','{S}',2,decode(repeat('01',32),'hex'),NULL,NULL,clock_timestamp());"
test('temporary-relation-cannot-forge-trusted-auth-receipt',session,shadow,expected='P0002',invoke=call.replace(A,fake))

test('unregistered-deployment-pin-blocked',session,'UPDATE application_deployment_head SET application_deployment_epoch=8;',expected='P0002')
test('caller-contract-digest-cannot-override-registry',session,expected='23514',invoke=call.replace(pinned['contractDigest'].hex(),'ff'*32))
for field,value in [('operationContractRevision','MODEL_REVISION'),('stableCallerObjectId','10000000-0000-4000-8000-000000000002'),('callerAuthorityKind','AUTOMATED_MAINTENANCE'),('operationContractId','secret.create'),('stableBusinessTargetKey','CREATE_ROOT:secret_record'),('stableCallerRevisionId','MODEL_REVISION')]:
 bad=json.loads(desc);bad[field]=value;raw=json.dumps(bad,sort_keys=True,separators=(',',':')).encode();test('descriptor-server-binding-'+field,session,expected='23514',invoke=call.replace(desc.hex(),raw.hex()))
bad=json.loads(desc);bad['modelAuthority']=True;raw=json.dumps(bad,sort_keys=True,separators=(',',':')).encode();test('descriptor-extra-field-rejected',session,expected='23514',invoke=call.replace(desc.hex(),raw.hex()))
raw=json.dumps(json.loads(desc),sort_keys=True,indent=2).encode();test('descriptor-noncanonical-bytes-rejected',session,expected='23514',invoke=call.replace(desc.hex(),raw.hex()))
raw=b'{"callerAuthorityKind":"OWNER_FULL","callerAuthorityKind":"OWNER_FULL"}';test('descriptor-duplicate-json-key-rejected',session,expected='22023',invoke=call.replace(desc.hex(),raw.hex()))
test('descriptor-invalid-json-encoding-rejected',session,expected='22023',invoke=call.replace(desc.hex(),b'{'.hex()))
test('descriptor-invalid-utf8-rejected',session,expected='22023',invoke=call.replace(desc.hex(),'ff'))
test('immutable-contract-pin-cannot-be-retargeted',session,'UPDATE generation_create_contract_pin SET operation_contract_revision=operation_contract_revision;',expected='55000',invoke='')
test('domain-writer-cannot-install-contract-pin',session,'SET LOCAL ROLE kcml_domain_writer;'+pin_insert_sql(8,'70000000-0000-4000-8000-000000000002'),expected='42501',invoke='')
# Start from actual valid native pin and recompute dependent content hashes so
# missing required metadata is rejected for its own CHECK, not stale byte hash.
for field in ['operationId','operationRevision']:
 altered=dict(pinned);record=json.loads(altered['operationRecordBytes']);record.pop(field);altered['operationRecordBytes']=json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();rev=json.loads(altered['contractRevisionBytes']);rev['operationRecord']=record;altered['contractRevisionBytes']=json.dumps(rev,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();altered['contractDigest']=hashlib.sha256(altered['contractRevisionBytes']).digest()
 test('pin-missing-authoritative-'+field,session,pin_insert_sql(8,'70000000-0000-4000-8000-000000000002',altered),expected='23514',invoke='')

test('singleton-owner-exact-case',session,"UPDATE owner_identity SET username='krmar78';",expected='23514',invoke='')
test('singleton-owner-no-trim',session,"UPDATE owner_identity SET username='KRMAR78 ';",expected='23514',invoke='')
test('owner-singleton-cannot-be-deleted',session,'DELETE FROM owner_identity;',expected='55000',invoke='')
test('descriptor-derived-digest-actual-bytes',session,call,invoke="DO $$BEGIN IF EXISTS(SELECT 1 FROM generation_create_trusted_context WHERE execution_descriptor_digest<>sha256(execution_descriptor_bytes)) THEN RAISE EXCEPTION 'digest';END IF;END$$;")
report={'format':'KCML-PG-TRUSTED-CONTEXT-CONSUMER/1','inputCommit':'d362487999bd795d4723c2a930e93fc7aa8aa295','sourceDocumentSha256':hashlib.sha256(source_document_bytes).hexdigest(),'postgresVersion':'18.6','sqlSha256':hashlib.sha256(proposal.encode()).hexdigest(),'authenticationRootsSqlSha256':hashlib.sha256(HERE.joinpath('authentication-roots-proposed.sql').read_bytes()).hexdigest(),'contractPinSqlSha256':hashlib.sha256(HERE.joinpath('generation-contract-pin-proposed.sql').read_bytes()).hexdigest(),'pinAuthorSha256':hashlib.sha256(HERE.joinpath('generation_descriptor_registry.py').read_bytes()).hexdigest(),'actualContractDigest':pinned['contractDigest'].hex(),'roleSqlSha256':hashlib.sha256(HERE.joinpath('generation-context-role-bindings.sql').read_bytes()).hexdigest(),'verifierSha256':hashlib.sha256(source_self_bytes).hexdigest(),'fixtureSetupSha256':hashlib.sha256(setup.encode()).hexdigest(),'checks':checks,'summary':{'checks':len(checks),'failed':sum(c['status']!='PASS' for c in checks)},'notProven':['actual session/API authentication hash verification service','remaining auth child/Secret-version composite FKs','actual deployed service-login group grants','main-mutation recovery/admission guard','whole operation transaction closure'],'futureImplementationAcceptance':'NOT_EVALUATED'};assert SSOT.read_bytes()==source_document_bytes, 'SOURCE_DOCUMENT_CHANGED_DURING_PROOF'
assert Path(__file__).read_bytes()==source_self_bytes, 'VERIFIER_CHANGED_DURING_PROOF'
HERE.joinpath('postgres-context-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))
