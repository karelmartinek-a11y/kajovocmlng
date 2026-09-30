from pathlib import Path
import sys,subprocess,json,hashlib,struct,copy,time
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p55432','-d','postgres','-X','-At','-v','ON_ERROR_STOP=1']
q=subprocess.run(PSQL,input="SELECT 1 FROM pg_database WHERE datname='failure_sql_34d';",capture_output=True,text=True)
if not q.stdout.strip():
 q=subprocess.run(PSQL,input='CREATE DATABASE failure_sql_34d;',capture_output=True,text=True);assert q.returncode==0,q.stderr
PSQL[5]='failure_sql_34d'
def run(s):return subprocess.run(PSQL,input=s,capture_output=True,text=True)
q=run('DROP SCHEMA public CASCADE; CREATE SCHEMA public;');assert q.returncode==0,q.stderr
input_source=SSOT.read_bytes();resources=resource_index();canonical=resources['database/generation-create-foundations.sql']['raw'];candidate=(HERE/'failure-before-root-extension.sql').read_bytes();preroot_resource=resources.get('database/generation-create-preroot.sql');extension=preroot_resource['raw']if preroot_resource else candidate
if preroot_resource:assert extension==candidate,'EMBEDDED_PREROOT_PROPOSAL_BYTES_DIFFER'
q=run(canonical.decode()+extension.decode());assert q.returncode==0,q.stderr
# Reuse exact current native positive with full authentication/context pin producer.
source=(ROOT/'audit/generated/resume-d362/events/verify_combined_generation.py').read_text().split('checks=[]')[0]
source=source.replace("'generation_combined_fixture'","'failure_sql_34d'")
source=source.replace('from ssot_sources import resource_index,SSOT','from ssot_sources import resource_index,SSOT\nsys.path.insert(0,str(ROOT/"audit/generated/resume-d362/persistence"))\nfrom generation_descriptor_registry import pin,descriptor as pinned_descriptor\nfrom context_fixture_exports import common as auth_common,call as auth_call')
source=source.replace("descriptor=canonical_bytes(freeze_descriptor(native,{'owner':owner},'fixture-pinned-v1'));","pinned=pin();descriptor=pinned_descriptor(owner,'sha256:'+key.hex(),pinned);")
ns={'__file__':str(ROOT/'audit/generated/resume-d362/events/verify_combined_generation.py')};exec(source,ns)
b=ns['b'];owner=ns['owner'];op=ns['op'];job=ns['job'];snap=ns['snap'];auth=ns['auth'];audit=ns['audit'];context=ns['context'] if 'context' in ns else '(SELECT id FROM generation_create_trusted_context LIMIT 1)'
authsql=ns['auth_common'](owner,owner,1)+f"INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,state_version,credential_activation_epoch,created_at) VALUES(1,'90000000-0000-4000-8000-000000000001','90000000-0000-4000-8000-000000000002','SYNTHETIC_HASH_NOT_VERIFIER','synthetic-fingerprint',1,0,1,clock_timestamp());INSERT INTO generation_create_authentication_acceptance(id,owner_id,access_channel,api_credential_version,api_credential_fingerprint,accepted_at)VALUES('{auth}','{owner}','OWNER_API_KEY',1,'synthetic-fingerprint',clock_timestamp());"
contextsql=ns['auth_call'](owner,auth,ns['request_digest'].hex(),'sha256:'+ns['key'].hex())
def parts(state='FAILED',terminal=True,directive='DO_NOT_RETRY'):
 from create_completion_contracts import ERRORS,semantic_result
 from jsonschema import Draft202012Validator,FormatChecker
 stable='CREATE_CANCELLED' if state=='CANCELLED' else 'SIDE_EFFECT_OUTCOME_UNKNOWN' if directive=='RECONCILE_THEN_RETRY' else 'CREATE_PERSISTENCE_FAILED' if directive=='RETRY_SAME_OPERATION' else 'CREATE_POLICY_UNRESOLVED'
 er=next(x for x in ERRORS if x['stableCode']==stable)
 error={k:er[k]for k in ['stableCode','classification','retryDirective']};error.update(message='Synthetic fixture retained error.',detailsDigest=None)
 response=copy.deepcopy(ns['response']);response.update(status=state,terminal=terminal,output=None,error=error if state!='ACCEPTED' else None,stateVersion=None,eventSequence=None)
 response['resultDigest']=ns['canonical_digest'](semantic_result(response))
 assert Draft202012Validator(ns['row']['responseSchema'],format_checker=FormatChecker()).is_valid(response),'INVALID_POSITIVE_NATIVE_RESPONSE'
 semantic=semantic_result(response)
 raw=ns['canonical_bytes'](semantic);digest=hashlib.sha256(raw).digest();ab=ns['canonical_bytes']({'objectId':op,'actorId':owner,'logicalOperationId':op,'afterDigest':'sha256:'+digest.hex(),'previousHash':'sha256:'+'00'*32,'chainSequence':'1'})
 ah=hashlib.sha256(b'KCML-AUDIT-CHAIN'+struct.pack('>I',1)+bytes(32)+struct.pack('>q',1)+struct.pack('>q',len(ab))+ab).digest()
 idem='FAILED_FINAL' if terminal and state=='FAILED' else 'CANCELLED_FINAL' if terminal else 'EXECUTING' if state=='ACCEPTED' else 'WAITING_FOR_RECONCILIATION' if directive=='RECONCILE_THEN_RETRY' else 'EXECUTING'
 cmd=f"INSERT INTO domain_command VALUES('{op}','generation.job.create','{owner}',{b(ns['request_digest'])},{b(ns['descriptor'])},{b(ns['dd'])},'{state}',{str(terminal).lower()},1,{b(digest)},'{owner}',1,clock_timestamp(),clock_timestamp(),'{op}','{ns['pinned']['operationRevision']}','OWNER_API_KEY',{context},'GENERATION_JOB','{job}','{snap}',{b(ns['scope'])},{b(ns['key'])},NULL,NULL,NULL,NULL,NULL,NULL,'{op}',NULL,clock_timestamp(),{'clock_timestamp()' if terminal else 'NULL'},NULL);"
 return {'auth':authsql,'context':contextsql,'command':cmd,'snapshot':f"INSERT INTO generation_create_preroot_snapshot VALUES('{snap}','{op}','{job}',{context},'urn:kcml:r9:semantic:route.0215:body',{b(hashlib.sha256(ns['canonical_bytes'](ns['row']['requestSchema']['properties']['body'])).digest())},{b(ns['initialdigest'])},decode('0102','hex'),decode('03','hex'),'FIXTURE_OPAQUE_NOT_CRYPTO','FIXTURE_ONLY',{b(bytes.fromhex('04'*32))},clock_timestamp());",'locator':f"INSERT INTO idempotency_locator VALUES('{ns['locatorid']}','GENERATION','OWNER_FULL','{owner}','CREATE_ROOT','generation_job',{b(ns['key'])},'{op}',{b(ns['request_digest'])},{b(ns['dd'])},{b(ns['scope'])},clock_timestamp(),clock_timestamp(),clock_timestamp()+interval '1day');",'idempotency':f"INSERT INTO domain_idempotency_record VALUES({b(ns['scope'])},{b(ns['key'])},{b(ns['request_digest'])},'{op}','{idem}',1,{b(digest)});",'outcome':f"INSERT INTO generation_create_preroot_outcome VALUES('{op}',1,{b(raw)},{b(digest)},'{audit}');",'audit':f"SELECT * FROM audit_head WHERE singleton_key=1 FOR UPDATE;INSERT INTO audit_event VALUES('{audit}',1,{b(bytes(32))},{b(ah)},1,'{op}',NULL,{b(ab)},false);UPDATE audit_head SET last_sequence=1,last_hash={b(ah)},state_version=1;"}
