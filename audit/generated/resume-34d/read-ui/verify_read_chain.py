"""Actual canonical embedded PG18.6 foundation -> storage query -> bytes consumer."""
import os,sys,json,hashlib,re,subprocess,copy,time
from pathlib import Path
HERE=Path(__file__).parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
from generation_read_hydration import hydrate_storage,ContractFailure,digest
import generation_read_hydration,generation_create_consumer
assert Path(generation_read_hydration.__file__).resolve()==ROOT/'scripts/generation_read_hydration.py'
assert Path(generation_create_consumer.__file__).resolve()==ROOT/'scripts/generation_create_consumer.py'
DB='read_ui_34d';PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p55432','-X','-At','-v','ON_ERROR_STOP=1']
def admin(s):return subprocess.run(PSQL+['-d','postgres'],input=s,text=True,capture_output=True)
assert admin('SHOW server_version').stdout.strip()=='18.6'
if not admin("SELECT 1 FROM pg_database WHERE datname='"+DB+"';").stdout.strip():assert admin('CREATE DATABASE '+DB+';').returncode==0
source=SSOT.read_bytes();rs=resource_index();canonical_sql=rs['database/generation-create-foundations.sql']['raw'].decode()
program=(ROOT/'audit/generated/resume-d362/review/verify_scoped_generation_links.py').read_text().split('# Commit the positive',1)[0]
program=program.replace('generation_independent_review_fixture',DB)
# Redirect every generated artifact inside this agent-owned directory.
program=program.replace("source=source.replace('foundation=module.foundations();',", "source=source.replace(\"(HERE/'combined-foundations.sql').write_text(foundation)\",'')\nsource=source.replace('foundation=module.foundations();',")
needle="ns={'__file__':str(HERE/'verify_scoped_generation_links.py')};exec"
program=program.replace(needle,"source=re.sub(r'foundation=module\\.foundations\\(\\).*?\\n','foundation=canonical_sql\\n',source,count=1)\nns={'__file__':str(HERE/'verify_scoped_generation_links.py'),'canonical_sql':canonical_sql};exec")
ns={'__file__':str(ROOT/'audit/generated/resume-d362/review/verify_scoped_generation_links.py'),'canonical_sql':canonical_sql}
exec(compile(program,'read-ui fixture foundations','exec'),ns)
x=ns['ns'];assert x['foundation']==canonical_sql
run=x['run'];base=ns['base'];owner=x['owner'];job=x['job'];other='77777777-7777-4777-8777-777777777777';cases=[]
def record(name,passed,**kw):cases.append({'id':name,'passed':bool(passed),**kw});assert passed,(name,kw)
readsql=rs['database/generation-create-read.sql']['raw'].decode();assert readsql==(HERE/'generation-create-read-storage.sql').read_text(),'CURRENT_CANONICAL_READ_SQL_DIFFERS_FROM_REVIEWED_CANDIDATE'
q=run(readsql);record('exact-embedded-canonical-DDL-plus-own-read-query-install',q.returncode==0,diagnostic=q.stderr[-1200:])
q=run('BEGIN;'+''.join(base.values())+'COMMIT;');record('canonical-native-positive-atomic-create-commit',q.returncode==0,diagnostic=q.stderr[-1200:])
def sqlread(o=owner,j=job):return run("SELECT kcml_generation_create_read_storage_v1('"+o+"','"+j+"');")
q=sqlread();record('joined-storage-read-one-row',q.returncode==0 and bool(q.stdout.strip()),diagnostic=q.stderr[-1200:]);row=json.loads(q.stdout)
record('all-39-root-columns',len(row['root'])==39)
record('no-protected-bytes-in-metadata-query',not any(k in q.stdout for k in ['ciphertext','nonce','verifier_hash','SYNTHETIC_HASH_NOT_VERIFIER','execution_descriptor_bytes']))
record('wrong-owner-does-not-disclose-root',not sqlread(other).stdout.strip())
record('wrong-selected-job-does-not-select-latest',not sqlread(j=other).stdout.strip())
query="SELECT kcml_generation_create_read_storage_v1('"+owner+"','"+job+"');"
q=run("BEGIN; SET LOCAL ROLE kcml_authentication_writer;"+query+'ROLLBACK;');record('ungranted-auth-producer-cannot-execute-read-query',q.returncode!=0 and 'permission denied for function' in q.stderr)
# Actual decrypt remains sibling crypto agent's obligation. Fixture callback
# returns exactly the natively valid canonical body bytes bound to persisted
# content digest; no synthetic AES/authorized-valid flag claims are made here.
plain=x['canonical_bytes'](x['body']);opened=[]
def opener(sid,expected):
 opened.append((sid,dict(expected)))
 assert sid==row['initialRequestRef']['snapshotId']
 return plain
