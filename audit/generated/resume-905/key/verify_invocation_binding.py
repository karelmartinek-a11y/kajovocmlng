from pathlib import Path
import sys,tempfile,secrets,os,copy,json,hashlib
HERE=Path(__file__).parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from invocation_key_binding import load_bound_invocation_key
from generation_auth_crypto import profile_digest
checks=[]
with tempfile.TemporaryDirectory(prefix='kcml-key-loader-fixture-')as tmp:
 path=Path(tmp)/'kcml-master-key';key=secrets.token_bytes(32);path.write_bytes(key);path.chmod(0o400)
 r={'keyId':'isolated-key','keyGeneration':1,'keyFingerprint':hashlib.sha256(key).digest(),'serviceUnit':'isolated-fixture.service','credentialName':'kcml-master-key','cryptoProfileDigest':profile_digest()}
 m={'serviceUnit':'isolated-fixture.service','invocationId':'1'*32,'mainPid':os.getpid(),'effectiveCredentialGeneration':1,'credentialDirectory':tmp,'credentialName':'kcml-master-key'}
 def run(name,change=None,code=None):
  rr=copy.deepcopy(r);mm=copy.deepcopy(m)
  if change:change(rr,mm)
  try:actual=load_bound_invocation_key(rr,lambda service:mm,'1'*32);ok=code is None and actual==key;diag=None
  except ValueError as e:diag=str(e);ok=diag==code
  checks.append({'case':name,'passed':ok,'actualDiagnostic':diag,'expectedDiagnostic':code})
 run('actual-readonly-bytes-and-interface-positive')
 for name,change,code in [
 ('wrong-invocation',lambda r,m:m.update(invocationId='2'*32),'CRYPTO_INVOCATION_IDENTITY_MISMATCH'),
 ('wrong-process',lambda r,m:m.update(mainPid=os.getpid()+1),'CRYPTO_INVOCATION_IDENTITY_MISMATCH'),
 ('wrong-unit',lambda r,m:m.update(serviceUnit='other.service'),'CRYPTO_INVOCATION_SERVICE_MISMATCH'),
 ('wrong-credential-name',lambda r,m:m.update(credentialName='other-key'),'CRYPTO_INVOCATION_SERVICE_MISMATCH'),
 ('stale-generation',lambda r,m:m.update(effectiveCredentialGeneration=2),'CRYPTO_KEY_GENERATION_MISMATCH'),
 ('wrong-fingerprint',lambda r,m:r.update(keyFingerprint=bytes(32)),'CRYPTO_KEY_FINGERPRINT_MISMATCH'),
 ('wrong-profile',lambda r,m:r.update(cryptoProfileDigest=bytes(32)),'CRYPTO_KEY_PROFILE_MISMATCH'),
 ('extra-client-authority',lambda r,m:r.update(authorized=True),'CRYPTO_KEY_REGISTRY_MASK_INVALID')]:run(name,change,code)
 path.chmod(0o600);run('writable-materialization-rejected',code='SYSTEMD_CREDENTIAL_MATERIALIZATION_NOT_READ_ONLY');path.chmod(0o400)
 path.chmod(0o600);path.write_bytes(b'short');path.chmod(0o400);run('wrong-material-size',code='SYSTEMD_MASTER_KEY_SIZE_INVALID')
report={'status':'PASS'if all(c['passed']for c in checks)else'BLOCKED','checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'sourceDocumentSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'scope':'Actual readonly isolated file and key fingerprint plus synthetic manager-interface negative reference tests. Not authentic systemd provenance, root-encrypted source or verified bus-reader proof.','systemdSourceProof':'BLOCKED','wholeOperationClosed':False}
(HERE/'invocation-binding-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}))
