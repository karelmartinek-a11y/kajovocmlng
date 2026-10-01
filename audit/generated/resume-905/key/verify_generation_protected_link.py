"""Bounded real PG chain: actual auth/context/root + candidate typed nonce link.
Random fixture keys are not systemd evidence. No secret/key bytes in report.
"""
from pathlib import Path
import sys,json,copy
HERE=Path(__file__).parent;ROOT=HERE.parents[3]
for p in [ROOT/'scripts',ROOT/'audit/generated/resume-34d/auth-crypto',ROOT/'audit/generated/resume-d362/persistence']:sys.path.insert(0,str(p))
from ssot_sources import SSOT,resource_index
from generation_auth_crypto import canonical,sha,aad,open_snapshot
from libpq_fixture import DB,lit
original=ROOT/'audit/generated/resume-34d/auth-crypto/verify_authenticated_full_chain.py'
program=original.read_text().split('# Full positive')[0]
program=program.replace("database='auth_crypto_full_34d'","database='key_typed_chain_905'").replace('from auth_crypto_reference import *','from generation_auth_crypto import *').replace('from acceptance_reference import authenticate_owner_api','from generation_auth_acceptance import authenticate_owner_api')
ns={'__file__':str(original)};exec(compile(program,'reviewed-existing-auth-chain-positive-factory','exec'),ns)
db=ns['db'];rs=resource_index()
for name in ['database/generation-create-preroot.sql','database/canonical-crypto-registry.sql']:db.query(rs[name]['raw'].decode())
candidate=(HERE/'generation-protected-registry-link.sql').read_bytes();db.query(candidate.decode())
checks=[]
def b(v):return "decode('"+v.hex()+"','hex')"
def run(name,mut=None,code=None,commit=False):
 db.query('BEGIN')
 try:
  parts,meta,plain=ns['build']();env=ns['enc'] if 'enc'in ns else None
  # Extract actual bytes from native positive build's snapshot, never reencrypt.
  snapshot=parts['snapshot'];keyid='fixture-systemd-key-generation-1'
  # Current build returns metadata/plaintext; envelope is recoverable from SQL
  # after inserts before constraints. Reserve from actual row values.
  db.query(''.join(parts.values()))
  row=db.query("SELECT encode(ciphertext,'hex'),encode(nonce,'hex') FROM generation_job_initial_request_snapshot")[0]
  cipher=bytes.fromhex(row[0]);nonce=bytes.fromhex(row[1]);md=copy.deepcopy(meta);op=meta['logicalOperationId'];obj=meta['snapshotId']
  if mut=='wrong-context':md['trustedContextId']='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  if mut=='extra-aad-field':md['extraClientAuthority']=True
  if mut=='wrong-job':md['jobId']='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  if mut=='wrong-op':op='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  if mut=='wrong-object':obj='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  if mut=='wrong-cipherdigest':cipher=b'not the ciphertext'
  if mut=='wrong-nonce':nonce=b'123456789012'
  metadata=(canonical({'purpose':'GENERATION_INITIAL_REQUEST','keyId':keyid,'profile':ns['CRYPTO_PROFILE'],'identity':md}) if mut=='extra-aad-field' else aad(md,key_id=keyid))
  if mut=='whitespace-aad':metadata=json.dumps(json.loads(metadata),sort_keys=True,ensure_ascii=False,indent=2).encode('utf8')
  if mut=='different-order-aad':metadata=json.dumps(dict(reversed(list(json.loads(metadata).items()))),separators=(',',':'),ensure_ascii=False).encode('utf8')
  if mut=='numeric-recoding-aad':metadata=metadata.replace(b'\"applicationDeploymentEpoch\":1',b'\"applicationDeploymentEpoch\":1.0')
  db.query("INSERT INTO canonical_authenticated_crypto_profile VALUES('KCML_PROTECTED_INPUT_AES256_GCM_V1',"+b(ns['profile_bytes']())+','+b(ns['profile_digest']())+",'AES_256_GCM');")
  db.query('INSERT INTO canonical_master_key_generation VALUES('+lit(keyid)+','+b(sha(ns['key']))+",1,'kcml-master-key','isolated-fixture.service',"+b(ns['profile_digest']())+',clock_timestamp());')
  if mut!='missing-reservation':
   db.query('INSERT INTO canonical_protected_nonce_reservation VALUES('+','.join([lit(keyid),b(nonce),"'GENERATION_INITIAL_REQUEST'",lit(obj),lit(op),b(metadata),b(sha(metadata)),b(sha(cipher))])+');')
  db.query('SET CONSTRAINTS ALL IMMEDIATE')
  if code:ok=False;actual='ACCEPTED_UNEXPECTEDLY'
  else:
   actual=None;ok=True
   # Exact row metadata then actual authenticated decrypt/native validation.
   envelope={'algorithm':'AES_256_GCM','keyId':keyid,'cryptoProfileDigest':ns['profile_digest'](),'nonce':nonce,'ciphertext':cipher}
   with open_snapshot(envelope,ns['key'],keyid,meta,lambda raw:ns['validate_body']('generation.job.create',ns['strict_json'](raw))) as view:ok=bytes(view)==plain
  if commit and ok:db.query('COMMIT')
  else:db.query('ROLLBACK')
 except Exception as e:
  actual=str(e);ok=code is not None and code in actual;db.query('ROLLBACK')
 checks.append({'case':name,'passed':ok,'expectedDiagnostic':code,'actualDiagnostic':actual})
