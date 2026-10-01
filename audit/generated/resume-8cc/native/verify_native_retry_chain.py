"""Actual native RETRY auth→AES→locked physical producer scan→child commit.
A bounded isolated reference: real PG/CAS/AES, no systemd or app runtime claim.
"""
from native_basis_factory import *
from generation_locked_retry import hydrate_locked_scan_for_admission as hydrate_locked_scan
from generation_basis_consumer import consume_inherited_basis
from generation_frozen_archive import policy_bytes,DOMAIN_IMPLEMENTATION,POLICY_ID
from generation_read_hydration_archive import hydrate_storage
from generation_frozen_archive import compile_archived_request
from generation_admission_contracts import ContractFailure
import threading,time
OUT=Path(__file__).parent
f=Factory('native_retry_joined_8cc');db=f.db;checks=[];rs=f.resources
w=witness_factory();parentbody={'kind':'CREATE','targetKind':'PLATFORM_COMPONENT','intent':'Create synthetic native technical source','sources':[{'kind':'TEXT','text':'Native source fixture'}]}
def rec(n,ok,actual=None):checks.append({'case':n,'passed':bool(ok),'actualDiagnostic':actual});assert ok,(n,actual)
for name in ['database/generation-locked-retry.sql','database/generation-retry-producer-child.sql','database/generation-frozen-archive.sql','database/generation-preroot-frozen-archive.sql']:db.query(rs[name]['raw'].decode())
ledgerpath=ROOT/'audit/generated/resume-8cc/ledger/side-effect-producer.sql';ledgerbytes=ledgerpath.read_bytes();db.query('DROP SCHEMA IF EXISTS kcml_effect_v1 CASCADE;'+ledgerbytes.decode())
lineagesql=(OUT/'generation-native-lineage.sql').read_bytes();db.query('DROP SCHEMA IF EXISTS kcml_native_basis_v1 CASCADE;'+lineagesql.decode())
archivepath=ROOT/'audit/generated/resume-8cc/archive/generation-trusted-policy-publisher.sql';archivebytes=archivepath.read_bytes();db.query(archivebytes.decode())
sys.path.insert(0,str(archivepath.parent))
from generation_policy_package import build_package,dispatch_own_kind,PACKAGE_ID
schema=f.pinned['domainSchemaBytes'];sid=strict_json(schema)['$id'];authority=f.source[f.source.index(b'### 12.47'):f.source.index(b'### 12.48')];policy=policy_bytes(authority,DOMAIN_IMPLEMENTATION)
package,blobs=build_package(rs,schema,policy,authority)
release='SET LOCAL ROLE kcml_generation_policy_installer;INSERT INTO generation_policy_release_v1(application_deployment_epoch,operation_contract_digest,package_id,package_digest,package_bytes,request_schema_id,request_schema_digest,request_policy_id,request_policy_digest)VALUES('+','.join(['1',b(f.pinned['contractDigest']),lit(PACKAGE_ID),b(sha(package)),b(package),lit(sid),b(sha(schema)),lit(POLICY_ID),b(sha(policy))])+');'
for (kind,id,dg),raw in blobs.items():release+='INSERT INTO generation_policy_release_blob_v1 VALUES('+','.join(['1',lit(kind),lit(id),b(sha(raw)),b(raw),lit('trusted-fixture-deployment-source'),b(sha(raw))])+');'
db.query('BEGIN;'+release+'RESET ROLE;COMMIT')
def acceptance_hook(context,command):db.query('SET LOCAL ROLE kcml_domain_writer;SELECT kcml_pin_policy_acceptance_v1('+lit(context)+','+lit(command)+');RESET ROLE;')
f.acceptance_hook=acceptance_hook
# Publisher never reacquires lower acceptance B locks after root/outbox writes.
def bind(meta):db.query('SET LOCAL ROLE kcml_domain_writer;SELECT kcml_publish_accepted_policy_package_v1('+','.join(lit(meta[k])for k in ['trustedContextId','logicalOperationId','snapshotId'])+');RESET ROLE;')
db.query('BEGIN');parent=f.build(parentbody,uid(1),uid(1001),uid(2001),key='native-source');f.insert(parent);bind(parent['meta']);db.query('COMMIT');persist(db,w,exclude={w['phase']['phaseRunId'],w['phase']['resultDigest']})
def publish(kind,id,raw):
 existing=db.query("SELECT encode(exact_bytes,'hex')FROM generation_frozen_bundle_v1 WHERE bundle_kind="+lit(kind)+' AND bundle_id='+lit(id)+' AND bundle_digest='+b(sha(raw)))
 if existing:
  assert bytes.fromhex(existing[0][0])==raw;return
 db.query('SELECT kcml_archive_publish_v1('+','.join([lit(kind),lit(id),b(sha(raw)),b(raw),"'isolated-current-native-producer'",b(sha(f.source))])+');')
