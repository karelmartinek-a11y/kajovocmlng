from pathlib import Path
import sys, subprocess, hashlib, json, concurrent.futures
ROOT=Path('/workspace/kajovocmlng'); OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT, resource_index
from secret_profile_reference import INVENTORY,SCHEMA,compiled_schema_bytes
from secret_profile_import import registry_profile
source=SSOT.read_bytes(); resources=resource_index(); canonical=resources['database/secret-profile-roots.sql']['raw']
candidate=(OUT/'secret-profile-publication.sql').read_bytes()
assert candidate==resources['database/secret-profile-publication.sql']['raw'], 'canonical publication byte mismatch'
BASE=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-v','ON_ERROR_STOP=1','-At']
def run(sql,db='secret_publication_review_905'):
 return subprocess.run(BASE+['-d',db],input=sql,text=True,capture_output=True)
q=run("SELECT 1 FROM pg_database WHERE datname='secret_publication_review_905'",'postgres')
if not q.stdout.strip(): assert run('CREATE DATABASE secret_publication_review_905','postgres').returncode==0
q=run('DROP SCHEMA IF EXISTS kcml_secret_v1 CASCADE;\n'+canonical.decode()+'\n'+candidate.decode()); assert q.returncode==0,q.stderr
cases=[]
def check(name,sql,expected=None):
 r=run(sql); good=(r.returncode==0 if expected is None else r.returncode!=0 and expected in r.stderr)
 cases.append({'id':name,'status':'PASS' if good else 'FAIL','expectedDiagnostic':expected,'actualDiagnostic':r.stderr.strip()[-450:] if not good else None})
 if not good: raise AssertionError((name,r.stderr,r.stdout))
review=(ROOT/'audit/generated/resume-34d/review/secret-current/secret-native-review.json').read_bytes()
def b(x):return "decode('"+x.hex()+"','hex')"
def call(profile,rev=review,src=source,sections="ARRAY['§8.12']"):
 typ=INVENTORY[profile]['secretType']; raw=compiled_schema_bytes(profile)
 return "SELECT encode(kcml_secret_v1.publish_profile_v1('"+typ+"','"+profile+"','"+SCHEMA['$id']+'#/$defs/'+profile+"',"+b(raw)+','+b(hashlib.sha256(src).digest())+','+b(rev)+','+sections+"),'hex');"
