import sys,json,subprocess,hashlib,uuid,os,time,copy
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
# Own fixture first: exact canonical roots/key registry + actual crypto/native
# broker boundary. No other agent DB or output is touched.
import verify_broker as base
from secret_owner_value_read import open_owner_value
from generation_auth_crypto import verifier_hash,fingerprint,seal,aad,sha
from secret_profile_reference import canonical_value_digest
P=base.P;DB=base.DB;run=base.run;r=base.r;lit=base.lit;b=base.b
src=base.source;foundation=r['database/generation-create-foundations.sql']['raw'];tables={}
for name in ['owner_identity','owner_api_credential','platform_incarnation','application_deployment_head']:
 a=foundation.index(('CREATE TABLE '+name+' (').encode());z=foundation.index(b'\n);',a)+3;tables[name]=foundation[a:z]
candidate=(OUT/'secret-owner-api-value-read.sql').read_bytes()
q=run('DROP TABLE IF EXISTS owner_api_credential,owner_identity,platform_incarnation,application_deployment_head CASCADE;DROP TABLE IF EXISTS kcml_secret_v1.owner_value_read_audit CASCADE;DROP FUNCTION IF EXISTS kcml_secret_v1.owner_api_value_read_begin_v1(uuid,uuid),kcml_secret_v1.owner_api_value_read_audit_v1(uuid,bigint,bigint,uuid,uuid,uuid) CASCADE;CREATE EXTENSION IF NOT EXISTS citext;'+b'\n'.join(tables.values()).decode()+r['database/secret-owner-binding.sql']['raw'].decode()+candidate.decode());assert q.returncode==0,q.stderr
owner=base.ids['owner'];sid=str(uuid.uuid4());version=str(uuid.uuid4());context=str(uuid.uuid4());creation=str(uuid.uuid4());incarnation=str(uuid.uuid4());token=os.urandom(32).hex().encode()
meta={'ownerId':owner,'secretId':sid,'secretVersionId':version,'secretType':'API_KEY','representation':'RAW_UTF8','profileId':None,'schemaId':None,'schemaDigest':None,'plaintextByteLength':len(token),'originalImportBytesDigest':'sha256:'+sha(token).hex(),'canonicalValueDigest':canonical_value_digest({'type':'API_KEY','representation':'RAW_UTF8','profileId':None,'bytes':token}),'trustedContextId':context,'logicalOperationId':creation}
def version_sql(version,token,meta):
 env=seal(token,base.key,base.KEYID,meta,'SECRET_IMMUTABLE_VERSION');auth=aad(meta,'SECRET_IMMUTABLE_VERSION',base.KEYID)
 cols={'id':version,'secret_id':sid,'version_number':1 if version==globals()['version']else 2,'secret_type':'API_KEY','value_representation':'RAW_UTF8','payload_format':'EXACT_SECRET_BYTES_V1','plaintext_byte_length':len(token),'ciphertext':env['ciphertext'],'nonce':env['nonce'],'algorithm':env['algorithm'],'key_id':base.KEYID,'fingerprint':fingerprint(token),'original_import_bytes_digest':sha(token),'canonical_value_digest':bytes.fromhex(meta['canonicalValueDigest'][7:]),'lifecycle':'CREATED','created_at':'2026-10-01T00:00:00Z','creator_context_id':context}
 sql='INSERT INTO canonical_protected_nonce_reservation VALUES('+lit(base.KEYID)+','+b(env['nonce'])+",'SECRET_IMMUTABLE_VERSION',"+lit(version)+','+lit(creation)+','+b(auth)+','+b(sha(auth))+','+b(sha(env['ciphertext']))+');'
 sql+='INSERT INTO kcml_secret_v1.secret_version('+','.join(cols)+')VALUES('+','.join(lit(v)for v in cols.values())+');'
 return sql
