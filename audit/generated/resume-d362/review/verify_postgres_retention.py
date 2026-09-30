from pathlib import Path
import json,subprocess,hashlib
HERE=Path(__file__).parent
cmd=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-d','generation_independent_review_fixture','-X','-At','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose']
def run(sql):return subprocess.run(cmd,input=sql,text=True,capture_output=True)
version=run('SELECT version();').stdout.strip()
rows=[]
cases=[
 ('terminal-idempotency-state',"UPDATE domain_idempotency_record SET state='EXECUTING';"),
 ('terminal-idempotency-outcome',"UPDATE domain_idempotency_record SET canonical_outcome_digest=decode(repeat('00',32),'hex');"),
 ('outbox-consumer-retarget',"UPDATE transactional_outbox SET consumer_scope='untrusted-consumer';"),
 ('outbox-payload-retarget',"UPDATE transactional_outbox SET payload_digest=decode(repeat('00',32),'hex');"),
 ('outbox-delete-after-delivery',"DELETE FROM transactional_outbox;"),
 ('terminal-delivery-state-rewrite',"UPDATE transactional_outbox SET state='DELIVERED',state_version=state_version+1;"),
 ('terminal-command-delete',"DELETE FROM domain_command;"),
 ('audit-byte-change',"UPDATE audit_event SET canonical_bytes=convert_to('{}','UTF8');"),
]
for name,sql in cases:
 q=run('BEGIN;'+sql+'ROLLBACK;')
 expected=('CREATE_IDEMPOTENCY_FROZEN_SCOPE' if name.startswith('terminal-idempotency') else 'CREATE_OUTBOX_FROZEN_DELIVERY' if name in ['outbox-consumer-retarget','outbox-payload-retarget'] else 'CREATE_OUTBOX_RETENTION_AUTHORITY_REQUIRED' if name=='outbox-delete-after-delivery' else 'CREATE_OUTBOX_TERMINAL_IMMUTABLE' if name=='terminal-delivery-state-rewrite' else 'generation_job_latest_command_logical_operation_id_fkey' if name=='terminal-command-delete' else 'CREATE_IMMUTABLE_RECORD')
 rows.append({'id':name,'mutation':sql,'expectedDiagnostic':expected,'rejected':q.returncode!=0 and expected in q.stderr,'diagnostic':q.stderr.strip()[-1500:]})
report={'scope':'Independent post-commit PostgreSQL retention/adversarial checks; every mutation runs inside rollback-only transaction. Not production implementation acceptance.','version':version,'checks':rows,'unexpectedAccepted':sum(not x['rejected'] for x in rows),'database':'generation_independent_review_fixture','sourceSha256':hashlib.sha256((HERE.parents[3]/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'filesSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in [HERE/'combined-foundations.sql',HERE/'generation-command-links-corrected.sql',HERE.parent/'events/generation-event-storage-proposed.sql',HERE.parent/'persistence/trusted-generation-context-proposed.sql',HERE.parent/'persistence/authentication-roots-proposed.sql',HERE.parent/'persistence/generation-contract-pin-proposed.sql',HERE.parent/'persistence/generation_descriptor_registry.py',HERE.parent/'persistence/context_fixture_exports.py',HERE.parent/'persistence/generation-root-proposed.sql',HERE.parent/'persistence/generation-context-role-bindings.sql',HERE.parents[3]/'audit/generated/resume-5334/sql/generation-create-persistence-proposed.sql']}}
(HERE/'postgres-retention-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':len(rows),'unexpectedAccepted':report['unexpectedAccepted']}))