result=hydrate_storage(row,selected_job_id=job,authenticated_owner_id=owner,open_snapshot=opener)
record('actual-stored-receipt-event-root-request-bytes-consumer',result['jobId']==job and result['executionApproved']is False and result['activationAuthorized']is False)
record('authenticated-open-receives-exact-immutable-reference',opened[-1][1]==row['initialRequestRef'])
record('public-consumer-result-does-not-echo-sensitive-inputs',set(result)=={'jobId','state','stateVersion','eventSequence','nextAction','executionApproved','activationAuthorized'})
def bad(name,code,mutate,*,own=owner,opener=opener):
 value=copy.deepcopy(row);mutate(value)
 try:hydrate_storage(value,selected_job_id=job,authenticated_owner_id=own,open_snapshot=opener)
 except ContractFailure as e:record(name,e.code==code,expectedDiagnostic=code,actualDiagnostic=e.code);return
 raise AssertionError(name+' accepted')
bad('selected-owner-source-mismatch','GENERATION_READ_OWNER_MISMATCH',lambda r:None,own=other)
bad('immutable-snapshot-swapped','INITIAL_SNAPSHOT_IDENTITY_MISMATCH',lambda r:r['initialRequestRef'].update(snapshotId=other))
bad('read-command-cross-link','GENERATION_READ_COMMAND_IDENTITY_MISMATCH',lambda r:r['event'].update(logicalOperationId=other))
bad('same-schema-different-event-root','GENERATION_READ_EVENT_IDENTITY_MISMATCH',lambda r:r['event'].update(aggregateId=other))
bad('missing-atomic-audit-link','GENERATION_READ_ATOMIC_LINKS_MISSING',lambda r:r['links'].update(auditId=None))
bad('retained-result-corrupt','GENERATION_READ_RETAINED_RESULT_DIGEST_MISMATCH',lambda r:r['creation'].update(resultDigest='sha256:'+'0'*64))
bad('raw-event-encoding-corrupt','GENERATION_READ_STORED_BYTES_ENCODING_INVALID',lambda r:r['event'].update(payloadHex='xyz'))
bad('frozen-schema-policy-unavailable','GENERATION_READ_FROZEN_REQUEST_POLICY_UNAVAILABLE',lambda r:r['initialRequestRef'].update(schemaDigest='sha256:'+'0'*64))
bad('missing-authenticated-open','GENERATION_READ_AUTHENTICATED_OPEN_UNAVAILABLE',lambda r:None,opener=None)
bad('authenticated-open-returned-other-bytes','INITIAL_REQUEST_BYTES_DIGEST_MISMATCH',lambda r:None,opener=lambda sid,ref:plain+b' ')
# Malformed decrypted JSON mutates valid domain witness coherently: byte and
# receipt/result hashes are rebound, so rejection reaches the HTTP JSON decoder.
def malformed_bind(r,raw):
 newdigest=digest(raw);r['root']['initialRequestDigest']=newdigest;r['initialRequestRef']['contentDigest']=newdigest
 receipt=json.loads(bytes.fromhex(r['creation']['receiptHex']));receipt['initialRequestDigest']=newdigest
 rb=x['canonical_bytes'](receipt);r['creation']['receiptHex']=rb.hex();r['creation']['receiptDigest']=digest(rb)
 r['event']['payloadHex']=rb.hex();r['event']['payloadDigest']=digest(rb)
 sem=json.loads(bytes.fromhex(r['creation']['semanticResponseHex']));sem['output']=receipt
 sb=x['canonical_bytes'](sem);r['creation']['semanticResponseHex']=sb.hex();r['creation']['resultDigest']=digest(sb);r['links']['canonicalOutcomeDigest']=digest(sb)
