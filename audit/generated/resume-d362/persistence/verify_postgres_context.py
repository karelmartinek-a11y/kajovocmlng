#!/usr/bin/env python3
from pathlib import Path
import subprocess,json,hashlib,re,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'scripts'));from ssot_sources import SSOT
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-d','postgres','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','--set=VERBOSITY=verbose']
def sql(s):return subprocess.run(PSQL,input=s,text=True,capture_output=True)
assert sql('SHOW server_version;').stdout.strip()=='18.6'
proposal=HERE.joinpath('trusted-generation-context-proposed.sql').read_text()
setup='''DROP SCHEMA IF EXISTS generation_context_fixture CASCADE;CREATE SCHEMA generation_context_fixture;SET search_path=generation_context_fixture,pg_catalog;
-- Source-owned columns used by consuming guards, not full auth migration closure.
CREATE TABLE owner_identity(id uuid PRIMARY KEY,singleton_key smallint NOT NULL DEFAULT 1 UNIQUE CHECK(singleton_key=1),session_epoch bigint NOT NULL);
CREATE TABLE owner_session(id uuid PRIMARY KEY,owner_identity_id uuid NOT NULL REFERENCES owner_identity(id),lookup_digest bytea NOT NULL,session_hash text NOT NULL,created_at timestamptz,last_seen_at timestamptz,expires_at timestamptz NOT NULL,revoked_at timestamptz,session_epoch bigint NOT NULL);
CREATE TABLE owner_api_credential(singleton_key smallint PRIMARY KEY DEFAULT 1 CHECK(singleton_key=1),credential_version bigint NOT NULL,fingerprint text NOT NULL);
CREATE TABLE platform_incarnation(singleton_key smallint PRIMARY KEY DEFAULT 1 CHECK(singleton_key=1),platform_incarnation_id uuid NOT NULL);
CREATE TABLE application_deployment_head(singleton_key smallint PRIMARY KEY DEFAULT 1 CHECK(singleton_key=1),platform_incarnation_id uuid NOT NULL,application_deployment_epoch bigint NOT NULL);
CREATE FUNCTION kcml_reject_generation_create_snapshot_update_v1() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='GENERATION_CREATE_IMMUTABLE_SNAPSHOT';END;$$;
'''+proposal
r=sql(setup+HERE.joinpath('generation-context-role-bindings.sql').read_text());assert r.returncode==0,r.stderr
O='10000000-0000-4000-8000-000000000001';S='20000000-0000-4000-8000-000000000001';A='30000000-0000-4000-8000-000000000001';I='40000000-0000-4000-8000-000000000001'
prefix='SET search_path=generation_context_fixture,pg_catalog;BEGIN;'
common=f"INSERT INTO owner_identity VALUES('{O}',1,2);INSERT INTO platform_incarnation VALUES(1,'{I}');INSERT INTO application_deployment_head VALUES(1,'{I}',7);"
session=common+f"INSERT INTO owner_session(id,owner_identity_id,lookup_digest,session_hash,expires_at,session_epoch) VALUES('{S}','{O}',decode(repeat('01',32),'hex'),'SYNTHETIC_NOT_AUTH_IMPLEMENTATION',clock_timestamp()+interval '1hour',2);INSERT INTO generation_create_authentication_acceptance(id,owner_id,access_channel,session_id,session_epoch,session_lookup_digest,accepted_at)VALUES('{A}','{O}','OWNER_SESSION','{S}',2,decode(repeat('01',32),'hex'),clock_timestamp());"
api=common+f"INSERT INTO owner_api_credential VALUES(1,3,'synthetic-fingerprint');INSERT INTO generation_create_authentication_acceptance(id,owner_id,access_channel,api_credential_version,api_credential_fingerprint,accepted_at)VALUES('{A}','{O}','OWNER_API_KEY',3,'synthetic-fingerprint',clock_timestamp());"
call=f"SELECT kcml_generation_create_context_v1('{A}',decode(repeat('03',32),'hex'),decode(repeat('04',32),'hex'),convert_to('{{\"synthetic\":true}}','UTF8'));"
checks=[]
def test(name,base,pre='',expected=None,invoke=call):
 r=sql(prefix+base+pre+invoke+'ROLLBACK;');m=re.search(r'ERROR:\s+(\w+):',r.stderr);actual=m[1] if m else None;ok=r.returncode==0 if expected is None else r.returncode!=0 and actual==expected
 checks.append({'id':name,'status':'PASS' if ok else 'FAIL','expectedSqlstate':expected,'actualSqlstate':actual,'witness':'persisted synthetic server authentication acceptance +actual current-row values','secretValuesIncluded':False})
 assert ok,(name,r.stderr)
test('session-context-from-current-owned-receipt',session)
test('api-context-from-current-singleton-receipt',api)
for table in ['owner_identity','platform_incarnation','application_deployment_head']:
 test('physical-singleton-key-one-'+table,session,f'UPDATE {table} SET singleton_key=2;',expected='23514',invoke='')
test('physical-singleton-key-one-owner-api',api,'UPDATE owner_api_credential SET singleton_key=2;',expected='23514',invoke='')
test('domain-writer-executes-reviewed-constructor',session,'SET LOCAL ROLE kcml_domain_writer;')
test('domain-writer-cannot-forge-authentication-receipt',session,'SET LOCAL ROLE kcml_domain_writer;DELETE FROM generation_create_authentication_acceptance;',expected='42501',invoke='')
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

test('descriptor-derived-digest-actual-bytes',session,call,invoke="DO $$BEGIN IF EXISTS(SELECT 1 FROM generation_create_trusted_context WHERE execution_descriptor_digest<>sha256(execution_descriptor_bytes)) THEN RAISE EXCEPTION 'digest';END IF;END$$;")
report={'format':'KCML-PG-TRUSTED-CONTEXT-CONSUMER/1','inputCommit':'d362487999bd795d4723c2a930e93fc7aa8aa295','sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'postgresVersion':'18.6','sqlSha256':hashlib.sha256(proposal.encode()).hexdigest(),'roleSqlSha256':hashlib.sha256(HERE.joinpath('generation-context-role-bindings.sql').read_bytes()).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fixtureSetupSha256':hashlib.sha256(setup.encode()).hexdigest(),'checks':checks,'summary':{'checks':len(checks),'failed':sum(c['status']!='PASS' for c in checks)},'notProven':['actual session/API authentication hash verification service','complete source authentication tableDDL','actual deployed service-login group grants','main-mutation recovery/admission guard','whole operation transaction closure'],'futureImplementationAcceptance':'NOT_EVALUATED'};HERE.joinpath('postgres-context-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))