phase=w['phase'];plan=w['plan'];body=w['body'];basis=body['generationBasis'];rd=w['phaseDigest']
# Physical accepted approved source is fixture-seeded, not an invented user role.
db.query("UPDATE generation_job SET state_version=state_version+1,approved_spec_revision_id="+lit(basis['approvedRevisionId'])+',approved_specification_digest='+b(bytes.fromhex(basis['expectedSpecificationDigest'][7:]))+',active_phase_run_id='+lit(phase['phaseRunId'])+',current_plan_id='+lit(basis['planId'])+',coordinator_lease_owner_id='+lit(OWNER)+",coordinator_fencing_token=7,coordinator_lease_expires_at=clock_timestamp()+interval '1hour' WHERE id="+lit(uid(1)))
db.query('SELECT kcml_effect_v1.begin_phase('+','.join([lit(phase['phaseRunId']),lit(uid(1)),b(canonical_bytes(plan)),b(bytes.fromhex(basis['expectedSpecificationDigest'][7:]))])+');')
# Checkpoint refs are exact archived native source graph artifacts and plan bytes.
for dg,raw in w['repo'].bundles.items():publish('SCHEMA',strict_json(raw)['$id'],raw)
for key,r in w['repo'].records.items():publish('AUTHORITY',key,r['bytes'])
publish('DOMAIN_POLICY',basis['authorityId'],w['repo'].records[basis['authorityId']]['bytes'])
refs=[]
for key,r in w['repo'].records.items():
 if r.get('schema') and r['schema']['definition'] in ['GenerationAuthority','GenerationSpecification','GenerationPlan']:
  refs.append({'recordId':key,'contentDigest':r['contentDigest'],'schemaId':r['schema']['schemaId'],'schemaDigest':r['schema']['bundleDigest']})