for name,raw,code in [('actual-open-invalid-json',b'{','INVALID_JSON'),('actual-open-duplicate-json',b'{"intent":"first","intent":"second"}','DUPLICATE_JSON_KEY')]:
 bad(name,code,lambda r,raw=raw:malformed_bind(r,raw),opener=lambda sid,ref,raw=raw:raw)

# Independent PostgreSQL transactions: one REPEATABLE READ storage view remains
# consistent across a concurrent legal root version/sequence update; a fresh
# read observes the new current values and retains exactly frozen create bytes.
marker=HERE/'read-snapshot.marker';marker.unlink(missing_ok=True)
cmd='BEGIN ISOLATION LEVEL REPEATABLE READ;'+query+'\\! touch '+str(marker)+'\nSELECT pg_sleep(0.4);'+query+'COMMIT;'
p=subprocess.Popen(x['PSQL'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);p.stdin.write(cmd);p.stdin.close()
deadline=time.monotonic()+3
while not marker.exists()and time.monotonic()<deadline:time.sleep(.02)
record('independent-read-snapshot-linearized',marker.exists())
u=run("UPDATE generation_job SET state='ANALYZING',state_version=state_version+1,aggregate_event_sequence=aggregate_event_sequence+1 WHERE id='"+job+"';")
record('concurrent-own-root-advance',u.returncode==0,diagnostic=u.stderr[-1200:]);p.wait(timeout=5);out=p.stdout.read();err=p.stderr.read();vals=[json.loads(line)for line in out.splitlines()if line.startswith('{')]
record('same-read-snapshot-does-not-tear',p.returncode==0 and len(vals)==2 and vals[0]==vals[1],diagnostic=err[-1200:]);marker.unlink(missing_ok=True)
new=json.loads(sqlread().stdout);record('fresh-read-sees-new-state-retains-create-event',new['root']['state']=='ANALYZING'and new['root']['stateVersion']=='2'and new['creation']==row['creation']and new['event']==row['event'])
result=hydrate_storage(new,selected_job_id=job,authenticated_owner_id=owner,open_snapshot=opener)
record('consumer-allows-own-current-state-advance-without-new-create',result['state']=='ANALYZING'and result['stateVersion']=='2')
record('read-has-no-command-event-outbox-audit-side-effects',run('SELECT(SELECT count(*)FROM domain_command),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM transactional_outbox),(SELECT count(*)FROM audit_event);').stdout.strip()=='1|1|1|1')
report={'entryHead':'34d3a75c47a92ab7d8e0dac84f581549a15445ca','verifiedHead':subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip(),'sourceDocumentSha256':hashlib.sha256(source).hexdigest(),'canonicalSqlSha256':rs['database/generation-create-foundations.sql']['sha256'],'canonicalReadSqlSha256':rs['database/generation-create-read.sql']['sha256'],'postgresqlVersion':'18.6','database':DB,'checks':cases,'checked':len(cases),'failed':sum(not c['passed']for c in cases),'status':'PASS','supportSha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),HERE/'generation-create-read-storage.sql',HERE/'generation-root-storage-read.schema.json',ROOT/'scripts/generation_read_hydration.py',ROOT/'scripts/generation_create_consumer.py',ROOT/'scripts/create_operation_contracts.py',ROOT/'scripts/create_completion_contracts.py',ROOT/'scripts/follow_up_contracts.py',ROOT/'scripts/verify_create_completion.py',ROOT/'audit/generated/resume-d362/review/verify_scoped_generation_links.py',ROOT/'audit/generated/resume-d362/events/verify_combined_generation.py',ROOT/'audit/generated/resume-d362/persistence/generation_descriptor_registry.py',ROOT/'audit/generated/resume-d362/persistence/context_fixture_exports.py']},'limitations':['Protected opening callback supplies actual fixture bytes; canonical crypto proof belongs to separate integrated verifier','Authenticated owner from trusted service; actual token verification and route/channel binding belong to dedicated verifier','39 physical root columns are INTERNAL projection; not full native child read/public UI contract','Failure-before-root retained outcomes remain separate persistence producer contract','No browser rerender or generated backend/runtime acceptance'],'wholeOperationsClosed':0,'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
assert source==SSOT.read_bytes(),'SOURCE_CHANGED_DURING_FIXTURE'
(HERE/'read-chain-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':len(cases),'failed':report['failed'],'status':'PASS'}))
