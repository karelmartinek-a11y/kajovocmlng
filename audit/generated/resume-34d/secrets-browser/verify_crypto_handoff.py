"""Actual shared canonical-profile primitive handoff, no systemd provisioning claim."""
import hashlib,importlib.util,json,os
from pathlib import Path
from synthetic_profile_fixtures import fixtures
from secret_import_adapter import candidate_from_http,APPROVED_PROFILES
from profile_reference import schema_digest,canonical_value_digest,parse_profile,digest
D=Path(__file__).resolve().parent;crypto_path=D.parent/'auth-crypto/auth_crypto_reference.py'
spec=importlib.util.spec_from_file_location('shared_auth_crypto',crypto_path);crypto=importlib.util.module_from_spec(spec);spec.loader.exec_module(crypto)
checks=[]
def yes(id_,fn):
 try:checks.append({'id':id_,'passed':fn()is not False})
 except Exception as e:checks.append({'id':id_,'passed':False,'unexpectedException':type(e).__name__,'code':getattr(e,'code',str(e)if len(str(e))<80 else None)})
def no(id_,fn,code):
 try:fn();checks.append({'id':id_,'passed':False,'actual':'ACCEPTED','expected':code})
 except ValueError as e:checks.append({'id':id_,'passed':str(e)==code,'actualCode':str(e),'expectedCode':code})
for p in APPROVED_PROFILES:
 from profile_reference import INVENTORY,SCHEMA
 body={'stableName':'SYNTHETIC','displayName':'Synthetic','type':INVENTORY[p]['secretType'],'value':{'representation':'PROFILE_JSON_V1','profileId':p,'profile':fixtures[p]}}
 candidate=candidate_from_http(json.dumps(body,ensure_ascii=True,indent=2).encode());key=os.urandom(32)
 metadata={'ownerId':'11111111-1111-4111-8111-111111111111','secretId':'22222222-2222-4222-8222-222222222222','secretVersionId':'33333333-3333-4333-8333-333333333333','secretType':candidate['type'],'representation':candidate['representation'],'profileId':p,'schemaId':SCHEMA['$id']+'#/$defs/'+p,'schemaDigest':schema_digest(p),'plaintextByteLength':len(candidate['bytes']),'originalImportBytesDigest':digest(candidate['bytes']),'canonicalValueDigest':canonical_value_digest(candidate),'trustedContextId':'44444444-4444-4444-8444-444444444444','logicalOperationId':'55555555-5555-4555-8555-555555555555'}
 envelope=crypto.seal(candidate['bytes'],key,'SYNTHETIC_EPHEMERAL',metadata,purpose='SECRET_IMMUTABLE_VERSION')
 def open_(env=envelope,k=key,m=metadata,p=p,expected=candidate['bytes']):
  with crypto.open_snapshot(env,k,'SYNTHETIC_EPHEMERAL',m,lambda raw:parse_profile(p,raw),purpose='SECRET_IMMUTABLE_VERSION')as plaintext:
   assert bytes(plaintext)==expected
  # Shared helper zeros its yielded mutable view after context exit.
  assert bytes(plaintext)==b'\0'*len(expected)
  return True
 yes(p+'/exact-shared-profile-seal-open-parser-and-view-lifetime',open_)
 wrong=dict(metadata);wrong['secretVersionId']='66666666-6666-4666-8666-666666666666'
 no(p+'/wrong-immutable-version-authentication',lambda wrong=wrong:open_(m=wrong),'PROTECTED_INPUT_AUTHENTICATION_FAILED')
 no(p+'/wrong-key-authentication',lambda:open_(k=os.urandom(32)),'PROTECTED_INPUT_AUTHENTICATION_FAILED')
 corrupt=dict(envelope);corrupt['ciphertext']=envelope['ciphertext'][:-1]+bytes([envelope['ciphertext'][-1]^1])
 no(p+'/ciphertext-corruption-authentication',lambda corrupt=corrupt:open_(env=corrupt),'PROTECTED_INPUT_AUTHENTICATION_FAILED')
report={'input':json.loads((D/'input-source.json').read_text()),'checked':len(checks),'failed':sum(not x['passed']for x in checks),'checks':checks,'supportSha256':{str(p.relative_to(D.parent)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [crypto_path,D/'verify_crypto_handoff.py',D/'profile_reference.py',D/'secret_import_adapter.py',D/'secret-profile-handoffs.schema.json',D/'synthetic_profile_fixtures.py']},'sensitiveValuesInReport':False,'actualCryptoPrimitive':True,'profile':crypto.CRYPTO_PROFILE,'canonicalSystemdKeyProvisioning':'NOT_EVALUATED','excluded':['Authentic systemd credentials producer','Application broker authorization/physical DB transaction','Guaranteed erasure of Python immutable parser copies']}
(D/'crypto-handoff-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':report['checked'],'failed':report['failed']}));raise SystemExit(bool(report['failed']))
