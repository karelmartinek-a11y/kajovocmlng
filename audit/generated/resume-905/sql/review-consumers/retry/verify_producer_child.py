from pathlib import Path
import sys,subprocess,json,hashlib,re,copy,time
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(1,str(ROOT/'audit/generated/resume-d362/admission'))
from ssot_sources import SSOT,resource_index
from generation_retry_inventory_fixtures import fixture,ids,INVENTORY,ib
from generation_admission_contracts import canonical,digest,ContractFailure
from generation_locked_retry import hydrate_locked_scan
SQL=resource_index()['database/generation-locked-retry.sql']['raw'].decode();canonical_sql=resource_index()['database/generation-create-foundations.sql']['raw'].decode();entry=SSOT.read_bytes()
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p55432','-X','-At','-v','ON_ERROR_STOP=1'];DB='retry_independent_sql_905'
def run(sql,db=DB):return subprocess.run(PSQL+['-d',db],input=sql,text=True,capture_output=True)
if not run("SELECT 1 FROM pg_database WHERE datname='"+DB+"'",'postgres').stdout.strip():assert run('CREATE DATABASE '+DB,'postgres').returncode==0
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
# Candidate extension with exact canonical foundations/locked scan; candidate is
# not passed off as canonical, and fixture auth/opaque snapshot remain synthetic.
SQL2=resource_index()['database/generation-retry-producer-child.sql']['raw'].decode();assert SQL2.encode()==(OUT/'producer-child.sql').read_bytes(),'CANONICAL_RETRY_CANDIDATE_BYTE_MISMATCH';r=run(SQL2);assert r.returncode==0,r.stderr
r=run(f"UPDATE generation_job SET state_version=state_version+1,coordinator_lease_owner_id='{ns['owner']}',coordinator_fencing_token=7,coordinator_lease_expires_at=clock_timestamp()+interval '1hour' WHERE id='{job}';");assert r.returncode==0,r.stderr
child=ids(600)
reserve=f"SELECT kcml_retry_v1.reserve_child('{child}','{phase['phaseRunId']}','{job}',{b(bytes.fromhex(rd[7:]))},7);"
pgnegative('reservation-without-child-cannot-commit',reserve+'SET CONSTRAINTS ALL IMMEDIATE;','child_scan_child_job_id_fkey')
pgnegative('stale-source-fence',reserve.replace(',7);',',6);'),'RETRY_SOURCE_FENCE_STALE')
pgnegative('incomplete-membership',"ALTER TABLE kcml_retry_v1.phase_membership DISABLE TRIGGER membership_immutable;DELETE FROM kcml_retry_v1.phase_membership;"+reserve,'RETRY_PHASE_MEMBERSHIP_INCOMPLETE')
pgnegative('expired-source-lease',f"UPDATE generation_job SET state_version=state_version+1,coordinator_lease_expires_at=clock_timestamp()-interval '1second' WHERE id='{job}';"+reserve,'RETRY_SOURCE_FENCE_STALE')
vstate=json.loads(repo.records[ids(522)]['bytes']);vstate.update(state='UNKNOWN',stateVersion='3');sr=canonical(vstate)
vop=json.loads(repo.records[ids(520)]['bytes']);vop.update(jobId=job,state='UNKNOWN',currentAttemptStateVersion='3');orr=canonical(vop)
pgnegative('unfinished-source-producer-does-not-reserve-child',f"UPDATE kcml_retry_v1.current_state SET state_version=3,source_bytes={b(sr)},source_digest={b(hashlib.sha256(sr).digest())};UPDATE kcml_retry_v1.operation SET source_bytes={b(orr)},source_digest={b(hashlib.sha256(orr).digest())};"+reserve,'RETRY_SOURCE_PRODUCER_INCOMPLETE')
# Build actual RETRY physical completion from existing canonical bounded fixture.
# This exercises all command/event/outbox/audit/locator closure bytes together.
# Native request/schema admission and opaque snapshot crypto are NOT proved here.
oldid={k:ns[k]for k in ['op','job','eventid','out','auth','snap','audit','locatorid']}
newid={k:ids(600+i) for i,k in enumerate(oldid)};newid['job']=child
newkey=hashlib.sha256(b'retry-child-905').digest()
desc=ns['pinned_descriptor'](ns['owner'],'sha256:'+newkey.hex(),ns['pinned']);newdesc=desc;newscope=hashlib.sha256(newdesc).digest()
parts={k:v for k,v in base.items() if k!='auth'}
for k,v in list(parts.items()):
 for label,old in oldid.items():v=v.replace(old,newid[label])
 for old,new in [(ns['descriptor'],newdesc),(ns['dd'],newscope),(ns['scope'],newscope),(ns['key'],newkey)]:v=v.replace(b(old),b(new))
 v=v.replace(ns['context'],f"(SELECT id FROM generation_create_trusted_context WHERE execution_descriptor_digest={b(newscope)})")
 v=v.replace('combined-reference-key','retry-child-905')
 parts[k]=v
