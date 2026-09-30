"""Exact profile value parsers. No authorization, activation or live authentication."""
import base64,copy,hashlib,json,re,struct
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from jsonschema import Draft202012Validator,FormatChecker
from cryptography import x509
from cryptography.hazmat.primitives import serialization
SCHEMA_PATH=Path(__file__).resolve().parents[1]/'01_UI_CONTRACT/contracts/secrets/profile-handoffs.schema.json'
class Rejected(ValueError):
 def __init__(self,code,pointer):self.code,self.pointer=code,pointer;super().__init__(code+':'+pointer)
def reject(code,pointer):raise Rejected(code,pointer)
def schemas():
 data=json.loads(SCHEMA_PATH.read_text());inventory=data['x-profileInventory']
 return {t:{'schema':{'oneOf':[v['schema'] for v in inventory if v['secretType']==t and v['profileId']!='BROWSER_AUTH_STATE_GRAPH_V1']}} for t in {v['secretType']for v in inventory}}
def endpoint(value,code,pointer,origin_only=False):
 p=urlsplit(value)
 try:port=p.port
 except ValueError:reject(code,pointer)
 if p.scheme not in (['http','https'] if origin_only else ['https']) or not p.hostname or p.username is not None or p.password is not None or p.fragment or (origin_only and (p.path or p.query)):reject(code,pointer)
 return p

def cookies(values,target):
 seen=set()
 for i,c in enumerate(values):
  at='/cookies/'+str(i);key=(c['name'],c['domain'],c['path'])
  if key in seen:reject('COOKIE_DUPLICATE',at)
  seen.add(key);domain=c['domain'];d=domain[1:] if domain.startswith('.') else domain
  if not re.fullmatch(r'(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?',d):reject('COOKIE_DOMAIN_INVALID',at+'/domain')
  if not any(host.lower()==d.lower() or host.lower().endswith('.'+d.lower()) for host in target['cookieHosts']):reject('COOKIE_SCOPE_MISMATCH',at+'/domain')
  if c['sameSite']=='None' and c['secure'] is not True:reject('COOKIE_SAMESITE_SECURE_REQUIRED',at+'/secure')

def pem_block(text,label,code,pointer):
 raw=text.encode('utf8')
 if not re.fullmatch(rb'[ \t\r\n]*-----BEGIN '+label.encode()+rb'-----\r?\n[A-Za-z0-9+/=\r\n]+-----END '+label.encode()+rb'-----[ \t\r\n]*',raw):reject(code,pointer)
 return raw

