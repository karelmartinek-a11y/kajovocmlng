from pathlib import Path
import sys,subprocess,json,hashlib,re,copy,time
ROOT=Path("/workspace/kajovocmlng");OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(1,str(ROOT/'audit/generated/resume-d362/admission'))
from ssot_sources import SSOT,resource_index
from generation_retry_inventory_fixtures import fixture,ids,INVENTORY,ib
from generation_admission_contracts import canonical,digest,ContractFailure
from generation_locked_retry import hydrate_locked_scan
SQL=resource_index()['database/generation-locked-retry.sql']['raw'].decode();canonical_sql=resource_index()['database/generation-create-foundations.sql']['raw'].decode();entry=SSOT.read_bytes()
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p55432','-X','-At','-v','ON_ERROR_STOP=1'];DB='effect_order_repair_8cc'
def run(sql,db=DB):return subprocess.run(PSQL+['-d',db],input=sql,text=True,capture_output=True)
if not run("SELECT 1 FROM pg_database WHERE datname='"+DB+"'",'postgres').stdout.strip():assert run('CREATE DATABASE '+DB,'postgres').returncode==0
assert run('DROP SCHEMA IF EXISTS kcml_effect_v1 CASCADE;').returncode==0
# Reuse independent fixture assembly; replace ONLY its foundation SQL with exact
# effective embedded source. Never mutate its source files or use its database.
HERE=ROOT/'audit/generated/resume-d362/review'
program=(HERE/'verify_scoped_generation_links.py').read_text().split('# Commit the positive',1)[0]
program=program.replace('generation_independent_review_fixture',DB)
needle="ns={'__file__':str(HERE/'verify_scoped_generation_links.py')};exec"
program=program.replace(needle,"source=re.sub(r'foundation=module\\.foundations\\(\\).*?\\n','foundation=canonical_sql\\n',source,count=1)\nns={'__file__':str(HERE/'verify_scoped_generation_links.py'),'canonical_sql':canonical_sql};exec")
# Existing fixture writes assembled SQL to its events directory. Redirect that
# otherwise-shared audit write into OWN output directory.
program=program.replace("ns={'__file__':str(HERE/'verify_scoped_generation_links.py'),'canonical_sql':canonical_sql};exec", "source=source.replace(\"(HERE/'combined-foundations.sql').write_text(foundation)\",\"(own_out/'executed-canonical-foundations.sql').write_text(foundation)\")\nns={'__file__':str(HERE/'verify_scoped_generation_links.py'),'canonical_sql':canonical_sql,'own_out':own_out};exec")
namespace={'__file__':str(HERE/'verify_scoped_generation_links.py'),'canonical_sql':canonical_sql,'own_out':OUT};exec(compile(program,'own-current-canonical-fixture','exec'),namespace)
ns=namespace['ns'];assert ns['foundation']==canonical_sql
base=namespace['base'];q=run('BEGIN;'+''.join(base.values())+'COMMIT;');assert q.returncode==0,q.stderr
q=run('DROP SCHEMA IF EXISTS kcml_retry_v1 CASCADE;'+SQL);assert q.returncode==0,q.stderr
f=list(fixture());repo,phase,rd,plan,ind,physical,classifiers=f
# Ledger producer FK refers to actual newly committed canonical generation root.
job=ns['job'];phase=copy.deepcopy(phase);phase['jobId']=job;rd=digest(canonical(phase));q=ns['q'];b=ns['b']
def insert_records():
 docs={key:json.loads(repo.records[key]['bytes'])for key in [ids(520),ids(521),ids(522),ids(523)]}
 for value in docs.values():
  if 'jobId'in value:value['jobId']=job
 docs[ids(522)]['evidenceDigest']=digest(canonical(docs[ids(523)]))
 statements=[f"INSERT INTO kcml_retry_v1.phase VALUES('{phase['phaseRunId']}','{job}',{b(canonical(phase))},{b(bytes.fromhex(rd[7:]))});"]
 for key,table in [(ids(520),'operation'),(ids(521),'attempt'),(ids(522),'current_state'),(ids(523),'evidence')]:
  value=docs[key]
  raw=canonical(value);dg=hashlib.sha256(raw).digest()
  if table=='operation':head=f"'{key}','{phase['phaseRunId']}','{job}'"
  elif table=='attempt':head=f"'{key}','{ids(520)}','{phase['phaseRunId']}','{job}',1"
  elif table=='current_state':head=f"'{ids(521)}','{ids(520)}','{key}',2"
  else:head=f"'{key}','{ids(520)}','{ids(521)}'"
  statements.append(f'INSERT INTO kcml_retry_v1.{table} VALUES({head},{b(raw)},{b(dg)});')
 return ''.join(statements)
