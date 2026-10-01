import sys,json,subprocess,hashlib,uuid,copy
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
# Own positive authenticated current reader/key fixture; never foreign DB state.
import verify_owner_value_read as owner
from ssot_sources import resources,SSOT
from jsonschema import Draft202012Validator,FormatChecker
from generation_auth_crypto import seal,aad,sha
from secret_profile_reference import canonical_value_digest
from secret_profile_import import candidate_from_http
from secret_owner_value_read import open_owner_value
base=owner.base;run=base.run;lit=base.lit;b=base.b;candidate=(OUT/'secret-legacy-raw-origin.sql').read_bytes();q=run(candidate.decode());assert q.returncode==0,q.stderr
oldcommit='34d3a75c47a92ab7d8e0dac84f581549a15445ca';oldsrc=subprocess.run(['git','show',oldcommit+':00_SSOT/KajovoCMLNG_SSOT.md'],capture_output=True).stdout;assert sha(oldsrc).hex()=='2bc1ce83521b398966723169b1523e9a15a350abfb3131c0ff6b8fa8727c2854'
oldresources={x['path']:x for x in resources(oldsrc.decode())};oldmask=oldresources['contracts/create-operation-design.schema.json']['raw'];oldschema=json.loads(oldmask);oldid=oldschema['$id']
legacy_secret=str(uuid.uuid4());legacy_version=str(uuid.uuid4());context=str(uuid.uuid4());logical=str(uuid.uuid4());original=b'JBSWY3DPEHPK3PXP'
request={'stableName':'SYNTHETIC_LEGACY_TOTP','displayName':'Synthetic historical RAW','type':'TOTP_SEED','value':{'encoding':'UTF8','text':original.decode()}}
# ACTUAL archived schema, no current/global-id substitution. Structural proof
# does not assert that this invented fixture is an authentic historical admission.
Draft202012Validator({**oldschema,'$ref':'#/$defs/SecretCreateBody'},format_checker=FormatChecker()).validate(request)
try:candidate_from_http(json.dumps(request).encode());raise AssertionError('freshcomplexRAW accepted')
except Exception as e:assert getattr(e,'code',None)=='SECRET_PROFILE_REQUIRED',repr(e)
cases=[{'id':'archived-real-schema-accepts-original-RAW-representation','status':'PASS'},{'id':'fresh-complex-RAW-create-still-specific-profile-required','status':'PASS','diagnostic':'SECRET_PROFILE_REQUIRED'}]
meta={'ownerId':owner.owner,'secretId':legacy_secret,'secretVersionId':legacy_version,'secretType':'TOTP_SEED','representation':'RAW_UTF8','profileId':None,'schemaId':None,'schemaDigest':None,'plaintextByteLength':len(original),'originalImportBytesDigest':'sha256:'+sha(original).hex(),'canonicalValueDigest':canonical_value_digest({'type':'TOTP_SEED','representation':'RAW_UTF8','profileId':None,'bytes':original}),'trustedContextId':context,'logicalOperationId':logical}
env=seal(original,base.key,base.KEYID,meta,'SECRET_IMMUTABLE_VERSION');auth=aad(meta,'SECRET_IMMUTABLE_VERSION',base.KEYID)
immutable={'versionId':legacy_version,'secretId':legacy_secret,'versionNumber':'1','secretType':'TOTP_SEED','representation':'RAW_UTF8','profileId':None,'schemaId':None,'schemaDigest':None,'payloadFormat':'EXACT_SECRET_BYTES_V1','plaintextByteLength':len(original),'ciphertextHex':env['ciphertext'].hex(),'nonceHex':env['nonce'].hex(),'algorithm':env['algorithm'],'keyId':base.KEYID,'fingerprint':sha(original).hex()[:16],'originalImportBytesDigest':sha(original).hex(),'canonicalValueDigest':meta['canonicalValueDigest'][7:],'creatorContextId':context}
def compact(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
rowbytes=compact(immutable);receipt={'receiptKind':'ORIGINAL_RETAINED_SECRET_ADMISSION','secretId':legacy_secret,'versionId':legacy_version,'representation':'RAW_UTF8','secretType':'TOTP_SEED','originalSchemaId':oldid,'originalSchemaDigest':sha(oldmask).hex(),'originalSourceDigest':sha(oldsrc).hex(),'originalCreatorContextId':context,'originalLogicalOperationId':logical,'originalImmutableRowDigest':sha(rowbytes).hex()};receiptbytes=compact(receipt)
cols={'id':legacy_version,'secret_id':legacy_secret,'version_number':1,'secret_type':'TOTP_SEED','value_representation':'RAW_UTF8','payload_format':'EXACT_SECRET_BYTES_V1','plaintext_byte_length':len(original),'ciphertext':env['ciphertext'],'nonce':env['nonce'],'algorithm':env['algorithm'],'key_id':base.KEYID,'fingerprint':sha(original).hex()[:16],'original_import_bytes_digest':sha(original),'canonical_value_digest':bytes.fromhex(meta['canonicalValueDigest'][7:]),'lifecycle':'CREATED','created_at':'2026-09-30T00:00:00Z','creator_context_id':context}
create="INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,status,state_version,secret_activation_epoch,created_at,updated_at)VALUES("+lit(legacy_secret)+",'SYNTHETIC_LEGACY_TOTP','Historical RAW','TOTP_SEED','INACTIVE',0,0,now(),now());"
create+='INSERT INTO canonical_protected_nonce_reservation VALUES('+lit(base.KEYID)+','+b(env['nonce'])+",'SECRET_IMMUTABLE_VERSION',"+lit(legacy_version)+','+lit(logical)+','+b(auth)+','+b(sha(auth))+','+b(sha(env['ciphertext']))+');'
create+='INSERT INTO kcml_secret_v1.secret_version('+','.join(cols)+')VALUES('+','.join(lit(v)for v in cols.values())+');'
def origin(rb=rowbytes,rec=receiptbytes,schema=oldmask):
 return 'INSERT INTO kcml_secret_v1.legacy_raw_origin VALUES('+lit(legacy_version)+','+lit(legacy_secret)+','+lit(oldid)+','+b(schema)+','+b(sha(schema))+','+lit('git:'+oldcommit)+','+b(sha(oldsrc))+','+b(rec)+','+b(sha(rec))+','+b(rb)+','+b(sha(rb))+',now(),session_user);'
def reject(name,sql,code):
 q=run(sql);assert q.returncode!=0 and code in q.stderr,(name,q.stderr);cases.append({'id':name,'status':'PASS','diagnostic':code})
reject('complex-RAW-store-without-retained-original-origin','BEGIN;'+create+'COMMIT;','SECRET_LEGACY_RAW_ORIGIN_REQUIRED')
bad={**immutable,'representation':'PROFILE_JSON_V1'};reject('original-representation-cannot-be-rewritten','BEGIN;'+create+origin(compact(bad))+'COMMIT;','SECRET_LEGACY_IMMUTABLE_ROW_MISMATCH')
bad={**receipt,'originalCreatorContextId':str(uuid.uuid4())};reject('wrong-original-context-with-valid-receipt-digest','BEGIN;'+create+origin(rec=compact(bad))+'COMMIT;','SECRET_LEGACY_RETAINED_ADMISSION_BINDING_MISMATCH')
bad={**receipt,'originalLogicalOperationId':str(uuid.uuid4())};reject('wrong-original-logical-operation-with-valid-digest','BEGIN;'+create+origin(rec=compact(bad))+'COMMIT;','SECRET_LEGACY_RETAINED_ADMISSION_BINDING_MISMATCH')
q=run('BEGIN;'+create+origin()+'COMMIT;');assert q.returncode==0,q.stderr;cases.append({'id':'exact-protected-original-row-schema-retained-receipt-restore-commit','status':'PASS'})
# Read inactive immutable CREATED legacy version through exact selector. No
# activation, schema/profile migration, trim or reinterpretation is performed.
q=run('BEGIN;SELECT kcml_secret_v1.owner_api_value_read_begin_v1('+lit(legacy_secret)+','+lit(legacy_version)+');ROLLBACK;');assert q.returncode==0,q.stderr;snapshot=json.loads(next(x for x in q.stdout.splitlines()if x.startswith('{')))
assert open_owner_value(snapshot,[('Authorization',b'Bearer '+owner.token2)],1024,base.key,base.KEYID)==original;cases.append({'id':'authenticated-immutable-RAW-owner-read-byte-preserving-no-profile-guess','status':'PASS'})
reject('original-archive-row-immutable',"UPDATE kcml_secret_v1.legacy_raw_origin SET original_source_identity='OTHER';",'SECRET_PROFILE_DEFINITION_IMMUTABLE')
reject('legacy-ciphertext-still-immutable',"UPDATE kcml_secret_v1.secret_version SET ciphertext=decode('00','hex') WHERE id="+lit(legacy_version)+';','SECRET_VERSION_CRYPTO_IMMUTABLE')
reject('untrusted-caller-cannot-publish-legacy-origin','SET SESSION AUTHORIZATION kcml_broker_untrusted_fixture;'+origin(),'permission denied for table')
report={'sourceSha256':sha(SSOT.read_bytes()).hex(),'checked':len(cases),'failed':0,'cases':cases,'postgresVersion':run('SHOW server_version;').stdout.strip(),'candidateSqlSha256':sha(candidate).hex(),'historicalSchemaResourceDigest':sha(oldmask).hex(),'historicalSourceCommit':oldcommit,'historicalSourceDigest':sha(oldsrc).hex(),'originalSecretType':'TOTP_SEED','originalRepresentation':'RAW_UTF8','syntheticRestoredFixture':True,'authenticHistoricalAdmissionProducer':'NOT_EVALUATED_REQUIRED_ARCHIVE_PUBLISHER','plaintextInReport':False,'wholeOperationClosed':False,'implementationAcceptance':'NOT_EVALUATED'}
(OUT/'legacy-restore-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'legacy restoration PASS')
