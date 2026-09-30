from pathlib import Path
import subprocess,json,re,hashlib
HERE=Path(__file__).parent;ROOT=HERE.parents[3];PERSIST=HERE.parent/'persistence'
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-d','postgres','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','--set=VERBOSITY=verbose']
def sql(s):return subprocess.run(PSQL,input=s,text=True,capture_output=True)
assert sql('SHOW server_version;').stdout.strip()=='18.6'
auth='''CREATE TABLE owner_identity(id uuid PRIMARY KEY,singleton_key smallint UNIQUE CHECK(singleton_key=1),session_epoch bigint NOT NULL);
CREATE TABLE owner_session(id uuid PRIMARY KEY,owner_identity_id uuid NOT NULL,lookup_digest bytea NOT NULL,session_epoch bigint NOT NULL,revoked_at timestamptz,expires_at timestamptz NOT NULL);
CREATE TABLE owner_api_credential(singleton_key smallint PRIMARY KEY CHECK(singleton_key=1),credential_version bigint NOT NULL,fingerprint text NOT NULL);
CREATE TABLE platform_incarnation(singleton_key smallint PRIMARY KEY CHECK(singleton_key=1),platform_incarnation_id uuid NOT NULL);
CREATE TABLE application_deployment_head(singleton_key smallint PRIMARY KEY CHECK(singleton_key=1),platform_incarnation_id uuid NOT NULL,application_deployment_epoch bigint NOT NULL);
'''
# Actual candidate generic domain_command DDL, not a fake boolean command.
command=(HERE.parent/'events/generation-event-storage-proposed.sql').read_text().split('CREATE TABLE domain_idempotency_record',1)[0]
proposal=(HERE/'owner-ui-intent-worker-proposed.sql').read_text();roles=(HERE/'owner-ui-role-bindings-proposed.sql').read_text()
r=sql('DROP SCHEMA IF EXISTS owner_ui_fixture CASCADE;CREATE SCHEMA owner_ui_fixture;SET search_path=owner_ui_fixture,pg_catalog;'+auth+command+proposal+roles);assert r.returncode==0,r.stderr
O='10000000-0000-4000-8000-000000000001';S='20000000-0000-4000-8000-000000000001';A='30000000-0000-4000-8000-000000000001';I='40000000-0000-4000-8000-000000000001';V='50000000-0000-4000-8000-000000000001';L='60000000-0000-4000-8000-000000000001'

