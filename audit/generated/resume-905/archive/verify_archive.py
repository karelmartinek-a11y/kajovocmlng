"""Actual canonical embedded PG18.6 foundation -> storage query -> bytes consumer."""
import os,sys,json,hashlib,re,subprocess,copy,time
from pathlib import Path
HERE=Path(__file__).parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT,resources
from generation_read_hydration import hydrate_storage,ContractFailure,digest
import generation_read_hydration,generation_create_consumer
assert Path(generation_read_hydration.__file__).resolve()==ROOT/'scripts/generation_read_hydration.py'
assert Path(generation_create_consumer.__file__).resolve()==ROOT/'scripts/generation_create_consumer.py'
DB='archive_905';PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p55432','-X','-At','-v','ON_ERROR_STOP=1']
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
sys.path.insert(0,str(HERE))
from generation_frozen_archive import *
from generation_read_hydration_archive import hydrate_storage
archive=(HERE/'generation-frozen-archive.sql').read_text()
q=run(archive);record('archive-candidate-installs-on-exact-canonical-foundations',q.returncode==0,diagnostic=q.stderr[-1200:])
mask=json.loads(rs['contracts/payload-contracts.json']['raw'])['records']
mask=next(v['requestSchema']['properties']['body']for v in mask if v['operationId']=='generation.job.create')
schema_raw=json.dumps(mask,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
schema_id=mask['$id'];sd=sha(schema_raw)
authority=source[source.index(b'### 12.47'):source.index(b'### 12.48')]+source[source.index(b'### 12.54'):source.index(b'## 13.',source.index(b'### 12.54'))]
policy=policy_bytes(authority,DOMAIN_IMPLEMENTATION);pd=sha(policy)
def lit(t):return "'"+t.replace("'","''")+"'"
def byte(raw):return "decode('"+raw.hex()+"','hex')"
def publish(kind,id,raw,sourceid='SSOT#12.54',sourcebytes=authority):
 return 'SELECT kcml_archive_publish_v1('+','.join([lit(kind),lit(id),byte(hashlib.sha256(raw).digest()),byte(raw),lit(sourceid),byte(hashlib.sha256(sourcebytes).digest())])+');'
publication=publish('SCHEMA',schema_id,schema_raw)+publish('DOMAIN_POLICY',POLICY_ID,policy)+publish('AUTHORITY','SSOT#12.54',authority)+publish('POLICY_IMPLEMENTATION','GENERATION_CREATE_REQUEST_SEMANTICS_V1',DOMAIN_IMPLEMENTATION)
binding={'schemaId':schema_id,'schemaDigest':sd,'policyId':POLICY_ID,'policyDigest':pd,'dependencies':[]}
bindingSQL=f"INSERT INTO generation_frozen_policy_binding_v1(snapshot_id,logical_operation_id,schema_id,schema_digest,policy_id,policy_digest,dependency_closure)VALUES('{x['snap']}','{x['op']}',{lit(schema_id)},{byte(bytes.fromhex(sd[7:]))},{lit(POLICY_ID)},{byte(bytes.fromhex(pd[7:]))},'[]');"
# Missing archive must roll back the entire otherwise-valid root command chain.
q=run('BEGIN;'+''.join(base.values())+'COMMIT;');record('otherwise-valid-create-without-archive-exact-rejection',q.returncode!=0 and 'FROZEN_ARCHIVE_REQUIRED'in q.stderr,diagnostic=q.stderr[-700:])
record('missing-archive-leaves-no-command-root-event',run('SELECT(SELECT count(*)FROM domain_command),(SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_event);').stdout.strip()=='0|0|0')
badclosure=bindingSQL.replace("'[]'",lit(json.dumps([{'schemaId':'urn:missing','bundleDigest':'sha256:'+('00'*32)}])))
q=run('BEGIN;'+publication+''.join(base.values())+badclosure+'COMMIT;');record('declared-schema-dependency-must-have-actual-bytes',q.returncode!=0 and 'FROZEN_ARCHIVE_DEPENDENCY_UNAVAILABLE'in q.stderr)
wrongcmd=bindingSQL.replace(x['op'],'77777777-7777-4777-8777-777777777777')
extra="INSERT INTO domain_command SELECT (jsonb_populate_record(NULL::domain_command,to_jsonb(d)||'{\"logical_operation_id\":\"77777777-7777-4777-8777-777777777777\",\"command_id\":\"77777777-7777-4777-8777-777777777777\",\"operation_id\":\"config.rollback\"}'::jsonb)).* FROM domain_command d;"
q=run('BEGIN;'+publication+''.join(base.values())+extra+wrongcmd+'COMMIT;');record('snapshot-command-binding-swap-rejected-exactly',q.returncode!=0 and 'FROZEN_ARCHIVE_SNAPSHOT_BINDING_MISMATCH'in q.stderr,diagnostic=q.stderr[-500:])
other_schema=json.dumps(mask,sort_keys=True,indent=1).encode();other_sd=sha(other_schema)
wrong_schema=bindingSQL.replace(bytes.fromhex(sd[7:]).hex(),bytes.fromhex(other_sd[7:]).hex())
q=run('BEGIN;'+publication+publish('SCHEMA',schema_id,other_schema)+''.join(base.values())+wrong_schema+'COMMIT;');record('digest-valid-available-wrong-schema-snapshot-binding',q.returncode!=0 and 'FROZEN_ARCHIVE_SNAPSHOT_BINDING_MISMATCH'in q.stderr,diagnostic=q.stderr[-500:])
q=run('BEGIN;'+publication+''.join(base.values())+bindingSQL+'COMMIT;');record('archive-producer-binding-root-event-actual-one-commit',q.returncode==0,diagnostic=q.stderr[-1000:])
q=run(publication);record('same-exact-publication-replay',q.returncode==0)
q=run(publish('SCHEMA',schema_id,schema_raw,'OTHER',authority));record('source-identity-replay-conflict',q.returncode!=0 and'FROZEN_ARCHIVE_REPLAY_CONFLICT'in q.stderr)
# Unique-index race: follower blocks until the first publication commits,
# then uses exact retained content/provenance instead of latest replacement.
conraw=b'concurrent immutable archive bytes';conid='urn:kcml:fixture:concurrent'
marker=HERE/'archive-race.marker';marker.unlink(missing_ok=True)
cmd='BEGIN;'+publish('AUTHORITY',conid,conraw)+'\\! touch '+str(marker)+'\nSELECT pg_sleep(0.4);COMMIT;'
p=subprocess.Popen(x['PSQL'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);p.stdin.write(cmd);p.stdin.close()
deadline=time.monotonic()+3
while not marker.exists()and time.monotonic()<deadline:time.sleep(.01)
record('concurrent-first-publication-lock-acquired',marker.exists())
started=time.monotonic();q=run(publish('AUTHORITY',conid,conraw));elapsed=time.monotonic()-started;marker.unlink(missing_ok=True);p.wait(timeout=5);err=p.stderr.read();record('concurrent-identical-publication-one-retained-row',p.returncode==0 and q.returncode==0 and elapsed>.15 and run('SELECT count(*)FROM generation_frozen_bundle_v1 WHERE bundle_id='+lit(conid)+';').stdout.strip()=='1',diagnostic=err[-500:]+q.stderr[-500:])
q=run(publish('AUTHORITY',conid,conraw,'conflicting source',authority));record('concurrent-key-retained-source-cannot-replace',q.returncode!=0 and 'FROZEN_ARCHIVE_REPLAY_CONFLICT'in q.stderr)
q=run('UPDATE generation_frozen_bundle_v1 SET exact_bytes=exact_bytes;');record('schema-bytes-immutable',q.returncode!=0 and'FROZEN_ARCHIVE_IMMUTABLE'in q.stderr)
q=run('DELETE FROM generation_frozen_policy_binding_v1;');record('binding-retained-immutable',q.returncode!=0 and'FROZEN_ARCHIVE_IMMUTABLE'in q.stderr)
bundles={sha(schema_raw):schema_raw,pd:policy,sha(authority):authority}
impls={sha(DOMAIN_IMPLEMENTATION):DOMAIN_IMPLEMENTATION}
validator=compile_archived_request(binding,bundles,policy_implementations=impls)
validator(x['body']);record('real-schema-real-policy-positive',True)
def reject(name,code,fn):
 try:fn()
 except ContractFailure as e:record(name,e.code==code,actualDiagnostic=e.code,expectedDiagnostic=code);return
 raise AssertionError(name+' accepted')
reject('missing-archived-policy-no-current-fallback','FROZEN_DOMAIN_POLICY_UNAVAILABLE',lambda:compile_archived_request(binding,{sd:schema_raw},policy_implementations=impls))
reject('missing-archived-implementation-no-current-fallback','FROZEN_DOMAIN_POLICY_IMPLEMENTATION_UNAVAILABLE',lambda:compile_archived_request(binding,bundles,policy_implementations={}))
reject('policy-authentic-content-unavailable','FROZEN_DOMAIN_POLICY_AUTHORITY_UNAVAILABLE',lambda:compile_archived_request(binding,{sd:schema_raw,pd:policy},policy_implementations=impls))
empty=copy.deepcopy(x['body']);empty['intent']='  '
reject('domain-rule-from-valid-positive-empty-intent','EMPTY_INTENT',lambda:validator(empty))
# Two exact schema revisions with SAME $id. Old positive is structurally invalid
# in the later mask; retrieval addresses bytes rather than today's URI alias.
old=copy.deepcopy(mask);old['properties']['intent']={'type':'string','const':x['body']['intent']};oldraw=json.dumps(old,sort_keys=True,separators=(',',':')).encode()
new=copy.deepcopy(old);new['properties']['intent']['const']='different intent';newraw=json.dumps(new,sort_keys=True,separators=(',',':')).encode()
q=run(publish('SCHEMA',schema_id,oldraw)+publish('SCHEMA',schema_id,newraw));record('same-id-two-archived-revisions-actual-sql',q.returncode==0)
for raw,label in [(oldraw,'old'),(newraw,'new')]:
 r=run('SELECT encode(exact_bytes,\'hex\')FROM generation_frozen_bundle_v1 WHERE bundle_kind=\'SCHEMA\'AND bundle_id='+lit(schema_id)+'AND bundle_digest='+byte(hashlib.sha256(raw).digest())+';')
 fetched=bytes.fromhex(r.stdout.strip());record(label+'-exact-stored-bytes',fetched==raw);bundles[sha(raw)]=fetched
ob={**binding,'schemaDigest':sha(oldraw)};nb={**binding,'schemaDigest':sha(newraw)}
compile_archived_request(ob,bundles,policy_implementations=impls)(x['body']);record('historical-same-id-request-with-historical-policy',True)
reject('latest-same-id-is-not-historical-substitute','FROZEN_SCHEMA_CONTENT_INVALID',lambda:compile_archived_request(nb,bundles,policy_implementations=impls)(x['body']))
oldsource=subprocess.run(['git','show','d362487999bd795d4723c2a930e93fc7aa8aa295:00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT,capture_output=True,check=True).stdout
oldrs=resource_index(resources(oldsource.decode()))
oldmask=next(v['requestSchema']['properties']['body']for v in json.loads(oldrs['contracts/payload-contracts.json']['raw'])['records']if v['operationId']=='generation.job.create')
historical=json.dumps(oldmask,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
oldauthority=oldsource[oldsource.index(b'### 12.47'):oldsource.index(b'### 12.48')]
oldpolicy=policy_bytes(oldauthority,DOMAIN_IMPLEMENTATION)
q=run(publish('SCHEMA',oldmask['$id'],historical,'d362#payload/operation:generation.job.create',oldsource)+publish('DOMAIN_POLICY',POLICY_ID,oldpolicy,'d362#12.47',oldauthority)+publish('AUTHORITY','d362#12.47',oldauthority,'d362#12.47',oldauthority))
record('actual-historical-canonical-mask-policy-authority-publication',q.returncode==0)
bundles.update({sha(historical):historical,sha(oldpolicy):oldpolicy,sha(oldauthority):oldauthority})
legacy={'kind':'UPDATE','intent':'Update existing generated target','targetKind':'MCP_SERVER','targetObjectId':'11111111-1111-4111-8111-111111111111'}
hb={**binding,'schemaId':oldmask['$id'],'schemaDigest':sha(historical),'policyDigest':sha(oldpolicy)}
compile_archived_request(hb,bundles,policy_implementations=impls)(legacy);record('actual-historical-update-mask-plus-retained-domain-policy-valid',True)
reject('historical-update-not-current-policy-substitution','FROZEN_SCHEMA_CONTENT_INVALID',lambda:compile_archived_request(binding,bundles,policy_implementations=impls)(legacy))
q=run(rs['database/generation-create-read.sql']['raw'].decode());record('canonical-read-install',q.returncode==0,diagnostic=q.stderr[-700:])
row=json.loads(run(f"SELECT kcml_generation_create_read_storage_v1('{owner}','{job}');").stdout)
plain=x['canonical_bytes'](x['body'])
fetched=json.loads(run(f"SELECT kcml_archive_read_v1('{x['snap']}','{x['op']}');").stdout)
record('archive-repository-reader-selects-exact-binding',fetched['binding']==binding)
stored_bundles={d:bytes.fromhex(raw)for d,raw in fetched['bundles'].items()}
record('archive-repository-reader-returns-exact-policy-authority-schema-code',stored_bundles[sd]==schema_raw and stored_bundles[pd]==policy and stored_bundles[sha(authority)]==authority and stored_bundles[sha(DOMAIN_IMPLEMENTATION)]==DOMAIN_IMPLEMENTATION)
record('wrong-command-cannot-read-snapshot-archive',not run(f"SELECT kcml_archive_read_v1('{x['snap']}','77777777-7777-4777-8777-777777777777');").stdout.strip())
result=hydrate_storage(row,selected_job_id=job,authenticated_owner_id=owner,open_snapshot=lambda sid,ref:plain,archive_binding=fetched['binding'],archive_bundles=stored_bundles,policy_implementations=impls)
record('actual-root-event-receipt-storage-archive-domainpolicy-consumer-chain',result['jobId']==job and result['executionApproved']is False)
report={'inputHead':'905555e47f3547516439a699e262df62cbbec229','sourceDocumentSha256':hashlib.sha256(source).hexdigest(),'postgresqlVersion':'18.6','canonicalFoundationSha256':rs['database/generation-create-foundations.sql']['sha256'],'candidateArchiveSha256':hashlib.sha256(archive.encode()).hexdigest(),'supportSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),HERE/'generation_frozen_archive.py',HERE/'generation_request_policy_v1.py',HERE/'generation_create_consumer_archive.py',HERE/'generation_read_hydration_archive.py']},'checks':cases,'checked':len(cases),'failed':sum(not c['passed']for c in cases),'status':'PASS','wholeOperationClosed':False,'limitations':['Candidate SQL is not embedded canonical until root integration','OWNER authority and protected open are existing synthetic fixture context/opener; not actual credential or canonical crypto proof','Complete historical policy revisions require actual archived supported implementation; unknown revision fails BLOCKED','Pre-root accepted snapshot archive binding remains separate required extension']}
(HERE/'archive-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':len(cases),'failed':report['failed']}))