def parse_candidate(secret_type,value,consumer):
 original=copy.deepcopy(value);contract=schemas()[secret_type]
 variant=value.get('variant') if isinstance(value,dict) else None
 declared=[s['properties']['variant']['const'] for s in contract['schema']['oneOf']]
 if variant not in declared or (secret_type,variant) not in consumer['supported']:reject('SECRET_VARIANT_UNSUPPORTED','/variant')
 errors=list(Draft202012Validator(contract['schema'],format_checker=FormatChecker()).iter_errors(value))
 # Domain identity duplicates have their own explicit predicates, rather than
 # treating uniqueItems rejection of the same fixture as unrelated success.
 if secret_type in ['OAUTH_CLIENT','OAUTH_TOKEN_SET'] and isinstance(value.get('scopes'),list) and len(set(value['scopes']))!=len(value['scopes']):reject('OAUTH_SCOPE_DUPLICATE','/scopes')
 if secret_type in ['COOKIE_JAR','SESSION_STATE'] and isinstance(value.get('cookies'),list):
  keys=[(c.get('name'),c.get('domain'),c.get('path')) for c in value['cookies'] if isinstance(c,dict)]
  if len(set(keys))!=len(keys):reject('COOKIE_DUPLICATE','/cookies')
 if errors:reject('PROPOSAL_SCHEMA_INVALID',errors[0].json_path)
 if secret_type=='OAUTH_CLIENT':
  p=endpoint(value['tokenEndpoint'],'OAUTH_TOKEN_ENDPOINT_INVALID','/tokenEndpoint')
  if p.hostname not in consumer['oauthHosts']:reject('OAUTH_TOKEN_ENDPOINT_INVALID','/tokenEndpoint')
 elif secret_type=='OAUTH_TOKEN_SET':
  if 'expiresAt' in value:
   datetime.fromisoformat(value['expiresAt'].replace('Z','+00:00'))
 elif secret_type=='TOTP_SEED':
  seed=value['seedBase32']
  try:raw=base64.b32decode(seed+'='*((-len(seed))%8),casefold=False)
  except ValueError:reject('TOTP_BASE32_INVALID','/seedBase32')
  if base64.b32encode(raw).decode().rstrip('=')!=seed:reject('TOTP_BASE32_INVALID','/seedBase32')
 elif secret_type=='CERTIFICATE':
  certs=[];fingerprints=set()
  for i,text in enumerate(value['certificatesPem']):
   at='/certificatesPem/'+str(i);raw=pem_block(text,'CERTIFICATE','CERTIFICATE_PEM_INVALID',at)
   try:cert=x509.load_pem_x509_certificate(raw)
   except ValueError:reject('CERTIFICATE_PEM_INVALID',at)
   der=cert.public_bytes(serialization.Encoding.DER);fingerprint=hashlib.sha256(der).hexdigest()
   if fingerprint in fingerprints:reject('CERTIFICATE_DUPLICATE',at)
   fingerprints.add(fingerprint);certs.append(cert)
  for i in range(len(certs)-1):
   try:certs[i].verify_directly_issued_by(certs[i+1])
   except (ValueError,TypeError,__import__('cryptography.exceptions',fromlist=['InvalidSignature']).InvalidSignature):reject('CERTIFICATE_CHAIN_INVALID','/certificatesPem/'+str(i))
 elif secret_type=='PRIVATE_KEY':
  if 'BEGIN ENCRYPTED PRIVATE KEY' in value['pem']:reject('PRIVATE_KEY_ENCRYPTION_UNSUPPORTED','/pem')
  raw=pem_block(value['pem'],'PRIVATE KEY','PRIVATE_KEY_PEM_INVALID','/pem')
  try:key=serialization.load_pem_private_key(raw,password=None)
  except (ValueError,TypeError):reject('PRIVATE_KEY_PEM_INVALID','/pem')
  if not consumer['keyAlgorithmAllowed'](key):reject('PRIVATE_KEY_ALGORITHM_UNSUPPORTED','/pem')
 elif secret_type=='DATABASE_CREDENTIAL':
  if 'database' in value and value['database']!=consumer['database']:reject('DATABASE_CREDENTIAL_TARGET_MISMATCH','/database')
 elif secret_type in ['COOKIE_JAR','SESSION_STATE']:
  cookies(value['cookies'],consumer)
  if secret_type=='SESSION_STATE':
   origins=set()
   for i,item in enumerate(value['origins']):
    at='/origins/'+str(i);endpoint(item['origin'],'BROWSER_STATE_ORIGIN_INVALID',at+'/origin',True)
    if item['origin'] in origins:reject('BROWSER_STATE_DUPLICATE_ORIGIN',at+'/origin')
    if item['origin'] not in consumer['origins']:reject('BROWSER_STATE_ORIGIN_INVALID',at+'/origin')
    origins.add(item['origin']);keys=set()
    for j,entry in enumerate(item['localStorage']):
     if entry['name'] in keys:reject('BROWSER_STATE_DUPLICATE_STORAGE_KEY',at+'/localStorage/'+str(j)+'/name')
     keys.add(entry['name'])
 elif secret_type=='SSH_CREDENTIAL' and variant=='SSH_OPENSSH_PRIVATE_KEY_V1':
  raw=pem_block(value['privateKeyPem'],'OPENSSH PRIVATE KEY','SSH_KEY_INVALID','/privateKeyPem')
  try:
   binary=base64.b64decode(b''.join(raw.splitlines()[1:-1]),validate=True)
   if not binary.startswith(b'openssh-key-v1\0'):raise ValueError()
   n=struct.unpack('>I',binary[15:19])[0];cipher=binary[19:19+n]
   if len(cipher)!=n:raise ValueError()
  except (ValueError,struct.error):reject('SSH_KEY_INVALID','/privateKeyPem')
  encrypted=cipher!=b'none'
  if encrypted and 'passphrase' not in value:reject('SSH_KEY_PASSPHRASE_REQUIRED','/passphrase')
  if not encrypted and 'passphrase' in value:reject('SSH_KEY_PASSPHRASE_UNEXPECTED','/passphrase')
  try:serialization.load_ssh_private_key(raw,password=value['passphrase'].encode('utf8') if encrypted else None)
  except (ValueError,TypeError):reject('SSH_KEY_INVALID','/privateKeyPem')
 assert value==original,'Reference parser mutated exact imported values'
 return {'decision':'ACCEPT_CANDIDATE_ONLY','variant':variant,'formatEffective':False}