from ui_facade_pipeline_reference import launch_snapshot_schema,validate_binding,schemas,validate_schema
from generation_consumer_reference import UID,DIGEST,COUNTER
TARGET='70000000-0000-4000-8000-000000000001';COMP='80000000-0000-4000-8000-000000000001'
body={'schemaVersion':'RUNTIME_OWNER_INTENT/1','action':'START','componentId':COMP,'expectedComponentStateVersion':'2','runtimeInstanceId':TARGET,'expectedRuntimeGeneration':'2','expectedActivationEpoch':'2'}
validate_schema(schemas()['dashboard.start'],body,'FIXTURE_INPUT_INVALID')
manifest={k:(TARGET if v.get('format')=='uuid' else 'sha256:'+'a'*64 if v.get('pattern')==DIGEST['pattern'] else '2' if v.get('pattern')==COUNTER['pattern'] else 'fixture') for k,v in launch_snapshot_schema()['properties'].items()}
manifest.update(componentId=COMP,runtimeInstanceId=TARGET,applicationDeploymentEpoch='7',platformIncarnationId=I)
validate_schema(launch_snapshot_schema(),manifest,'FIXTURE_SNAPSHOT_INVALID')
def lit(v):return "'"+v.replace("'","''")+"'"
REQ_SQL=lit(json.dumps(body,sort_keys=True,separators=(',',':')))
CANON_SQL=lit(json.dumps({'actionId':'dashboard.start','body':body},sort_keys=True,separators=(',',':')))
SNAP_SQL=lit(json.dumps(manifest,sort_keys=True,separators=(',',':')))
prefix='SET search_path=owner_ui_fixture,pg_catalog;BEGIN;'
base=f"""INSERT INTO owner_identity VALUES('{O}',1,2);INSERT INTO owner_session VALUES('{S}','{O}',decode(repeat('01',32),'hex'),2,NULL,clock_timestamp()+interval '1hour');INSERT INTO platform_incarnation VALUES(1,'{I}');INSERT INTO application_deployment_head VALUES(1,'{I}',7);
INSERT INTO owner_ui_authentication_acceptance VALUES('{A}','{O}','OWNER_SESSION','{S}',2,decode(repeat('01',32),'hex'),NULL,NULL,clock_timestamp());
INSERT INTO owner_ui_dispatch_registry VALUES('runtime.owner.start.request','dashboard.start','runtime.instance.start','AUTOMATED_MAINTENANCE',decode(repeat('03',32),'hex'),decode(repeat('04',32),'hex'),decode(repeat('05',32),'hex'));
INSERT INTO owner_ui_validated_input VALUES('{V}','runtime.owner.start.request',decode(repeat('03',32),'hex'),convert_to({REQ_SQL},'UTF8'),sha256(convert_to({REQ_SQL},'UTF8')),convert_to({CANON_SQL},'UTF8'),sha256(convert_to({CANON_SQL},'UTF8')),'{TARGET}',convert_to({SNAP_SQL},'UTF8'),sha256(convert_to({SNAP_SQL},'UTF8')),clock_timestamp());
INSERT INTO domain_command(logical_operation_id,operation_id,owner_id,request_digest,execution_descriptor_bytes,execution_descriptor_digest,state,terminal,platform_incarnation_id,application_deployment_epoch,created_at,updated_at,command_id,operation_contract_revision,caller_channel,execution_context_id,target_aggregate_kind,target_aggregate_id,canonical_arguments_snapshot_id,scope_digest,client_key_digest,correlation_id,accepted_at)
VALUES('{L}','runtime.owner.start.request','{O}',sha256(convert_to({CANON_SQL},'UTF8')),kcml_owner_ui_descriptor_bytes_v1('{A}','{V}','{L}','{A}'),sha256(kcml_owner_ui_descriptor_bytes_v1('{A}','{V}','{L}','{A}')),'ACCEPTED',false,'{I}',7,clock_timestamp(),clock_timestamp(),'{L}','RUNTIME_OWNER_INTENT/1','OWNER_SESSION','{A}','RUNTIME_INSTANCE','{TARGET}','{V}',decode(repeat('07',32),'hex'),decode(repeat('08',32),'hex'),'{L}',clock_timestamp());
"""
accept=f"SELECT id FROM kcml_owner_ui_accept_v1('{A}','{V}','{L}');"
worker="SELECT worker_operation_id FROM kcml_owner_ui_worker_context_v1((SELECT id FROM owner_ui_accepted_intent LIMIT1));".replace('LIMIT1','LIMIT 1')
checks=[]
def test(name,pre='',call=accept,expected=None):
 r=sql(prefix+base+pre+call+'ROLLBACK;');diagnostic=re.search(r'ERROR:\s+\w+: ([^\n]+)',r.stderr);message=diagnostic[1] if diagnostic else None;m=re.search(r'ERROR:\s+(\w+):',r.stderr);actual=m[1] if m else None;ok=r.returncode==0 if expected is None else r.returncode!=0 and actual==expected
 expected_messages={'forged-execution-descriptor-rejected':'OWNER_UI_COMMAND_SCOPE_MISMATCH','wrong-caller-channel-rejected':'OWNER_UI_COMMAND_SCOPE_MISMATCH','revoked-owner-session-blocks-fresh-intent':'OWNER_UI_SESSION_STALE','cancelled-parent-blocks-worker':'OWNER_UI_WORKER_PARENT_NOT_ADMISSIBLE','changed-deployment-blocks-worker':'OWNER_UI_WORKER_HEAD_CHANGED','changed-worker-registry-blocks':'OWNER_UI_WORKER_INTENT_LINK_MISMATCH','changed-worker-schema-pin-blocks':'OWNER_UI_WORKER_INTENT_LINK_MISMATCH','forged-schema-pin-blocks-intent':'OWNER_UI_INPUT_SCHEMA_PIN_MISMATCH','frozen-input-update-rejected':'OWNER_UI_FROZEN_IMMUTABLE','different-worker-scope-rejected':'OWNER_UI_WORKER_OPERATION_SCOPE_MISMATCH','cancel-after-context-before-effect-rejected':'OWNER_UI_WORKER_PARENT_NOT_ADMISSIBLE','unknown-worker-context-rejected':'OWNER_UI_WORKER_CONTEXT_UNAVAILABLE','nonterminal-uncertain-parent-needs-reconciliation':'OWNER_UI_WORKER_RECONCILIATION_REQUIRED'}
 if name in expected_messages:ok=ok and message==expected_messages[name]
 checks.append({'id':name,'actualDiagnostic':message,'expectedDiagnostic':expected_messages.get(name),'status':'PASS' if ok else 'FAIL','expectedSqlstate':expected,'actualSqlstate':actual});assert ok,(name,r.stderr)
