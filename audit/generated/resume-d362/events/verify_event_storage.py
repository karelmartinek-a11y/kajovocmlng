"""Isolated PG fixtures; no application/production claim and no credentials."""
import copy,hashlib,json,os,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
from verify_create_completion import witnesses,canonical_bytes
from create_completion_contracts import canonical_digest,semantic_result
from create_replay_contract import freeze_descriptor
from jsonschema import Draft202012Validator,FormatChecker
from pglast import parse_sql
HERE=Path(__file__).parent
SQL=HERE/'generation-event-storage-proposed.sql'
checks=[]
def record(name,ok,detail=None):checks.append({'case':name,'passed':bool(ok),**({'detail':detail} if detail else {})})
def audit_hash(version,prev,sequence,raw):
 if version!=1 or len(prev)!=32 or sequence<1:raise ValueError('AUDIT_HASH_INPUT_INVALID')
 return hashlib.sha256(b'KCML-AUDIT-CHAIN'+struct.pack('>I',version)+prev+struct.pack('>q',sequence)+struct.pack('>q',len(raw))+raw).digest()
def quote(v):return "'"+v.replace("'","''")+"'"
def bytea(raw):return "decode('"+raw.hex()+"','hex')"
source=SSOT.read_bytes();r=resource_index();rows=json.loads(r['contracts/payload-contracts.json']['raw'])['records'];row=next(x for x in rows if x['operationId']=='generation.job.create')
response,event=witnesses('generation.job.create',row)
record('positive-exact-response',Draft202012Validator(row['responseSchema'],format_checker=FormatChecker()).is_valid(response))
record('positive-exact-event',Draft202012Validator(row['eventSchema'],format_checker=FormatChecker()).is_valid(event))
record('outer-postgres17-parser',bool(parse_sql(SQL.read_text())))
vector_data=[]
for seq,raw in [(1,b'{}'),(2,b'{"synthetic":true}'),(9223372036854775807,'{"label":"žluťoučký"}'.encode())]:
 h=audit_hash(1,bytes(32),seq,raw);vector_data.append({'version':1,'previousHash':'00'*32,'sequence':str(seq),'canonicalBytesHex':raw.hex(),'hashHex':h.hex()})
 record('hash-vector-deterministic/'+str(seq),h==audit_hash(1,bytes(32),seq,raw))