p=next(iter(INVENTORY))
check('public_cannot_publish',"SET SESSION AUTHORIZATION nobody;"+call(p),'permission denied') if run("SELECT 1 FROM pg_roles WHERE rolname='nobody'",'postgres').stdout.strip() else None
run("DO $$BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_secret_untrusted_fixture') THEN CREATE ROLE kcml_secret_untrusted_fixture NOLOGIN; END IF; END$$; GRANT USAGE ON SCHEMA kcml_secret_v1 TO kcml_secret_untrusted_fixture;")
check('untrusted_publish_denied',"SET SESSION AUTHORIZATION kcml_secret_untrusted_fixture;"+call(p),'permission denied for function')
check('publisher_cannot_direct_insert',"SET SESSION AUTHORIZATION kcml_secret_profile_publisher; INSERT INTO kcml_secret_v1.secret_value_profile_registry(secret_type) VALUES ('TOTP_SEED');",'permission denied for table')
check('valid_publication_explicit_rollback',"SET SESSION AUTHORIZATION kcml_secret_profile_publisher; BEGIN;"+call(p)+"ROLLBACK;")
assert run('SELECT count(*) FROM kcml_secret_v1.secret_value_profile_registry').stdout.strip()=='0'
assert run('SELECT count(*) FROM kcml_secret_v1.profile_publication_archive').stdout.strip()=='0'
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 first_results=list(pool.map(lambda _:run("SET SESSION AUTHORIZATION kcml_secret_profile_publisher;"+call(p)),range(2)))
cases.append({'id':'two_concurrent_first_publications','status':'PASS' if all(x.returncode==0 for x in first_results) else 'FAIL'})
ACTIVE_PROFILES=[p for p in INVENTORY if p!='BROWSER_AUTH_STATE_GRAPH_V1']
for p in ACTIVE_PROFILES: check('publish_'+p,"SET SESSION AUTHORIZATION kcml_secret_profile_publisher;"+call(p))
check('unactivated_full_browser_rejected',"SET SESSION AUTHORIZATION kcml_secret_profile_publisher;"+call('BROWSER_AUTH_STATE_GRAPH_V1'),'secret_value_profile_registry_check1')
p=next(iter(INVENTORY))
check('null_type_rejected',"SET SESSION AUTHORIZATION kcml_secret_profile_publisher;"+call(p).replace("'"+INVENTORY[p]['secretType']+"'",'NULL',1),'SECRET_PROFILE_PUBLICATION_INPUT_INVALID')
check('null_profile_rejected',"SET SESSION AUTHORIZATION kcml_secret_profile_publisher;"+call(p).replace("'"+p+"'",'NULL',1),'SECRET_PROFILE_PUBLICATION_INPUT_INVALID')
check('exact_replay',"SET SESSION AUTHORIZATION kcml_secret_profile_publisher;"+call(p))
check('changed_review_replay',"SET SESSION AUTHORIZATION kcml_secret_profile_publisher;"+call(p,b'changed'),'SECRET_PROFILE_PUBLICATION_REPLAY_CONFLICT')
check('changed_source_replay',"SET SESSION AUTHORIZATION kcml_secret_profile_publisher;"+call(p,src=b'changed'),'SECRET_PROFILE_PUBLICATION_REPLAY_CONFLICT')
check('missing_review',"SET SESSION AUTHORIZATION kcml_secret_profile_publisher;"+call(p,b''),'SECRET_PROFILE_PUBLICATION_INPUT_INVALID')
check('missing_source_sections',"SET SESSION AUTHORIZATION kcml_secret_profile_publisher;"+call(p,sections='ARRAY[]::text[]'),'SECRET_PROFILE_PUBLICATION_INPUT_INVALID')
check('publication_archive_immutable',"UPDATE kcml_secret_v1.profile_publication_archive SET source_sections=ARRAY['other'];",'SECRET_PROFILE_PUBLICATION_IMMUTABLE')
check('registry_definition_immutable',"DELETE FROM kcml_secret_v1.secret_value_profile_registry;",'SECRET_PROFILE_DEFINITION_IMMUTABLE')
# Delete neither prior row: exact concurrent replay is a write-free observation.
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(lambda _:run("SET SESSION AUTHORIZATION kcml_secret_profile_publisher;"+call(p)),range(2)))
cases.append({'id':'two_concurrent_exact_replays','status':'PASS' if all(x.returncode==0 for x in results) else 'FAIL'})
q=run("SELECT count(*),count(DISTINCT publisher_principal),bool_and(schema_digest=sha256(schema_document_bytes) AND review_evidence_digest=sha256(review_evidence_bytes)) FROM kcml_secret_v1.profile_publication_archive;")
assert q.stdout.strip()=='10|1|t',q.stdout
cases.append({'id':'ten_archived_exact_trusted_publications','status':'PASS'})
for profile in ACTIVE_PROFILES:
 raw=compiled_schema_bytes(profile); typ=INVENTORY[profile]['secretType']
 q=run("SET SESSION AUTHORIZATION kcml_secret_profile_reader; SELECT kcml_secret_v1.read_published_profile_v1('"+typ+"','"+profile+"',"+b(hashlib.sha256(raw).digest())+");")
 assert q.returncode==0,q.stderr
 row=json.loads(q.stdout.strip().splitlines()[-1]);row['schemaBytes']=bytes.fromhex(row['schemaBytes'])
 actual=registry_profile(profile,lambda _:row,'sha256:'+hashlib.sha256(source).hexdigest(),'sha256:'+hashlib.sha256(review).hexdigest())
 assert actual==row
 cases.append({'id':'database_publication_to_native_registry/'+profile,'status':'PASS'})
report={'status':'PASS' if all(x['status']=='PASS' for x in cases) else 'BLOCKED','checked':len(cases),'failed':sum(x['status']!='PASS' for x in cases),'cases':cases,'sourceSha256':hashlib.sha256(source).hexdigest(),'sourceUnchangedDuringRun':SSOT.read_bytes()==source,'canonicalSecretRootsSha256':hashlib.sha256(canonical).hexdigest(),'candidatePublicationSqlSha256':hashlib.sha256(candidate).hexdigest(),'canonicalEmbeddedRootsExecuted':True,'publicationCandidateExecuted':True,'canonicalIntegratedSqlExecuted':True,'canonicalByteEqualityVerified':True,'postgresVersion':run('SHOW server_version').stdout.strip(),'wholeOperationClosed':False,'proofScope':'Actual ACL-isolated trusted publication and exact immutable schema/review archive, not semantic approval, authenticator, key authority, Secret acceptance, or broker','reviewArtifactSourceSha256':json.loads(review).get('sourceDocumentSha256'),'reviewArtifactSha256':hashlib.sha256(review).hexdigest(),'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
(OUT/'publication-postgres-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','checked','failed','postgresVersion','sourceUnchangedDuringRun']}))