checks=[]
def case(name,ps,expected=None,commit=False):
 q=run('BEGIN;'+''.join(ps.values())+'SET CONSTRAINTS ALL IMMEDIATE;'+('COMMIT;' if commit else 'ROLLBACK;'))
 checks.append({'case':name,'passed':q.returncode==0 if expected is None else q.returncode!=0 and expected in q.stderr,'expectedDiagnostic':expected,'actualDiagnostic':q.stderr[-1200:]});return q
def content_mutant(ps,change):
 import re
 wrong=ps.copy();groups=re.findall("decode\\('([0-9a-f]+)','hex'\\)",ps['outcome']);oldraw=bytes.fromhex(groups[0]);oldhash=hashlib.sha256(oldraw).digest()
 j=json.loads(oldraw);change(j);raw=ns['canonical_bytes'](j);newhash=hashlib.sha256(raw).digest()
 wrong['outcome']=wrong['outcome'].replace(b(oldraw),b(raw)).replace(b(oldhash),b(newhash))
 for k in ['command','idempotency']:wrong[k]=wrong[k].replace(b(oldhash),b(newhash))
 ab=ns['canonical_bytes']({'objectId':op,'actorId':owner,'logicalOperationId':op,'afterDigest':'sha256:'+newhash.hex(),'previousHash':'sha256:'+'00'*32,'chainSequence':'1'})
 ah=hashlib.sha256(b'KCML-AUDIT-CHAIN'+struct.pack('>I',1)+bytes(32)+struct.pack('>q',1)+struct.pack('>q',len(ab))+ab).digest()
 wrong['audit']=f"SELECT * FROM audit_head WHERE singleton_key=1 FOR UPDATE;INSERT INTO audit_event VALUES('{audit}',1,{b(bytes(32))},{b(ah)},1,'{op}',NULL,{b(ab)},false);UPDATE audit_head SET last_sequence=1,last_hash={b(ah)},state_version=1;"
 return wrong
