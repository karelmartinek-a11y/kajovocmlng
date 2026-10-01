"""Scoped actual verifier -> fresh private TEMP facts in the SAME read snapshot.
A candidate technical SESSION_SHA256_V1 profile; not a completed login/MFA issuer.
"""
import uuid,hashlib,hmac,json,re
from generation_auth_crypto import TOKEN_PROFILE,fingerprint
from generation_auth_acceptance import lit

def b(v):return "decode('"+v.hex()+"','hex')"
def prepare(db,operation,credential,channel,descriptor):
 if operation not in ('ownerApiKey.read','ownerApiKey.reveal'):raise ValueError('SQL_OPERATION_TYPED_HANDLER_UNRESOLVED')
 if db.transaction_status()!=2:raise ValueError('OWNER_QUERY_TRANSACTION_REQUIRED')
 pi=db.query('SELECT platform_incarnation_id FROM public.platform_incarnation WHERE singleton_key=1')[0][0];dh=db.query('SELECT platform_incarnation_id,application_deployment_epoch FROM public.application_deployment_head WHERE singleton_key=1')[0]
 if pi!=dh[0]:raise ValueError('OWNER_QUERY_SNAPSHOT_AUTHORITY_MISMATCH')
 owner=db.query('SELECT id,session_epoch FROM public.owner_identity WHERE singleton_key=1')[0]
 a=db.query('SELECT secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,credential_activation_epoch FROM public.owner_api_credential WHERE singleton_key=1')[0]
 session=None
 if channel=='OWNER_API_KEY':
  # Input is exact server-extracted bytes. Transport policy/extraction stays a
  # separate prerequisite; no invented token-size limit is enforced here.
  if type(credential)is not bytes or not credential:raise ValueError('OWNER_API_TOKEN_ENCODING_INVALID')
  if type(a[2])is not str or not re.fullmatch(TOKEN_PROFILE+':[0-9a-f]{64}',a[2]):raise ValueError('OWNER_API_VERIFIER_PROFILE_UNSUPPORTED')
  if not hmac.compare_digest(hashlib.sha256(credential).digest(),bytes.fromhex(a[2].split(':',1)[1])):raise ValueError('OWNER_API_AUTHENTICATION_FAILED')
  fp=fingerprint(credential)
  if not hmac.compare_digest(fp,a[3]):raise ValueError('OWNER_API_VERIFIER_FINGERPRINT_MISMATCH')
 elif channel=='OWNER_SESSION':
  if type(credential)is not bytes:raise ValueError('OWNER_SESSION_CREDENTIAL_INVALID')
  raw=hashlib.sha256(credential).digest();row=db.query('SELECT id,owner_identity_id,session_epoch,session_hash,revoked_at,expires_at>clock_timestamp() FROM public.owner_session WHERE lookup_digest='+b(raw))
  if len(row)!=1 or row[0][1]!=owner[0] or row[0][2]!=owner[1] or row[0][4]is not None or row[0][5]!='t':raise ValueError('OWNER_SESSION_STALE')
  if not row[0][3].startswith('KCML_OWNER_SESSION_SHA256_V1:'):raise ValueError('OWNER_SESSION_PROFILE_UNRESOLVED')
  expected='KCML_OWNER_SESSION_SHA256_V1:'+raw.hex()
  if not hmac.compare_digest(row[0][3].encode(),expected.encode()):raise ValueError('OWNER_SESSION_VERIFIER_MISMATCH')
  session=row[0][0]
 else:raise ValueError('OWNER_QUERY_AUTH_CHANNEL_INVALID')
 id=str(uuid.uuid4());values=[lit(id),lit(operation),lit(descriptor),lit(owner[0]),lit(channel),lit(session)if session else'NULL',lit(pi),dh[1],lit(a[0]),lit(a[1]),a[4],a[5],lit(a[3]),'pg_current_xact_id()','pg_backend_pid()']
 db.query('SET LOCAL ROLE kcml_authentication_writer;INSERT INTO pg_temp.kcml_verified_owner_query VALUES('+','.join(values)+');RESET ROLE;')
 return id

def create_temp(db):
 # Executed fresh for this request before the read profile; ON COMMIT DROP.
 db.query('CREATE TEMP TABLE kcml_verified_owner_query(id uuid PRIMARY KEY,operation_id text NOT NULL CHECK(operation_id IN(\'ownerApiKey.read\',\'ownerApiKey.reveal\')),descriptor_digest text NOT NULL,owner_id uuid NOT NULL,access_channel text NOT NULL CHECK(access_channel IN(\'OWNER_SESSION\',\'OWNER_API_KEY\')),session_id uuid,incarnation uuid NOT NULL,deployment_epoch bigint NOT NULL,secret_id uuid NOT NULL,secret_version_id uuid NOT NULL,credential_version bigint NOT NULL,credential_epoch bigint NOT NULL,fingerprint text NOT NULL,transaction_id xid8 NOT NULL,backend_id integer NOT NULL)ON COMMIT PRESERVE ROWS;ALTER TABLE pg_temp.kcml_verified_owner_query OWNER TO kcml_authentication_writer;')
 # PostgreSQL CREATE outside transaction cannot ON COMMIT DROP across bootstrap.
 # This fresh per-request table is explicitly dropped by finish(), never reused.
def finish(db):db.query('DROP TABLE pg_temp.kcml_verified_owner_query')
