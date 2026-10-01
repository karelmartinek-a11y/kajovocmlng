"""Parser/reference-interface proof only; no fake provider PASS."""
from pathlib import Path
import sys,os,json,copy,hashlib,tempfile,secrets
from unittest.mock import patch
HERE=Path(__file__).parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from systemd_key_authority import *
checks=[]
def check(name,fn,expected=None):
 try:fn();diag=None;ok=expected is None
 except AuthorityError as e:diag=str(e);ok=diag==expected
 checks.append({'case':name,'passed':ok,'expectedDiagnostic':expected,'actualDiagnostic':diag})
unit='fixture-platform.service';path='/org/freedesktop/systemd1/unit/fixture_2dplatform_2eservice'
properties={'Id':{'type':'s','data':[unit]},'ActiveState':{'type':'s','data':['active']},'InvocationID':{'type':'ay','data':[[1]*16]},'MainPID':{'type':'u','data':[os.getpid()]},'ExecMainStartTimestampMonotonic':{'type':'t','data':[100]}}
def reference_observe(change=None):
 obs=SystemdManagerObserver();obs.manager_owner=':1.7';ps=copy.deepcopy(properties)
 if change:change(ps)
 calls=[]
 def replies(*args):
  calls.append(args)
  if args[0]=='call':return {'type':'o','data':[path]}
  return ps[args[-1]]
 with patch.object(obs,'_bus',replies):result=obs.observe(unit)
 assert result['serviceUnit']==unit and all(args[1]==':1.7'for args in calls)
 return result
check('parser-reference-positive-unique-owner-pinned',reference_observe)
# Transport provenance must use the same exact Unix socket verified by establish,
# even if inherited D-Bus address variables name an unrelated socket.
from types import SimpleNamespace
captured=[]
def mock_run(argv,**kwargs):
 captured.append(argv);return SimpleNamespace(returncode=0,stdout='{"type":"s","data":["fixture"]}')
with patch.dict(os.environ,{'DBUS_SYSTEM_BUS_ADDRESS':'unix:path=/tmp/untrusted-bus'}),patch('systemd_key_authority.subprocess.run',mock_run):
 response=SystemdManagerObserver()._bus('call','org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetNameOwner','s','org.freedesktop.systemd1')
checks.append({'case':'untrusted-bus-environment-cannot-change-pinned-socket-argv','passed':captured[0][1]=='--address=unix:path=/run/dbus/system_bus_socket'and '--system'not in captured[0] and '/tmp/untrusted-bus'not in ' '.join(captured[0])})

for name,change,code in [
 ('wrong-exact-unit',lambda p:p['Id'].update(data=['other.service']),'SYSTEMD_EXACT_UNIT_NOT_ACTIVE'),
 ('inactive-unit',lambda p:p['ActiveState'].update(data=['inactive']),'SYSTEMD_EXACT_UNIT_NOT_ACTIVE'),
 ('null-invocation',lambda p:p['InvocationID'].update(data=[[0]*16]),'SYSTEMD_INVOCATION_CHANGED'),
 ('wrong-invocation-size',lambda p:p['InvocationID'].update(data=[[1]*15]),'SYSTEMD_INVOCATION_BYTES_INVALID'),
 ('boolean-main-pid',lambda p:p['MainPID'].update(data=[True]),'SYSTEMD_REPLY_TYPE_INVALID'),
 ('zero-pid',lambda p:p['MainPID'].update(data=[0]),'SYSTEMD_INVOCATION_CHANGED'),
 ('extra-authority-field',lambda p:p['Id'].update(authorized=True),'SYSTEMD_REPLY_MASK_INVALID'),
 ('wrong-signature',lambda p:p['Id'].update(type='o'),'SYSTEMD_REPLY_MASK_INVALID')]:check(name,lambda c=change:reference_observe(c),code)