# Known semantic limitation: checkpoint binding/budget native producers still OPEN;
# exact source-reference presence validates bytes, not a new approved budget.
values=[lit(uid(1)),lit(basis['approvedRevisionId']),b(bytes.fromhex(basis['expectedSpecificationDigest'][7:])),lit(basis['planId']),b(bytes.fromhex(basis['expectedPlanDigest'][7:]))]+[lit(canonical_bytes(r).decode())+'::jsonb'for r in refs[:3]]+['0',"'[]'","'[]'","'[]'","'[]'"]
db.query('INSERT INTO kcml_effect_v1.checkpoint_context VALUES('+','.join(values)+');')
classifier=bytes.fromhex(db.query("SELECT encode(convert_to(pg_get_functiondef('kcml_effect_v1.classify_cas_v1(jsonb,bytea,text,uuid)'::regprocedure),'UTF8'),'hex')")[0][0]);publish('POLICY_IMPLEMENTATION','CAS_READ_BACK_V1',classifier)
operation=uid(800);attempt=uid(801);claim=sha(b'isolated-current-native-concurrency')
db.query('INSERT INTO kcml_effect_v1.concurrency_claim VALUES('+','.join([b(claim),lit(OWNER),'3',"clock_timestamp()+interval '1hour'"])+');')
request=canonical_bytes({'beforeVersion':'7','beforeValueDigest':'sha256:'+sha(b'old synthetic value').hex(),'targetKey':'fixed-target'})
intent='SELECT kcml_effect_v1.record_intent('+','.join([lit(operation),lit(phase['phaseRunId']),lit(uid(1)),lit(uid(1001)),"'SyntheticBuild'",lit(attempt),lit(uid(802)),lit(uid(803)),lit(uid(804)),b(request),lit(uid(824)),lit(uid(825)),"'fixed-target'",'7','0',"clock_timestamp()+interval '1hour'",b(claim),lit(OWNER),'3',b(sha(classifier)),'NULL'])+');'
db.query('BEGIN');db.query(intent);db.query('COMMIT');db.query("BEGIN;SELECT kcml_effect_v1.dispatch_guard('"+operation+"',1);COMMIT")
# Separate actual durable target; observations are read from committed rows.
admin=DB('postgres');targetname='native_retry_actual_target_8cc'
if not admin.query('SELECT 1 FROM pg_database WHERE datname='+lit(targetname)):admin.query('CREATE DATABASE '+targetname)
admin.close();target=DB(targetname);target.query("DROP TABLE IF EXISTS cas_target;CREATE TABLE cas_target(id text PRIMARY KEY,version bigint NOT NULL,value bytea NOT NULL,applied_operation uuid);INSERT INTO cas_target VALUES('fixed-target',7,convert_to('old synthetic value','UTF8'),NULL)")
before=target.query("SELECT version,encode(sha256(value),'hex')FROM cas_target WHERE id='fixed-target'")[0]
target.query("UPDATE cas_target SET version=version+1,value=convert_to('new synthetic value','UTF8'),applied_operation="+lit(operation)+" WHERE id='fixed-target'AND version=7")
after=target.query("SELECT version,encode(sha256(value),'hex'),applied_operation FROM cas_target WHERE id='fixed-target'")[0]
observed={'requestDigest':'sha256:'+sha(request).hex(),'targetIdempotencyKey':'fixed-target','beforeVersion':before[0],'afterVersion':after[0],'beforeValueDigest':'sha256:'+before[1],'afterValueDigest':'sha256:'+after[1],'appliedOperationId':after[2]}
db.query('BEGIN;SELECT kcml_effect_v1.append_evidence('+','.join([lit(operation),'1',lit(uid(840)),"'READ_BACK'",b(canonical_bytes(observed))])+');COMMIT;')
db.query('BEGIN;SELECT kcml_effect_v1.confirm_cas_v1('+','.join([lit(operation),'1',lit(uid(841)),'NULL',lit(uid(842)),lit(uid(843))])+');COMMIT;')
rec('actual-durable-target-readback-producer-confirmed-applied',db.query('SELECT state FROM kcml_effect_v1.state WHERE operation_id='+lit(operation))[0][0]=='CONFIRMED_APPLIED')
# Exact closed observation schema and publication receipt are trusted fixture
# registry entries, not arbitrary request values or format guesses.
obs_schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:fixture-cas-readback-observation:1','type':'object','additionalProperties':False,'required':['requestDigest','targetIdempotencyKey','beforeVersion','afterVersion','beforeValueDigest','afterValueDigest','appliedOperationId'],'properties':{'requestDigest':{'type':'string','pattern':'^sha256:[0-9a-f]{64}$'},'targetIdempotencyKey':{'type':'string','minLength':1},'beforeVersion':{'type':'string','pattern':'^(0|[1-9][0-9]*)$'},'afterVersion':{'type':'string','pattern':'^(0|[1-9][0-9]*)$'},'beforeValueDigest':{'type':'string','pattern':'^sha256:[0-9a-f]{64}$'},'afterValueDigest':{'type':'string','pattern':'^sha256:[0-9a-f]{64}$'},'appliedOperationId':{'anyOf':[{'type':'string','format':'uuid'},{'type':'null'}]}}}
obsid=uid(851);receiptid=uid(852);obraw=canonical_bytes(obs_schema);obdg='sha256:'+sha(obraw).hex();localdigest=digest(rs['contracts/generation/admission-basis.schema.json']['raw']);localid='urn:kcml:generation-admission-basis:1'
def add(key,value,definition,metadata=None):
 raw=canonical_bytes(value);r={'recordId':key,'jobId':uid(1),'owner':OWNER,'bytes':raw,'contentDigest':digest(raw),'schema':{'schemaId':localid,'bundleDigest':localdigest,'definition':definition},**(metadata or{})};w['repo'].records[key]=r;return r