base=parts();case('retained-failure-before-root',base)
case('accepted-pending-before-root',parts('ACCEPTED',False))
case('unknown-keeps-same-operation-nonterminal',parts('FAILED',False,'RECONCILE_THEN_RETRY'))
case('cancel-wins-before-root',parts('CANCELLED',True))
case('known-rollback-retry-same-operation-not-terminal',parts('FAILED',False,'RETRY_SAME_OPERATION'))
for name,mut in [('unknown-stable-error',lambda j:j['error'].update(stableCode='UNDECLARED')),('wrong-error-classification',lambda j:j['error'].update(classification='CONFLICT')),('error-extra-sensitive-field',lambda j:j['error'].update(secretValue='SYNTHETIC_ONLY')),('terminal-string-not-boolean',lambda j:j.update(terminal='true')),('wrong-route-identity',lambda j:j.update(routeId='route.0386'))]:case(name,content_mutant(base,mut),'GENERATION_PREROOT_NATIVE_OUTCOME_INVALID')
for key in ['snapshot','outcome','audit','locator','idempotency']:
 case('missing-'+key,{k:v for k,v in base.items()if k!=key},'GENERATION_COMMAND_TYPED_BINDING_REQUIRED' if key=='snapshot' else 'GENERATION_PREROOT_RETAINED_OUTCOME_REQUIRED' if key in ['outcome','audit'] else 'GENERATION_PREROOT_ATOMIC_CLOSURE_INCOMPLETE')
