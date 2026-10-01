"""Genuine OWNER verifier produces private in-process single-use material under B.
No authority flag or model/client dict accepted. Persistence is late H under the
SAME backend/transaction; actual C/E locks must be acquired by the typed adapter.
"""
from dataclasses import dataclass
import weakref,uuid
from generation_auth_crypto import verify_token,sha,fail
from generation_auth_acceptance import lit
@dataclass(frozen=True,eq=False)
class _VerifiedApiMaterial:
 receipt_id:str;context_id:str;owner_id:str;incarnation:str;epoch:int
 credential_version:int;credential_epoch:int;fingerprint:str
 request_digest:bytes;descriptor_bytes:bytes;accepted_at:str;secret_id:str;secret_version_id:str
_ISSUED=weakref.WeakKeyDictionary()
def verify_owner_api_material(db,token,request_digest,descriptor_bytes,ceiling):
 if db.transaction_status()!=2:fail('OWNER_API_ACCEPTANCE_TRANSACTION_REQUIRED')
 if type(request_digest)is not bytes or len(request_digest)!=32 or type(descriptor_bytes)is not bytes or not descriptor_bytes:fail('GENERATION_AUTH_DESCRIPTOR_REQUIRED')
 db.query('SELECT pg_advisory_xact_lock_shared(1000,0)')
 pi=db.query('SELECT platform_incarnation_id FROM platform_incarnation WHERE singleton_key=1 FOR SHARE')
 dh=db.query('SELECT platform_incarnation_id,application_deployment_epoch FROM application_deployment_head WHERE singleton_key=1 FOR SHARE')
 if len(pi)!=1 or len(dh)!=1 or pi[0][0]!=dh[0][0]:fail('OWNER_API_DEPLOYMENT_CONTEXT_MISMATCH')
 rows=db.query('SELECT verifier_hash,fingerprint,credential_version,credential_activation_epoch,secret_id,secret_version_id FROM public.owner_api_credential WHERE singleton_key=1 FOR SHARE')
 if len(rows)!=1:fail('OWNER_API_CREDENTIAL_UNRESOLVED')
 verifier,storedfp,version,epoch,secret_id,secret_version_id=rows[0];fp=verify_token(token,verifier,ceiling)
 if fp!=storedfp:fail('OWNER_API_VERIFIER_FINGERPRINT_MISMATCH')
 owner=db.query('SELECT id FROM owner_identity WHERE singleton_key=1')
 if len(owner)!=1:fail('OWNER_IDENTITY_UNRESOLVED')
 if __import__('json').loads(descriptor_bytes)['stableCallerObjectId']!=owner[0][0]:fail('GENERATION_AUTH_DESCRIPTOR_OWNER_MISMATCH')
 xid,pid,accepted=db.query("SELECT pg_current_xact_id(),pg_backend_pid(),clock_timestamp()")[0]
 cap=_VerifiedApiMaterial(str(uuid.uuid4()),str(uuid.uuid4()),owner[0][0],pi[0][0],int(dh[0][1]),int(version),int(epoch),fp,request_digest,descriptor_bytes,accepted,secret_id,secret_version_id)
 _ISSUED[cap]=(db,xid,pid)
 return cap

def persist_verified_material(db,cap,contract_digest):
 issued=_ISSUED.get(cap)if isinstance(cap,_VerifiedApiMaterial)else None
 if issued is None or issued[0]is not db or db.transaction_status()!=2:fail('GENERATION_AUTH_VERIFIED_MATERIAL_REQUIRED')
 xid,pid=db.query('SELECT pg_current_xact_id(),pg_backend_pid()')[0]
 if (xid,pid)!=issued[1:]:fail('GENERATION_AUTH_VERIFIED_TRANSACTION_MISMATCH')
 _ISSUED.pop(cap)
 def b(raw):return "decode('"+raw.hex()+"','hex')"
 db.query('SET LOCAL ROLE kcml_authentication_writer;INSERT INTO generation_create_authentication_acceptance(id,owner_id,access_channel,api_credential_version,api_credential_fingerprint,accepted_at,authenticated_request_digest,api_credential_activation_epoch,authenticated_descriptor_digest)VALUES('+','.join([lit(cap.receipt_id),lit(cap.owner_id),"'OWNER_API_KEY'",str(cap.credential_version),lit(cap.fingerprint),lit(cap.accepted_at),b(cap.request_digest),str(cap.credential_epoch),b(sha(cap.descriptor_bytes))])+');RESET ROLE;')
 db.query('SET LOCAL ROLE kcml_domain_writer;SELECT kcml_generation_create_context_ordered_v1('+','.join([lit(cap.receipt_id),lit(cap.context_id),b(cap.request_digest),b(contract_digest),b(cap.descriptor_bytes)])+');RESET ROLE;')
 return cap.context_id
