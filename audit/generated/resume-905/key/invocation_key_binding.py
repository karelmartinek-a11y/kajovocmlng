"""Candidate bounded consumer: actual bytes + server registry + manager identity.
Manager reader must be a verified platform system-bus adapter, not request data.
Fixture tests of this adapter interface are NOT systemd producer attestation.
"""
import os,hashlib
from generation_auth_crypto import SystemdInvocationKey,profile_digest
FIELDS={'keyId','keyGeneration','keyFingerprint','serviceUnit','credentialName','cryptoProfileDigest'}
MANAGER={'serviceUnit','invocationId','mainPid','effectiveCredentialGeneration','credentialDirectory','credentialName'}
def fail(code):raise ValueError(code)
def load_bound_invocation_key(registry,manager_reader,expected_invocation_id,own_pid=None):
 if type(registry)is not dict or set(registry)!=FIELDS:fail('CRYPTO_KEY_REGISTRY_MASK_INVALID')
 if not callable(manager_reader):fail('CRYPTO_INVOCATION_AUTHORITY_UNAVAILABLE')
 observed=manager_reader(registry['serviceUnit'])
 if type(observed)is not dict or set(observed)!=MANAGER:fail('CRYPTO_INVOCATION_AUTHORITY_UNAVAILABLE')
 if observed['serviceUnit']!=registry['serviceUnit'] or observed['credentialName']!=registry['credentialName']:fail('CRYPTO_INVOCATION_SERVICE_MISMATCH')
 if not expected_invocation_id or observed['invocationId']!=expected_invocation_id or observed['mainPid']!=(os.getpid()if own_pid is None else own_pid):fail('CRYPTO_INVOCATION_IDENTITY_MISMATCH')
 if type(registry['keyGeneration'])is not int or registry['keyGeneration']<1 or observed['effectiveCredentialGeneration']!=registry['keyGeneration']:fail('CRYPTO_KEY_GENERATION_MISMATCH')
 if registry['cryptoProfileDigest']!=profile_digest():fail('CRYPTO_KEY_PROFILE_MISMATCH')
 key=SystemdInvocationKey(observed['credentialDirectory'],registry['credentialName']).load()
 if registry['keyFingerprint']!=hashlib.sha256(key).digest():fail('CRYPTO_KEY_FINGERPRINT_MISMATCH')
 return key
