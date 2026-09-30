"""Exact current-source HTTP import/read/use boundary tests, synthetic only."""
import copy,hashlib,json,runpy
from pathlib import Path
from secret_import_adapter import *
from profile_reference import store_reference,load_reference
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
D=Path(__file__).resolve().parent
from synthetic_profile_fixtures import fixtures
checks=[]
def yes(id_,fn):
 try:checks.append({'id':id_,'passed':fn()is not False})
 except Exception as e:checks.append({'id':id_,'passed':False,'code':getattr(e,'code',None),'unexpectedException':type(e).__name__})
def no(id_,fn,code):
 try:fn();checks.append({'id':id_,'passed':False,'actual':'ACCEPTED','expected':code})
 except Rejected as e:checks.append({'id':id_,'passed':e.code==code,'actualCode':e.code,'expectedCode':code})
 except Exception as e:checks.append({'id':id_,'passed':False,'unexpectedException':type(e).__name__})
def body(p):return {'stableName':'SYNTHETIC','displayName':'Synthetic','type':INVENTORY[p]['secretType'],'value':{'representation':'PROFILE_JSON_V1','profileId':p,'profile':fixtures[p]}}
def registry(p):return {'secretType':INVENTORY[p]['secretType'],'profileId':p,'schemaId':SCHEMA['$id']+'#/$defs/'+p,'schemaDigest':schema_digest(p),'schemaBytes':compiled_schema_bytes(p),'status':'ACTIVE','normativeSourceDigest':'sha256:'+'1'*64,'reviewReceiptDigest':'sha256:'+'2'*64}
for p in APPROVED_PROFILES:
 raw=json.dumps(body(p),ensure_ascii=True,indent=2).encode()
 yes(p+'/active-mask-byte-preserving-import',lambda p=p,raw=raw:candidate_from_http(raw)['bytes']==original_profile_slice(raw))
 yes(p+'/pinned-schema-registry-reader',lambda p=p:registry_profile(p,registry,'sha256:'+'1'*64,'sha256:'+'2'*64)['schemaBytes']==compiled_schema_bytes(p))
 nullbody=copy.deepcopy(body(p));nullbody['value']['profile']['variant']=None
 no(p+'/null-discriminator',lambda nullbody=nullbody:candidate_from_http(json.dumps(nullbody).encode()),'SECRET_PROFILE_SCHEMA_INVALID')
 wrongtype=copy.deepcopy(body(p));wrongtype['type']='PASSWORD'
 no(p+'/incompatible-secret-type',lambda wrongtype=wrongtype:candidate_from_http(json.dumps(wrongtype).encode()),'SECRET_PROFILE_SCHEMA_INVALID')
 wrong=registry(p);wrong['schemaBytes']=wrong['schemaBytes']+b' '
 no(p+'/schema-bytes-not-only-declared-digest',lambda p=p,wrong=wrong:registry_profile(p,lambda _:wrong,'sha256:'+'1'*64,'sha256:'+'2'*64),'SECRET_PROFILE_REGISTRY_SCHEMA_MISMATCH')
 bad=registry(p);bad['status']='CANDIDATE'
 no(p+'/candidate-registry-not-active',lambda p=p,bad=bad:registry_profile(p,lambda _:bad,'sha256:'+'1'*64,'sha256:'+'2'*64),'SECRET_PROFILE_NOT_ACTIVE')
 rawduplicate=raw.rstrip()[:-1]+b',"value":'+json.dumps(body(p)['value']).encode()+b'}'
 no(p+'/actual-http-duplicate-json-key',lambda rawduplicate=rawduplicate:candidate_from_http(rawduplicate),'SECRET_IMPORT_DUPLICATE_JSON_KEY')