sql="INSERT INTO owner_identity(id,username,password_hash,password_changed_at,mfa_enabled,deployment_managed,created_at,updated_at,password_source) VALUES("+lit(owner)+",'KRMAR78','ISOLATED_NOT_PASSWORD_PROOF',now(),false,true,now(),now(),'GITHUB_ACTIONS_PASS');"
sql+='INSERT INTO platform_incarnation VALUES(1,'+lit(incarnation)+",1,now(),'ISOLATED',NULL,NULL);"
sql+='INSERT INTO application_deployment_head VALUES(1,1,'+lit(str(uuid.uuid4()))+','+b(b'M'*32)+','+lit(incarnation)+',0,now());'
sql+='BEGIN;INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,state_version,secret_activation_epoch,created_at,updated_at)VALUES('+lit(sid)+",'KCML_OWNER_API_KEY','Synthetic API credential','API_KEY','ISOLATED_NOT_RECORD_POLICY',0,0,now(),now());"+version_sql(version,token,meta)
sql+="UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=now(),activation_logical_operation_id="+lit(creation)+' WHERE id='+lit(version)+';UPDATE kcml_secret_v1.secret_record SET active_version_id='+lit(version)+',state_version=1,secret_activation_epoch=1 WHERE id='+lit(sid)+';'
sql+='INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,credential_activation_epoch,created_at)VALUES(1,'+lit(sid)+','+lit(version)+','+lit(verifier_hash(token))+','+lit(fingerprint(token))+',1,1,now());COMMIT;'
q=run(sql);assert q.returncode==0,q.stderr

# Fresh real credential and secret rows are now committed. The only mutation
# was key registry's actual declared profile at initial insertion; no immutable
# triggers were disabled, no caller authorization flag was used.
select="SELECT kcml_secret_v1.owner_api_value_read_begin_v1("+lit(base.ids['secret'])+",NULL);"
conn=subprocess.Popen(P+['-d',DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
conn.stdin.write('BEGIN;'+select+'\n\\echo SNAPSHOT_END\n');conn.stdin.flush()
lines=[]
while True:
 line=conn.stdout.readline()
 if not line:raise AssertionError('SQL snapshot terminated:'+conn.stderr.read())
 if line.strip()=='SNAPSHOT_END':break
 lines.append(line.strip())
snapshot=json.loads(next(x for x in lines if x.startswith('{')))
actual=base.run("SELECT encode(crypto_profile_digest,'hex') FROM canonical_master_key_generation WHERE key_id="+lit(base.KEYID)).stdout.strip()
try:
 value=open_owner_value(snapshot,[('Authorization',b'Bearer '+token)],1024,base.key,base.KEYID)
 accepted=value==base.imported['bytes'];diagnostic=None
except ValueError as e:accepted=False;diagnostic=str(e)
conn.stdin.write('ROLLBACK;\n');conn.stdin.close();assert conn.wait(timeout=5)==0
report={'status':'FIX_VERIFIED'if not accepted and diagnostic=='SECRET_KEY_CRYPTO_PROFILE_MISMATCH'and actual!=base.profile_digest().hex()else'BLOCKED','sourceDocumentSha256':hashlib.sha256(src).hexdigest(),'postgresqlVersion':base.run('SHOW server_version;').stdout.strip(),'case':'actual-key-registry-profile-misbinding-owner-read','actualRegistryProfileDigest':actual,'consumedCanonicalProfileDigest':base.profile_digest().hex(),'acceptedByteExactOwnerValue':accepted,'diagnostic':diagnostic,'meaning':'The preserved physical key-profile misbinding now rejects SECRET_KEY_CRYPTO_PROFILE_MISMATCH under actual valid token and held SQL locks. SQL returns actual registry digest/bytes and helper verifies them. No immutable trigger disabled; provider/systemd remains unproved.','candidateSqlSha256':hashlib.sha256(candidate).hexdigest(),'helperSha256':hashlib.sha256((OUT/'secret_owner_value_read.py').read_bytes()).hexdigest(),'plaintextInReport':False}
(OUT/'profile-binding-fix-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
