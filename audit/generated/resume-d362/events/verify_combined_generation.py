"""Combined PG18.6 physical roots/context/snapshot/publication reference fixture."""
from pathlib import Path
import sys,hashlib,json,re,subprocess,struct,copy,importlib.util
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
from create_operation_contracts import decode_http
from create_replay_contract import freeze_descriptor
from create_completion_contracts import canonical_digest,semantic_result
from verify_create_completion import witnesses,canonical_bytes
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p55432','-d','generation_combined_fixture','-X','-q','-At','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose']
def run(s):return subprocess.run(PSQL,input=s,text=True,capture_output=True)
def b(v):return "decode('"+v.hex()+"','hex')"
def q(v):return "'"+v.replace("'","''")+"'"
source=SSOT.read_bytes();rs=resource_index();row=next(x for x in json.loads(rs['contracts/payload-contracts.json']['raw'])['records'] if x['operationId']=='generation.job.create')
body={'intent':'Create a synthetic component.','kind':'CREATE','targetKind':'PLATFORM_COMPONENT','sources':[{'kind':'TEXT','text':'Synthetic positive fixture input.'}]}
native=decode_http('generation.job.create','POST',row['path'],[],[('Content-Type','application/json'),('Idempotency-Key','combined-reference-key')],canonical_bytes(body))
owner='00000000-0000-4000-8000-000000000005';op='00000000-0000-4000-8000-000000000001';job='00000000-0000-4000-8000-000000000002';eventid='00000000-0000-4000-8000-000000000004';out='00000000-0000-4000-8000-000000000006';auth='00000000-0000-4000-8000-000000000007';snap='00000000-0000-4000-8000-000000000008';audit='00000000-0000-4000-8000-000000000009';locatorid='00000000-0000-4000-8000-000000000010'
request_digest=bytes.fromhex(native['requestDigest'][7:]);initialdigest=hashlib.sha256(canonical_bytes(body)).digest();key=hashlib.sha256(b'combined-reference-key').digest();descriptor=canonical_bytes(freeze_descriptor(native,{'owner':owner},'fixture-pinned-v1'));dd=hashlib.sha256(descriptor).digest();scope=hashlib.sha256(descriptor).digest()
response,event=witnesses('generation.job.create',row);response['output']['initialRequestDigest']='sha256:'+initialdigest.hex();response['resultDigest']=canonical_digest(semantic_result(response));event['payload']=copy.deepcopy(response['output']);event['payloadDigest']=canonical_digest(event['payload']);receipt=canonical_bytes(response['output']);pd=hashlib.sha256(receipt).digest();sem=canonical_bytes(semantic_result(response));rd=hashlib.sha256(sem).digest()
modulefile=ROOT/'audit/generated/resume-d362/persistence/combined_foundations.py';spec=importlib.util.spec_from_file_location('foundations',modulefile);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);foundation=module.foundations();locator=rs['database/explicit-entities.sql']['raw'].decode();locator=locator[locator.index('CREATE TABLE idempotency_locator'):];split=foundation.index('CREATE FUNCTION kcml_generation_create_atomic_closure_v1');foundation=foundation[:split]+locator+foundation[split:]
checks=[]
def rec(n,ok,detail=None):checks.append({'case':n,'passed':bool(ok),**({'detail':detail} if detail else {})})
r=run(foundation);rec('combined-actual-proposals-executable',r.returncode==0,r.stderr[-1200:] if r.returncode else None)
if r.returncode:raise AssertionError(r.stderr)
(HERE/'combined-foundations.sql').write_text(foundation)
version=run('SHOW server_version;').stdout.strip();assert version=='18.6'
context="(SELECT id FROM generation_create_trusted_context LIMIT 1)"
auditbody={'chainSequence':'1','previousHash':'sha256:'+'00'*32,'eventId':eventid,'logicalOperationId':op,'actorId':owner,'objectId':job,'beforeDigest':None,'afterDigest':'sha256:'+pd.hex(),'correlationId':op,'causationId':None,'traceId':'fixture','occurredAt':event['occurredAt']};abytes=canonical_bytes(auditbody)
ah=hashlib.sha256(b'KCML-AUDIT-CHAIN'+struct.pack('>I',1)+bytes(32)+struct.pack('>q',1)+struct.pack('>q',len(abytes))+abytes).digest()
base={
'auth':f"INSERT INTO owner_identity VALUES('{owner}',1,1);INSERT INTO owner_api_credential VALUES(1,1,'synthetic-fingerprint');INSERT INTO platform_incarnation VALUES(1,'{owner}');INSERT INTO application_deployment_head VALUES(1,'{owner}',1);INSERT INTO generation_create_authentication_acceptance(id,owner_id,access_channel,api_credential_version,api_credential_fingerprint,accepted_at)VALUES('{auth}','{owner}','OWNER_API_KEY',1,'synthetic-fingerprint',clock_timestamp());",
'context':f"SELECT kcml_generation_create_context_v1('{auth}',{b(request_digest)},{b(hashlib.sha256(canonical_bytes(row['requestSchema'])).digest())},{b(descriptor)});",
'command':f"INSERT INTO domain_command VALUES('{op}','generation.job.create','{owner}',{b(request_digest)},{b(descriptor)},{b(dd)},'SUCCEEDED',true,1,{b(rd)},'{owner}',1,clock_timestamp(),clock_timestamp(),'{op}','fixture-pinned-v1','OWNER_API_KEY',{context},'GENERATION_JOB','{job}','{snap}',{b(scope)},{b(key)},NULL,NULL,NULL,NULL,NULL,NULL,'{op}',NULL,clock_timestamp(),clock_timestamp(),NULL);",
'locator':f"INSERT INTO idempotency_locator VALUES('{locatorid}','GENERATION','OWNER_FULL','{owner}','CREATE_ROOT','generation_job',{b(key)},'{op}',{b(request_digest)},{b(dd)},{b(scope)},clock_timestamp(),clock_timestamp(),clock_timestamp()+interval '1 day');",
'idempotency':f"INSERT INTO domain_idempotency_record VALUES({b(scope)},{b(key)},{b(request_digest)},'{op}','RESERVED',0,NULL);",
'root':f"INSERT INTO generation_job(id,owner_id,initiating_access_channel,initiating_execution_context_id,kind,target_kind,state,state_version,aggregate_event_sequence,initial_request_snapshot_id,initial_request_digest,platform_incarnation_id,application_deployment_epoch,created_at,client_request_id,latest_command_logical_operation_id) VALUES('{job}','{owner}','OWNER_API_KEY',{context},'CREATE','PLATFORM_COMPONENT','DISCUSSING',1,1,'{snap}',{b(initialdigest)},'{owner}',1,'{response['output']['createdAt']}','combined-reference-key','{op}');",
'snapshot':f"INSERT INTO generation_job_initial_request_snapshot VALUES('{job}','{snap}','{op}','urn:kcml:r9:semantic:route.0215:body',{b(hashlib.sha256(canonical_bytes(row['requestSchema']['properties']['body'])).digest())},{b(initialdigest)},decode('0102','hex'),decode('03','hex'),'FIXTURE_OPAQUE_NOT_CRYPTO','FIXTURE_ONLY',decode(repeat('04',32),'hex'),clock_timestamp());",
'event':f"INSERT INTO domain_event VALUES('{eventid}','{job}','GENERATION_JOB','{op}',1,'generation.job.created','{row['eventSchema']['$id']}',{b(hashlib.sha256(canonical_bytes(row['eventSchema'])).digest())},{b(receipt)},{b(pd)},'{op}',NULL,clock_timestamp());",
'outbox':f"INSERT INTO transactional_outbox VALUES('{out}','{eventid}','{op}','{job}','DOMAIN_EVENT','owner-generation-sse',clock_timestamp(),'READY',0,0,{b(pd)},0,NULL,NULL);",
'completion':f"INSERT INTO generation_job_create_completion VALUES('{op}','{job}',{b(sem)},{b(rd)},{b(receipt)},{b(pd)},'{eventid}',1,1,clock_timestamp());",
'finalize-idempotency':f"UPDATE domain_idempotency_record SET state='EXECUTING',state_version=1 WHERE logical_operation_id='{op}' AND state='RESERVED';UPDATE domain_idempotency_record SET state='SUCCEEDED',state_version=2,canonical_outcome_digest={b(rd)} WHERE logical_operation_id='{op}' AND state='EXECUTING';",
'audit':f"SELECT * FROM audit_head WHERE singleton_key=1 FOR UPDATE;INSERT INTO audit_event VALUES('{audit}',1,{b(bytes(32))},{b(ah)},1,'{op}','{eventid}',{b(abytes)},false);UPDATE audit_head SET last_sequence=1,last_hash={b(ah)},state_version=1 WHERE singleton_key=1;"
}
# All negatives mutate one physically and natively valid positive witness.
def case(n,parts=None,sqlstate=None,message=None):
 text='BEGIN;'+''.join((parts or base).values())+'SET CONSTRAINTS ALL IMMEDIATE;ROLLBACK;';r=run(text);m=re.search(r'ERROR:\s+(\w+):\s+([^\n]+)',r.stderr);actual=m[1] if m else None;msg=m[2] if m else None;ok=r.returncode==0 if sqlstate is None else r.returncode!=0 and actual==sqlstate and (message is None or message in msg);rec(n,ok,{'expectedSqlstate':sqlstate,'actualSqlstate':actual,'expectedMessage':message,'actualMessage':msg});return r