qresult=run('BEGIN;'+insert_records()+'COMMIT;');assert qresult.returncode==0,qresult.stderr
scan_sql=f"SELECT kcml_retry_v1.scan('{phase['phaseRunId']}','{job}',{b(bytes.fromhex(rd[7:]))});"
checks=[]
def check(name,ok,actual=None):checks.append({'case':name,'passed':bool(ok),'actual':actual})
def pgnegative(name,sql,code):
 r=run('BEGIN;'+sql+'ROLLBACK;');check(name,r.returncode!=0 and code in r.stderr,{'expected':code,'stderr':r.stderr[-1000:]})
r=run('BEGIN;'+scan_sql+'ROLLBACK;');assert r.returncode==0,r.stderr;scan=json.loads(next(x for x in r.stdout.splitlines()if x.startswith('{')))
actual=hydrate_locked_scan(repo,scan,INVENTORY,'2026-09-30T00:00:00.000Z',ib,plan,classifiers)
check('actual-scanned-native-bytes-to-classifier',actual['contentDecision']['operationCount']==1)
check('exact-canonical-foundations-installed',ns['foundation']==canonical_sql)
check('phase-parent-is-real-generation-root',run(f"SELECT count(*) FROM generation_job WHERE id='{job}';").stdout.strip()=='1')
pgnegative('wrong-source-lineage',scan_sql.replace(job,ids(999)),'RETRY_SOURCE_PHASE_IDENTITY')
pgnegative('source-digest-drift',scan_sql.replace(b(bytes.fromhex(rd[7:])),b(bytes(32))),'RETRY_SOURCE_PHASE_DIGEST')
pgnegative('append-only-evidence',"UPDATE kcml_retry_v1.evidence SET source_bytes=source_bytes;",'RETRY_APPEND_ONLY_SOURCE')
pgnegative('append-only-attempt',"UPDATE kcml_retry_v1.attempt SET source_bytes=source_bytes;",'RETRY_APPEND_ONLY_SOURCE')
pgnegative('state-stale-version',"UPDATE kcml_retry_v1.current_state SET state_version=2;",'RETRY_CURRENT_STATE_VERSION')
pgnegative('state-delete',"DELETE FROM kcml_retry_v1.current_state;",'RETRY_APPEND_ONLY_SOURCE')
# SQL scan rejects a perfectly schema-valid older state pointed by operation.
v=json.loads(repo.records[ids(520)]['bytes']);v['jobId']=job;v['currentAttemptStateVersion']='1';raw=canonical(v)
pgnegative('operation-older-current-pointer',f"UPDATE kcml_retry_v1.operation SET source_bytes={b(raw)},source_digest={b(hashlib.sha256(raw).digest())};"+scan_sql,'RETRY_CURRENT_LEDGER_JOIN_DRIFT')
pgnegative('deferred-current-version-commit-drift',f"UPDATE kcml_retry_v1.operation SET source_bytes={b(raw)},source_digest={b(hashlib.sha256(raw).digest())};SET CONSTRAINTS ALL IMMEDIATE;",'RETRY_DEFERRED_CURRENT_JOIN_DRIFT')
v=json.loads(repo.records[ids(520)]['bytes']);v['jobId']=job;v['targetIdempotencyKey']='different';raw2=canonical(v)
pgnegative('operation-cannot-rebind-target-key',f"UPDATE kcml_retry_v1.operation SET source_bytes={b(raw2)},source_digest={b(hashlib.sha256(raw2).digest())};",'RETRY_IMMUTABLE_OPERATION_REQUEST')
# Actual two-session lock tests: owner transaction stays open while contender
# attempts write/insert; do not use elapsed-time success as the only evidence.
for label,mutation in [('operation-update',"UPDATE kcml_retry_v1.operation SET source_bytes=source_bytes;"),('state-update',"UPDATE kcml_retry_v1.current_state SET source_bytes=source_bytes,state_version=state_version;"),('phase-delete',"DELETE FROM kcml_retry_v1.phase;"),('phase-update',"UPDATE kcml_retry_v1.phase SET source_bytes=source_bytes;")]:
 marker=OUT/(label+'.marker');marker.unlink(missing_ok=True)
 p=subprocess.Popen(PSQL+['-d',DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 p.stdin.write('BEGIN;'+scan_sql+'\\! touch '+str(marker)+'\n');p.stdin.flush()
 deadline=time.monotonic()+5
 while not marker.exists()and time.monotonic()<deadline:time.sleep(.01)
 r=run("BEGIN;SET LOCAL lock_timeout='100ms';"+mutation+'ROLLBACK;')
 check('concurrent/'+label,marker.exists() and r.returncode!=0 and 'lock timeout'in r.stderr,r.stderr[-600:])
 p.stdin.write('ROLLBACK;\n');p.stdin.close();p.wait(timeout=5);marker.unlink(missing_ok=True)
# Insert phantom with an independently valid new operation ID, same phase.
v=json.loads(repo.records[ids(520)]['bytes']);v['jobId']=job;v['operationId']=ids(540);raw=canonical(v)
marker=OUT/'phantom.marker';marker.unlink(missing_ok=True);p=subprocess.Popen(PSQL+['-d',DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
p.stdin.write('BEGIN;'+scan_sql+'\\! touch '+str(marker)+'\n');p.stdin.flush();deadline=time.monotonic()+5
while not marker.exists()and time.monotonic()<deadline:time.sleep(.01)
r=run("BEGIN;SET LOCAL lock_timeout='100ms';"+f"INSERT INTO kcml_retry_v1.operation VALUES('{ids(540)}','{phase['phaseRunId']}','{job}',{b(raw)},{b(hashlib.sha256(raw).digest())});ROLLBACK;")
check('concurrent/no-membership-phantom',marker.exists()and r.returncode!=0 and 'lock timeout'in r.stderr,r.stderr[-600:]);p.stdin.write('ROLLBACK;\n');p.stdin.close();p.wait(timeout=5);marker.unlink(missing_ok=True)
# Tampered actual scan bytes fail before content admission; valid positive first.
mutant=copy.deepcopy(scan);mutant['rows'][0]['evidenceBytes']+='20'
try:hydrate_locked_scan(repo,mutant,INVENTORY,'2026-09-30T00:00:00.000Z',ib,plan,classifiers);check('actual-row-cipher-independent-content-digest',False)
except ContractFailure as e:check('actual-row-cipher-independent-content-digest',e.code=='GENERATION_RETRY_SCAN_MEMBER_BYTES_MISMATCH',e.code)
reused_setup_checks=checks;checks=[]
encoder_resource=resource_index()['database/generation-protected-registry-link.sql']['raw'].decode();encoder_sql=encoder_resource[encoder_resource.index('CREATE FUNCTION kcml_crypto_compact_sorted_json_v1'):encoder_resource.index('CREATE FUNCTION kcml_generation_protected_registry_link_v1')]
r=run(encoder_sql);assert r.returncode==0,r.stderr
CANDIDATE=(OUT/'original-frozen.sql').read_text();r=run(CANDIDATE);assert r.returncode==0,r.stderr
# Archive current exact canonical frozen publisher resource independently.
archive=resource_index()['database/generation-frozen-archive.sql']['raw'].decode()
# Install archive AFTER existing root fixture; current fixture already has roots.
r=run(archive);assert r.returncode==0,r.stderr
r=run(f"UPDATE generation_job SET state_version=state_version+1,coordinator_lease_owner_id='{ns['owner']}',coordinator_fencing_token=7,coordinator_lease_expires_at=clock_timestamp()+interval '1hour' WHERE id='{job}';");assert r.returncode==0,r.stderr
code=run("SELECT encode(convert_to(pg_get_functiondef('kcml_effect_v1.classify_cas_v1(jsonb,bytea,text,uuid)'::regprocedure),'UTF8'),'hex');").stdout.strip();compiled=bytes.fromhex(code);cd=hashlib.sha256(compiled).digest()
r=run(f"SELECT kcml_archive_publish_v1('POLICY_IMPLEMENTATION','CAS_READ_BACK_V1',{b(cd)},{b(compiled)},'server-compiled:kcml_effect_v1.classify_cas_v1',{b(cd)});");assert r.returncode==0,r.stderr
# Compiler resolves actual archived fixture records rather booleans/digests alone.
ctx_schema=canonical({'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:synthetic-checkpoint-source:1','type':'object','additionalProperties':False,'required':['identity'],'properties':{'identity':{'type':'string'}}})
ctxsd=hashlib.sha256(ctx_schema).digest();r=run(f"SELECT kcml_archive_publish_v1('SCHEMA','urn:kcml:synthetic-checkpoint-source:1',{b(ctxsd)},{b(ctx_schema)},'synthetic-fixture',{b(ctxsd)});");assert r.returncode==0,r.stderr
refs=[]
for name in ['agent-graph','binding-set','budget']:
 ctxbytes=canonical({'identity':'synthetic-'+name});dg=hashlib.sha256(ctxbytes).digest()
 r=run(f"SELECT kcml_archive_publish_v1('DOMAIN_POLICY','synthetic-{name}',{b(dg)},{b(ctxbytes)},'synthetic-fixture',{b(dg)});");assert r.returncode==0,r.stderr
 refs.append({'recordId':'synthetic-'+name,'contentDigest':'sha256:'+dg.hex(),'schemaId':'urn:kcml:synthetic-checkpoint-source:1','schemaDigest':'sha256:'+ctxsd.hex()})
plan=copy.deepcopy(plan);plan['jobId']=job;planraw=canonical(plan);plandg=hashlib.sha256(planraw).digest()
r=run(f"SELECT kcml_archive_publish_v1('DOMAIN_POLICY','{plan['planId']}',{b(plandg)},{b(planraw)},'synthetic-actual-native-plan',{b(plandg)});");assert r.returncode==0,r.stderr
specdg=bytes.fromhex(phase['specificationDigest'][7:])
r=run(f"UPDATE generation_job SET state_version=state_version+1,approved_spec_revision_id='{ids(880)}',approved_specification_digest={b(specdg)},current_plan_id='{plan['planId']}' WHERE id='{job}';INSERT INTO kcml_effect_v1.checkpoint_context VALUES('{job}','{ids(880)}',{b(specdg)},'{plan['planId']}',{b(plandg)},{q(json.dumps(refs[0]))}::jsonb,{q(json.dumps(refs[1]))}::jsonb,{q(json.dumps(refs[2]))}::jsonb,1,'[]','[]','[]','[]');");assert r.returncode==0,r.stderr
ledger_phase=copy.deepcopy(phase);ledger_phase.update(phaseRunId=ids(885),state='RUNNING');plan=copy.deepcopy(plan);plan['jobId']=job;ledger_phase['planDigest']=digest(canonical(plan));phase=ledger_phase
r=run(f"UPDATE generation_job SET state_version=state_version+1,active_phase_run_id='{phase['phaseRunId']}' WHERE id='{job}';SELECT kcml_effect_v1.begin_phase('{phase['phaseRunId']}','{job}',{b(canonical(plan))},{b(bytes.fromhex(phase['specificationDigest'][7:]))});");assert r.returncode==0,r.stderr
op,aid,obox,ev,cp=[ids(800+i)for i in range(5)];claim=hashlib.sha256(b'synthetic-concurrency-key').digest()
r=run(f"INSERT INTO kcml_effect_v1.concurrency_claim VALUES({b(claim)},'{ns['owner']}',3,clock_timestamp()+interval '1hour');");assert r.returncode==0,r.stderr
request=canonical({'beforeVersion':'7','beforeValueDigest':digest(b'old synthetic value'),'targetKey':'fixed-target'});requestdg=digest(request)
def checkpoint(seq):return canonical({'parentId':job,'stateVersion':'2','fence':'7','incarnation':ns['owner'],'sequence':str(seq),'operationId':op})
intent=f"SELECT kcml_effect_v1.record_intent('{op}','{phase['phaseRunId']}','{job}','{ns['op']}','SyntheticBuild','{aid}','{obox}','{ev}','{cp}',{b(request)},'{ids(824)}','{ids(825)}','fixed-target',7,0,clock_timestamp()+interval '1hour',{b(claim)},'{ns['owner']}',3,{b(cd)},NULL);"

trace_sql="""CREATE TABLE kcml_effect_v1.order_trace(n bigint GENERATED ALWAYS AS IDENTITY,kind text,ordinal int,row_id uuid);
CREATE FUNCTION kcml_effect_v1.record_order_trace() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN INSERT INTO kcml_effect_v1.order_trace(kind,ordinal,row_id)VALUES(TG_ARGV[0],TG_ARGV[1]::int,(to_jsonb(NEW)->>TG_ARGV[2])::uuid);RETURN NEW;END $$;
CREATE TRIGGER debug_order AFTER INSERT ON kcml_effect_v1.operation FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.record_order_trace('OPERATION','140','id');
CREATE TRIGGER debug_order AFTER INSERT ON kcml_effect_v1.attempt FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.record_order_trace('ATTEMPT','150','id');
CREATE TRIGGER debug_order AFTER INSERT ON kcml_effect_v1.state FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.record_order_trace('STATE','150','state_id');
CREATE TRIGGER debug_order AFTER INSERT ON kcml_effect_v1.checkpoint FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.record_order_trace('CHECKPOINT','50','id');
"""
r=run(trace_sql);assert r.returncode==0,r.stderr
r=run('BEGIN;'+intent+'SET CONSTRAINTS ALL IMMEDIATE;COMMIT;');assert r.returncode==0,r.stderr
rows=run("SELECT json_agg(t ORDER BY n)FROM kcml_effect_v1.order_trace t;").stdout.strip();v=json.loads(rows);assert [x['ordinal']for x in v]==[140,150,150,50];(OUT/'original-order-gap.json').write_text(json.dumps({'postgresVersion':run('SHOW server_version;').stdout.strip(),'actualInsertOrder':v,'reproduced':'H140,H150 before new H50 checkpoint','candidateHash':hashlib.sha256(CANDIDATE.encode()).hexdigest()},indent=2)+'\n');print('GAP_REPRODUCED')
