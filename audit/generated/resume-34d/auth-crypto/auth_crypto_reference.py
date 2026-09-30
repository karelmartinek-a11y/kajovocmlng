"""Actual primitives for reviewed technical profiles; no caller authorization flags.
Synthetic fixture adapters are deliberately separate from systemd provisioning.
"""
import contextlib, hashlib, hmac, json, os, re, stat, uuid
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

TOKEN_PROFILE='KCML_OWNER_API_SHA256_V1'
CRYPTO_PROFILE={'profileId':'KCML_PROTECTED_INPUT_AES256_GCM_V1','version':1,'algorithm':'AES_256_GCM','keyBytes':32,'nonceBytes':12,'tagBytes':16,'aadEncoding':'SORTED_COMPACT_UTF8_JSON_V1','contentDigest':'SHA256_EXACT_PLAINTEXT_BYTES','keySource':'SYSTEMD_READ_ONLY_PER_INVOCATION_CREDENTIAL'}
IDENTITY_FIELDS=('ownerId','jobId','snapshotId','logicalOperationId','requestSchemaId','requestSchemaDigest','contentDigest','trustedContextId','platformIncarnationId','applicationDeploymentEpoch','executionDescriptorDigest','initiatingAccessChannel')

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf8')
def sha(v):return hashlib.sha256(v).digest()
def fail(code):raise ValueError(code)
def extract_owner_api_token(headers,transport_header_ceiling):
 if type(transport_header_ceiling)is not int or transport_header_ceiling<1:fail('OWNER_API_TRANSPORT_POLICY_UNRESOLVED')
 if type(headers)is not list:fail('OWNER_API_HEADER_ENCODING_INVALID')
 found=[]
 for item in headers:
  if type(item)not in (tuple,list) or len(item)!=2 or type(item[0])is not str or type(item[1])is not bytes:fail('OWNER_API_HEADER_ENCODING_INVALID')
  name,value=item
  if name.lower()=='authorization':found.append(value)
 if len(found)!=1:fail('OWNER_API_AUTHORIZATION_HEADER_CARDINALITY_INVALID')
 raw=found[0]
 if len(raw)>transport_header_ceiling:fail('OWNER_API_AUTHORIZATION_HEADER_TOO_LARGE')
 if len(raw)<8 or raw[:7].lower()!=b'bearer ':fail('OWNER_API_AUTHORIZATION_SCHEME_INVALID')
 token=raw[7:]
 # Bearer token68 wire grammar; no trim/normalization/decoding of token value.
 if not re.fullmatch(rb'[A-Za-z0-9._~+/-]+=*',token):fail('OWNER_API_TOKEN_ENCODING_INVALID')
 return token
def verifier_hash(token):
 if type(token)is not bytes or not token:fail('OWNER_API_TOKEN_ENCODING_INVALID')
 return TOKEN_PROFILE+':'+sha(token).hex()
def fingerprint(token):return sha(token).hex()[:16]
def verify_token(token,stored_verifier,transport_header_ceiling):
 # Ceiling is exact consumed gateway transport policy, not a new token entropy/max policy.
 if type(transport_header_ceiling)is not int or transport_header_ceiling<1:fail('OWNER_API_TRANSPORT_POLICY_UNRESOLVED')
 if type(token)is not bytes or not token or len(token)>transport_header_ceiling:fail('OWNER_API_TOKEN_ENCODING_INVALID')
 if type(stored_verifier)is not str or not re.fullmatch(TOKEN_PROFILE+':[0-9a-f]{64}',stored_verifier):fail('OWNER_API_VERIFIER_PROFILE_UNSUPPORTED')
 actual=sha(token);expected=bytes.fromhex(stored_verifier.split(':',1)[1])
 if not hmac.compare_digest(actual,expected):fail('OWNER_API_AUTHENTICATION_FAILED')
 return fingerprint(token)

def profile_bytes():return canonical(CRYPTO_PROFILE)+b'\n'
def profile_digest():return sha(profile_bytes())
SECRET_IDENTITY_FIELDS=('ownerId','secretId','secretVersionId','secretType','representation','profileId','schemaId','schemaDigest','plaintextByteLength','originalImportBytesDigest','canonicalValueDigest','trustedContextId','logicalOperationId')