# Source auth acceptance remains synthetic as explicit bounded fixture mechanism.
parts={'auth':f"INSERT INTO generation_create_authentication_acceptance(id,owner_id,access_channel,api_credential_version,api_credential_fingerprint,accepted_at)VALUES('{newid['auth']}','{ns['owner']}','OWNER_API_KEY',1,'synthetic-fingerprint',clock_timestamp());",**parts}
parts['root']=parts['root'].replace("'CREATE','PLATFORM_COMPONENT'","'RETRY','PLATFORM_COMPONENT'").replace('kind,target_kind,state','kind,target_kind,parent_job_id,state').replace("'RETRY','PLATFORM_COMPONENT','DISCUSSING'",f"'RETRY','PLATFORM_COMPONENT','{job}','DISCUSSING'")
response=copy.deepcopy(ns['response']);response['output']['jobId']=child;response['output']['kind']='RETRY';response['output']['parentJobId']=job
receipt=canonical(response['output']);pd=hashlib.sha256(receipt).digest();sem=canonical(ns['semantic_result'](response));resultdg=hashlib.sha256(sem).digest()
for k,v in list(parts.items()):
 for old,new in [(ns['receipt'],receipt),(ns['pd'],pd),(ns['sem'],sem),(ns['rd'],resultdg)]:v=v.replace(b(old),b(new))
 parts[k]=v