obrecord=add(obsid,obs_schema,'JsonSchemaBundle',{'artifactKind':'JSON_SCHEMA_BUNDLE','publicationReceiptId':receiptid});add(receiptid,{'receiptId':receiptid,'jobId':uid(1),'artifactId':obsid,'contentDigest':obdg,'outcome':'COMMITTED'},'PublicationReceipt')
from verify_phase2_handoffs import witness
from generation_admission_contracts import UID,DIGEST
ref={'artifactId':obsid,'kind':'JSON_SCHEMA_BUNDLE','schema':obrecord['schema'],'mediaType':'application/json','path':'observation.schema.json','contentDigest':obdg,'sizeBytes':len(obraw),'producerNodeId':'SyntheticBuild','provenanceDigest':'sha256:'+sha(f.source).hex()}
obsdescriptor={'schemaId':obs_schema['$id'],'dialect':obs_schema['$schema'],'rootPointer':'','bundle':ref,'nativeSchemaDigest':obdg}
w['repo'].records['CAS_READ_BACK_V1']={'recordId':'CAS_READ_BACK_V1','jobId':uid(1),'owner':OWNER,'bytes':classifier,'contentDigest':digest(classifier),'schema':None}
for key in [obsid,receiptid,'CAS_READ_BACK_V1']:
 r=w['repo'].records[key];s=r['schema'];db.query('INSERT INTO kcml_native_basis_v1.record VALUES('+','.join([lit(key),lit(uid(1)),lit(OWNER),b(bytes.fromhex(r['contentDigest'][7:])),b(r['bytes']),b(bytes.fromhex(s['bundleDigest'][7:]))if s else'NULL',lit(s['schemaId'])if s else'NULL',lit(s['definition'])if s else'NULL','NULL',lit(r['publicationReceiptId'])if r.get('publicationReceiptId')else'NULL',lit(r['artifactKind'])if r.get('artifactKind')else'NULL'])+');')