def aad(metadata,purpose='GENERATION_INITIAL_REQUEST',key_id=None):
 if type(key_id)is not str or not key_id:fail('PROTECTED_INPUT_KEY_ID_INVALID')
 fields=IDENTITY_FIELDS if purpose=='GENERATION_INITIAL_REQUEST' else SECRET_IDENTITY_FIELDS if purpose=='SECRET_IMMUTABLE_VERSION' else None
 if fields is None:fail('PROTECTED_INPUT_PURPOSE_UNSUPPORTED')
 if type(metadata)is not dict or set(metadata)!=set(fields):fail('PROTECTED_INPUT_METADATA_MASK_INVALID')
 if purpose=='GENERATION_INITIAL_REQUEST' and metadata['initiatingAccessChannel'] not in ('OWNER_SESSION','OWNER_API_KEY'):fail('PROTECTED_INPUT_CHANNEL_INVALID')
 if purpose=='GENERATION_INITIAL_REQUEST' and (type(metadata['applicationDeploymentEpoch'])is not int or metadata['applicationDeploymentEpoch']<0):fail('PROTECTED_INPUT_EPOCH_INVALID')
 if purpose=='SECRET_IMMUTABLE_VERSION' and (type(metadata['plaintextByteLength'])is not int or metadata['plaintextByteLength']<0):fail('PROTECTED_INPUT_LENGTH_INVALID')
 for k in fields:
  if k in ('applicationDeploymentEpoch','plaintextByteLength'):continue
  if purpose=='SECRET_IMMUTABLE_VERSION' and k in ('profileId','schemaId','schemaDigest') and metadata['representation'] in ('RAW_UTF8','RAW_BINARY') and metadata[k] is None:continue
  if type(metadata[k])is not str or not metadata[k]:fail('PROTECTED_INPUT_IDENTITY_INVALID')
 for k in ('ownerId','trustedContextId','logicalOperationId')+(('jobId','snapshotId','platformIncarnationId') if purpose=='GENERATION_INITIAL_REQUEST' else ('secretId','secretVersionId')):
  try:
   if str(uuid.UUID(metadata[k]))!=metadata[k]:fail('PROTECTED_INPUT_IDENTITY_INVALID')
  except (ValueError,AttributeError,TypeError):fail('PROTECTED_INPUT_IDENTITY_INVALID')
 if purpose=='SECRET_IMMUTABLE_VERSION' and metadata['representation'] not in ('RAW_UTF8','RAW_BINARY','PROFILE_JSON_V1'):fail('PROTECTED_INPUT_REPRESENTATION_INVALID')
 if purpose=='SECRET_IMMUTABLE_VERSION':
  raw=metadata['representation'] in ('RAW_UTF8','RAW_BINARY')
  if any((metadata[k] is None)!=raw for k in ('profileId','schemaId','schemaDigest')):fail('PROTECTED_INPUT_PROFILE_METADATA_INVALID')
 schema_field='requestSchemaId' if purpose=='GENERATION_INITIAL_REQUEST' else 'schemaId'
 if metadata[schema_field] is not None and not metadata[schema_field].startswith('urn:kcml:'):fail('PROTECTED_INPUT_SCHEMA_ID_INVALID')
 for k in (('requestSchemaDigest','contentDigest','executionDescriptorDigest') if purpose=='GENERATION_INITIAL_REQUEST' else ('schemaDigest','originalImportBytesDigest','canonicalValueDigest')):
  if purpose=='SECRET_IMMUTABLE_VERSION' and k=='schemaDigest' and metadata['representation'] in ('RAW_UTF8','RAW_BINARY') and metadata[k] is None:continue
  if not re.fullmatch('sha256:[0-9a-f]{64}',metadata[k]):fail('PROTECTED_INPUT_DIGEST_INVALID')
 return canonical({'profile':CRYPTO_PROFILE,'purpose':purpose,'keyId':key_id,'identity':metadata})