test('fresh-owner-intent-accepted')
test('forged-execution-descriptor-rejected',"UPDATE domain_command SET execution_descriptor_bytes=convert_to('{}','UTF8'),execution_descriptor_digest=sha256(convert_to('{}','UTF8'));",expected='23514')
test('wrong-caller-channel-rejected',"UPDATE domain_command SET caller_channel='AUTOMATED_MAINTENANCE';",expected='23514')
test('own-worker-authority-from-visible-intent',call=accept+worker)
test('accepted-intent-replay-one-row',call=accept+accept+"DO $$BEGIN IF (SELECT count(*) FROM owner_ui_accepted_intent)<>1 THEN RAISE EXCEPTION 'duplicate';END IF;END$$;")
test('different-wire-whitespace-same-semantic-request',call=accept+"INSERT INTO owner_ui_validated_input SELECT '50000000-0000-4000-8000-000000000002',operation_id,input_schema_digest,convert_to(' '||convert_from(request_bytes,'UTF8')||' ','UTF8'),sha256(convert_to(' '||convert_from(request_bytes,'UTF8')||' ','UTF8')),canonical_request_bytes,request_digest,target_id,target_snapshot_bytes,target_snapshot_digest,validated_at FROM owner_ui_validated_input;SELECT id FROM kcml_owner_ui_accept_v1('"+A+"','50000000-0000-4000-8000-000000000002','"+L+"');DO $$BEGIN IF (SELECT count(*) FROM owner_ui_accepted_intent)<>1 THEN RAISE EXCEPTION 'duplicate';END IF;END$$;")

test('changed-worker-schema-pin-blocks',call=accept+"UPDATE owner_ui_dispatch_registry SET worker_schema_digest=decode(repeat('ff',32),'hex');"+worker,expected='23514')
test('revoked-owner-session-blocks-fresh-intent',"UPDATE owner_session SET revoked_at=clock_timestamp();",expected='28000')
test('retained-intent-worker-not-new-owner-auth',call=accept+"UPDATE owner_session SET revoked_at=clock_timestamp();"+worker)
test('nonterminal-uncertain-parent-needs-reconciliation',call=accept+"UPDATE domain_command SET error_digest=decode(repeat('ab',32),'hex');"+worker,expected='55000')
test('cancelled-parent-blocks-worker',call=accept+"UPDATE domain_command SET state='CANCELLED';"+worker,expected='55000')
test('changed-deployment-blocks-worker',call=accept+"UPDATE application_deployment_head SET application_deployment_epoch=8;"+worker,expected='40001')
test('changed-worker-registry-blocks',call=accept+"UPDATE owner_ui_dispatch_registry SET contract_digest=decode(repeat('ff',32),'hex');"+worker,expected='23514')
test('worker-context-replay-single-row',call=accept+worker+worker+"DO $$BEGIN IF (SELECT count(*) FROM owner_ui_worker_context)<>1 THEN RAISE EXCEPTION 'duplicate';END IF;END$$;")
test('forged-schema-pin-blocks-intent',"UPDATE owner_ui_dispatch_registry SET input_schema_digest=decode(repeat('ff',32),'hex');",expected='23514')
test('frozen-input-update-rejected',"UPDATE owner_ui_validated_input SET target_id='00000000-0000-4000-8000-000000000001';",expected='55000',call='')
test('domain-role-cannot-forge-input','SET LOCAL ROLE kcml_domain_writer;',call='DELETE FROM owner_ui_validated_input;',expected='42501')
test('domain-role-cannot-build-worker','SET LOCAL ROLE kcml_domain_writer;',call=worker,expected='42501')
test('domain-role-can-only-accept-intent','SET LOCAL ROLE kcml_domain_writer;')
test('dispatcher-cannot-forge-owner-auth','SET LOCAL ROLE kcml_owner_ui_dispatcher;',call='DELETE FROM owner_ui_authentication_acceptance;',expected='42501')

