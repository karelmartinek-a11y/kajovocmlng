"""Bounded real PG chain: actual auth/context/root + candidate typed nonce link.
Random fixture keys are not systemd evidence. No secret/key bytes in report.
"""
from pathlib import Path
import sys,json,copy
HERE=Path(__file__).parent;ROOT=HERE.parents[4]
for p in [ROOT/'scripts',ROOT/'audit/generated/resume-34d/auth-crypto',ROOT/'audit/generated/resume-d362/persistence']:sys.path.insert(0,str(p))
from ssot_sources import SSOT,resource_index
from generation_auth_crypto import canonical,sha,aad,open_snapshot
from libpq_fixture import DB,lit
original=ROOT/'audit/generated/resume-34d/auth-crypto/verify_authenticated_full_chain.py'
program=original.read_text().split('# Full positive')[0]
program=program.replace("database='auth_crypto_full_34d'","database='archive_peer_key_mutants_905'").replace('from auth_crypto_reference import *','from generation_auth_crypto import *').replace('from acceptance_reference import authenticate_owner_api','from generation_auth_acceptance import authenticate_owner_api')
ns={'__file__':str(original)};exec(compile(program,'reviewed-existing-auth-chain-positive-factory','exec'),ns)
db=ns['db'];rs=resource_index()
for name in ['database/generation-create-preroot.sql','database/canonical-crypto-registry.sql']:db.query(rs[name]['raw'].decode())
candidate=rs['database/generation-protected-registry-link.sql']['raw'];db.query(candidate.decode())
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
  purpose='SECRET_IMMUTABLE_VERSION' if mut=='wrong-purpose' else 'GENERATION_INITIAL_REQUEST'
  if mut=='wrong-context':md['trustedContextId']='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  if mut=='extra-aad-field':md['extraClientAuthority']=True
  if mut=='wrong-job':md['jobId']='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  if mut=='wrong-op':op='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  if mut=='wrong-object':obj='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  if mut=='wrong-cipherdigest':cipher=b'not the ciphertext'
  if mut=='wrong-nonce':nonce=b'123456789012'
  metadata=(canonical({'purpose':'GENERATION_INITIAL_REQUEST','keyId':keyid,'profile':ns['CRYPTO_PROFILE'],'identity':md}) if mut=='extra-aad-field' else canonical({'purpose':purpose,'keyId':keyid,'profile':ns['CRYPTO_PROFILE'],'identity':md}) if mut=='wrong-purpose' else aad(md,key_id=keyid))
  if mut=='noncanonical-aad':metadata=json.dumps(json.loads(metadata),sort_keys=True,indent=2,ensure_ascii=False).encode('utf8')
  db.query("INSERT INTO canonical_authenticated_crypto_profile VALUES('KCML_PROTECTED_INPUT_AES256_GCM_V1',"+b(ns['profile_bytes']())+','+b(ns['profile_digest']())+",'AES_256_GCM');")
  db.query('INSERT INTO canonical_master_key_generation VALUES('+lit(keyid)+','+b(sha(ns['key']))+",1,'kcml-master-key','isolated-fixture.service',"+b(ns['profile_digest']())+',clock_timestamp());')
  if mut!='missing-reservation':
   db.query('INSERT INTO canonical_protected_nonce_reservation VALUES('+','.join([lit(keyid),b(nonce),lit(purpose),lit(obj),lit(op),b(metadata),b(sha(metadata)),b(sha(cipher))])+');')
  db.query('SET CONSTRAINTS ALL IMMEDIATE')
  if code and mut not in ('open-context-swap','open-envelope-swap'):ok=False;actual='ACCEPTED_UNEXPECTEDLY'
  else:
   actual=None;ok=True
   # Exact row metadata then actual authenticated decrypt/native validation.
   envelope={'algorithm':'AES_256_GCM','keyId':keyid,'cryptoProfileDigest':ns['profile_digest'](),'nonce':nonce,'ciphertext':cipher}
   opening_metadata=copy.deepcopy(meta)
   if mut=='open-context-swap':opening_metadata['trustedContextId']='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
   if mut=='open-envelope-swap':envelope['ciphertext']=envelope['ciphertext'][:-1]+bytes([envelope['ciphertext'][-1]^1])
   with open_snapshot(envelope,ns['key'],keyid,opening_metadata,lambda raw:ns['validate_body']('generation.job.create',ns['strict_json'](raw))) as view:ok=bytes(view)==plain
  if commit and ok:db.query('COMMIT')
  else:db.query('ROLLBACK')
 except Exception as e:
  actual=str(e);ok=code is not None and code in actual;db.query('ROLLBACK')
 checks.append({'case':name,'passed':ok,'expectedDiagnostic':code,'actualDiagnostic':actual})
run('independent-counterexample-whitespace-AAD-reservation',mut='noncanonical-aad')
report={'status':'DEFECT_REPRODUCED'if checks[0]['passed']else'NOT_REPRODUCED','sourceDocumentSha256':sha(SSOT.read_bytes()).hex(),'canonicalExtensionSha256':sha(candidate).hex(),'postgresqlVersion':db.query('SHOW server_version')[0][0],'checks':checks,'meaning':'Accepted SQL reservation and actual authenticated opening despite whitespace-bearing stored authenticated_metadata_bytes. §12.54 mandates exact sorted compact actual AAD bytes; semantic jsonb equality loses this condition. Does not demonstrate caller authorization or systemd source.','supportSha256':sha(Path(__file__).read_bytes()).hex()}
(HERE/'aad-byte-counterexample.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status']}));db.close()