def seal(plaintext,key,key_id,metadata,purpose='GENERATION_INITIAL_REQUEST'):
 if type(plaintext)is not bytes:fail('PROTECTED_INPUT_BYTES_REQUIRED')
 if type(key)is not bytes or len(key)!=32:fail('PROTECTED_INPUT_KEY_INVALID')
 if type(key_id)is not str or not key_id:fail('PROTECTED_INPUT_KEY_ID_INVALID')
 authenticated=aad(metadata,purpose,key_id)
 digest_field='contentDigest' if purpose=='GENERATION_INITIAL_REQUEST' else 'originalImportBytesDigest'
 if metadata[digest_field]!='sha256:'+sha(plaintext).hex():fail('PROTECTED_INPUT_CONTENT_DIGEST_MISMATCH')
 nonce=os.urandom(12)
 return {'algorithm':'AES_256_GCM','keyId':key_id,'cryptoProfileDigest':profile_digest(),'nonce':nonce,'ciphertext':AESGCM(key).encrypt(nonce,plaintext,authenticated)}
@contextlib.contextmanager
def open_snapshot(envelope,key,expected_key_id,server_metadata,content_validator,purpose='GENERATION_INITIAL_REQUEST'):
 # server_metadata MUST be hydrated from trusted context + persisted immutable FK rows.
 if set(envelope)!={'algorithm','keyId','cryptoProfileDigest','nonce','ciphertext'}:fail('PROTECTED_INPUT_ENVELOPE_MASK_INVALID')
 if envelope['algorithm']!='AES_256_GCM' or envelope['cryptoProfileDigest']!=profile_digest():fail('PROTECTED_INPUT_PROFILE_MISMATCH')
 if envelope['keyId']!=expected_key_id:fail('PROTECTED_INPUT_KEY_ID_MISMATCH')
 if type(key)is not bytes or len(key)!=32:fail('PROTECTED_INPUT_KEY_INVALID')
 if type(envelope['nonce'])is not bytes or len(envelope['nonce'])!=12:fail('PROTECTED_INPUT_NONCE_INVALID')
 if type(envelope['ciphertext'])is not bytes or len(envelope['ciphertext'])<16:fail('PROTECTED_INPUT_CIPHERTEXT_INVALID')
 try:plaintext=bytearray(AESGCM(key).decrypt(envelope['nonce'],envelope['ciphertext'],aad(server_metadata,purpose,expected_key_id)))
 except InvalidTag:fail('PROTECTED_INPUT_AUTHENTICATION_FAILED')
 try:
  digest_field='contentDigest' if purpose=='GENERATION_INITIAL_REQUEST' else 'originalImportBytesDigest'
  if server_metadata[digest_field]!='sha256:'+sha(plaintext).hex():fail('PROTECTED_INPUT_CONTENT_DIGEST_MISMATCH')
  # Python reference explicitly cannot guarantee erasure of immutable parser/decrypt copies.
  # Validates actual decoded domain bytes; a valid=True flag is not accepted.
  if not callable(content_validator):fail('PROTECTED_INPUT_CONSUMER_UNRESOLVED')
  content_validator(bytes(plaintext))
  yield memoryview(plaintext)
 finally:
  for i in range(len(plaintext)):plaintext[i]=0

class SystemdInvocationKey:
 """Read ONLY actual service-invocation materialization, never host source/blob.
 Authentic invocation/directory origin is a service-manager producer obligation.
 Path is server startup configuration, never a request field.
 """
 def __init__(self,credential_directory,credential_name='kcml-master-key'):
  if '/' in credential_name or credential_name in ('','.', '..'):fail('SYSTEMD_CREDENTIAL_NAME_INVALID')
  self.path=Path(credential_directory)/credential_name
 def load(self):
  fd=os.open(self.path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
  try:
   s=os.fstat(fd)
   if not stat.S_ISREG(s.st_mode) or s.st_mode&0o222:fail('SYSTEMD_CREDENTIAL_MATERIALIZATION_NOT_READ_ONLY')
   raw=os.read(fd,33)
   if len(raw)!=32:fail('SYSTEMD_MASTER_KEY_SIZE_INVALID')
   return raw
  finally:os.close(fd)