wrong=base.copy();wrong['snapshot']=wrong['snapshot'].replace("'"+job+"'","'99999999-9999-4999-8999-999999999999'");case('wrong-prospective-job',wrong,'GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID')
wrong=base.copy();wrong['idempotency']=wrong['idempotency'].replace('FAILED_FINAL','SUCCEEDED');case('failure-cannot-retain-success-idempotency',wrong,'GENERATION_PREROOT_ATOMIC_CLOSURE_INCOMPLETE')
wrong=base.copy();wrong['locator']=wrong['locator'].replace("'CREATE_ROOT'","'TARGET'");case('wrong-locator-business-scope',wrong,'GENERATION_PREROOT_ATOMIC_CLOSURE_INCOMPLETE')
case('known-rollback-persists-nothing',base)
q=run('SELECT (SELECT count(*) FROM domain_command),(SELECT count(*) FROM generation_job),(SELECT count(*) FROM audit_event);');checks.append({'case':'rollback-no-partial-records','passed':q.stdout.strip()=='0|0|0'})
case('commit-exact-retained-failure',base,commit=True)
q=run('SELECT (SELECT count(*) FROM generation_job),(SELECT count(*) FROM domain_event),(SELECT count(*) FROM transactional_outbox),(SELECT count(*) FROM generation_create_preroot_outcome);');checks.append({'case':'failure-no-root-no-created-event-no-delivery','passed':q.stdout.strip()=='0|0|0|1'})
for name,sql,expected in [('terminal-command-rewrite',"UPDATE domain_command SET state='SUCCEEDED';",'CREATE_COMMAND_FROZEN_SCOPE'),('retained-outcome-rewrite',"UPDATE generation_create_preroot_outcome SET canonical_bytes=convert_to('{}','UTF8');",'CREATE_IMMUTABLE_RECORD'),('retained-outcome-delete','DELETE FROM generation_create_preroot_outcome;','CREATE_IMMUTABLE_RECORD'),('snapshot-delete','DELETE FROM generation_create_preroot_snapshot;','CREATE_IMMUTABLE_RECORD')]:case(name,{'mutation':sql},expected)
q=run(f"BEGIN;SELECT logical_operation_id FROM idempotency_locator WHERE client_key_digest={b(ns['key'])} FOR UPDATE;SELECT encode(canonical_bytes,'hex') FROM generation_create_preroot_outcome WHERE logical_operation_id='{op}';COMMIT;");checks.append({'case':'lost-response-read-original-retained-bytes','passed':q.returncode==0 and ns['op'] in q.stdout and len(q.stdout.splitlines())>=2})
marker=HERE/'retained-lock.marker'
marker.unlink(missing_ok=True)
holder=subprocess.Popen(PSQL,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
holder.stdin.write("BEGIN;SELECT logical_operation_id FROM idempotency_locator FOR UPDATE;\\! touch "+str(marker)+"\nSELECT pg_sleep(0.35);COMMIT;");holder.stdin.close()
deadline=time.monotonic()+3
while not marker.exists() and time.monotonic()<deadline:time.sleep(.02)
t0=time.monotonic();q=run(f"BEGIN;SELECT CASE WHEN client_request_digest={b(ns['request_digest'])} THEN 'FROZEN_FAILURE_REPLAY' ELSE 'IDEMPOTENCY_CONFLICT' END FROM idempotency_locator WHERE client_key_digest={b(ns['key'])} FOR UPDATE;COMMIT;");elapsed=time.monotonic()-t0
holder.wait(timeout=5);checks.append({'case':'two-process-retained-replay-waits-original-locator-lock','passed':marker.exists() and holder.returncode==0 and q.returncode==0 and 'FROZEN_FAILURE_REPLAY'in q.stdout and elapsed>.15,'elapsedSeconds':elapsed});marker.unlink(missing_ok=True)
q=run(f"BEGIN;SELECT CASE WHEN client_request_digest={b(bytes(32))} THEN 'FROZEN_REPLAY' ELSE 'IDEMPOTENCY_CONFLICT' END FROM idempotency_locator WHERE client_key_digest={b(ns['key'])} FOR UPDATE;COMMIT;");checks.append({'case':'different-request-digest-same-locator-conflicts-without-new-root','passed':q.returncode==0 and 'IDEMPOTENCY_CONFLICT'in q.stdout})
report={'inputHead':'34d3a75c47a92ab7d8e0dac84f581549a15445ca','sourceSha256':hashlib.sha256(input_source).hexdigest(),'canonicalSqlSha256':hashlib.sha256(canonical).hexdigest(),'extensionSqlSha256':hashlib.sha256(extension).hexdigest(),'prerootEmbeddedBytesExecuted':preroot_resource is not None,'postgresqlVersion':run('SHOW server_version;').stdout.strip(),'checks':checks,'failed':sum(not x['passed']for x in checks),'wholeOperationClosed':False,'crypto':'OPAQUE_FIXTURE_NOT_CRYPTO','authentication':'SERVER_ACCEPTANCE_ROW_FIXTURE_NOT_REAL_TOKEN_VERIFIER','scope':'Exact canonical foundation SQL; prereoot embedded bytes executed and candidate equality asserted if resource present, otherwise clearly labeled proposal; no created event invented'}
report['sourceUnchangedDuringRun']=input_source==SSOT.read_bytes();report['supportSha256']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),ROOT/'scripts/create_completion_contracts.py',ROOT/'scripts/create_operation_contracts.py',ROOT/'audit/generated/resume-d362/events/verify_combined_generation.py',ROOT/'audit/generated/resume-d362/persistence/generation_descriptor_registry.py',ROOT/'audit/generated/resume-d362/persistence/context_fixture_exports.py',ROOT/'requirements-audit.txt']}
report['status']='PASS'if report['failed']==0 and report['sourceUnchangedDuringRun']else'BLOCKED'
(HERE/'failure-before-root-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(checks),'failed':report['failed']}))
for c in checks:
 if not c['passed']:print(c)
