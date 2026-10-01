from pathlib import Path
import sys,subprocess,json,hashlib
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
P=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-v','ON_ERROR_STOP=1','-At','-d','secret_owner_review_905']
def run(sql):return subprocess.run(P,input=sql,text=True,capture_output=True)
assert (OUT/'owner-secret-binding.sql').read_bytes()==resource_index()['database/secret-owner-binding.sql']['raw'], 'canonical owner binding byte mismatch'
cases=[]
def reject(i,sql,code):
 q=run(sql);assert q.returncode!=0 and code in q.stderr,(i,q.stderr)
 cases.append({'id':i,'status':'PASS','actualDiagnostic':code})
sid='11111111-1111-4111-8111-111111111111';other='22222222-2222-4222-8222-222222222222'
q=run('SELECT count(*) FROM owner_api_credential;');assert q.stdout.strip()=='1';cases.append({'id':'genuine-committed-positive-baseline','status':'PASS'})
reject('wrong-owner-secret-root',f"UPDATE owner_api_credential SET secret_id='{other}';",'owner_credential_secret_version_fk')
reject('root-type-changed',"UPDATE kcml_secret_v1.secret_record SET secret_type='PASSWORD';",'secret_active_version_owns_parent')
reject('version-type-changed',"UPDATE kcml_secret_v1.secret_version SET secret_type='PASSWORD';",'SECRET_VERSION_CRYPTO_IMMUTABLE')
reject('root-active-version-changed',f"UPDATE kcml_secret_v1.secret_record SET active_version_id='{other}';",'secret_active_version_owns_parent')
reject('version-deactivated',"UPDATE kcml_secret_v1.secret_version SET lifecycle='RETIRED',retired_at=now();",'OWNER_CREDENTIAL_SECRET_BINDING_MISMATCH')
# Observe missing producer enforcement truthfully: non-equal arbitrary head
# versions/epochs are accepted by the bounded identity trigger, not PASS of the
# normative atomic rotation. Roll back both probes to preserve baseline.
observed=[]
for field in ['credential_version','credential_activation_epoch']:
 q=run(f'BEGIN;UPDATE owner_api_credential SET {field}={field}+99;ROLLBACK;')
 observed.append({'id':field+'-producer-not-enforced','accepted':q.returncode==0,'status':'OPEN','authority':'SSOT §51.20 atomic rotation/deferred consistency; cannot infer equality to Secret version_number because reactivation is permitted','scope':'Identity-only candidate expressly leaves monotonic epoch/version rotation producer unresolved'})
 assert q.returncode==0,q.stderr
q=run("SELECT credential_version,credential_activation_epoch FROM owner_api_credential;");assert q.stdout.strip()=='1|1';cases.append({'id':'all-rejected-mutations-rolled-back-baseline-unchanged','status':'PASS'})
report={'checked':len(cases),'failed':0,'cases':cases,'openProducerObservations':observed,'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'postgresVersion':run('SHOW server_version').stdout.strip(),'candidateSqlHashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'owner-secret-binding.sql',OUT/'secret-profile-publication.sql']},'wholeOperationClosed':False,'canonicalIntegratedSqlExecuted':True,'canonicalByteEqualityVerified':True,'scope':'Extra independently derived actual PG negatives against exact candidate SQL, canonical roots. No authenticated broker/crypto/rotation proof.'}
(OUT/'additional-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':len(cases),'failed':0,'openProducerObservations':len(observed)}))