# Exercise both other operation/class bindings with genuinely conforming
# same-family domain input, rather than relabeling the START fixture.
stop_body={**body,'action':'STOP'}
validate_schema(schemas()['dashboard.stop'],stop_body,'FIXTURE_STOP_INVALID')
stop_req=lit(json.dumps(stop_body,sort_keys=True,separators=(',',':')))
stop_canon=lit(json.dumps({'actionId':'dashboard.stop','body':stop_body},sort_keys=True,separators=(',',':')))
stop_base=base.replace(REQ_SQL,stop_req).replace(CANON_SQL,stop_canon).replace('runtime.owner.start.request','runtime.owner.stop.request').replace('dashboard.start','dashboard.stop').replace('runtime.instance.start','runtime.stop')
rr=sql(prefix+stop_base+accept+worker+'ROLLBACK;');assert rr.returncode==0 and 'runtime.stop' in rr.stdout,rr.stderr
checks.append({'id':'stop-own-operation-authority-dispatch','status':'PASS'})
from ui_facade_pipeline_reference import native_bundle
from verify_phase2_handoffs import witness
import copy
bundle=native_bundle();defs=copy.deepcopy(bundle['$defs'])
for k,vv in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-30T12:00:00Z','RelPath':'fixture.json','JsonPointer':'','NonemptyJsonPointer':'/fixture'}.items():defs[k]={'const':vv}
spec=witness(defs['GenerationSpecification'],defs);spec['jobId']=TARGET
from generation_consumer_reference import canonical_digest
edit_body={'schemaVersion':'SPECIFICATION_OWNER_INPUT/1','variant':'OWNER_TEXT','jobId':TARGET,'expectedStateVersion':'2','expectedRevisionId':S,'expectedSpecificationDigest':canonical_digest(spec),'text':'Synthetic exact OWNER change  '}
validate_schema(schemas()['gen.editSpec'],edit_body,'FIXTURE_EDIT_INVALID')
edit_req=lit(json.dumps(edit_body,sort_keys=True,separators=(',',':')));edit_canon=lit(json.dumps({'actionId':'gen.editSpec','body':edit_body},sort_keys=True,separators=(',',':')));edit_snap=lit(json.dumps(spec,sort_keys=True,separators=(',',':')))
edit_base=base.replace(REQ_SQL,edit_req).replace(CANON_SQL,edit_canon).replace(SNAP_SQL,edit_snap).replace('runtime.owner.start.request','generation.spec.owner_input.append').replace('dashboard.start','gen.editSpec').replace('runtime.instance.start','generation.spec.propose').replace('AUTOMATED_MAINTENANCE','INTERNAL_PROTOCOL').replace("'RUNTIME_INSTANCE'","'GENERATION_JOB'").replace('RUNTIME_OWNER_INTENT/1','SPECIFICATION_OWNER_INPUT/1')
rr=sql(prefix+edit_base+accept+worker+'ROLLBACK;');assert rr.returncode==0 and 'generation.spec.propose' in rr.stdout,rr.stderr
checks.append({'id':'specification-owner-input-internal-worker-dispatch','status':'PASS'})
validation="SELECT worker_operation_id FROM kcml_owner_ui_validate_worker_context_v1((SELECT id FROM owner_ui_worker_context LIMIT 1),'runtime.instance.start','AUTOMATED_MAINTENANCE');"
test('exact-worker-context-use',call=accept+worker+validation)
test('different-worker-scope-rejected',call=accept+worker+validation.replace('runtime.instance.start','generation.spec.propose'),expected='23514')
test('cancel-after-context-before-effect-rejected',call=accept+worker+"UPDATE domain_command SET state='CANCELLED';"+validation,expected='55000')
test('unknown-worker-context-rejected',call=validation,expected='55000')

