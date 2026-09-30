#!/usr/bin/env python3
"""PG18.6 root/immutable snapshot constraint proof, NOT whole-operation/crypto proof."""
from pathlib import Path
import subprocess,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,load_resource
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-d','postgres','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','--set=VERBOSITY=verbose']
def sql(s):return subprocess.run(PSQL,input=s,text=True,capture_output=True)
r=sql('SHOW server_version;');assert r.returncode==0 and r.stdout.strip()=='18.6',r.stderr
root=HERE.joinpath('generation-root-proposed.sql').read_text(); initial=root.split('-- Immutable initial request')[0]; tail=root[root.index('CREATE OR REPLACE FUNCTION kcml_generation_job_write_guard_v1'):]
sub=ROOT.joinpath('audit/generated/resume-5334/sql/generation-create-persistence-proposed.sql').read_text()
# Deliberately marked FOREIGN-KEY FIXTURE roots, not authoritative definitions.
setup='''DROP SCHEMA IF EXISTS generation_root_fixture CASCADE; CREATE SCHEMA generation_root_fixture;
SET search_path=generation_root_fixture,pg_catalog;
CREATE TABLE owner_identity(id uuid PRIMARY KEY);
CREATE TABLE domain_command(logical_operation_id uuid PRIMARY KEY);
'''+initial+sub+root[root.index('-- Immutable initial request'):root.index('CREATE OR REPLACE FUNCTION kcml_generation_job_write_guard_v1')]+tail
r=sql(setup);assert r.returncode==0,r.stderr
OWNER='10000000-0000-4000-8000-000000000001';JOB='20000000-0000-4000-8000-000000000001';COMMAND='30000000-0000-4000-8000-000000000001';SNAP='40000000-0000-4000-8000-000000000001'
body=json.dumps({'intent':'Synthetic operation','kind':'CREATE'},sort_keys=True,separators=(',',':')).encode();digest=hashlib.sha256(body).hexdigest()
prefix="SET search_path=generation_root_fixture,pg_catalog;"
base=f'''INSERT INTO owner_identity VALUES('{OWNER}');INSERT INTO domain_command VALUES('{COMMAND}');
INSERT INTO generation_job(id,owner_id,initiating_access_channel,initiating_execution_context_id,kind,state,initial_request_snapshot_id,initial_request_digest,platform_incarnation_id,application_deployment_epoch,created_at,client_request_id,latest_command_logical_operation_id)
VALUES('{JOB}','{OWNER}','OWNER_SESSION','50000000-0000-4000-8000-000000000001','CREATE','DISCUSSING','{SNAP}',decode('{digest}','hex'),'60000000-0000-4000-8000-000000000001',1,'2026-09-30T00:00:00Z','synthetic-create','{COMMAND}');
INSERT INTO generation_job_initial_request_snapshot(job_id,snapshot_id,logical_operation_id,request_schema_id,request_schema_digest,content_digest,ciphertext,nonce,algorithm,key_id,crypto_profile_digest,created_at)
VALUES('{JOB}','{SNAP}','{COMMAND}','urn:kcml:r9:semantic:route.0215:body',decode(repeat('01',32),'hex'),decode('{digest}','hex'),decode('0102','hex'),decode('03','hex'),'FIXTURE_OPAQUE_NOT_CRYPTO','FIXTURE_ONLY',decode(repeat('04',32),'hex'),'2026-09-30T00:00:00Z');'''
checks=[]
def check(name,action='',state=None,pre='',mutate=None):
 witness=base if mutate is None else mutate(base)
 # Every operation test starts from valid domain fixture. SQL-negative initial invariants
 # explicitly mutate that same witness, not an unrelated incomplete row.
 command=prefix+'BEGIN;'+witness+pre+action+';SET CONSTRAINTS ALL IMMEDIATE;ROLLBACK;'
 r=sql(command); ok=r.returncode==0 if state is None else r.returncode!=0 and re.search(r'ERROR:\s+'+state+r':',r.stderr) is not None
 checks.append({'id':name,'status':'PASS' if ok else 'FAIL','expectedSqlstate':state,'actualSqlstate':(re.search(r'ERROR:\s+(\w+):',r.stderr).group(1) if re.search(r'ERROR:\s+(\w+):',r.stderr) else None),'positiveWitness':'typed-create-body+root+immutable-snapshot','valuesIncluded':False})
 if not ok: raise AssertionError((name,r.stderr))
