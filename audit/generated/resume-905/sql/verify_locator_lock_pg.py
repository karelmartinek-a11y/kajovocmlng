"""Exact canonical foundation/preroot/auth SQL plus bounded locator candidate."""
from pathlib import Path
import sys,subprocess,json,hashlib,time,os,uuid
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
rs=resource_index();entry=SSOT.read_bytes();db='locator_helpers_905'
psql=['/tmp/kcml-pg18/bin/psql','-X','-h','/tmp/kcml-pg18-socket','-p','55432','-d','postgres','-At','-q','-v','ON_ERROR_STOP=1']
def admin(s):return subprocess.run(psql,input=s,text=True,capture_output=True)
if not admin("SELECT 1 FROM pg_database WHERE datname='"+db+"'").stdout.strip():assert admin('CREATE DATABASE '+db).returncode==0
psql[7]=db
def run(s):return subprocess.run(psql,input=s,text=True,capture_output=True)
assert run('DROP SCHEMA public CASCADE;CREATE SCHEMA public').returncode==0
sql=b''.join(rs[x]['raw'] for x in ['database/generation-create-foundations.sql','database/generation-create-preroot.sql','database/generation-create-authentication.sql'])
r=run(sql.decode());assert r.returncode==0,r.stderr
# Reuse reviewed positive fixture setup; adaptation isolated here, no writes in its directory.
old=ROOT/'audit/generated/resume-34d/failure-sql/verify_failure_before_root.py'
text=old.read_text();text=text[text.index('# Reuse exact current native positive'):text.index('\nchecks=[]')]
ns=dict(ROOT=ROOT,SSOT=SSOT,HERE=HERE,Path=Path,sys=sys,subprocess=subprocess,json=json,hashlib=hashlib,struct=__import__('struct'),copy=__import__('copy'),time=time)
exec(text,ns)
# Fresh authentication receipt includes actual constructor-required request/descriptor/epoch binding.
ns['authsql']=ns['authsql'].replace('api_credential_fingerprint,accepted_at)VALUES','api_credential_fingerprint,accepted_at,authenticated_request_digest,authenticated_descriptor_digest,api_credential_activation_epoch)VALUES')
needle="'synthetic-fingerprint',clock_timestamp());"
ns['authsql']=ns['authsql'].replace(needle,"'synthetic-fingerprint',clock_timestamp(),"+ns['b'](ns['ns']['request_digest'])+','+ns['b'](ns['ns']['dd'])+',1);')
base=ns['parts']();r=run('BEGIN;'+''.join(base.values())+'SET CONSTRAINTS ALL IMMEDIATE;COMMIT;');assert r.returncode==0,r.stderr
candidate=(HERE/'generation-locator-lock-proposed.sql').read_bytes();embedded=rs.get('database/generation-locator-lock.sql');extension=embedded['raw']if embedded else candidate;assert extension==candidate,'CANONICAL_LOCATOR_CANDIDATE_BYTE_MISMATCH';r=run(extension.decode());assert r.returncode==0,r.stderr
checks=[]
def check(id,good,**data):checks.append(dict(id=id,passed=bool(good),**data))
context=run('SELECT id FROM generation_create_trusted_context').stdout.strip();invoke="SELECT logical_operation_id,state FROM kcml_generation_lock_retained_locator_v1('"+context+"');"
r=run('BEGIN;'+invoke+'COMMIT;');check('actual-retained-failure-hydrates-original-idempotency',r.returncode==0 and r.stdout.strip()==ns['op']+'|FAILED_FINAL')
r=run("BEGIN;SELECT * FROM kcml_generation_lock_retained_locator_v1('ffffffff-ffff-4fff-8fff-ffffffffffff');COMMIT;");check('missing-context-specific-rejection',r.returncode!=0 and 'GENERATION_LOCK_CONTEXT_UNRESOLVED'in r.stderr,positiveWitness='actual-retained-failure-hydrates-original-idempotency')
# Positive-derived mutant context stays exact schema/constraints and authenticated digest.
# Insert another trusted receipt + context for same client key but different request.
import re
mut=ns['authsql'].replace(ns['auth'],'10000000-0000-4000-8000-000000000007');mut=mut[mut.index('INSERT INTO generation_create_authentication_acceptance'):]
wrong=bytes([1])*32;mut=mut.replace(ns['b'](ns['ns']['request_digest']),ns['b'](wrong))
call=ns['contextsql'].replace(ns['auth'],'10000000-0000-4000-8000-000000000007').replace(ns['ns']['request_digest'].hex(),wrong.hex())
r=run('BEGIN;'+mut+call+"SELECT * FROM kcml_generation_lock_retained_locator_v1((SELECT id FROM generation_create_trusted_context WHERE authentication_acceptance_id='10000000-0000-4000-8000-000000000007'));ROLLBACK;")
check('same-key-different-authenticated-request-conflicts',r.returncode!=0 and 'IDEMPOTENCY_CONFLICT'in r.stderr,positiveWitness='actual-retained-failure-hydrates-original-idempotency')
# Existing terminal replay locks C0 then C1; no root/event creation/rewrite.
before=run('SELECT (SELECT count(*) FROM generation_job),(SELECT count(*) FROM domain_event),(SELECT count(*) FROM domain_command)').stdout
for _ in range(2):assert run('BEGIN;'+invoke+'COMMIT').returncode==0
check('terminal-replay-no-root-event-command-duplication',before==run('SELECT (SELECT count(*) FROM generation_job),(SELECT count(*) FROM domain_event),(SELECT count(*) FROM domain_command)').stdout)
# Two genuine DB sessions contend on same physical locator, not only advisory codec.
tag='locator_'+uuid.uuid4().hex[:8];holder=subprocess.Popen(psql,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=dict(os.environ,PGAPPNAME=tag))
holder.stdin.write('BEGIN;'+invoke+'\n');holder.stdin.flush()
locked=False
for _ in range(50):
 if run("SELECT count(*) FROM pg_locks l JOIN pg_stat_activity a USING(pid) WHERE a.application_name='"+tag+"' AND l.relation='idempotency_locator'::regclass AND l.granted").stdout.strip()!='0':locked=True;break
 time.sleep(.02)