# Real source fence transition is classified against immutable server-captured
# phase start_fence. No caller's FAILED/errorCode assertion supplies the result.
db.query('UPDATE generation_job SET state_version=state_version+1,coordinator_fencing_token=8 WHERE id='+lit(uid(1)))
produced=bytes.fromhex(db.query('SELECT encode(kcml_effect_v1.produce_fenced_failure('+lit(phase['phaseRunId'])+','+b(canonical_bytes(phase))+"),'hex')")[0][0]);previous_result=phase['resultDigest'];phase=strict_json(produced);rd=digest(produced)
phase_record=w['repo'].records[phase['phaseRunId']];phase_record.update(bytes=produced,contentDigest=rd)
resultbytes=bytes.fromhex(db.query("SELECT encode(exact_bytes,'hex') FROM generation_frozen_bundle_v1 WHERE bundle_kind='DOMAIN_POLICY' AND bundle_digest="+b(bytes.fromhex(phase['resultDigest'][7:])))[0][0]);resultrecord=copy.deepcopy(w['repo'].records.pop(previous_result));resultrecord.update(recordId=phase['resultDigest'],bytes=resultbytes,contentDigest=digest(resultbytes));w['repo'].records[phase['resultDigest']]=resultrecord
body['generationBasis']['expectedDigest']=rd;w['phase']=phase;w['phaseDigest']=rd;w['repo'].consulted={};w['repo'].usedBundles=set();w['decision']=select_generation_basis(body,w['repo']);persist(db,w,only={phase['phaseRunId'],phase['resultDigest']})
rec('actual-server-start-fence-to-known-failure-native-phase',strict_json(resultbytes)['errorCodes']==['FENCING_TOKEN_STALE']and phase['state']=='FAILED')
db.query('BEGIN;SELECT kcml_effect_v1.publish_native_projection('+','.join([lit(operation),b(canonical_bytes(plan)),lit(canonical_bytes(obsdescriptor).decode())+'::jsonb'])+');COMMIT;')
rec('real-producer-native-current-state-projection',db.query('SELECT count(*)FROM kcml_retry_v1.operation WHERE operation_id='+lit(operation))[0][0]=='1')
# SAME acceptance transaction holds current credential and source/phase locks,
# validates actual selected bytes/classifier and commits precise native child.
def evaluate(obs,op,attempt):return db.query('SELECT kcml_effect_v1.classify_cas_v1('+lit(canonical_bytes(obs).decode())+'::jsonb,'+b(bytes.fromhex(op['requestDigest'][7:]))+','+lit(op['targetIdempotencyKey'])+','+lit(op['operationId'])+')')[0][0]
classifiers={'CAS_READ_BACK_V1':{'sourceRecordId':'CAS_READ_BACK_V1','activeSourceDigest':digest(classifier),'evaluate':evaluate}}
def prepare():
 child=f.build(body,uid(600),uid(1600),uid(2600),2,parent['auditHash'],'native-retained-child')
 # Claim actual fresh C0/C1 rows before source-root E gate; empty lookup alone does not hold it.
 for part in ['locator','idempotency']:db.query(child['parts'].pop(part))
 db.query('SELECT kcml_generation_lock_retained_locator_v1('+lit(child['context'])+')')
 scan=strict_json(db.query('SELECT kcml_retry_v1.reserve_child('+','.join([lit(uid(600)),lit(phase['phaseRunId']),lit(uid(1)),b(bytes.fromhex(rd[7:])),'8'])+')')[0][0].encode())
 repo=hydrate(db,w);decision=select_generation_basis(body,repo)
 verified=hydrate_locked_scan(repo,scan,uid(853),'2026-10-01T00:00:00.000Z',w['inventoryBundleDigest'],plan,classifiers)
 consumed=consume_inherited_basis(body,repo,w['domain_map'],w['raw_kinds'],uid(600),decision['frozenInputs'],decision['frozenSchemaBundleDigests'])
 lineage=canonical_bytes({'basis':decision,'inventoryDigest':verified['inventoryDigest'],'inventoryBytesHex':verified['inventoryBytes'].hex(),'sourceSpecificationDigest':consumed['sourceSpecificationDigest'],'childSpecificationDigest':consumed['childSpecificationDigest']})
 return child,verified,consumed,lineage

# Valid native positive under all required locks is the basis of every race/rollback.
for case,mutation in [('source-fence',"UPDATE generation_job SET state_version=state_version+1,coordinator_fencing_token=9 WHERE id="+lit(uid(1))),('second-retry',"SELECT kcml_retry_v1.reserve_child("+','.join([lit(uid(601)),lit(phase['phaseRunId']),lit(uid(1)),b(bytes.fromhex(rd[7:])),"8"])+")"),('owner-credential',"UPDATE owner_api_credential SET state_version=state_version+1,credential_version=credential_version+1,credential_activation_epoch=credential_activation_epoch+1")]:
 db.query('BEGIN');c,v,consumer,lin=prepare();f.insert(c);bind(c['meta'])
 contender=DB(f.database);diagnostics=[]
 def race():
  try:
   contender.query("BEGIN;SET LOCAL lock_timeout='150ms';");contender.query(mutation);diagnostics.append('UNEXPECTED_WRITE')
  except Exception as ex:diagnostics.append('LOCK_TIMEOUT'if'lock timeout'in str(ex)else str(ex))
  finally:contender.query('ROLLBACK')
 thread=threading.Thread(target=race);thread.start();thread.join(5);rec('native-child-transaction-blocks-'+case,diagnostics==['LOCK_TIMEOUT'],diagnostics)
 db.query('ROLLBACK');contender.close();rec('failed-'+case+'-leaves-no-child-scan-or-root',db.query('SELECT(SELECT count(*)FROM generation_job WHERE id='+lit(uid(600))+')+(SELECT count(*)FROM kcml_retry_v1.child_scan WHERE child_job_id='+lit(uid(600))+')')[0][0]=='0')