case('full-root-context-snapshot-event-outbox-audit-positive')
for k in ['event','outbox','audit','snapshot']:
 bad={x:v for x,v in base.items() if x!=k};case('missing-'+k+'-rejects-entire-create',bad,'23503' if k in ['event','snapshot'] else '23514')
bad=base.copy();bad['command']=bad['command'].replace("'GENERATION_JOB','"+job+"'", "'GENERATION_JOB','"+owner+"'");case('command-target-must-equal-frozen-snapshot-job',bad,'23514','GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID')
# Caller-channel adapter binding remains OPEN; acceptance of an unbound label
# is not counted as a successful required-policy check.
bad=base.copy();bad['context']=bad['context'].replace(b(request_digest),b(bytes(32)));case('context-caller-digest-cannot-disagree-with-command',bad,'23514','GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID')
bad=base.copy();bad['root']=bad['root'].replace(b(initialdigest),b(bytes(32)));case('root-body-digest-cannot-disagree-with-frozen-receipt-and-snapshot',bad,'23514','GENERATION_CREATE_ATOMIC_CLOSURE_INCOMPLETE')
# Fresh same-business-key concurrent creation uses the exact physical roots.
# Auth fixtures are committed separately; they are not fabricated per attempt.
r=run('BEGIN;'+base['auth']+base['context']+'COMMIT;');rec('persisted-auth-context-for-concurrency',r.returncode==0)
import time
marker=HERE/'combined-locator-lock.marker'
if marker.exists():marker.unlink()
claims=base['locator'][:-1]+' ON CONFLICT DO NOTHING;'+f"SELECT logical_operation_id FROM idempotency_locator WHERE locator_id='{locatorid}' FOR UPDATE;"+base['idempotency'][:-1]+' ON CONFLICT DO NOTHING;'+f"SELECT logical_operation_id FROM domain_idempotency_record WHERE scope_digest={b(scope)} AND key_digest={b(key)} FOR UPDATE;"
heads="SELECT * FROM platform_incarnation WHERE singleton_key=1 FOR SHARE;SELECT * FROM application_deployment_head WHERE singleton_key=1 FOR SHARE;SELECT * FROM owner_api_credential WHERE singleton_key=1 FOR SHARE;"
newparts=''.join(base[k] for k in ['root','command','snapshot','event','outbox','completion','finalize-idempotency','audit'])
first="BEGIN;SET LOCAL lock_timeout='2s';"+heads+claims+newparts+'SET CONSTRAINTS ALL IMMEDIATE;\\! touch '+str(marker)+"\nSELECT pg_sleep(0.4);COMMIT;"
holder=subprocess.Popen(PSQL,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);holder.stdin.write(first);holder.stdin.close();deadline=time.monotonic()+3
while not marker.exists() and time.monotonic()<deadline:time.sleep(.02)
rec('fresh-create-race-first-transaction-ready',marker.exists())
# Competing request proposes a distinct server UUID but the unique stable key
# resolves to the first logical operation. It never inserts a second root.
contender_locator=base['locator'].replace(locatorid,'00000000-0000-4000-8000-000000000011').replace("'"+op+"'","'00000000-0000-4000-8000-000000000012'")[:-1]+' ON CONFLICT DO NOTHING;'
lookup=f"SELECT logical_operation_id FROM idempotency_locator WHERE operation_family='GENERATION' AND caller_authority_kind='OWNER_FULL' AND caller_stable_id='{owner}' AND business_target_kind='CREATE_ROOT' AND business_target_id='generation_job' AND client_key_digest={b(key)} FOR UPDATE;"
r=run('BEGIN;'+heads+contender_locator+lookup+f"SELECT CASE WHEN client_request_digest={b(request_digest)} THEN 'FROZEN_REPLAY' ELSE 'IDEMPOTENCY_CONFLICT' END FROM idempotency_locator WHERE client_key_digest={b(key)};COMMIT;")
holder.wait(timeout=5);herr=holder.stderr.read();rec('concurrent-first-create-valid-commit',holder.returncode==0,herr[-1000:] if holder.returncode else None);rec('concurrent-same-key-resolves-first-operation-no-new-root',r.returncode==0 and op in r.stdout and 'FROZEN_REPLAY' in r.stdout)
if marker.exists():marker.unlink()
r=run("SELECT (SELECT count(*) FROM generation_job),(SELECT count(*) FROM domain_command),(SELECT count(*) FROM domain_event),(SELECT count(*) FROM transactional_outbox),(SELECT count(*) FROM audit_event);");rec('fresh-concurrent-creation-exactly-one-observable-outcome',r.stdout.strip()=='1|1|1|1|1')
report={'format':'KCML-PG-GENERATION-COMBINED-PROOF/1','entryHead':'d362487999bd795d4723c2a930e93fc7aa8aa295','sourceSha256':hashlib.sha256(source).hexdigest(),'postgresVersion':version,'foundationSha256':hashlib.sha256(foundation.encode()).hexdigest(),'nativeRequestDecoderPositive':True,'syntheticOnly':True,'crypto':'OPAQUE_FIXTURE_NOT_PROOF','sourceAuthenticationRoots':'FIXTURE_REQUIRED_COLUMNS_NOT_COMPLETE_AUTH_DDL','checks':checks,'summary':{'checks':len(checks),'failed':sum(not c['passed'] for c in checks)},'wholeOperationClosed':False,'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED','open':['Canonical authentication service credential verification and grants','Exact caller-channel adapter binding','Actual authenticated crypto profile and snapshot decrypt/hash/native hydration','Fresh new-scope idempotency concurrency and full failure injection']}
assert SSOT.read_bytes()==source
(HERE/'combined-generation-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']));sys.exit(bool(report['summary']['failed']))
