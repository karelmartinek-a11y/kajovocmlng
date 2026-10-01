"""Actual current OWNER API verifier and immutable value hydration.
Caller owns one PostgreSQL transaction from begin getter through audit commit.
OWNER credential reveal remains independently session-authorized (§51.20).
"""
import json
from generation_auth_crypto import extract_owner_api_token,verify_token,open_snapshot,profile_digest,profile_bytes,CRYPTO_PROFILE
def fail(code):raise ValueError(code)
def sql_bytes(value):
 if not isinstance(value,str) or not value.startswith("\\x"):fail("SECRET_SQL_BINARY_ENCODING_INVALID")
 return bytes.fromhex(value[2:])
from secret_profile_reference import parse_profile,canonical_value_digest

def authenticate_snapshot(snapshot,headers,transport_header_ceiling):
 token=extract_owner_api_token(headers,transport_header_ceiling)
 fingerprint=verify_token(token,snapshot['verifierHash'],transport_header_ceiling)
 if fingerprint!=snapshot['fingerprint']:fail('OWNER_VALUE_READ_VERIFIER_FINGERPRINT_MISMATCH')
 # Verification ALWAYS precedes diagnostic/target/creator inspection.
 if snapshot['diagnostic']!='VALUE_READ_READY':fail(snapshot['diagnostic'])
 return snapshot['protectedRow']
def open_owner_value(snapshot,headers,transport_header_ceiling,invocation_key,key_id):
 protected=authenticate_snapshot(snapshot,headers,transport_header_ceiling)
 v=protected['version'];authority=protected['protectedAuthority']
 if authority.get('keyProfileDigestHex')!=profile_digest().hex() or bytes.fromhex(authority.get('keyProfileBytesHex',''))!=profile_bytes():fail('SECRET_KEY_CRYPTO_PROFILE_MISMATCH')
 aad=json.loads(bytes.fromhex(authority['metadataHex']))
 if set(aad)!={'profile','purpose','keyId','identity'} or aad['profile']!=CRYPTO_PROFILE or aad['purpose']!='SECRET_IMMUTABLE_VERSION' or aad['keyId']!=key_id:fail('SECRET_PROTECTED_AAD_PROFILE_MISMATCH')
 metadata=aad['identity']
 if metadata['ownerId']!=snapshot['ownerId'] or metadata['secretId']!=v['secret_id'] or metadata['secretVersionId']!=v['id'] or metadata['trustedContextId']!=v['creator_context_id'] or metadata['logicalOperationId']!=authority['creationLogicalOperationId']:fail('SECRET_OWNER_IMMUTABLE_IDENTITY_MISMATCH')
 expected={'secretType':v['secret_type'],'representation':v['value_representation'],'profileId':v['profile_id'],'schemaId':v['value_schema_id'],'schemaDigest':None if v['value_schema_digest']is None else 'sha256:'+sql_bytes(v['value_schema_digest']).hex(),'plaintextByteLength':v['plaintext_byte_length'],'originalImportBytesDigest':'sha256:'+sql_bytes(v['original_import_bytes_digest']).hex(),'canonicalValueDigest':'sha256:'+sql_bytes(v['canonical_value_digest']).hex()}
 if any(metadata[k]!=value for k,value in expected.items()):fail('SECRET_OWNER_STORED_METADATA_MISMATCH')
 import hashlib
 if hashlib.sha256(invocation_key).hexdigest()!=authority['keyFingerprintHex']:fail('SECRET_INVOCATION_KEY_FINGERPRINT_MISMATCH')
 cipher=sql_bytes(v['ciphertext'])
 if hashlib.sha256(cipher).hexdigest()!=authority['ciphertextDigestHex']:fail('SECRET_PROTECTED_ROW_DIGEST_MISMATCH')
 envelope={'algorithm':v['algorithm'],'keyId':v['key_id'],'cryptoProfileDigest':bytes.fromhex(authority['keyProfileDigestHex']),'nonce':sql_bytes(v['nonce']),'ciphertext':cipher}
 def actual_content(raw):
  candidate={'type':v['secret_type'],'representation':v['value_representation'],'profileId':v['profile_id'],'bytes':raw}
  if canonical_value_digest(candidate)!=metadata['canonicalValueDigest']:fail('SECRET_STORED_CANONICAL_DIGEST_MISMATCH')
  if len(raw)!=v['plaintext_byte_length']:fail('SECRET_STORED_BYTES_MISMATCH')
  if v['value_representation']=='PROFILE_JSON_V1':parse_profile(v['profile_id'],raw)
  elif v['value_representation']=='RAW_UTF8':raw.decode('utf8',errors='strict')
  # Legacy immutable RAW is revealed exactly, not reinterpreted as a profile.
 with open_snapshot(envelope,invocation_key,key_id,metadata,actual_content,purpose='SECRET_IMMUTABLE_VERSION')as value:return bytes(value)