# Positive-derived omitted required event must roll back every new artifact.
db.query('BEGIN');c,v,consumer,lin=prepare();bad={k:value for k,value in c['parts'].items()if k!='event'}
try:
 db.query(''.join(bad.values()));bind(c['meta']);db.query('SET CONSTRAINTS ALL IMMEDIATE');rec('native-missing-event-rejects',False)
except Exception as ex:rec('native-missing-event-rejects','transactional_outbox_event_id_fkey'in str(ex),str(ex).splitlines()[0])
finally:db.query('ROLLBACK')
rec('missing-event-rollback-removes-auth-nonce-root-scan',db.query('SELECT(SELECT count(*)FROM generation_job WHERE id='+lit(uid(600))+')+(SELECT count(*)FROM kcml_retry_v1.child_scan WHERE child_job_id='+lit(uid(600))+')+(SELECT count(*)FROM canonical_protected_nonce_reservation WHERE protected_object_id='+lit(uid(2600))+')')[0][0]=='0')
db.query('BEGIN');child,verified,consumed,lineage=prepare();rec('applied-effect-admission-preserves-without-repeat',any(d['decision']=='PRESERVE_CONFIRMED_EFFECT_NO_REPEAT'for d in verified['contentDecision']['selectedTechnicalPartEffectDecisions']))
f.insert(child);bind(child['meta']);db.query('INSERT INTO kcml_native_basis_v1.child_lineage(child_job_id,logical_operation_id,trusted_context_id,source_job_id,phase_run_id,body_digest,lineage_digest,exact_lineage)VALUES('+','.join([lit(uid(600)),lit(uid(1600)),lit(child['context']),lit(uid(1)),lit(phase['phaseRunId']),b(sha(child['plain'])),b(sha(lineage)),b(lineage)])+');')
db.query('SET CONSTRAINTS ALL IMMEDIATE');db.query('COMMIT')
rec('native-retry-auth-crypto-producer-scan-child-all-artifacts-commit',db.query("SELECT count(*)FROM generation_job j JOIN generation_job_create_completion c ON c.job_id=j.id JOIN domain_command d ON d.logical_operation_id=c.logical_operation_id JOIN domain_event e ON e.id=c.immutable_event_id JOIN transactional_outbox o ON o.event_id=e.id JOIN audit_event a ON a.domain_event_id=e.id JOIN idempotency_locator l ON l.logical_operation_id=d.logical_operation_id JOIN kcml_native_basis_v1.child_lineage n ON n.child_job_id=j.id JOIN kcml_retry_v1.child_scan s ON s.child_job_id=j.id WHERE j.id="+lit(uid(600)))[0][0]=='1')
stored=db.query("SELECT j.owner_id,j.id,s.snapshot_id,s.logical_operation_id,s.request_schema_id,encode(s.request_schema_digest,'hex'),encode(s.content_digest,'hex'),c.id,c.platform_incarnation_id,c.application_deployment_epoch,encode(c.execution_descriptor_digest,'hex'),c.initiating_access_channel,s.algorithm,s.key_id,encode(s.crypto_profile_digest,'hex'),encode(s.nonce,'hex'),encode(s.ciphertext,'hex')FROM generation_job j JOIN generation_job_initial_request_snapshot s ON s.job_id=j.id JOIN domain_command d ON d.logical_operation_id=s.logical_operation_id JOIN generation_create_trusted_context c ON c.id=d.execution_context_id WHERE j.id="+lit(uid(600)))[0]
actualmeta=dict(zip(IDENTITY_FIELDS,stored[:12]));actualmeta['applicationDeploymentEpoch']=int(actualmeta['applicationDeploymentEpoch'])
for field in ['requestSchemaDigest','contentDigest','executionDescriptorDigest']:actualmeta[field]='sha256:'+actualmeta[field]
actualenv={'algorithm':stored[12],'keyId':stored[13],'cryptoProfileDigest':bytes.fromhex(stored[14]),'nonce':bytes.fromhex(stored[15]),'ciphertext':bytes.fromhex(stored[16])}
with open_snapshot(actualenv,f.key,stored[13],actualmeta,lambda v:validate_body('generation.job.create',strict_json(v)))as view:rec('committed-persisted-protected-child-opens-exact-native-selector',strict_json(bytes(view))==body)
storage=strict_json(db.query('SELECT kcml_generation_create_read_storage_v1('+lit(OWNER)+','+lit(uid(600))+')')[0][0].encode());archive=strict_json(db.query('SELECT kcml_archive_read_v1('+lit(uid(2600))+','+lit(uid(1600))+')')[0][0].encode());bundles={key:bytes.fromhex(raw)for key,raw in archive['bundles'].items()};implementations={digest(DOMAIN_IMPLEMENTATION):DOMAIN_IMPLEMENTATION};validator=compile_archived_request(archive['binding'],bundles,policy_implementations=implementations)
def opener(snapshot,expected):
 assert snapshot==uid(2600)and expected['jobId']==uid(600)
 with open_snapshot(actualenv,f.key,stored[13],actualmeta,lambda raw:validator(strict_json(raw)))as view:return bytes(view)