(HERE/'audit-hash-vectors.json').write_text(json.dumps(vector_data,indent=2)+'\n')
pg_cmd=json.loads(os.getenv('KCML_EVENT_PSQL_COMMAND','null'))
pg_status='NOT_RUN';pg_version=None
if pg_cmd:
 def run(sql):return subprocess.run(pg_cmd+['-X','-q','-At','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose'],input=sql,text=True,capture_output=True)
 probe=run('SELECT version();');assert probe.returncode==0,probe.stderr;pg_version=probe.stdout.strip();pg_status='EXECUTED'
 # Disposable fixture database only. Minimal root is explicitly a FK dependency
 # fixture; it is not claimed to be the complete generation_job declaration.
 init="""CREATE TABLE generation_job(id uuid PRIMARY KEY,aggregate_event_sequence bigint NOT NULL,kind text NOT NULL,initial_request_digest bytea NOT NULL,state_version bigint NOT NULL,created_at timestamptz NOT NULL);
 CREATE TABLE generation_job_create_completion(logical_operation_id uuid PRIMARY KEY,job_id uuid NOT NULL,semantic_response_bytes bytea NOT NULL,result_digest bytea NOT NULL CHECK(result_digest=sha256(semantic_response_bytes)),output_receipt_bytes bytea NOT NULL,output_receipt_digest bytea NOT NULL CHECK(output_receipt_digest=sha256(output_receipt_bytes)),immutable_event_id uuid NOT NULL UNIQUE,aggregate_event_sequence bigint NOT NULL,committed_state_version bigint NOT NULL,created_at timestamptz NOT NULL);
 """
 loc=r['database/explicit-entities.sql']['raw'].decode();loc=loc[loc.index('CREATE TABLE idempotency_locator'):]
 # Order command before locator before trigger definitions referencing locator.
 ddl=SQL.read_text();split=ddl.index('CREATE FUNCTION kcml_generation_create_atomic_closure_v1')
 setup=run(init+ddl[:split]+loc+ddl[split:]);record('postgres-DDL-and-plpgsql-executable',setup.returncode==0,setup.stderr[-1000:] if setup.returncode else None)
 if setup.returncode==0:
  for v in vector_data:
   q=run(f"SELECT encode(kcml_audit_hash(1,decode('{v['previousHash']}','hex'),{v['sequence']},decode('{v['canonicalBytesHex']}','hex')),'hex');")
   record('postgres-hash-vector/'+v['sequence'],q.returncode==0 and q.stdout.strip()==v['hashHex'])
  owner='00000000-0000-4000-8000-000000000005';op=response['logicalOperationId'];job=response['output']['jobId'];ev=event['immutableEventId'];out='00000000-0000-4000-8000-000000000006';audit='00000000-0000-4000-8000-000000000007';loc_id='00000000-0000-4000-8000-000000000008';scope=hashlib.sha256(b'fixture-frozen-scope').digest();key=hashlib.sha256(b'fixture-client-key').digest();req=hashlib.sha256(b'fixture-business-body').digest();desc=canonical_bytes(freeze_descriptor({'operationId':'generation.job.create','idempotencyKey':'fixture-client-key'},{'owner':owner},'fixture-pinned-v1'));sem=canonical_bytes(semantic_result(response));receipt=canonical_bytes(response['output']);rd=hashlib.sha256(sem).digest();pd=hashlib.sha256(receipt).digest()
  audit_value={'chainSequence':'1','previousHash':'sha256:'+'00'*32,'eventId':ev,'logicalOperationId':op,'actorId':owner,'objectId':job,'beforeDigest':None,'afterDigest':canonical_digest(response['output']),'correlationId':response['correlationId'],'causationId':None,'traceId':'fixture','occurredAt':event['occurredAt']};abytes=canonical_bytes(audit_value);ah=audit_hash(1,bytes(32),1,abytes)
  stmts={
   'command':f"INSERT INTO domain_command VALUES('{op}','generation.job.create','{owner}',{bytea(req)},{bytea(desc)},{bytea(hashlib.sha256(desc).digest())},'SUCCEEDED',true,1,{bytea(rd)},'{owner}',1,clock_timestamp(),clock_timestamp(),'{op}','fixture-pinned-v1','OWNER_UI','{owner}','GENERATION_JOB','{job}','{owner}',{bytea(scope)},{bytea(key)},NULL,NULL,NULL,NULL,NULL,NULL,'{response['correlationId']}',NULL,clock_timestamp(),clock_timestamp(),NULL);",
   'locator':f"INSERT INTO idempotency_locator VALUES('{loc_id}','GENERATION','OWNER_FULL','{owner}','CREATE_ROOT','generation_job',{bytea(key)},'{op}',{bytea(req)},{bytea(hashlib.sha256(desc).digest())},{bytea(scope)},clock_timestamp(),clock_timestamp(),clock_timestamp()+interval '1 day');",
   'idempotency':f"INSERT INTO domain_idempotency_record VALUES({bytea(scope)},{bytea(key)},{bytea(req)},'{op}','RESERVED',0,NULL);",
   'root':f"INSERT INTO generation_job VALUES('{job}',1,'CREATE',decode('{response['output']['initialRequestDigest'][7:]}','hex'),1,'{response['output']['createdAt']}');",
   'event':f"INSERT INTO domain_event VALUES('{ev}','{job}','GENERATION_JOB','{op}',1,'generation.job.created','{row['eventSchema']['$id']}',{bytea(hashlib.sha256(canonical_bytes(row['eventSchema'])).digest())},{bytea(receipt)},{bytea(pd)},'{response['correlationId']}',NULL,clock_timestamp());",
   'outbox':f"INSERT INTO transactional_outbox VALUES('{out}','{ev}','{op}','{job}','DOMAIN_EVENT','owner-generation-sse',clock_timestamp(),'READY',0,0,{bytea(pd)},0,NULL,NULL);",
   'completion':f"INSERT INTO generation_job_create_completion VALUES('{op}','{job}',{bytea(sem)},{bytea(rd)},{bytea(receipt)},{bytea(pd)},'{ev}',1,1,clock_timestamp());",
   'finalize-idempotency':f"UPDATE domain_idempotency_record SET state='EXECUTING',state_version=1 WHERE logical_operation_id='{op}' AND state='RESERVED';UPDATE domain_idempotency_record SET state='SUCCEEDED',state_version=2,canonical_outcome_digest={bytea(rd)} WHERE logical_operation_id='{op}' AND state='EXECUTING';",
   'head':"SELECT * FROM audit_head WHERE singleton_key=1 FOR UPDATE;",
   'audit':f"INSERT INTO audit_event VALUES('{audit}',1,{bytea(bytes(32))},{bytea(ah)},1,'{op}','{ev}',{bytea(abytes)},false);UPDATE audit_head SET last_sequence=1,last_hash={bytea(ah)},state_version=state_version+1 WHERE singleton_key=1;"
  }
  def tx(parts):return 'BEGIN;'+''.join(parts)+'COMMIT;'
  order=list(stmts)
  # Mutation negatives begin with this exact valid witness; each database is
  # restored by ROLLBACK/failed commit before the next case. No unrelated failure
  # is accepted as proof: exact SQLSTATE+message are required.
  for missing in ['outbox','idempotency','locator','audit']:
   q=run(tx([v for k,v in stmts.items() if k!=missing]));record('reject-missing-'+missing,q.returncode!=0 and '23514' in q.stderr and 'GENERATION_CREATE_ATOMIC_CLOSURE_INCOMPLETE' in q.stderr,q.stderr[-500:] if q.returncode==0 else None)
   count=run('SELECT count(*) FROM generation_job;');record('rollback-no-root/'+missing,count.stdout.strip()=='0')
  bad_audit_value={**audit_value,'objectId':owner};bad_bytes=canonical_bytes(bad_audit_value);bad_hash=audit_hash(1,bytes(32),1,bad_bytes)
  bad_audit=f"INSERT INTO audit_event VALUES('{audit}',1,{bytea(bytes(32))},{bytea(bad_hash)},1,'{op}','{ev}',{bytea(bad_bytes)},false);UPDATE audit_head SET last_sequence=1,last_hash={bytea(bad_hash)},state_version=state_version+1 WHERE singleton_key=1;"
  q=run(tx([bad_audit if k=='audit' else v for k,v in stmts.items()]));record('reject-audit-bytes-wrong-object-despite-valid-hash',q.returncode!=0 and '23514' in q.stderr and 'GENERATION_CREATE_ATOMIC_CLOSURE_INCOMPLETE' in q.stderr)
  bad_head=stmts['audit'].replace(f'last_hash={bytea(ah)}',f'last_hash={bytea(bytes(32))}')
  q=run(tx([bad_head if k=='audit' else v for k,v in stmts.items()]));record('reject-head-hash-not-current-audit-tail',q.returncode!=0 and '23514' in q.stderr and 'GENERATION_CREATE_ATOMIC_CLOSURE_INCOMPLETE' in q.stderr)
  q=run(tx(list(stmts.values())));record('postgres-valid-atomic-create',q.returncode==0,q.stderr[-800:] if q.returncode else None)
  q=run("SELECT (SELECT count(*) FROM generation_job),(SELECT count(*) FROM domain_event),(SELECT count(*) FROM transactional_outbox),(SELECT count(*) FROM audit_event),(SELECT last_sequence FROM audit_head);");record('committed-root-event-outbox-audit-join',q.stdout.strip()=='1|1|1|1|1')
  q=run(f"UPDATE domain_event SET payload_bytes=convert_to('changed','UTF8') WHERE id='{ev}';");record('immutable-event-specific-rejection',q.returncode!=0 and 'CREATE_IMMUTABLE_RECORD' in q.stderr)
  q=run(f"UPDATE domain_command SET request_digest={bytea(hashlib.sha256(b'changed').digest())} WHERE logical_operation_id='{op}';");record('frozen-command-replay-specific-rejection',q.returncode!=0 and 'CREATE_COMMAND_FROZEN_SCOPE' in q.stderr)
  q=run(f"UPDATE domain_idempotency_record SET request_digest={bytea(hashlib.sha256(b'changed').digest())} WHERE logical_operation_id='{op}';");record('idempotency-request-immutable-specific-rejection',q.returncode!=0 and 'CREATE_IDEMPOTENCY_FROZEN_SCOPE' in q.stderr)
  q=run(f"UPDATE idempotency_locator SET logical_operation_id='00000000-0000-4000-8000-000000000009' WHERE locator_id='{loc_id}';");record('locator-operation-immutable-specific-rejection',q.returncode!=0 and 'CREATE_LOCATOR_FROZEN_SCOPE' in q.stderr)
  q=run(f"UPDATE transactional_outbox SET payload_digest={bytea(hashlib.sha256(b'changed').digest())} WHERE id='{out}';");record('outbox-payload-digest-frozen-specific-rejection',q.returncode!=0 and 'CREATE_OUTBOX_FROZEN_DELIVERY' in q.stderr)
  q=run(f"UPDATE transactional_outbox SET event_id='00000000-0000-4000-8000-000000000009' WHERE id='{out}';");record('outbox-event-retarget-frozen-specific-rejection',q.returncode!=0 and 'CREATE_OUTBOX_FROZEN_DELIVERY' in q.stderr)
  q=run(f"DELETE FROM transactional_outbox WHERE id='{out}';");record('outbox-deletion-requires-retention-authority',q.returncode!=0 and 'CREATE_OUTBOX_RETENTION_AUTHORITY_REQUIRED' in q.stderr)
  q=run(f"UPDATE transactional_outbox SET state='DELIVERED',state_version=1 WHERE id='{out}';");record('outbox-ready-cannot-skip-claim',q.returncode!=0 and 'CREATE_OUTBOX_TRANSITION_INVALID' in q.stderr)
  q=run(f"UPDATE transactional_outbox SET state='CLAIMED',state_version=1,delivery_fence=1,lease_owner_id='{owner}',lease_expires_at=clock_timestamp()+interval '10 minutes' WHERE id='{out}' AND state='READY' AND state_version=0;");record('outbox-positive-fenced-claim',q.returncode==0)
  q=run(f"UPDATE transactional_outbox SET state='DELIVERED',state_version=2 WHERE id='{out}' AND state='CLAIMED' AND delivery_fence=1 AND lease_owner_id='{owner}';");record('outbox-positive-fenced-delivery',q.returncode==0)
  q=run(f"UPDATE transactional_outbox SET state='READY',state_version=3 WHERE id='{out}';");record('outbox-delivered-terminal-immutable',q.returncode!=0 and 'CREATE_OUTBOX_TERMINAL_IMMUTABLE' in q.stderr)
  q=run(f"UPDATE domain_idempotency_record SET state='EXECUTING' WHERE logical_operation_id='{op}';");record('terminal-idempotency-state-immutable-specific-rejection',q.returncode!=0 and 'CREATE_IDEMPOTENCY_FROZEN_SCOPE' in q.stderr)
  q=run(f"UPDATE domain_idempotency_record SET canonical_outcome_digest={bytea(hashlib.sha256(b'changed').digest())} WHERE logical_operation_id='{op}';");record('terminal-idempotency-outcome-immutable-specific-rejection',q.returncode!=0 and 'CREATE_IDEMPOTENCY_FROZEN_SCOPE' in q.stderr)
  # Two concurrent processes read the same stable locator under its row lock.
  # The contender's no-op INSERT uses the exact stable scope, then compares
  # original digest. It does not acquire a target or activation lock.
  import time
  locked=HERE/'pg-race-lock.marker'
  if locked.exists():locked.unlink()
  hold_sql=f"BEGIN;SELECT logical_operation_id FROM idempotency_locator WHERE locator_id='{loc_id}' FOR UPDATE;\\! touch {locked}\nSELECT pg_sleep(0.4);COMMIT;"
  holder=subprocess.Popen(pg_cmd+['-X','-q','-At','-v','ON_ERROR_STOP=1'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  holder.stdin.write(hold_sql);holder.stdin.close()
  deadline=time.monotonic()+3
  while not locked.exists() and time.monotonic()<deadline:time.sleep(0.02)
  record('concurrent-locator-holder-established',locked.exists())
  contender=run(f"BEGIN;SELECT logical_operation_id FROM idempotency_locator WHERE locator_id='{loc_id}' FOR UPDATE;SELECT CASE WHEN client_request_digest={bytea(req)} THEN 'FROZEN_REPLAY' ELSE 'IDEMPOTENCY_CONFLICT' END FROM idempotency_locator WHERE locator_id='{loc_id}';COMMIT;")
  holder.wait(timeout=5)
  if locked.exists():locked.unlink()
  record('concurrent-same-locator-replay',holder.returncode==0 and contender.returncode==0 and 'FROZEN_REPLAY' in contender.stdout)
  q=run(f"BEGIN;SELECT logical_operation_id FROM idempotency_locator WHERE locator_id='{loc_id}' FOR UPDATE;SELECT CASE WHEN client_request_digest={bytea(hashlib.sha256(b'different-request').digest())} THEN 'FROZEN_REPLAY' ELSE 'IDEMPOTENCY_CONFLICT' END FROM idempotency_locator WHERE locator_id='{loc_id}';COMMIT;")
  record('different-request-specific-idempotency-conflict',q.returncode==0 and 'IDEMPOTENCY_CONFLICT' in q.stdout)
  # UNKNOWN is distinguished from a proved rollback: lose only transport,
  # reconnect and resolve the original persisted locator/receipt. No re-create.
  q=run(f"SELECT c.state,encode(c.result_digest,'hex') FROM domain_command c JOIN idempotency_locator l USING(logical_operation_id) WHERE l.locator_id='{loc_id}';")
  record('unknown-transport-outcome-reconciles-original-receipt',q.returncode==0 and q.stdout.strip()=='SUCCEEDED|'+rd.hex())
  # Positive replay only SELECTs frozen rows; no target lock or mutation.
  q=run(f"SELECT encode(result_digest,'hex') FROM domain_command WHERE logical_operation_id='{op}';SELECT count(*) FROM domain_event;");record('replay-frozen-result-no-second-event',q.stdout.strip()==rd.hex()+'\n1')
report={'format':'KCML-GENERATION-EVENT-STORAGE-PROOF/1','entryHead':'d362487999bd795d4723c2a930e93fc7aa8aa295','sourceSha256':hashlib.sha256(source).hexdigest(),'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [SQL,Path(__file__)]},'postgres':{'status':pg_status,'version':pg_version,'fixtureRoot':'MINIMAL_FK_DEPENDENCY_NOT_COMPLETE_ROOT'},'checks':checks,'summary':{'checks':len(checks),'failed':sum(not c['passed'] for c in checks)},'runtimeAcceptance':'NOT_EVALUATED','open':['Full trusted context and exact owner/platform foreign keys','Full generic outbox purpose extensions','Archive policy collector and retention governance','Independent semantic integration review']}
assert SSOT.read_bytes()==source,'source changed during fixture'
(HERE/'event-storage-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))
if report['summary']['failed']:sys.exit(1)