ab=copy.deepcopy(ns['auditbody']);ab.update(chainSequence='2',previousHash='sha256:'+ns['ah'].hex(),eventId=newid['eventid'],logicalOperationId=newid['op'],objectId=child,afterDigest='sha256:'+pd.hex(),correlationId=newid['op']);abr=canonical(ab)
import struct
ah=hashlib.sha256(b'KCML-AUDIT-CHAIN'+struct.pack('>I',1)+ns['ah']+struct.pack('>q',2)+struct.pack('>q',len(abr))+abr).digest()
parts['audit']=f"SELECT * FROM audit_head WHERE singleton_key=1 FOR UPDATE;INSERT INTO audit_event VALUES('{newid['audit']}',2,{b(ns['ah'])},{b(ah)},1,'{newid['op']}','{newid['eventid']}',{b(abr)},false);UPDATE audit_head SET last_sequence=2,last_hash={b(ah)},state_version=state_version+1 WHERE singleton_key=1;"
childsql=''.join(parts.values())
pgnegative('child-without-scan-cannot-insert',childsql,'RETRY_CHILD_SCAN_TRANSACTION_REQUIRED')
pgnegative('child-without-event-rolls-back',reserve+''.join(v for k,v in parts.items()if k!='event')+'SET CONSTRAINTS ALL IMMEDIATE;','transactional_outbox_event_id_fkey')
# Real concurrent writer/second RETRY transaction stays blocked through child
# root publication; session holder then rolls back and no partial child remains.
for name,contender in [('second-retry',reserve),('source-fence-change',f"UPDATE generation_job SET state_version=state_version+1,coordinator_fencing_token=8 WHERE id='{job}';")]:
 marker=OUT/(name+'.marker');marker.unlink(missing_ok=True)
 holder=subprocess.Popen(PSQL+['-d',DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 holder.stdin.write('BEGIN;'+reserve+childsql+'\\! touch '+str(marker)+'\n');holder.stdin.flush();deadline=time.monotonic()+5
 while not marker.exists() and time.monotonic()<deadline:time.sleep(.01)
 r=run("BEGIN;SET LOCAL lock_timeout='100ms';"+contender+'ROLLBACK;')
 check('concurrent-child-transaction/'+name,marker.exists() and r.returncode!=0 and 'lock timeout' in r.stderr,r.stderr[-500:])
 holder.stdin.write('ROLLBACK;\n');holder.stdin.close();holder.wait(timeout=5);marker.unlink(missing_ok=True)
 check('rollback-no-child-or-reservation/'+name,run(f"SELECT (SELECT count(*) FROM generation_job WHERE id='{child}')+(SELECT count(*) FROM kcml_retry_v1.child_scan WHERE child_job_id='{child}');").stdout.strip()=='0')
holder=subprocess.Popen(PSQL+['-d',DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
holder.stdin.write('BEGIN;'+reserve+'\n');holder.stdin.flush()
while True:
 line=holder.stdout.readline()
 if not line:raise AssertionError('scan holder ended before actual locked rows returned')
 if line.startswith('{'):locked_scan=json.loads(line);break
# Actual observations and frozen classifier bytes are validated while the SAME
# PostgreSQL transaction retains source/phase locks through publication commit.
inside=hydrate_locked_scan(repo,locked_scan,INVENTORY,'2026-10-01T00:00:00.000Z',ib,plan,classifiers)
check('actual-domain-classifier-under-lock-through-child-commit',inside['contentDecision']['operationCount']==1 and inside['contentDecision']['decision']=='SOURCE_PHASE_EFFECT_INVENTORY_CONTENT_VALIDATED')
holder.stdin.write(childsql+'SET CONSTRAINTS ALL IMMEDIATE;COMMIT;\n');holder.stdin.close();holder.wait(timeout=5);herr=holder.stderr.read();assert holder.returncode==0,herr

check('actual-retry-child-command-root-event-outbox-audit-locator-commit',run(f"SELECT count(*) FROM generation_job g JOIN generation_job_create_completion c ON c.job_id=g.id JOIN domain_command d ON d.logical_operation_id=c.logical_operation_id JOIN domain_event e ON e.id=c.immutable_event_id JOIN transactional_outbox o ON o.event_id=e.id JOIN audit_event a ON a.domain_event_id=e.id JOIN idempotency_locator l ON l.logical_operation_id=d.logical_operation_id JOIN kcml_retry_v1.child_scan s ON s.child_job_id=g.id WHERE g.id='{child}' AND g.kind='RETRY';").stdout.strip()=='1')
r=run('BEGIN;'+reserve+'COMMIT;');check('idempotent-frozen-child-replay',r.returncode==0,r.stderr[-500:])
pgnegative('replay-conflict',reserve.replace(b(bytes.fromhex(rd[7:])),b(bytes(32))),'RETRY_CHILD_REPLAY_CONFLICT')
report={'inputCommit':'905555e47f3547516439a699e262df62cbbec229','sourceDocumentSha256':hashlib.sha256(entry).hexdigest(),'checkCount':len(checks),'failedCount':sum(not c['passed']for c in checks),'checks':checks,'postgresqlVersion':run('SHOW server_version;').stdout.strip(),'canonicalExtensionSqlSha256':hashlib.sha256(SQL2.encode()).hexdigest(),'canonicalSqlSha256':{'database/generation-create-foundations.sql':hashlib.sha256(canonical_sql.encode()).hexdigest(),'database/generation-locked-retry.sql':hashlib.sha256(SQL.encode()).hexdigest()},'wholeOperationClosed':False,'limits':['Actual canonical SQL physical RETRY child closure; source admission and protected snapshot remain synthetic/opaque','Complete 49.8 dispatch/checkpoint/evidence producers not replaced by membership capture','Exact embedded retry producer extension executed with independent candidate byte-equality assertion']}
(OUT/'producer-child-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(checks),'failed':report['failedCount']}));sys.exit(bool(report['failedCount']))