hydrated=hydrate_storage(storage,selected_job_id=uid(600),authenticated_owner_id=OWNER,open_snapshot=opener,archive_binding=archive['binding'],archive_bundles=bundles,policy_implementations=implementations)
rec('read-archive-open-native-consumer-safe-ui-result',hydrated['jobId']==uid(600)and not hydrated['executionApproved'])
storedpackage=bytes.fromhex(db.query("SELECT encode(package_bytes,'hex')FROM generation_policy_release_v1 WHERE application_deployment_epoch=1")[0][0]);storedblobs={}
for kind,id,dg,raw in db.query("SELECT bundle_kind,bundle_id,'sha256:'||encode(bundle_digest,'hex'),encode(exact_bytes,'hex')FROM generation_frozen_bundle_v1"):storedblobs[(kind,id,dg)]=bytes.fromhex(raw)
archive_repo=hydrate(db,w);historicaldecision=dispatch_own_kind(storedpackage,digest(storedpackage),storedblobs,body,archive_repo.records,OWNER)
rec('actual-admitted-package-static-source-bytes-historical-selector',historicaldecision['lineageDigest']==w['decision']['lineageDigest'])
rec('frozen-native-source-hydrates-real-43-artifact-consumer',consumed['graph']['hydratedArtifactCount']==43 and not consumed['executionAuthorityCreated'] and not consumed['dispatchPermitted'])
# Retained replay authenticates again, follows original C0/C1 scope, and
# returns original committed command outcome rather than inserting new roots.
db.query('BEGIN');replay=f.build(body,uid(600),uid(1601),uid(2601),3,child['auditHash'],'native-retained-child')
retained=db.query('SELECT logical_operation_id,state FROM kcml_generation_lock_retained_locator_v1('+lit(replay['context'])+')')
replayscan=db.query('SELECT kcml_retry_v1.reserve_child('+','.join([lit(uid(600)),lit(phase['phaseRunId']),lit(uid(1)),b(bytes.fromhex(rd[7:])),"8"])+')')[0][0]
rec('reauthenticated-retained-replay-original-command',retained==[[uid(1600),'SUCCEEDED']]and strict_json(replayscan.encode())['phaseDigest']==rd[7:])
db.query('COMMIT');rec('replay-no-extra-root-command-or-nonce',db.query('SELECT(SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_command),(SELECT count(*)FROM canonical_protected_nonce_reservation)')[0]==['2','2','2'])
# A positive native body with same business key but changed intent is an exact
# request-digest conflict, not generic input-schema failure.
changed=copy.deepcopy(body);changed['intent']='Different immutable native request under same key'
db.query('BEGIN')
try:f.build(changed,uid(601),uid(1602),uid(2602),3,child['auditHash'],'native-retained-child');rec('retained-replay-request-conflict',False)
except Exception as ex:rec('retained-replay-request-conflict','IDEMPOTENCY_CONFLICT'in str(ex),str(ex).splitlines()[0])
finally:db.query('ROLLBACK')
# Wrong server crypto metadata is rejected only after a valid persisted witness.
wrong=copy.deepcopy(actualmeta);wrong['jobId']=uid(999)
try:
 with open_snapshot(actualenv,f.key,stored[13],wrong,lambda v:validate_body('generation.job.create',strict_json(v)))as view:pass
 rec('persisted-protected-identity-substitution',False)