# Reserved-role adversarial install tests use only disposable alias roles.
# Real/common roles are not ALTERed; every alias transaction rolls back or is
# automatically rolled back when psql closes after ON_ERROR_STOP.
role_names=['kcml_owner_ui_builder','kcml_owner_ui_input_validator','kcml_owner_ui_dispatcher','kcml_authentication_writer','kcml_domain_writer']
aliases={name:'kcml_ui_review_'+name for name in role_names}
profile_sql=roles.split('DO $$DECLARE s text=current_schema();BEGIN',1)[0]
for name,alias in aliases.items():profile_sql=profile_sql.replace(name,alias)
alias_setup=''.join('CREATE ROLE '+alias+' NOLOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS;' for alias in aliases.values())
r=sql('BEGIN;'+alias_setup+profile_sql+'ROLLBACK;');assert r.returncode==0,r.stderr
checks.append({'id':'reserved-role-safe-profile-install','status':'PASS','fixtureRoles':'disposable alias names only'})
for name,alias in aliases.items():
 for attribute in ['LOGIN','SUPERUSER','CREATEROLE','CREATEDB','REPLICATION','BYPASSRLS']:
  r=sql('BEGIN;'+alias_setup+'ALTER ROLE '+alias+' '+attribute+';'+profile_sql+'ROLLBACK;')
  match=re.search(r'ERROR:\s+(\w+): ([^\n]+)',r.stderr)
  assert r.returncode!=0 and match and match[1]=='55000' and match[2]=='OWNER_UI_RESERVED_ROLE_PROFILE_UNSAFE',(name,attribute,r.stderr)
  absent=sql("SELECT count(*) FROM pg_roles WHERE rolname='"+alias+"';")
  assert absent.stdout.strip()=='0',alias+' survived fixture transaction'
  checks.append({'id':'reserved-role-profile/'+name+'/'+attribute,'status':'PASS','expectedSqlstate':'55000','actualSqlstate':match[1],'expectedDiagnostic':'OWNER_UI_RESERVED_ROLE_PROFILE_UNSAFE','actualDiagnostic':match[2],'fixtureRoles':'disposable aliases; no real role mutation'})
# Actual independent PostgreSQL sessions: worker cannot see or claim a pending
# intent; after COMMIT the same exact ID becomes resolvable without new inputs.
proc=subprocess.Popen(PSQL,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
proc.stdin.write(prefix+base+accept+"SELECT 'BARRIER_READY';\n");proc.stdin.flush()
intent_id=None
while True:
 line=proc.stdout.readline().strip()
 if re.fullmatch(r'[0-9a-f-]{36}',line):intent_id=line
 if line=='BARRIER_READY':break
 if not line:raise AssertionError('writer barrier missing')
assert intent_id
before=sql("SET search_path=owner_ui_fixture,pg_catalog;SELECT worker_operation_id FROM kcml_owner_ui_worker_context_v1('"+intent_id+"');")
assert before.returncode!=0 and 'OWNER_UI_WORKER_DEPENDENCY_UNAVAILABLE' in before.stderr
checks.append({'id':'independent-worker-cannot-see-uncommitted-owner-intent','status':'PASS','actualDiagnostic':'OWNER_UI_WORKER_DEPENDENCY_UNAVAILABLE'})
proc.stdin.write("COMMIT;SELECT 'COMMIT_READY';\n");proc.stdin.flush()
while proc.stdout.readline().strip()!='COMMIT_READY':pass
proc.stdin.close();proc.wait(timeout=10);assert proc.returncode==0,proc.stderr.read()
after=sql("SET search_path=owner_ui_fixture,pg_catalog;SELECT worker_operation_id FROM kcml_owner_ui_worker_context_v1('"+intent_id+"');")
assert after.returncode==0 and after.stdout.strip()=='runtime.instance.start',after.stderr
checks.append({'id':'independent-worker-resolves-same-intent-after-commit','status':'PASS'})
report={'inputCommit':'6ac0e89','postgresVersion':'18.6','scope':'Actual own intent/auth/worker context SQL guards and role isolation; producer validator/auth fixture values synthetic, not whole UI closure','checks':checks,'summary':{'checks':len(checks),'failed':sum(c['status']!='PASS' for c in checks)},'sqlSHA256':hashlib.sha256(proposal.encode()).hexdigest(),'rolesSHA256':hashlib.sha256(roles.encode()).hexdigest(),'fixtureSetupSHA256':hashlib.sha256((auth+command).encode()).hexdigest(),'verifierSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'notProven':['actual credential/schema validator service producers','full own target current-state/head resolver','worker effects/readiness/cleanup/spec DRAFT','full canonical facade operation/response/error/event catalog','actual end-to-end event/outbox/audit transaction']}
(HERE/'postgres-owner-ui-bridge-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(report['summary'])