check('typed-create-root-snapshot-roundtrip',f"SELECT initial_request_digest FROM generation_job WHERE id='{JOB}'")
check('missing-owner-identity',state='23503',mutate=lambda s:s.replace(f"INSERT INTO owner_identity VALUES('{OWNER}');",''))
check('missing-logical-operation',state='23503',mutate=lambda s:s.replace(f"INSERT INTO domain_command VALUES('{COMMAND}');",''))
check('unknown-job-kind',state='23514',mutate=lambda s:s.replace("'CREATE','DISCUSSING'","'GUESS','DISCUSSING'"))
check('unknown-job-state',state='23514',mutate=lambda s:s.replace("'CREATE','DISCUSSING'","'CREATE','READY'"))
check('wrong-owned-digest',state='23503',mutate=lambda s:s.replace(f"decode('{digest}','hex')", "decode(repeat('ff',32),'hex')",1))
check('wrong-snapshot-identity',state='23503',mutate=lambda s:s.replace(f"'{SNAP}'", "'40000000-0000-4000-8000-000000000002'",1))
check('unknown-request-schema',state='23514',mutate=lambda s:s.replace('urn:kcml:r9:semantic:route.0215:body','urn:guess'))
check('null-required-request-digest',state='23502',mutate=lambda s:s.replace(f"decode('{digest}','hex')",'NULL',1))
check('root-id-immutable',f"UPDATE generation_job SET id='20000000-0000-4000-8000-000000000002',state_version=1",state='55000')
check('owner-immutable',f"UPDATE generation_job SET owner_id='10000000-0000-4000-8000-000000000002',state_version=1",state='55000')
check('initiating-context-immutable',"UPDATE generation_job SET initiating_access_channel='OWNER_API_KEY',state_version=1",state='55000')
check('target-identity-immutable',"UPDATE generation_job SET target_kind='AI_AGENT',state_version=1",state='55000')
check('request-bytes-digest-immutable',"UPDATE generation_job SET initial_request_digest=decode(repeat('ff',32),'hex'),state_version=1",state='55000')
check('state-version-exact-increment',"UPDATE generation_job SET state_version=2",state='40001')
check('state-version-positive-increment',"UPDATE generation_job SET state_version=1")
check('terminal-row-immutable',"UPDATE generation_job SET state_version=2",state='55000',pre="UPDATE generation_job SET state='FAILED',state_version=1;")
check('snapshot-update-forbidden',"UPDATE generation_job_initial_request_snapshot SET ciphertext=decode('0506','hex')",state='55000')
check('replay-does-not-create-second-root',f"INSERT INTO generation_job SELECT * FROM generation_job WHERE id='{JOB}'",state='23505')
check('update-requires-existing-target',state='23514',mutate=lambda s:s.replace("'CREATE','DISCUSSING'","'UPDATE','DISCUSSING'"))
check('follow-up-requires-own-source-job',state='23514',mutate=lambda s:s.replace("'CREATE','DISCUSSING'","'FOLLOW_UP','DISCUSSING'"))
check('parent-self-forbidden',f"UPDATE generation_job SET parent_job_id=id,state_version=1",state='55000')
check('initial-counter-zero',"DO $$BEGIN IF EXISTS(SELECT 1 FROM generation_job WHERE state_version<>0 OR aggregate_event_sequence<>0) THEN RAISE EXCEPTION 'bad counters';END IF;END$$")
# Demonstrate failed deferred FK rolls back actual created root rather than leaving an orphan.
r=sql(prefix+'BEGIN;'+base.replace(f"decode('{digest}','hex')", "decode(repeat('ff',32),'hex')",1)+'COMMIT;');assert r.returncode!=0
r=sql(prefix+'SELECT count(*) FROM generation_job;');assert r.stdout.strip()=='0';checks.append({'id':'failed-commit-rolls-back-root-snapshot','status':'PASS','expectedSqlstate':'23503','valuesIncluded':False})
report={'format':'KCML-PG-GENERATION-ROOT-FIXTURE/1','inputCommit':'d362487999bd795d4723c2a930e93fc7aa8aa295','sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'postgresVersion':'18.6','connection':'isolated Unix socket; TCP disabled','sourceArchiveSha256':hashlib.sha256(Path('/tmp/kcml-pg18-build/source.tar.gz').read_bytes()).hexdigest(),'rootSqlSha256':hashlib.sha256(root.encode()).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fixtureSetupSha256':hashlib.sha256(setup.encode()).hexdigest(),'subordinateSqlSha256':hashlib.sha256(sub.encode()).hexdigest(),'checks':checks,'summary':{'checks':len(checks),'failed':sum(x['status']!='PASS' for x in checks)},'fixtureOnlyPrerequisites':['owner_identity UUID identity fixture','domain_command UUID identity fixture'],'notProven':['trusted authentication constructor','full physical external FK roots','current phase own-map','native policy admission','atomic event/outbox/audit closure','canonical production cryptography','generated application'],'wholeOperationClosed':False,'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
HERE.joinpath('postgres-root-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))
