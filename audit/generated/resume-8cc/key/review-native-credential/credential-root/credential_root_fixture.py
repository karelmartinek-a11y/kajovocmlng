from pathlib import Path
import sys
ROOT=Path('/workspace/kajovocmlng');sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from native_auth_factory import *
def install_current_credential_secret(f):
 db=f.db;rs=f.resources;db.query('DROP SCHEMA IF EXISTS kcml_secret_v1 CASCADE')
 for n in ['database/secret-profile-roots.sql','database/secret-profile-publication.sql','database/secret-command-chain.sql','database/secret-record-status.sql']:db.query(rs[n]['raw'].decode())
 sid,vid=uid(9901),uid(9902);digest='sha256:'+sha(f.token).hex();ctx,op=uid(9910),uid(9911)
 meta={'ownerId':OWNER,'secretId':sid,'secretVersionId':vid,'secretType':'API_KEY','representation':'RAW_UTF8','profileId':None,'schemaId':None,'schemaDigest':None,'plaintextByteLength':len(f.token),'originalImportBytesDigest':digest,'canonicalValueDigest':digest,'trustedContextId':ctx,'logicalOperationId':op}
 envelope=seal(f.token,f.key,f.keyid,meta,purpose='SECRET_IMMUTABLE_VERSION')
 db.query('BEGIN;INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,state_version,secret_activation_epoch,created_at,updated_at)VALUES('+lit(sid)+",'KCML_OWNER_API_KEY','Synthetic fixture authority','API_KEY',0,0,clock_timestamp(),clock_timestamp());")
 db.query('INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,creator_context_id)VALUES('+','.join([lit(vid),lit(sid),'1',"'API_KEY'","'RAW_UTF8'","'EXACT_SECRET_BYTES_V1'",str(len(f.token)),b(envelope['ciphertext']),b(envelope['nonce']),lit(envelope['algorithm']),lit(f.keyid),lit(fingerprint(f.token)),b(sha(f.token)),b(sha(f.token)),"'CREATED'",'clock_timestamp()',lit(ctx)])+');')
 db.query("UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=clock_timestamp(),activation_logical_operation_id="+lit(op)+'WHERE id='+lit(vid)+';UPDATE kcml_secret_v1.secret_record SET active_version_id='+lit(vid)+',state_version=1,secret_activation_epoch=1 WHERE id='+lit(sid)+';COMMIT;')
 db.query(rs['database/secret-owner-binding.sql']['raw'].decode())
 return sid,vid
