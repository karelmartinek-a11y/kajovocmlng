"""Read-only exports for independently authored combined PostgreSQL proofs."""
from pathlib import Path
from generation_descriptor_registry import pin,descriptor,pin_insert_sql
OWNER='10000000-0000-4000-8000-000000000001';SESSION='20000000-0000-4000-8000-000000000001';AUTH='30000000-0000-4000-8000-000000000001';INC='40000000-0000-4000-8000-000000000001'
def common(owner=OWNER,inc=INC,epoch=7):
 return f"INSERT INTO owner_identity(id,username,password_hash,password_changed_at,mfa_enabled,deployment_managed,session_epoch,created_at,updated_at,password_source) VALUES('{owner}','KRMAR78','SYNTHETIC_HASH_NOT_VERIFIER',clock_timestamp(),true,true,2,clock_timestamp(),clock_timestamp(),'GITHUB_ACTIONS_PASS');INSERT INTO platform_incarnation VALUES(1,'{inc}',1,clock_timestamp(),'SYNTHETIC_BOOTSTRAP',NULL,NULL);INSERT INTO application_deployment_head VALUES(1,{epoch},'80000000-0000-4000-8000-000000000001',decode(repeat('01',32),'hex'),'{inc}',0,clock_timestamp());"+pin_insert_sql(epoch)
def session_acceptance(owner=OWNER,session=SESSION,auth=AUTH):
 return f"INSERT INTO owner_session(id,owner_identity_id,lookup_digest,session_hash,created_at,last_seen_at,expires_at,session_epoch)VALUES('{session}','{owner}',decode(repeat('01',32),'hex'),'SYNTHETIC_NOT_AUTH_IMPLEMENTATION',clock_timestamp()-interval '2hour',clock_timestamp()-interval '1min',clock_timestamp()+interval '1hour',2);INSERT INTO generation_create_authentication_acceptance(id,owner_id,access_channel,session_id,session_epoch,session_lookup_digest,accepted_at)VALUES('{auth}','{owner}','OWNER_SESSION','{session}',2,decode(repeat('01',32),'hex'),clock_timestamp());"
def call(owner=OWNER,auth=AUTH,request_digest='03'*32,client_key_digest='sha256:'+'05'*32):
 p=pin();d=descriptor(owner,client_key_digest,p)
 return f"SELECT kcml_generation_create_context_v1('{auth}',decode('{request_digest}','hex'),decode('{p['contractDigest'].hex()}','hex'),decode('{d.hex()}','hex'));"
# Synthetic hashes/ciphertext are explicitly NOT actual token-verifier/crypto proof.