run('positive-real-auth-protected-row-global-registry-native-open')
for mut,code in [('missing-reservation','GENERATION_PROTECTED_RESERVATION_REQUIRED'),('wrong-context','GENERATION_PROTECTED_TYPED_AAD_INVALID'),('extra-aad-field','GENERATION_PROTECTED_TYPED_AAD_INVALID'),('wrong-job','GENERATION_PROTECTED_TYPED_AAD_INVALID'),('wrong-op','GENERATION_PROTECTED_RESERVATION_BINDING_INVALID'),('wrong-object','GENERATION_PROTECTED_RESERVATION_REQUIRED'),('wrong-cipherdigest','GENERATION_PROTECTED_RESERVATION_BINDING_INVALID'),('wrong-nonce','GENERATION_PROTECTED_RESERVATION_BINDING_INVALID'),('whitespace-aad','GENERATION_PROTECTED_TYPED_AAD_INVALID'),('different-order-aad','GENERATION_PROTECTED_TYPED_AAD_INVALID'),('numeric-recoding-aad','GENERATION_PROTECTED_TYPED_AAD_INVALID')]:run(mut,mut,code)
counts=db.query('SELECT (SELECT count(*) FROM generation_job),(SELECT count(*) FROM canonical_protected_nonce_reservation),(SELECT count(*) FROM domain_command)')[0]
checks.append({'case':'rollback-leaves-no-root-reservation-command','passed':counts==['0','0','0']})
run('actual-commit-and-authenticated-consumer',commit=True)
observer=DB('key_typed_chain_905');counts=observer.query('SELECT (SELECT count(*) FROM generation_job),(SELECT count(*) FROM canonical_protected_nonce_reservation),(SELECT count(*) FROM domain_command),(SELECT count(*) FROM transactional_outbox),(SELECT count(*) FROM audit_event)')[0]
checks.append({'case':'committed-root-reservation-command-outbox-audit-visible','passed':counts==['1']*5});observer.close()
# Codec equivalence exercises exact escaping and UTF8; these are bounded
# codec tests, not an admission of arbitrary profile names or Unicode identities.
for name,value in [('unicode-and-escapes',{'žluťoučký':'α/\\\"\b\f\n\r\t\x01','z':[None,True,False,1,{'é':'雪'}],'a':{}}),('empty-members',{'b':[],'a':{}})]:
 expected=canonical(value)
 actual=db.query('SELECT encode(convert_to(kcml_crypto_compact_sorted_json_v1('+lit(expected.decode())+'::jsonb),\'UTF8\'),\'hex\')')[0][0]
 checks.append({'case':'codec-'+name,'passed':bytes.fromhex(actual)==expected})
report={'status':'PASS'if all(c['passed'] for c in checks)else'BLOCKED','sourceDocumentSha256':sha(ns['raw']).hex(),'checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'postgresqlVersion':db.query('SHOW server_version')[0][0],'candidateSqlSha256':sha(candidate).hex(),'canonicalInputs':{n:rs[n]['sha256']for n in ['database/generation-create-foundations.sql','database/generation-create-authentication.sql','database/generation-create-preroot.sql','database/canonical-crypto-registry.sql']},'supportSha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()).hex()for p in [Path(__file__),original,ROOT/'scripts/generation_auth_crypto.py',ROOT/'scripts/generation_auth_acceptance.py',ROOT/'scripts/create_operation_contracts.py']},'systemdSourceProof':'BLOCKED','secretTypedJoinProof':'NOT_EVALUATED','wholeOperationClosed':False}
(HERE/'generation-protected-link-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));db.close()
