"""Run only via actual isolated root system-manager transient service."""
import os,stat,json,hashlib
from pathlib import Path
fd=os.open(Path(os.environ['CREDENTIALS_DIRECTORY'])/'kcml-master-key',os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
try:
 st=os.fstat(fd);key=bytearray(os.read(fd,33))
 assert stat.S_ISREG(st.st_mode) and not st.st_mode&0o222 and len(key)==32
 receipt={'invocationId':os.environ['INVOCATION_ID'],'pid':os.getpid(),'uid':os.geteuid(),'readOnly':True,'exact32ByteSyntheticCredential':True,'syntheticKeyFingerprintSha256':hashlib.sha256(key).hexdigest()}
 print(json.dumps(receipt),flush=True)
finally:
 if 'key'in globals():
  for i in range(len(key)):key[i]=0
 os.close(fd)
