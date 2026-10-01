from pathlib import Path
import sys,json,hashlib,os,copy
ROOT=Path('/workspace/kajovocmlng');HERE=Path(__file__).parent;AUTHOR=ROOT/'audit/generated/resume-8cc/key'
sys.path.insert(0,str(AUTHOR))
program=(AUTHOR/'verify_key_receipts_pg.py').read_text().split('report={',1)[0]
program=program.replace("sql=(HERE/'key-invocation-receipts.sql').read_bytes();db.query(sql.decode())","sql=rs['database/canonical-key-invocation-receipts.sql']['raw'];assert sql==(HERE/'key-invocation-receipts.sql').read_bytes();db.query(sql.decode())")
program=program.replace('HERE=Path(__file__).parent;ROOT=HERE.parents[3]',"HERE=Path("+repr(str(AUTHOR))+");ROOT=Path('/workspace/kajovocmlng')").replace("name='key_receipts_8cc'","name='peer_key_receipts_archive_8cc_integrated'")
ns={'__file__':str(AUTHOR/'verify_key_receipts_pg.py')};exec(compile(program,'independent-reproduction-key-receipts-author','exec'),ns)
assert all(c['passed']for c in ns['checks']),ns['checks']
assert Path(ns['adapter'].__file__).resolve()==ROOT/'scripts/systemd_key_authority.py'
assert (ROOT/'scripts/systemd_key_authority.py').read_bytes()==(AUTHOR/'systemd_key_authority.py').read_bytes()
db=ns['db'];base=ns['base'];receipt=ns['receipt'];b=ns['b'];checks=[]
def run(name,sql,expected=None):
 db.query('BEGIN')
 try:db.query(sql);passed=expected is None;actual=None
 except Exception as e:actual=str(e);passed=expected is not None and expected in actual
 finally:db.query('ROLLBACK')
 checks.append({'id':name,'passed':passed,'expectedDiagnostic':expected,'actualDiagnostic':actual});assert passed,(name,actual)
# Verify actual narrow installer + publisher chain COMMIT and fresh-reader bytes.
db.query('BEGIN');db.query(base.split('INSERT INTO canonical_master_key_generation',1)[0]);db.query('SET LOCAL ROLE kcml_key_source_installer;INSERT INTO canonical_master_key_generation'+base.split('INSERT INTO canonical_master_key_generation',1)[1]);db.query('SET LOCAL ROLE kcml_key_invocation_publisher;'+receipt);db.query('COMMIT')
observer=ns['DB']('peer_key_receipts_archive_8cc_integrated');actual=observer.query("SELECT k.key_generation,r.key_generation,k.exact_service_unit,r.exact_service_unit,encode(s.encrypted_source_digest,'hex'),encode(r.encrypted_source_digest,'hex'),encode(k.key_fingerprint,'hex'),encode(r.observed_key_fingerprint,'hex') FROM canonical_master_key_generation k JOIN canonical_encrypted_key_source_version s USING(key_id)JOIN canonical_key_invocation_receipt r USING(key_id)")[0]
checks.append({'id':'restricted-roles-source-key-invocation-atomic-commit-fresh-observer','passed':actual[0]==actual[1] and actual[2]==actual[3] and actual[4]==actual[5] and actual[6]==actual[7]});assert checks[-1]['passed']
# Existing committed positive stays present; all independent bad receipts have distinct invocation IDs.
new=receipt.replace(b(bytes([1]*16)),b(bytes([2]*16)))
run('wrong-source-receipt-same-live-key',new.replace(b(ns['blob']),b(bytes([5]*32))),'key_receipt_encrypted_source_fkey')
run('wrong-source-record-key-identity',"INSERT INTO canonical_encrypted_key_source_version VALUES('unknown-key',"+b(ns['blob'])+",1,7,0,384,clock_timestamp());",'canonical_encrypted_key_source_version_key_id_fkey')
run('missing-authorized-purposes',new.replace("ARRAY['GENERATION_INITIAL_REQUEST','SECRET_IMMUTABLE_VERSION']","ARRAY[]::text[]"),'key_receipt_purpose_mask')
run('null-authorized-purpose',new.replace("ARRAY['GENERATION_INITIAL_REQUEST','SECRET_IMMUTABLE_VERSION']","ARRAY['GENERATION_INITIAL_REQUEST',NULL]"),'key_receipt_purpose_mask')
run('multidimensional-authorized-purpose',new.replace("ARRAY['GENERATION_INITIAL_REQUEST','SECRET_IMMUTABLE_VERSION']","ARRAY[['GENERATION_INITIAL_REQUEST','SECRET_IMMUTABLE_VERSION']]"),'key_receipt_purpose_mask')
run('direct-same-invocation-insert-cannot-overwrite-receipt',receipt.replace(',123,1234,',',456,1234,'),'canonical_key_invocation_receipt_pkey')
run('installer-cannot-publish-invocation','SET LOCAL ROLE kcml_key_source_installer;'+new,'permission denied')
run('publisher-cannot-register-source','SET LOCAL ROLE kcml_key_invocation_publisher;INSERT INTO canonical_encrypted_key_source_version SELECT * FROM canonical_encrypted_key_source_version;','permission denied')
run('public-auth-writer-cannot-publish-key-invocation','SET LOCAL ROLE kcml_authentication_writer;'+new,'permission denied')
run('source-metadata-immutable-update','UPDATE canonical_encrypted_key_source_version SET source_inode=999;','CANONICAL_CRYPTO_REGISTRY_IMMUTABLE')
# Explicit actual environment provider probe: no monkeypatches or alternative socket.
from systemd_key_authority import SystemdManagerObserver,AuthorityError
try:SystemdManagerObserver().observe('fixture-platform.service');provider='UNEXPECTED_PROVIDER_AVAILABLE'
except AuthorityError as e:provider=str(e)
assert provider=='SYSTEMD_MANAGER_NOT_PID1',provider
# Independent busctl subprocess binding inspection uses clearly synthetic stdout.
from unittest.mock import patch
import subprocess,systemd_key_authority as adapter
captured=[]
def subprocess_fixture(argv,**kwargs):
 captured.append(argv);return subprocess.CompletedProcess(argv,0,'{"type":"s","data":[":1.77"]}','')