no('mandatory-full-browser-profile-not-silent-limited-substitute',lambda:candidate_from_http(json.dumps(body('BROWSER_AUTH_STATE_GRAPH_V1')).encode()),'SECRET_PROFILE_SCHEMA_INVALID')
no('registry-absent-not-authorized-flag',lambda:registry_profile(APPROVED_PROFILES[0],True,'sha256:'+'1'*64,'sha256:'+'2'*64),'SECRET_PROFILE_REGISTRY_UNAVAILABLE')
p='TOTP_BASE32_V1';b=body(p);raw=json.dumps(b).encode();other=raw.replace(b'"periodSeconds": 30',b'"periodSeconds": 30.0')
yes('exact-import-bytes-not-collapsed-in-idempotency-digest',lambda:request_digest(raw)!=request_digest(other))
yes('canonical-semantic-digest-integral-decimal-equality',lambda:canonical_value_digest(candidate_from_http(raw))==canonical_value_digest(candidate_from_http(other)))
legacy={'type':'OAUTH_CLIENT','representation':'RAW_UTF8','profileId':None,'bytes':b' EXACT LEGACY VALUE \n'}
k=AESGCM.generate_key(bit_length=256);stored=store_reference(legacy,'11111111-1111-4111-8111-111111111111','22222222-2222-4222-8222-222222222222',k);plain=load_reference(stored,k,'11111111-1111-4111-8111-111111111111','22222222-2222-4222-8222-222222222222')
yes('immutable-legacy-complex-RAW-load-no-profile-sniff',lambda:load_use_profile(plain,stored['metadata'],{'secretId':'11111111-1111-4111-8111-111111111111','versionId':'22222222-2222-4222-8222-222222222222','type':'OAUTH_CLIENT'},{'consumerId':'SYNTHETIC_RAW_ADAPTER','consumerRevision':'1','purposeKind':'REFERENCE_TEST','rawTypes':['OAUTH_CLIENT']},datetime.now(timezone.utc))['status']=='RAW_REFERENCE_PREFLIGHT_PASSED')
no('legacy-RAW-consumer-declaration-required',lambda:load_use_profile(plain,stored['metadata'],{'secretId':'11111111-1111-4111-8111-111111111111','versionId':'22222222-2222-4222-8222-222222222222','type':'OAUTH_CLIENT'},{'consumerId':'SYNTHETIC_RAW_ADAPTER','consumerRevision':'1','purposeKind':'REFERENCE_TEST','rawTypes':[]},datetime.now(timezone.utc)),'SECRET_RAW_CONSUMER_UNSUPPORTED')
no('edited-parent-type-not-historical-version-type',lambda:load_use_profile(plain,stored['metadata'],{'secretId':'11111111-1111-4111-8111-111111111111','versionId':'22222222-2222-4222-8222-222222222222','type':'API_KEY'},{'consumerId':'SYNTHETIC_RAW_ADAPTER','consumerRevision':'1','purposeKind':'REFERENCE_TEST','rawTypes':['API_KEY']},datetime.now(timezone.utc)),'SECRET_STORED_TYPE_MISMATCH')
def wrong_authority():return registry_profile(APPROVED_PROFILES[0],registry,'sha256:'+'3'*64,'sha256:'+'2'*64)
no('registry-current-normative-source-receipt-authority-mismatch',wrong_authority,'SECRET_PROFILE_REGISTRY_AUTHORITY_UNRESOLVED')
report={'input':json.loads((D/'input-source.json').read_text()),'checked':len(checks),'failed':sum(not x['passed']for x in checks),'checks':checks,'supportSha256':{n:hashlib.sha256((D/n).read_bytes()).hexdigest()for n in ['secret_import_adapter.py','secret_value_parsers.py','profile_reference.py','secret-profile-handoffs.schema.json','verify_import_adapter.py']},'sensitiveValuesInReport':False,'status':'BOUNDED_CURRENT_SOURCE_REFERENCE_VERIFIED','excluded':['Actual trusted registry review receipt authority and DB acceptance locks','Canonical encryption/systemd key authority','Whole secret.create transaction/event/error closure']}
(D/'import-adapter-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':report['checked'],'failed':report['failed']}))
for c in checks:
 if not c['passed']:print(json.dumps(c))
raise SystemExit(bool(report['failed']))
