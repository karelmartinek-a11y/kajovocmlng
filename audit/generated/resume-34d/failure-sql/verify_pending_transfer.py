"""Actual pending→success protected-snapshot handoff using current embedded SQL."""
from pathlib import Path
import hashlib,json,struct
HERE=Path(__file__).parent
prefix=(HERE/'verify_failure_before_root.py').read_text().split('base=parts();')[0].replace('failure_sql_34d','pending_transfer_34d')
ns={'__file__':str((HERE/'verify_failure_before_root.py').resolve())};exec(compile(prefix,'reuse actual native/current canonical fixture factory','exec'),ns)
ROOT=ns['ROOT'];run=ns['run'];b=ns['b'];checks=[];case=ns['case']
pending=ns['parts']('ACCEPTED',False);q=case('accepted-pending-actual-commit',pending,commit=True);assert q.returncode==0,q.stderr
previous=run("SELECT encode(event_hash,'hex') FROM audit_event;").stdout.strip();before=run("SELECT encode(canonical_bytes,'hex') FROM generation_create_preroot_outcome;").stdout.strip()
# Reuse existing current native positive publication factory without its DB setup,
# proposal rewrite or any writes outside our own directory.
source=(ROOT/'audit/generated/resume-d362/events/verify_combined_generation.py').read_text()
positive=source[source.index('context="'):source.index('# All negatives mutate')]
v=ns['ns'];exec(compile(positive,'canonical native publication positive factory','exec'),v)
parts={k:v['base'][k]for k in ['root','snapshot','event','outbox','completion']}
parts['typed-binding']=f"INSERT INTO generation_create_command_binding VALUES('{v['op']}',{v['context']},'{v['snap']}');"
parts['command']=f"UPDATE domain_command SET state='SUCCEEDED',terminal=true,state_version=state_version+1,result_digest={b(v['rd'])},terminal_at=clock_timestamp(),updated_at=clock_timestamp() WHERE logical_operation_id='{v['op']}' AND state='ACCEPTED' AND state_version=1;"
parts['idempotency']=f"UPDATE domain_idempotency_record SET state='SUCCEEDED',state_version=state_version+1,canonical_outcome_digest={b(v['rd'])} WHERE logical_operation_id='{v['op']}' AND state='EXECUTING' AND state_version=1;"
abody=v['auditbody'].copy();abody.update(chainSequence='2',previousHash='sha256:'+previous)
ab=v['canonical_bytes'](abody);ah=hashlib.sha256(b'KCML-AUDIT-CHAIN'+struct.pack('>I',1)+bytes.fromhex(previous)+struct.pack('>q',2)+struct.pack('>q',len(ab))+ab).digest();newaudit='00000000-0000-4000-8000-000000000012'
parts['audit']=f"SELECT * FROM audit_head WHERE singleton_key=1 FOR UPDATE;INSERT INTO audit_event VALUES('{newaudit}',2,{b(bytes.fromhex(previous))},{b(ah)},1,'{v['op']}','{v['eventid']}',{b(ab)},false);UPDATE audit_head SET last_sequence=2,last_hash={b(ah)},state_version=state_version+1 WHERE singleton_key=1 AND last_sequence=1;"
# Mutation uses the valid native transfer and changes only encrypted bytes.
wrong=parts.copy();wrong['snapshot']=wrong['snapshot'].replace("decode('0102','hex')","decode('0103','hex')")
case('changed-protected-transfer-refused',wrong,'GENERATION_PREROOT_SNAPSHOT_TRANSFER_MISMATCH')
wrong=parts.copy();wrong['command']=wrong['command'].replace('state_version=state_version+1','state_version=state_version+2');case('pending-success-version-skip-refused',wrong,'GENERATION_COMMAND_STATE_VERSION_STEP')
q=case('pending-to-success-same-identity-actual-commit',parts,commit=True)
if q.returncode:raise AssertionError(q.stderr)
q=run("SELECT encode(canonical_bytes,'hex') FROM generation_create_preroot_outcome;");ns['checks'].append({'case':'earlier-pending-bytes-unchanged-after-success','passed':q.returncode==0 and q.stdout.strip()==before})
q=run("SELECT (SELECT count(*) FROM generation_job),(SELECT count(*) FROM domain_command),(SELECT count(*) FROM generation_job_initial_request_snapshot),(SELECT count(*) FROM generation_create_preroot_snapshot),(SELECT count(*) FROM generation_create_preroot_outcome),(SELECT count(*) FROM domain_event),(SELECT count(*) FROM transactional_outbox),(SELECT count(*) FROM audit_event);");ns['checks'].append({'case':'exact-one-job-command-created-event-outbox-two-audits-and-pending-history','passed':q.returncode==0 and q.stdout.strip()=='1|1|1|1|1|1|1|2'})
q=run("SELECT count(*) FROM generation_create_preroot_snapshot p JOIN generation_job_initial_request_snapshot s USING(snapshot_id) JOIN generation_create_command_binding c ON c.argument_snapshot_id=s.snapshot_id WHERE p.logical_operation_id=s.logical_operation_id AND p.prospective_job_id=s.job_id AND p.trusted_context_id=c.trusted_context_id AND p.ciphertext=s.ciphertext AND p.nonce=s.nonce AND p.key_id=s.key_id AND p.algorithm=s.algorithm AND p.request_schema_digest=s.request_schema_digest AND p.crypto_profile_digest=s.crypto_profile_digest AND p.content_digest=s.content_digest;");ns['checks'].append({'case':'identical-frozen-protected-snapshot-producer-consumer-joins','passed':q.returncode==0 and q.stdout.strip()=='1'})
report={'sourceSha256':hashlib.sha256(ns['input_source']).hexdigest(),'canonicalSqlSha256':hashlib.sha256(ns['canonical']).hexdigest(),'prerootSqlSha256':hashlib.sha256(ns['extension']).hexdigest(),'prerootEmbeddedBytesExecuted':ns['preroot_resource']is not None,'postgresqlVersion':run('SHOW server_version;').stdout.strip(),'checks':ns['checks'],'failed':sum(not c['passed']for c in ns['checks']),'sourceUnchangedDuringRun':ns['input_source']==ns['SSOT'].read_bytes(),'crypto':'OPAQUE_FIXTURE_NOT_CRYPTO','wholeOperationClosed':False}
report['database']='pending_transfer_34d'
history=HERE/'pending-transfer-invocation-history.json'
report['invocationHistory']=json.loads(history.read_text())['entries']if history.exists()else[]
report['status']='PASS'if not report['failed']and report['sourceUnchangedDuringRun']else'BLOCKED'
report['supportSha256']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),HERE/'verify_failure_before_root.py',ROOT/'audit/generated/resume-d362/events/verify_combined_generation.py',HERE/'pending-transfer-invocation-history.json']}
(HERE/'pending-transfer-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(ns['checks']),'failed':report['failed'],'status':report['status']}))