r=run("BEGIN;SET LOCAL lock_timeout='100ms';"+invoke+'COMMIT;');check('concurrent-replay-waits-real-locator',locked and r.returncode!=0 and 'lock timeout'in r.stderr)
holder.stdin.write('ROLLBACK;\n');holder.stdin.close();holder.wait(timeout=5)
r=run('BEGIN;'+invoke+'COMMIT;');check('rollback-holder-allows-original-replay',r.returncode==0 and ns['op']in r.stdout)
check('public-execute-revoked',run("SELECT has_function_privilege('public','kcml_generation_lock_retained_locator_v1(uuid)','EXECUTE')").stdout.strip()=='f')
report=dict(entryCommit='905555e47f3547516439a699e262df62cbbec229',sourceDocumentSha256=hashlib.sha256(entry).hexdigest(),sourceUnchangedDuringRun=entry==SSOT.read_bytes(),consumedResources={x:rs[x]['sha256']for x in ['database/generation-create-foundations.sql','database/generation-create-preroot.sql','database/generation-create-authentication.sql']},candidateSqlSha256=hashlib.sha256(candidate).hexdigest(),canonicalEmbeddedBytesExecuted=embedded is not None,postgresVersion=run('SHOW server_version').stdout.strip(),checks=checks,failed=sum(not x['passed']for x in checks),scope='Bounded canonical trusted-context -> stable locator -> retained domain idempotency row locks and actual failure receipt. Authentication setup synthetic server fixture, not API-token proof. Fresh missing-locator claim, archive producer and source/root/child transaction remain OPEN.',wholeOperationClosed=False)
(HERE/'locator-lock-postgres-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(checks),'failed':report['failed']}))
for x in checks:
 if not x['passed']:print(x)
raise SystemExit(bool(report['failed']))
