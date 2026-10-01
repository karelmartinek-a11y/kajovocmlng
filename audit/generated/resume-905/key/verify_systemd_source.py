"""Safe current-host mechanism probe; no root/production source read or modification."""
from pathlib import Path
import os,subprocess,tempfile,secrets,json,hashlib,shutil
HERE=Path(__file__).parent;ROOT=HERE.parents[3]
def call(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=10)
 return {'command':args,'exitCode':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()}
checks=[call(['systemd-creds','--version']),call(['systemctl','is-system-running']),call(['systemctl','--user','is-system-running'])]
with tempfile.TemporaryDirectory(prefix='kcml-isolated-key-probe-')as tmp:
 p=Path(tmp);key=p/'synthetic';key.write_bytes(secrets.token_bytes(32));key.chmod(0o600)
 checks.append(call(['systemd-creds','encrypt','--user','--with-key=host','--name=kcml-master-key',str(key),str(p/'encrypted')]))
report={'status':'BLOCKED','blockerType':'ENVIRONMENT','remainingId':'GENERATION_KEY_SYSTEMD_SOURCE_FIXTURE','sourceDocumentSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'uid':os.geteuid(),'pid1':Path('/proc/1/comm').read_text().strip(),'sockets':{p:Path(p).exists()for p in ['/run/systemd/private','/run/dbus/system_bus_socket','/run/user/1000/bus']},'containerTools':{p:shutil.which(p)for p in ['docker','podman','qemu-system-x86_64']},'checks':checks,'rootOwnedEncryptedSourceVerified':False,'readOnlyInvocationVerified':False,'scope':'Actual user-host encrypt attempted only with random temporary isolated key, deleted automatically. No manager means root system source/per-invocation materialization cannot be established. User encryption is not canonical proof; no alternate/null backend used.'}
(HERE/'systemd-source-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'uid':report['uid'],'pid1':report['pid1'],'encryptExit':checks[-1]['exitCode']}))
