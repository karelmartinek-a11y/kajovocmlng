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
cases=[]
conn=subprocess.Popen(P+['-d',DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
def tx(sql):
 conn.stdin.write(sql+'\n\\echo TX_END\n');conn.stdin.flush();lines=[]
 while True:
  line=conn.stdout.readline()
  if not line:raise AssertionError('transaction terminated:'+conn.stderr.read())
  if line.strip()=='TX_END':return lines
  lines.append(line.strip())
headers=[('Authorization',b'Bearer '+token)]
target=base.ids['secret'];corr=str(uuid.uuid4());select="SELECT kcml_secret_v1.owner_api_value_read_begin_v1("+lit(target)+',NULL);'
lines=tx('BEGIN;'+select);snapshot=json.loads(next(x for x in lines if x.startswith('{')))
assert open_owner_value(snapshot,headers,1024,base.key,base.KEYID)==base.imported['bytes'];cases.append({'id':'current-owner-API-verified-locked-target-canonical-open-native-profile-byteexact','status':'PASS'})
for label,badheaders,code in [('wrong-bearer',[('Authorization',b'Bearer WRONG')],'OWNER_API_AUTHENTICATION_FAILED'),('create-context-is-not-credential',[('Authorization',('Bearer '+base.ids['creationctx']).encode())],'OWNER_API_AUTHENTICATION_FAILED')]:
 try:open_owner_value(snapshot,badheaders,1024,base.key,base.KEYID);raise AssertionError(label+' accepted')
 except ValueError as e:assert str(e)==code,(label,e);cases.append({'id':label,'status':'PASS','diagnostic':code})
bad=copy.deepcopy(snapshot);bad['protectedRow']['version']['id']=str(uuid.uuid4())
try:open_owner_value(bad,headers,1024,base.key,base.KEYID);raise AssertionError('wrong version accepted')
except ValueError as e:assert str(e)=='SECRET_OWNER_IMMUTABLE_IDENTITY_MISMATCH';cases.append({'id':'wrong-immutable-version','status':'PASS','diagnostic':str(e)})
# Independent positive-derived consumer mutations. Actual ciphertext/domain
# witness above is valid before each mutation; check exact intended diagnostic.
for label,edit,code in [
 ('peer-foreign-creator-context',lambda v:v['protectedRow']['version'].update(creator_context_id=str(uuid.uuid4())),'SECRET_OWNER_IMMUTABLE_IDENTITY_MISMATCH'),
 ('peer-swapped-nonce',lambda v:v['protectedRow']['version'].update(nonce='\\x'+os.urandom(12).hex()),'PROTECTED_INPUT_AUTHENTICATION_FAILED'),
 ('peer-wrong-server-owner',lambda v:v.update(ownerId=str(uuid.uuid4())),'SECRET_OWNER_IMMUTABLE_IDENTITY_MISMATCH'),
 ('peer-different-original-byte-digest',lambda v:v['protectedRow']['version'].update(original_import_bytes_digest='\\x'+bytes(32).hex()),'SECRET_OWNER_STORED_METADATA_MISMATCH'),
 ('peer-ciphertext-digest-substitution',lambda v:v['protectedRow']['protectedAuthority'].update(ciphertextDigestHex=bytes(32).hex()),'SECRET_PROTECTED_ROW_DIGEST_MISMATCH')]:
 bad=copy.deepcopy(snapshot);edit(bad)
 try:open_owner_value(bad,headers,1024,base.key,base.KEYID);raise AssertionError(label+' accepted')
 except ValueError as e:assert str(e)==code,(label,str(e));cases.append({'id':label,'status':'PASS','diagnostic':str(e)})
audit="SELECT kcml_secret_v1.owner_api_value_read_audit_v1("+lit(owner)+',1,1,'+lit(target)+','+lit(base.ids['version'])+','+lit(corr)+');';assert len(tx(audit))==1
cases.append({'id':'actual-read-audit-after-verifier-and-open-same-held-transaction','status':'PASS'})
# Actual credential rotation SQL candidate in independent session must wait on
# B3 SHARE; physical deferred Secret/version/fingerprint constraints execute.
token2=os.urandom(32).hex().encode();vid2=str(uuid.uuid4());meta2={**meta,'secretVersionId':vid2,'plaintextByteLength':len(token2),'originalImportBytesDigest':'sha256:'+sha(token2).hex(),'canonicalValueDigest':canonical_value_digest({'type':'API_KEY','representation':'RAW_UTF8','profileId':None,'bytes':token2})}
rotation='SELECT pg_backend_pid();BEGIN;SELECT 1 FROM owner_api_credential WHERE singleton_key=1 FOR UPDATE;SELECT 1 FROM owner_identity WHERE id='+lit(owner)+' FOR UPDATE;SELECT 1 FROM kcml_secret_v1.secret_record WHERE id='+lit(sid)+' FOR UPDATE;'+version_sql(vid2,token2,meta2)
rotation+="UPDATE kcml_secret_v1.secret_version SET lifecycle='RETIRED',retired_at=now() WHERE id="+lit(version)+";UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at=now(),activation_logical_operation_id="+lit(creation)+' WHERE id='+lit(vid2)+';UPDATE kcml_secret_v1.secret_record SET active_version_id='+lit(vid2)+',state_version=state_version+1,secret_activation_epoch=secret_activation_epoch+1 WHERE id='+lit(sid)+';UPDATE owner_api_credential SET secret_version_id='+lit(vid2)+',verifier_hash='+lit(verifier_hash(token2))+',fingerprint='+lit(fingerprint(token2))+',credential_version=credential_version+1,credential_activation_epoch=credential_activation_epoch+1;COMMIT;'
rot=subprocess.Popen(P+['-d',DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1);rot.stdin.write(rotation+'\n');rot.stdin.close();pid=int(rot.stdout.readline().strip());deadline=time.monotonic()+3
while time.monotonic()<deadline:
 if run('SELECT wait_event_type FROM pg_stat_activity WHERE pid='+str(pid)).stdout.strip()=='Lock':break
 time.sleep(.01)
else:raise AssertionError('credential rotation did not wait on real B3 lock')
assert open_owner_value(snapshot,headers,1024,base.key,base.KEYID)==base.imported['bytes'];tx('COMMIT;');assert rot.wait(timeout=5)==0,rot.stderr.read();cases.append({'id':'actual-credential-rotation-linearizes-after-read-open-audit-commit','status':'PASS'})
lines=tx('BEGIN;'+select);new=json.loads(next(x for x in lines if x.startswith('{')))
try:open_owner_value(new,headers,1024,base.key,base.KEYID);raise AssertionError('rotated stale key accepted')
except ValueError as e:assert str(e)=='OWNER_API_AUTHENTICATION_FAILED';cases.append({'id':'old-credential-rejected-after-rotation-commit','status':'PASS','diagnostic':str(e)})
assert open_owner_value(new,[('Authorization',b'Bearer '+token2)],1024,base.key,base.KEYID)==base.imported['bytes'];cases.append({'id':'new-current-credential-read-after-rotation','status':'PASS'});tx('ROLLBACK;')
# Explicit OWN credential reveal is NOT granted by a valid API token.
lines=tx('BEGIN;SELECT kcml_secret_v1.owner_api_value_read_begin_v1('+lit(sid)+',NULL);');reserved=json.loads(next(x for x in lines if x.startswith('{')))
try:open_owner_value(reserved,[('Authorization',b'Bearer '+token2)],1024,base.key,base.KEYID);raise AssertionError('OWNER credential API reveal accepted')
except ValueError as e:assert str(e)=='OWNER_CREDENTIAL_REVEAL_REQUIRES_OWNER_SESSION';cases.append({'id':'reserved-credential-reveal-preserves-OWNER-session-authority','status':'PASS','diagnostic':str(e)})
# Target existence is never exposed before fresh authentication.
try:open_owner_value(reserved,[('Authorization',b'Bearer WRONG')],1024,base.key,base.KEYID);raise AssertionError('wrong bearer bypassed auth ordering')
except ValueError as e:assert str(e)=='OWNER_API_AUTHENTICATION_FAILED';cases.append({'id':'authentication-precedes-reserved-resource-diagnostic','status':'PASS','diagnostic':str(e)})
tx('ROLLBACK;')
lines=tx('BEGIN;SELECT kcml_secret_v1.owner_api_value_read_begin_v1('+lit(target)+','+lit(version)+');');wrongparent=json.loads(next(x for x in lines if x.startswith('{')))
try:open_owner_value(wrongparent,[('Authorization',b'Bearer '+token2)],1024,base.key,base.KEYID);raise AssertionError('cross-secret version accepted')
except ValueError as e:assert str(e)=='SECRET_OWNER_VERSION_UNAVAILABLE';cases.append({'id':'explicit-immutable-version-must-belong-to-selected-secret','status':'PASS','diagnostic':str(e)})
tx('ROLLBACK;');conn.stdin.close();assert conn.wait(timeout=5)==0
q=run('SET SESSION AUTHORIZATION kcml_broker_untrusted_fixture;'+select);assert q.returncode!=0 and 'permission denied for function'in q.stderr;cases.append({'id':'untrusted-role-cannot-invoke-private-owner-read','status':'PASS'})
report={'sourceSha256':hashlib.sha256(src).hexdigest(),'sourceUnchanged':src==base.SSOT.read_bytes(),'checked':len(cases),'failed':0,'cases':cases,'postgresVersion':run('SHOW server_version;').stdout.strip(),'candidateSqlSha256':hashlib.sha256(candidate).hexdigest(),'independentReviewScope':'Actual candidate SQL/auth/open/profile/rotation chain reproduced in separate DB; five new positive-derived identity/nonce/digest negatives; no whole Secret or actual systemd claim','supportSha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),OUT/'verify_broker.py',OUT/'secret_owner_value_read.py',OUT/'secret_broker_open.py',OUT/'secret-owner-api-value-read.sql',OUT/'secret-broker-boundary.sql']},'canonicalAuthTableStatementHashes':{k:hashlib.sha256(v).hexdigest()for k,v in tables.items()},'plaintextInReport':False,'actualCanonicalAPIVerifier':True,'actualCanonicalCrypto':True,'systemdCredentialSource':'NOT_EVALUATED_SYNTHETIC_KEY','wholeOperationClosed':False,'excluded':['Canonical root-producer create/rotation command/event/outbox/audit joins','Global audit chain integration','OWNER-session credential reveal verifier','Explicit historical version HTTP mask'],'implementationAcceptance':'NOT_EVALUATED'}
(OUT/'owner-value-read-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'owner read PASS')
