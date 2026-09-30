from pathlib import Path
import sys,json,hashlib
HERE=Path(__file__).parent;ROOT=Path(__file__).resolve().parents[5];AUTHOR=ROOT/'audit/generated/resume-34d/auth-crypto';sys.path.insert(0,str(AUTHOR))
p=AUTHOR/'verify_authenticated_full_chain.py';original=p.read_text();program=original.replace("database='auth_crypto_full_34d'","database='review_auth_chain_34d'").replace("(HERE/'authenticated-full-chain-proof.json').write_text", "(review_out/'authenticated-chain-review.json').write_text")
# Additional independent mutations are injected only after real persisted-row
# hydration succeeded. They do not replace installed SQL or actual producer bytes.
needle="version=db.query('SHOW server_version')[0][0]"
additional='''
from generation_read_hydration import hydrate_storage
storage=json.loads(db.query('SELECT kcml_generation_create_read_storage_v1('+lit(owner)+','+lit(ns['job'])+')')[0][0])
def authenticated_storage_open(snapshot_id,ref):
 assert snapshot_id==actual['snapshotId'] and ref['contentDigest']==actual['contentDigest'] and ref['schemaId']==actual['requestSchemaId'] and ref['schemaDigest']==actual['requestSchemaDigest']
 with open_snapshot(e,key,'fixture-systemd-key-generation-1',actual,consumer) as view:return bytes(view)
result=hydrate_storage(storage,selected_job_id=ns['job'],authenticated_owner_id=owner,open_snapshot=authenticated_storage_open)
rec('independent-entire-current-auth-persist-read-open-native-consumer-chain',result['jobId']==ns['job']and result['executionApproved']is False and result['activationAuthorized']is False)
for field,expected in [('selectedJob','READ_JOB_IDENTITY_MISMATCH'),('owner','GENERATION_READ_OWNER_MISMATCH'),('event','GENERATION_READ_EVENT_IDENTITY_MISMATCH')]:
 wrong=copy.deepcopy(storage); selected=ns['job']; reader=owner
 if field=='selectedJob':selected='99999999-9999-4999-8999-999999999999'
 elif field=='owner':reader='99999999-9999-4999-8999-999999999999'
 else:wrong['event']['id']='99999999-9999-4999-8999-999999999999'
 try:hydrate_storage(wrong,selected_job_id=selected,authenticated_owner_id=reader,open_snapshot=authenticated_storage_open);rec('independent-read-'+field,False)
 except Exception as ex:rec('independent-read-'+field,getattr(ex,'code',None)==expected,str(ex))
for field,value in [('jobId','99999999-9999-4999-8999-999999999999'),('trustedContextId','99999999-9999-4999-8999-999999999999'),('applicationDeploymentEpoch',2)]:
 altered=copy.deepcopy(actual);altered[field]=value
 try:
  with open_snapshot(e,key,'fixture-systemd-key-generation-1',altered,consumer):pass
  rec('independent-persisted-hydration-identity-'+field,False)
 except ValueError as ex:rec('independent-persisted-hydration-identity-'+field,str(ex)=='PROTECTED_INPUT_AUTHENTICATION_FAILED',str(ex))
version=db.query('SHOW server_version')[0][0]
'''
assert needle in program;program=program.replace(needle,additional)
program=program.replace("db.query('DROP SCHEMA public CASCADE;CREATE SCHEMA public;')","db.query('DROP SCHEMA public CASCADE;DROP SCHEMA IF EXISTS kcml_retry_v1 CASCADE;CREATE SCHEMA public;')")
needle_install='db.query(auth_sql.decode());'
assert program.count(needle_install)==1,'EXACT_CURRENT_INSTALLATION_HOOK_UNRESOLVED'
program=program.replace(needle_install,"[db.query(rs[path]['raw'].decode()) for path in integrated_paths];\nassert db.query(\"SELECT count(*)FROM pg_proc WHERE proname='kcml_generation_create_read_storage_v1'\")[0][0]=='1';\nassert db.query(\"SELECT count(*) FROM information_schema.tables WHERE table_schema='kcml_retry_v1' AND table_name='phase'\")[0][0]=='1';\nassert db.query(\"SELECT count(*) FROM information_schema.tables WHERE table_schema='public'AND table_name='generation_create_preroot_outcome'\")[0][0]=='1';")
# Current integrated root implementation rather than candidate code modules.
program=program.replace('from auth_crypto_reference import *','from generation_auth_crypto import *').replace('from acceptance_reference import authenticate_owner_api','from generation_auth_acceptance import authenticate_owner_api')
# libpq_fixture remains the isolated adapter; domainlogic imports rootmodules.
integrated_paths=['database/generation-create-authentication.sql','database/generation-create-preroot.sql','database/generation-create-read.sql','database/generation-locked-retry.sql']
ns={'__file__':str(p),'review_out':HERE,'integrated_paths':integrated_paths};exec(compile(program,str(p),'exec'),ns)
r=json.loads((HERE/'authenticated-chain-review.json').read_text());r['integratedSqlDigests']={path:ns['rs'][path]['sha256']for path in integrated_paths};r['rootImplementationDigests']={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest()for name in ['generation_auth_crypto.py','generation_auth_acceptance.py','generation_read_hydration.py','generation_create_consumer.py']};r.update(independentDatabase='review_auth_chain_34d',originalVerifierSha256=hashlib.sha256(original.encode()).hexdigest(),executedReviewProgramSha256=hashlib.sha256(program.encode()).hexdigest(),independentScope='Actual canonicalfoundation installedunchanged+authscopeextension; fresh isolated PG verification through full token→root/event/outbox/audit→canonicalSQLread→rootread_hydration→actualAESopening→rootnativeconsumer; selectedjob/OWNER/event plusthreeidentityAADmutants; systemdmaterialization remainsBLOCKED')
(HERE/'authenticated-chain-review.json').write_text(json.dumps(r,indent=2)+'\n')
