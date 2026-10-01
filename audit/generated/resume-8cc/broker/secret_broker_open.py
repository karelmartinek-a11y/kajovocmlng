"""Protected SQL row → canonical authenticated open → exact native consumer.
Internal broker-only return, no plaintext in public metadata/evidence/report.
The key argument is an invocation-loaded service key, never a handler ENV key;
fixture provisioning explicitly does not certify the systemd producer.
"""
import json,hashlib
from generation_auth_crypto import open_snapshot,profile_digest,profile_bytes,CRYPTO_PROFILE
from secret_profile_import import load_use_profile

def fail(code):raise ValueError(code)
def sql_bytes(v):
 if not isinstance(v,str) or not v.startswith('\\x'):fail('SECRET_SQL_BINARY_ENCODING_INVALID')
 return bytes.fromhex(v[2:])
def sha(v):return 'sha256:'+hashlib.sha256(v).hexdigest()
def open_for_consumer(protected_row,invocation_key,expected_key_id,now):
 v=protected_row['version'];authority=protected_row['protectedAuthority']
 if authority.get('keyProfileDigestHex')!=profile_digest().hex() or bytes.fromhex(authority.get('keyProfileBytesHex',''))!=profile_bytes():fail('SECRET_KEY_CRYPTO_PROFILE_MISMATCH')
 if hashlib.sha256(invocation_key).hexdigest()!=authority['keyFingerprintHex']:fail('SECRET_INVOCATION_KEY_FINGERPRINT_MISMATCH')
 meta_envelope=json.loads(bytes.fromhex(authority['metadataHex']))
 if set(meta_envelope)!={'profile','purpose','keyId','identity'} or meta_envelope['profile']!=CRYPTO_PROFILE or meta_envelope['purpose']!='SECRET_IMMUTABLE_VERSION' or meta_envelope['keyId']!=expected_key_id:fail('SECRET_PROTECTED_AAD_PROFILE_MISMATCH')
 metadata=meta_envelope['identity']
 if metadata['secretId']!=v['secret_id'] or metadata['secretVersionId']!=v['id'] or metadata['trustedContextId']!=v['creator_context_id'] or metadata['logicalOperationId']!=authority['creationLogicalOperationId']:fail('SECRET_PROTECTED_CREATOR_BINDING_MISMATCH')
 expected={'secretId':v['secret_id'],'versionId':v['id'],'type':v['secret_type']}
 stored={'secretId':v['secret_id'],'versionId':v['id'],'type':v['secret_type'],'representation':v['value_representation'],'profileId':v['profile_id'],'schemaId':v['value_schema_id'],'schemaDigest':None if v['value_schema_digest']is None else 'sha256:'+sql_bytes(v['value_schema_digest']).hex(),'plaintextByteLength':v['plaintext_byte_length'],'valueDigest':'sha256:'+sql_bytes(v['original_import_bytes_digest']).hex(),'canonicalValueDigest':'sha256:'+sql_bytes(v['canonical_value_digest']).hex(),'payloadFormat':v['payload_format']}
 for aad_field,stored_field in [('secretType','type'),('representation','representation'),('profileId','profileId'),('schemaId','schemaId'),('schemaDigest','schemaDigest'),('plaintextByteLength','plaintextByteLength'),('originalImportBytesDigest','valueDigest'),('canonicalValueDigest','canonicalValueDigest')]:
  if metadata[aad_field]!=stored[stored_field]:fail('SECRET_PROTECTED_METADATA_BINDING_MISMATCH')
 cipher=sql_bytes(v['ciphertext'])
 if hashlib.sha256(cipher).hexdigest()!=authority['ciphertextDigestHex']:fail('SECRET_PROTECTED_ROW_DIGEST_MISMATCH')
 envelope={'algorithm':v['algorithm'],'keyId':v['key_id'],'cryptoProfileDigest':bytes.fromhex(authority['keyProfileDigestHex']),'nonce':sql_bytes(v['nonce']),'ciphertext':cipher}
 consumer=json.loads(bytes.fromhex(protected_row['consumerDeclarationHex']))
 if consumer.get('purposeKind')!=protected_row['consumerPurpose']:fail('SECRET_CONSUMER_PURPOSE_MISMATCH')
 def validate(raw):load_use_profile(raw,stored,expected,consumer,now)
 with open_snapshot(envelope,invocation_key,expected_key_id,metadata,validate,purpose='SECRET_IMMUTABLE_VERSION')as plaintext:
  # Immutable bytes are returned ONLY to the exact pending capability request
  # in the trusted caller. Python immutable-return erasure cannot be guaranteed.
  return bytes(plaintext)