obs=SystemdManagerObserver();obs.manager_owner=':1.7';seq=iter([{'type':'o','data':[path]},properties['Id'],properties['ActiveState'],properties['InvocationID'],properties['MainPID'],properties['ExecMainStartTimestampMonotonic'],{'type':'ay','data':[[2]*16]}])
with patch.object(obs,'_bus',lambda *args:next(seq)):check('restart-between-manager-reads',lambda:obs.observe(unit),'SYSTEMD_INVOCATION_CHANGED')
check('request-unit-path-injection',lambda:SystemdManagerObserver().observe('../malicious.service'),'SYSTEMD_EXACT_UNIT_INVALID')
check('request-callable-not-manager',lambda:load_observed_key(lambda service:True,{}, {},'GENERATION_INITIAL_REQUEST'),'SYSTEMD_OBSERVER_REQUIRED')
check('actual-nonroot-installer-denied-before-source-read',lambda:source_installation_metadata('/tmp/not-read'),'SYSTEMD_SOURCE_INSTALLER_NOT_ROOT')
fixture_key=secrets.token_bytes(32)
r={'keyId':'synthetic-version','keyGeneration':1,'keyFingerprint':hashlib.sha256(fixture_key).digest(),'serviceUnit':unit,'credentialName':'kcml-master-key','cryptoProfileDigest':profile_digest()}
actual={'managerUniqueOwner':':1.7','serviceUnit':unit,'invocationId':'01'*16,'mainPid':os.getpid(),'startMonotonicUsec':100}
receipt={'keyId':r['keyId'],'keyGeneration':1,'serviceUnit':unit,'invocationId':actual['invocationId'],'mainPid':os.getpid(),'startMonotonicUsec':100,'credentialDirectory':'/run/credentials/'+unit,'authorizedPurposes':['GENERATION_INITIAL_REQUEST'],'retiredForEncryption':False}
obs=SystemdManagerObserver()
for name,mut,code in [
 ('receipt-wrong-invocation',lambda r,p:p.update(invocationId='02'*16),'CRYPTO_INVOCATION_RECEIPT_STALE'),
 ('receipt-wrong-mainpid',lambda r,p:p.update(mainPid=os.getpid()+1),'CRYPTO_INVOCATION_RECEIPT_STALE'),
 ('receipt-wrong-generation',lambda r,p:p.update(keyGeneration=2),'CRYPTO_KEY_GENERATION_MISMATCH'),
 ('receipt-boolean-generation',lambda r,p:p.update(keyGeneration=True),'CRYPTO_INVOCATION_RECEIPT_MASK_INVALID'),
 ('record-boolean-generation',lambda r,p:r.update(keyGeneration=True),'CRYPTO_KEY_REGISTRY_MASK_INVALID'),
 ('receipt-wrong-key-id',lambda r,p:p.update(keyId='other-version'),'CRYPTO_KEY_GENERATION_MISMATCH'),
 ('purpose-unknown',lambda r,p:p.update(authorizedPurposes=['UNKNOWN']),'CRYPTO_KEY_PURPOSE_MASK_INVALID'),
 ('purpose-duplicate',lambda r,p:p.update(authorizedPurposes=['GENERATION_INITIAL_REQUEST']*2),'CRYPTO_KEY_PURPOSE_MASK_INVALID'),
 ('purpose-denied',lambda r,p:p.update(authorizedPurposes=['SECRET_IMMUTABLE_VERSION']),'CRYPTO_KEY_PURPOSE_DENIED'),
 ('receipt-client-directory',lambda r,p:p.update(credentialDirectory='/tmp/client-selected'),'SYSTEMD_CREDENTIAL_DIRECTORY_BINDING_INVALID'),
 ('wrong-profile',lambda r,p:r.update(cryptoProfileDigest=bytes(32)),'CRYPTO_KEY_PROFILE_MISMATCH')]:
 rr=copy.deepcopy(r);pp=copy.deepcopy(receipt);mut(rr,pp)
 with patch.object(obs,'observe',lambda unit:actual):check(name,lambda:load_observed_key(obs,rr,pp,'GENERATION_INITIAL_REQUEST'),code)
check('retired-key-new-seal-denied',lambda:assert_seal_authority(dict(receipt,retiredForEncryption=True)),'CRYPTO_RETIRED_KEY_ENCRYPTION_DENIED')
# Valid reference-only loader witness uses actual ephemeral readonly bytes;
# constructor path adaptation and manager replies are deliberately fixture-only.
import systemd_key_authority as adapter
real_key_loader=SystemdInvocationKey
with tempfile.TemporaryDirectory(prefix='kcml-key-adapter-reference-')as tmp:
 f=Path(tmp)/'kcml-master-key';f.write_bytes(fixture_key);f.chmod(0o400)
 with patch.object(obs,'observe',lambda unit:actual),patch.object(adapter,'SystemdInvocationKey',lambda directory,name:real_key_loader(tmp,name)):
  check('reference-loader-readonly-fingerprint-positive',lambda:load_observed_key(obs,r,receipt,'GENERATION_INITIAL_REQUEST'))
  check('reference-retained-key-readable-without-current-key-substitution',lambda:load_observed_key(obs,r,dict(receipt,retiredForEncryption=True),'GENERATION_INITIAL_REQUEST'))
report={'status':'PASS'if all(c['passed']for c in checks)else'BLOCKED','checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'sourceDocumentSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'helperSha256':hashlib.sha256((HERE/'systemd_key_authority.py').read_bytes()).hexdigest(),'proofScope':'Parser and deliberately patched reference manager replies; actual non-root source-installer denial and real temporary readonly bytes via explicitly fixture-only path adapter. NO live systemd provider positive, root-owned encrypted source, bus attestation, fingerprint materialization or registry publication proof.','providerStatus':'ENV_BLOCKED','wholeOperationClosed':False}
(HERE/'manager-adapter-reference-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}))
