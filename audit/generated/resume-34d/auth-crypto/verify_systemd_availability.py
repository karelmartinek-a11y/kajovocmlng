"""Execute real systemd-creds attempt; managerless environment is BLOCKED, not PASS."""
from pathlib import Path
import tempfile,secrets,os,subprocess,json,hashlib
HERE=Path(__file__).parent;ROOT=HERE.parents[3];ssot=ROOT/'00_SSOT/KajovoCMLNG_SSOT.md'
version=subprocess.run(['systemd-creds','--version'],capture_output=True,text=True).stdout.splitlines()[0]
pid1=Path('/proc/1/comm').read_text().strip()
with tempfile.TemporaryDirectory(prefix='kcml-systemd-fixture-')as tmp:
 p=Path(tmp);key=p/'synthetic';key.write_bytes(secrets.token_bytes(32));os.chmod(key,0o600)
 q=subprocess.run(['systemd-creds','encrypt','--user','--with-key=host','--name=kcml-master-key',str(key),str(p/'encrypted')],capture_output=True,text=True)
 report={'sourceDocumentSha256':hashlib.sha256(ssot.read_bytes()).hexdigest(),'status':'BLOCKED','blockerType':'AUDIT_ENVIRONMENT_REQUIRED_CANONICAL_MECHANISM_UNAVAILABLE','systemdVersion':version,'pid1':pid1,'uid':os.geteuid(),'actualCommand':'systemd-creds encrypt --user --with-key=host --name=kcml-master-key synthetic encrypted','exitCode':q.returncode,'diagnostic':q.stderr.strip(),'rootOwnedSystemEncryptedSourceVerified':False,'readOnlyPerInvocationMaterializationVerified':False,'noNullKeyOrAlternateHostMechanismUsed':True,'scope':'Actual supported user-host mechanism probe only. Cannot create/verify canonical root-owned system source or service invocation in managerless isolated environment. AES reference is not a replacement. Required A fixture stays BLOCKED.'}
 (HERE/'systemd-availability-proof.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'exitCode':q.returncode,'diagnostic':q.stderr.strip()}))
