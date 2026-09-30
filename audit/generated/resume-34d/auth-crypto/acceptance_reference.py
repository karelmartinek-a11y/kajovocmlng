"""Application-side canonical OWNER API verifier under actual PostgreSQL locks.
The caller MUST own a live transaction; function does not commit or claim acceptance.
Every request/replay authenticates. No expiry/roles/scopes/account relation is added.
"""
import uuid
from auth_crypto_reference import verify_token,fail,sha
from libpq_fixture import lit

def authenticate_owner_api(db,token,request_digest,transport_header_ceiling,execution_descriptor_bytes):
 if type(execution_descriptor_bytes)is not bytes or not execution_descriptor_bytes:fail('GENERATION_AUTH_DESCRIPTOR_REQUIRED')
 if not isinstance(request_digest,bytes) or len(request_digest)!=32:fail('GENERATION_REQUEST_DIGEST_INVALID')
 # Do not silently begin or split an existing acceptance transaction.
 if db.transaction_status()!=2:fail('OWNER_API_ACCEPTANCE_TRANSACTION_REQUIRED')
 pi=db.query('SELECT platform_incarnation_id FROM platform_incarnation WHERE singleton_key=1 FOR SHARE')
 dh=db.query('SELECT platform_incarnation_id,application_deployment_epoch FROM application_deployment_head WHERE singleton_key=1 FOR SHARE')
 if len(pi)!=1 or len(dh)!=1 or pi[0][0]!=dh[0][0]:fail('OWNER_API_DEPLOYMENT_CONTEXT_MISMATCH')
 rows=db.query('SELECT verifier_hash,fingerprint,credential_version,credential_activation_epoch,secret_id,secret_version_id FROM owner_api_credential WHERE singleton_key=1 FOR SHARE')
 if len(rows)!=1:fail('OWNER_API_CREDENTIAL_UNRESOLVED')
 verifier,storedfp,version,epoch,secret,secret_version=rows[0]
 fp=verify_token(token,verifier,transport_header_ceiling)
 if fp!=storedfp:fail('OWNER_API_VERIFIER_FINGERPRINT_MISMATCH')
 owner=db.query('SELECT id FROM owner_identity WHERE singleton_key=1 FOR SHARE')
 if len(owner)!=1:fail('OWNER_IDENTITY_UNRESOLVED')
 # Current singleton credential has no owner/account relation: OWNER is resolved
 # separately and its fixed identity projects public gateway OWNER_FULL context.
 receipt=str(uuid.uuid4())
 db.query('INSERT INTO generation_create_authentication_acceptance(id,owner_id,access_channel,api_credential_version,api_credential_fingerprint,accepted_at,authenticated_request_digest,api_credential_activation_epoch,authenticated_descriptor_digest) VALUES('+','.join([lit(receipt),lit(owner[0][0]),"'OWNER_API_KEY'",str(int(version)),lit(fp),'clock_timestamp()',"decode('"+request_digest.hex()+"','hex')",str(int(epoch)),"decode('"+sha(execution_descriptor_bytes).hex()+"','hex')"])+')')
 return {'authenticationAcceptanceId':receipt,'ownerId':owner[0][0],'accessChannel':'OWNER_API_KEY','platformIncarnationId':pi[0][0],'applicationDeploymentEpoch':int(dh[0][1]),'requestDigest':request_digest,'apiCredentialVersion':int(version),'apiCredentialActivationEpoch':int(epoch)}
