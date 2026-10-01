"""Restricted system-manager observer; key/credential paths are server installation data.
No request callback/mapping can substitute for the manager observer. Local parser
fixtures do not attest the real provider. Historical retained encrypted sources
use the same canonical systemd mechanism, never a plaintext/ENV key fallback.
"""
from pathlib import Path
import hashlib,json,os,re,socket,stat,struct,subprocess
from generation_auth_crypto import SystemdInvocationKey,profile_digest
class AuthorityError(ValueError):pass
def fail(code):raise AuthorityError(code)
def typed(response,signature):
 if type(response)is not dict or set(response)!={'type','data'} or response['type']!=signature or type(response['data'])is not list or len(response['data'])!=1:fail('SYSTEMD_REPLY_MASK_INVALID')
 value=response['data'][0]
 if signature in('s','o') and type(value)is not str:fail('SYSTEMD_REPLY_TYPE_INVALID')
 if signature in('u','t') and(type(value)is not int or value<0):fail('SYSTEMD_REPLY_TYPE_INVALID')
 if signature=='ay' and(type(value)is not list or len(value)!=16 or any(type(v)is not int or not 0<=v<=255 for v in value)):fail('SYSTEMD_INVOCATION_BYTES_INVALID')
 return value
class SystemdManagerObserver:
 SOCKET='/run/dbus/system_bus_socket'
 def __init__(self):self.manager_owner=None
 def _bus(self,*args):
  try:r=subprocess.run(['/usr/bin/busctl','--address=unix:path='+self.SOCKET,'--json=short','--timeout=5',*args],capture_output=True,text=True,timeout=6,check=False)
  except(OSError,subprocess.TimeoutExpired):fail('SYSTEMD_MANAGER_UNAVAILABLE')
  if r.returncode:fail('SYSTEMD_MANAGER_QUERY_FAILED')
  try:return json.loads(r.stdout)
  except(json.JSONDecodeError,UnicodeError):fail('SYSTEMD_REPLY_ENCODING_INVALID')
 def _call(self,destination,path,interface,method,signature,*args):
  return self._bus('call',destination,path,interface,method,signature,*args)
 def establish(self):
  # Pin socket owner/peer and well-known name's unique owner. Further calls use
  # the unique owner, so name replacement cannot redirect a multi-call read.
  if Path('/proc/1/comm').read_text().strip()!='systemd':fail('SYSTEMD_MANAGER_NOT_PID1')
  try:
   st=os.lstat(self.SOCKET)
   if not stat.S_ISSOCK(st.st_mode)or st.st_uid!=0:fail('SYSTEMD_BUS_SOURCE_INVALID')
   with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)as conn:
    conn.settimeout(5);conn.connect(self.SOCKET);pid,uid,gid=struct.unpack('3i',conn.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
    if uid!=0:fail('SYSTEMD_BUS_PEER_INVALID')
  except OSError:fail('SYSTEMD_MANAGER_UNAVAILABLE')
  dest='org.freedesktop.DBus';path='/org/freedesktop/DBus';iface=dest
  owner=typed(self._call(dest,path,iface,'GetNameOwner','s','org.freedesktop.systemd1'),'s')
  if not re.fullmatch(r':[0-9]+\.[0-9]+',owner):fail('SYSTEMD_MANAGER_OWNER_INVALID')
  uid=typed(self._call(dest,path,iface,'GetConnectionUnixUser','s',owner),'u')
  pid=typed(self._call(dest,path,iface,'GetConnectionUnixProcessID','s',owner),'u')
  if uid!=0 or pid!=1:fail('SYSTEMD_MANAGER_OWNER_INVALID')
  self.manager_owner=owner
 def observe(self,exact_unit):
  if type(exact_unit)is not str or not re.fullmatch(r'[A-Za-z0-9_.:@\\-]+\.service',exact_unit):fail('SYSTEMD_EXACT_UNIT_INVALID')
  if self.manager_owner is None:self.establish()
  owner=self.manager_owner
  path=typed(self._call(owner,'/org/freedesktop/systemd1','org.freedesktop.systemd1.Manager','GetUnit','s',exact_unit),'o')
  if not re.fullmatch(r'/org/freedesktop/systemd1/unit/[A-Za-z0-9_]+',path):fail('SYSTEMD_UNIT_OBJECT_INVALID')
  def prop(iface,name,signature):return typed(self._bus('get-property',owner,path,iface,name),signature)
  unit='org.freedesktop.systemd1.Unit';service='org.freedesktop.systemd1.Service'
  if prop(unit,'Id','s')!=exact_unit or prop(unit,'ActiveState','s')!='active':fail('SYSTEMD_EXACT_UNIT_NOT_ACTIVE')
  first=bytes(prop(unit,'InvocationID','ay')).hex();pid=prop(service,'MainPID','u');start=prop(service,'ExecMainStartTimestampMonotonic','t')
  second=bytes(prop(unit,'InvocationID','ay')).hex()
  if first!=second or first=='0'*32 or pid<=0 or start<=0:fail('SYSTEMD_INVOCATION_CHANGED')
  return {'managerUniqueOwner':owner,'serviceUnit':exact_unit,'invocationId':first,'mainPid':pid,'startMonotonicUsec':start}

def source_installation_metadata(source):
 """Run only by canonical root installer against its exact encrypted source.
 Does not decrypt/print source; caller supplies no plaintext or authority flags.
 """
 if os.geteuid()!=0:fail('SYSTEMD_SOURCE_INSTALLER_NOT_ROOT')
 fd=os.open(source,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
 try:
  st=os.fstat(fd)
  if not stat.S_ISREG(st.st_mode)or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=0o600:fail('SYSTEMD_ENCRYPTED_SOURCE_OWNERSHIP_INVALID')
  hashed=hashlib.sha256();size=0
  while chunk:=os.read(fd,65536):hashed.update(chunk);size+=len(chunk)
  after=os.fstat(fd)
  if size==0:fail('SYSTEMD_ENCRYPTED_SOURCE_EMPTY')
  if (st.st_size,st.st_mtime_ns,st.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):fail('SYSTEMD_ENCRYPTED_SOURCE_CHANGED')
  return {'encryptedSourceDigest':hashed.digest(),'sourceUid':st.st_uid,'sourceMode':stat.S_IMODE(st.st_mode),'device':st.st_dev,'inode':st.st_ino}
 finally:os.close(fd)

def load_observed_key(observer,key_record,receipt,purpose):
 """Inputs are trusted locked DB rows, never public native request members.
 receipt binds confirmed systemd invocation to installed desired generation.
 No arbitrary callable/authorized flag is accepted as manager authority.
 """
 if type(observer)is not SystemdManagerObserver:fail('SYSTEMD_OBSERVER_REQUIRED')
 required={'keyId','keyGeneration','keyFingerprint','serviceUnit','credentialName','cryptoProfileDigest'}
 if type(key_record)is not dict or set(key_record)!=required:fail('CRYPTO_KEY_REGISTRY_MASK_INVALID')
 if type(key_record['keyGeneration'])is not int or key_record['keyGeneration']<1 or any(type(key_record[n])is not str or not key_record[n]for n in('keyId','serviceUnit','credentialName')) or type(key_record['keyFingerprint'])is not bytes or len(key_record['keyFingerprint'])!=32:fail('CRYPTO_KEY_REGISTRY_MASK_INVALID')
 fields={'keyId','keyGeneration','serviceUnit','invocationId','mainPid','startMonotonicUsec','credentialDirectory','authorizedPurposes','retiredForEncryption'}
 if type(receipt)is not dict or set(receipt)!=fields:fail('CRYPTO_INVOCATION_RECEIPT_MASK_INVALID')
 if type(receipt['keyGeneration'])is not int or receipt['keyGeneration']<1 or type(receipt['retiredForEncryption'])is not bool:fail('CRYPTO_INVOCATION_RECEIPT_MASK_INVALID')
 purposes=receipt['authorizedPurposes']
 if type(purposes)is not list or any(type(p)is not str or p not in('GENERATION_INITIAL_REQUEST','SECRET_IMMUTABLE_VERSION')for p in purposes)or len(set(purposes))!=len(purposes):fail('CRYPTO_KEY_PURPOSE_MASK_INVALID')
 actual=observer.observe(key_record['serviceUnit'])
 for name in('serviceUnit','invocationId','mainPid','startMonotonicUsec'):
  if receipt[name]!=actual[name]:fail('CRYPTO_INVOCATION_RECEIPT_STALE')
 if actual['mainPid']!=os.getpid():fail('CRYPTO_INVOCATION_PROCESS_MISMATCH')
 if receipt['keyId']!=key_record['keyId']or receipt['keyGeneration']!=key_record['keyGeneration']:fail('CRYPTO_KEY_GENERATION_MISMATCH')
 if purpose not in('GENERATION_INITIAL_REQUEST','SECRET_IMMUTABLE_VERSION')or type(receipt['authorizedPurposes'])is not list or purpose not in receipt['authorizedPurposes']:fail('CRYPTO_KEY_PURPOSE_DENIED')
 if receipt['credentialDirectory']!='/run/credentials/'+actual['serviceUnit']:fail('SYSTEMD_CREDENTIAL_DIRECTORY_BINDING_INVALID')
 if key_record['cryptoProfileDigest']!=profile_digest():fail('CRYPTO_KEY_PROFILE_MISMATCH')
 raw=SystemdInvocationKey(receipt['credentialDirectory'],key_record['credentialName']).load()
 if hashlib.sha256(raw).digest()!=key_record['keyFingerprint']:fail('CRYPTO_KEY_FINGERPRINT_MISMATCH')
 return raw

def assert_seal_authority(receipt):
 if receipt['retiredForEncryption'] is not False:fail('CRYPTO_RETIRED_KEY_ENCRYPTION_DENIED')

def publish_current_invocation(db,observer,server_selected_key_id):
 """Actual observer→DB producer candidate. Invoke within acceptance/install TX.
 Key selection comes from locked server retained/current authority, not HTTP.
 No client source path, fingerprint, purpose list, invocation mapping or flags.
 SQL installation/current-role provenance remains a mandatory separate fixture.
 """
 if type(observer)is not SystemdManagerObserver:fail('SYSTEMD_OBSERVER_REQUIRED')
 if db.transaction_status()!=2:fail('CRYPTO_KEY_PUBLICATION_TRANSACTION_REQUIRED')
 if type(server_selected_key_id)is not str or not server_selected_key_id or '\0'in server_selected_key_id:fail('CRYPTO_KEY_ID_INVALID')
 def lit(value):return "'"+value.replace("'","''")+"'"
 rows=db.query("SELECT k.key_id,k.key_generation,k.exact_service_unit,k.systemd_credential_name,encode(k.key_fingerprint,'hex'),encode(k.crypto_profile_digest,'hex'),encode(s.encrypted_source_digest,'hex') FROM canonical_master_key_generation k JOIN canonical_encrypted_key_source_version s ON s.key_id=k.key_id WHERE k.key_id="+lit(server_selected_key_id))
 if len(rows)!=1:fail('CRYPTO_INSTALLED_KEY_AUTHORITY_UNAVAILABLE')
 row=rows[0];generation=int(row[1]);actual=observer.observe(row[2])
 if actual['mainPid']!=os.getpid():fail('CRYPTO_INVOCATION_PROCESS_MISMATCH')
 if bytes.fromhex(row[5])!=profile_digest():fail('CRYPTO_KEY_PROFILE_MISMATCH')
 raw=SystemdInvocationKey('/run/credentials/'+row[2],row[3]).load()
 if hashlib.sha256(raw).hexdigest()!=row[4]:fail('CRYPTO_KEY_FINGERPRINT_MISMATCH')
 def b(hexvalue):return "decode("+lit(hexvalue)+",'hex')"
 values=[lit(row[0]),str(generation),lit(row[2]),b(actual['invocationId']),str(actual['mainPid']),str(actual['startMonotonicUsec']),lit(actual['managerUniqueOwner']),b(row[6]),b(row[4]),"ARRAY['GENERATION_INITIAL_REQUEST','SECRET_IMMUTABLE_VERSION']",'clock_timestamp()']
 db.query('INSERT INTO canonical_key_invocation_receipt VALUES('+','.join(values)+') ON CONFLICT(key_id,invocation_id) DO NOTHING')
 retained=db.query("SELECT key_generation,exact_service_unit,main_pid,start_monotonic_usec,manager_unique_owner,encode(encrypted_source_digest,'hex'),encode(observed_key_fingerprint,'hex'),array_to_json(authorized_purposes)::text FROM canonical_key_invocation_receipt WHERE key_id="+lit(row[0])+" AND invocation_id="+b(actual['invocationId']))
 expected=[str(generation),row[2],str(actual['mainPid']),str(actual['startMonotonicUsec']),actual['managerUniqueOwner'],row[6],row[4],'["GENERATION_INITIAL_REQUEST","SECRET_IMMUTABLE_VERSION"]']
 if retained!=[expected]:fail('CRYPTO_INVOCATION_REPLAY_CONFLICT')
 return {'keyId':row[0],'keyGeneration':generation,'invocationId':actual['invocationId'],'serviceUnit':row[2]}
