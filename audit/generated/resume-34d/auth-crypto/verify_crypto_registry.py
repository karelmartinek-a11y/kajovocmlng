from pathlib import Path
import sys,json,secrets,uuid
HERE=Path(__file__).parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
from libpq_fixture import DB,lit
from auth_crypto_reference import *
raw=SSOT.read_bytes();rs=resource_index();database='auth_crypto_nonce_34d';admin=DB('postgres')
if not admin.query('SELECT 1 FROM pg_database WHERE datname='+lit(database)):admin.query('CREATE DATABASE '+database)
admin.close();db=DB(database);db.query('DROP SCHEMA public CASCADE;CREATE SCHEMA public;');db.query(rs['database/generation-create-foundations.sql']['raw'].decode());candidate=(HERE/'canonical-crypto-registry-proposed.sql').read_bytes();consumed=rs.get('database/canonical-crypto-registry.sql',{}).get('raw',candidate);assert consumed==candidate;db.query(consumed.decode())
def b(v):return "decode('"+v.hex()+"','hex')"
key=secrets.token_bytes(32);keyid='synthetic-one-immutable-key';obj=str(uuid.uuid4());op=str(uuid.uuid4());nonce=secrets.token_bytes(12);metadata=canonical({'purpose':'GENERATION_INITIAL_REQUEST','keyId':keyid,'identity':{'syntheticExample':'typed producer/consumer guard remains separately mandatory'},'profile':CRYPTO_PROFILE});cipher=secrets.token_bytes(40)
profile="INSERT INTO canonical_authenticated_crypto_profile VALUES('KCML_PROTECTED_INPUT_AES256_GCM_V1',"+b(profile_bytes())+','+b(profile_digest())+",'AES_256_GCM');"
master="INSERT INTO canonical_master_key_generation VALUES("+lit(keyid)+','+b(sha(key))+",1,'kcml-master-key','isolated-fixture.service',"+b(profile_digest())+",clock_timestamp());"
reservation="INSERT INTO canonical_protected_nonce_reservation VALUES("+','.join([lit(keyid),b(nonce),"'GENERATION_INITIAL_REQUEST'",lit(obj),lit(op),b(metadata),b(sha(metadata)),b(sha(cipher))])+');'
checks=[]
def test(name,sql,diagnostic=None):
 db.query('BEGIN')
 try:db.query(sql);ok=diagnostic is None;actual=None
 except Exception as e:actual=str(e);ok=diagnostic is not None and diagnostic in actual
 finally:db.query('ROLLBACK')
 checks.append({'case':name,'passed':ok,'expectedDiagnostic':diagnostic,'actualDiagnostic':actual})
test('exact-profile-key-nonce-positive',profile+master+reservation)
test('same-key-bytes-second-id-forbidden',profile+master+master.replace(lit(keyid),"'second-id'"),'canonical_master_key_generation_key_fingerprint_key')
test('cross-purpose-same-key-nonce-forbidden',profile+master+reservation+reservation.replace("'GENERATION_INITIAL_REQUEST'","'SECRET_IMMUTABLE_VERSION'").replace(lit(obj),lit(str(uuid.uuid4()))).replace(b(metadata),b(canonical({'purpose':'SECRET_IMMUTABLE_VERSION','keyId':keyid}))).replace(b(sha(metadata)),b(sha(canonical({'purpose':'SECRET_IMMUTABLE_VERSION','keyId':keyid})))),'canonical_protected_nonce_reservation_pkey')
test('same-object-reencryption-forbidden',profile+master+reservation+reservation.replace(b(nonce),b(secrets.token_bytes(12))),'canonical_crypto_nonce_one_object')
test('invalid-nonce-length',profile+master+reservation.replace(b(nonce),b(b'short')),'canonical_protected_nonce_reservation_nonce_check')
test('profile-not-actual-source-bytes-digest',profile.replace(b(profile_digest()),b(bytes(32))),'canonical_crypto_profile_bytes_digest')
for field in ('purpose','keyId'):
 bad=json.loads(metadata);del bad[field];badraw=canonical(bad)
 test('missing-linked-aad-'+field,profile+master+reservation.replace(b(metadata),b(badraw)).replace(b(sha(metadata)),b(sha(badraw))),'canonical_crypto_nonce_purpose_binding' if field=='purpose' else 'canonical_crypto_nonce_key_binding')
for table in ('canonical_authenticated_crypto_profile','canonical_master_key_generation','canonical_protected_nonce_reservation'):
 test('immutable-delete-'+table,profile+master+reservation+'DELETE FROM '+table+';','CANONICAL_CRYPTO_REGISTRY_IMMUTABLE')
report={'status':'PASS'if all(c['passed']for c in checks)else'BLOCKED','sourceDocumentSha256':sha(raw).hex(),'canonicalFoundationSha256':rs['database/generation-create-foundations.sql']['sha256'],'proposalRegistrySha256':sha(consumed).hex(),'postgresqlVersion':db.query('SHOW server_version')[0][0],'checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'scope':'Actual PostgreSQL exact canonical foundation plus explicit candidate crypto registry. Global key/nonce uniqueness and immutable registry only; full typed producer FK/install/service/systemd proof remains required. Registry presence does NOT attest systemd or authorize plaintext.','wholeOperationClosed':False,'supportSha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()).hex()for p in [Path(__file__),HERE/'canonical-crypto-registry-proposed.sql',HERE/'auth_crypto_reference.py',HERE/'libpq_fixture.py']}}
(HERE/'crypto-registry-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ('status','checked','failed')}));db.close()