except ValueError as ex:rec('persisted-protected-identity-substitution',str(ex)=='PROTECTED_INPUT_AUTHENTICATION_FAILED',str(ex))
assert (OUT/'generation-native-lineage.sql').read_bytes()==lineagesql,'OWN_LINEAGE_SQL_CHANGED_DURING_JOINED_PROOF'
assert archivepath.read_bytes()==archivebytes,'PEER_ARCHIVE_CHANGED_DURING_JOINED_PROOF'
assert ledgerpath.read_bytes()==ledgerbytes,'PEER_LEDGER_CHANGED_DURING_JOINED_PROOF'
assert SSOT.read_bytes()==f.source,'CANONICAL_SOURCE_CHANGED_DURING_JOINED_PROOF'
report={'status':'PASS','checked':len(checks),'checks':checks,'sourceDocumentSha256':sha(f.source).hex(),'postgresqlVersion':db.query('SHOW server_version')[0][0],'canonicalInputs':{n:rs[n]['sha256']for n in ['database/generation-create-foundations.sql','database/generation-create-authentication.sql','database/canonical-crypto-registry.sql','database/generation-protected-registry-link.sql','database/generation-locked-retry.sql','database/generation-retry-producer-child.sql','database/generation-frozen-archive.sql']},'consumedRootSupport':{str(p.relative_to(ROOT)):sha(p.read_bytes()).hex()for p in [ROOT/'scripts/generation_auth_acceptance.py',ROOT/'scripts/generation_auth_crypto.py',ROOT/'scripts/generation_locked_retry.py',ROOT/'scripts/generation_admission_contracts.py',ROOT/'scripts/generation_retry_inventory.py',ROOT/'scripts/generation_basis_consumer.py',ROOT/'scripts/generation_native_graph.py',ROOT/'scripts/generation_frozen_archive.py',ROOT/'scripts/generation_read_hydration_archive.py',ROOT/'scripts/generation_create_consumer_archive.py',ROOT/'audit/generated/resume-34d/retry-graph/graph_current_fixtures.py',ROOT/'audit/generated/resume-d362/admission/generation_admission_fixtures.py',ROOT/'audit/generated/resume-d362/persistence/generation_descriptor_registry.py',ROOT/'audit/generated/resume-d362/persistence/context_fixture_exports.py',ROOT/'audit/generated/resume-34d/auth-crypto/libpq_fixture.py']},'candidateInputs':{str(p.relative_to(ROOT)):sha(p.read_bytes()).hex()for p in [Path(__file__),OUT/'native_auth_factory.py',OUT/'native_basis_factory.py',OUT/'generation-native-lineage.sql',OUT/'generation_locked_retry_admission.py',ledgerpath,archivepath,archivepath.parent/'generation_policy_package.py',archivepath.parent/'generation_own_kind_policy_v1.py']},'wholeOperationClosed':False,'limitations':['AUTH.TRANSPORT trusted ceiling producer OPEN;4096 fixtureonly','Canonical encrypted systemd actual source independent;randomfixturekeys do not prove it','Original SQL.HELPERS.CONCRETE_CALL_SITES generic wrapper not replaced by direct adapter','KnownTechnicalFailureResult current bounded FENCING_TOKEN_STALE producer is exercised; other predicates/phase lifecycle remain outside this proof','Source OWNER approval/graph/binding/budget/observation-schema producers and activation remain independent OPEN; archive availability is not semantic authority','GENERATION.AUTH.API_ACCEPTANCE lock-order OPEN: actual legacy auth receipt/context INSERT and implicit OWNER FK lock occur before C; bounded passing fixtures do not certify 51.6 order','Nonce recorded after seal in primitive fixture; real global producer ordering independent','Browser/UI/public gateway runtime not evaluated'],'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
(OUT/'native-retry-chain-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','checked':len(checks)}));db.close();target.close()