with patch.dict(os.environ,{'DBUS_SYSTEM_BUS_ADDRESS':'unix:path=/tmp/untrusted-bus'}),patch.object(adapter.subprocess,'run',subprocess_fixture):
 parsed=SystemdManagerObserver()._bus('call','org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetNameOwner','s','org.freedesktop.systemd1')
checks.append({'id':'explicit-socket-address-not-inherited-environment','passed':parsed['data']==[':1.77'] and captured[0][1]=='--address=unix:path=/run/dbus/system_bus_socket' and all('/tmp/untrusted-bus'not in arg for arg in captured[0])});assert checks[-1]['passed']
report={'sourceDocumentSha256':hashlib.sha256(ns['raw']).hexdigest(),'head':'451b556067cb7cdd4f411cd742ab8fcaec8a379a','canonicalKeyInvocationBytesExecuted':True,'canonicalHelperPath':str(Path(ns['adapter'].__file__).resolve()),'candidateSqlSha256':hashlib.sha256((AUTHOR/'key-invocation-receipts.sql').read_bytes()).hexdigest(),'candidateHelperSha256':hashlib.sha256((AUTHOR/'systemd_key_authority.py').read_bytes()).hexdigest(),'reproducedAuthorChecks':len(ns['checks']),'independentChecks':checks,'pass':sum(c['passed']for c in checks),'fail':sum(not c['passed']for c in checks),'postgresqlVersion':db.query('SHOW server_version')[0][0],'providerStatus':'ENV_BLOCKED','providerDiagnostic':provider,'limitations':['Exact integrated canonical resource and root helper executed; source provider remains ENV_BLOCKED.','Restricted SQL role fixture bootstrap and synthetic encrypted-source digest/temporary key adapter are not root installer or systemd provider attestation.','Exact service LOGIN/membership/installer transport and key desired/effective rotation producer remain unmet; no defaults inferred.']}
(HERE/'peer-key-receipts-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'authorReproduced':report['reproducedAuthorChecks'],'independentPASS':report['pass'],'FAIL':report['fail'],'provider':provider}))
