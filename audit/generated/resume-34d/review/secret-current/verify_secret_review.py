from pathlib import Path
import sys,copy,json,hashlib
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'audit/generated/resume-34d/secrets-browser'))
from ssot_sources import SSOT,resource_index
from secret_profile_import import *
from secret_profile_reference import SCHEMA,INVENTORY,original_profile_slice,canonical_value_digest
from synthetic_profile_fixtures import fixtures
from create_operation_contracts import decode_http,admit,ContractFailure
from generation_auth_crypto import seal,open_snapshot
SOURCE=hashlib.sha256(SSOT.read_bytes()).hexdigest();OWNER='00000000-0000-4000-8000-000000000001';PROFILE='TOTP_BASE32_V1';HEADERS=[('Content-Type','application/json'),('Idempotency-Key','synthetic-independent-review-key')]
body={'stableName':'SYNTHETIC_REVIEW','displayName':'Synthetic','type':'TOTP_SEED','value':{'representation':'PROFILE_JSON_V1','profileId':PROFILE,'profile':copy.deepcopy(fixtures[PROFILE])}}
body['value']['profile']['periodSeconds']=30
raw=json.dumps(body,ensure_ascii=True,indent=2).encode()
def decode(raw,query=[]):return decode_http('secret.create','POST','/secrets',query,HEADERS,raw)
def registry(p):return {'secretType':INVENTORY[p]['secretType'],'profileId':p,'schemaId':SCHEMA['$id']+'#/$defs/'+p,'schemaDigest':schema_digest(p),'schemaBytes':compiled_schema_bytes(p),'status':'ACTIVE','normativeSourceDigest':'sha256:'+SOURCE,'reviewReceiptDigest':'sha256:'+'2'*64}
server={'owner':OWNER,'actor':'OWNER','authenticated':True,'recovery':'READY','stableNames':[],'secretProfileRegistryReader':registry,'secretProfileNormativeSourceDigest':'sha256:'+SOURCE,'secretProfileReviewReceiptDigest':'sha256:'+'2'*64}
checks=[]
def check(name,passed,**details):checks.append({'case':name,'passed':bool(passed),**details})
def negative(name,fn,expected):
 try:fn();check(name,False,actual='ACCEPTED',expected=expected)
 except Exception as e:
  required_pointer={'stored-schema-id-mismatch':'$.schemaId','stored-profile-type-mismatch-despite-matching-selectedtype':'$.type','RAW-nonnull-profile-binding':'$.profileId'}.get(name)
  actual_pointer=getattr(e,'pointer',None)
  check(name,getattr(e,'code',None)==expected and(required_pointer is None or actual_pointer==required_pointer),actual=getattr(e,'code',type(e).__name__),expected=expected,actualPointer=actual_pointer,expectedPointer=required_pointer)
native=decode(raw);check('native-domain-positive',admit(native,server)['action']=='RESERVE_ATOMIC_CREATE')
for field,value in [('type',None),('type','PRIVATE_KEY')]:
 mutant=copy.deepcopy(body);mutant[field]=value;negative('top-level-'+str(value),lambda m=mutant:decode(json.dumps(m).encode()),'SCHEMA_TYPE'if value is None else'SCHEMA_CONST')
mutant=copy.deepcopy(body);mutant['value']['profile']['variant']='OAUTH_CLIENT_SECRET_V1';negative('profile-discriminator-mismatch',lambda:decode(json.dumps(mutant).encode()),'SCHEMA_ONEOF')
negative('unknown-query',lambda:decode(raw,[('unexpected','value')]),'UNKNOWN_QUERY_PARAMETER')
negative('wrong-review-authority',lambda:admit(native,{**server,'secretProfileReviewReceiptDigest':'sha256:'+'3'*64}),'SECRET_PROFILE_REGISTRY_AUTHORITY_UNRESOLVED')
def wrong_schema(p):return {**registry(p),'schemaBytes':registry(p)['schemaBytes']+b' '}
negative('actual-registry-schema-bytes-wrong-despite-valid-id',lambda:admit(native,{**server,'secretProfileRegistryReader':wrong_schema}),'SECRET_PROFILE_REGISTRY_SCHEMA_MISMATCH')
negative('boolean-registry-not-authority',lambda:admit(native,{**server,'secretProfileRegistryReader':True}),'SECRET_PROFILE_REGISTRY_UNAVAILABLE')
negative('duplicate-real-json-profile-key',lambda:decode(raw.replace(b'"periodSeconds":',b'"periodSeconds":99,"periodSeconds":',1)),'DUPLICATE_JSON_KEY')
variant=raw.replace(b'"periodSeconds": 30',b'"periodSeconds": 30.0');a=decode(raw);b=decode(variant)
check('equivalent-integer-same-typed-value-digest',canonical_value_digest(a['secretImportCandidate'])==canonical_value_digest(b['secretImportCandidate']))
check('lexically-distinct-original-span-retained',a['secretImportCandidate']['bytes']!=b['secretImportCandidate']['bytes'] and a['secretImportCandidate']['bytes']==original_profile_slice(raw)and b['secretImportCandidate']['bytes']==original_profile_slice(variant))
check('exact-sensitive-original-bytes-bound-into-request-digest',a['requestDigest']!=b['requestDigest'])
# Synthetic canonical primitive opening: no actual systemd/OWNER/DB bridge claim.
import secrets
candidate=a['secretImportCandidate'];key=secrets.token_bytes(32)
metadata={'ownerId':OWNER,'secretId':OWNER,'secretVersionId':'00000000-0000-4000-8000-000000000002','secretType':candidate['type'],'representation':candidate['representation'],'profileId':PROFILE,'schemaId':SCHEMA['$id']+'#/$defs/'+PROFILE,'schemaDigest':schema_digest(PROFILE),'plaintextByteLength':len(candidate['bytes']),'originalImportBytesDigest':'sha256:'+hashlib.sha256(candidate['bytes']).hexdigest(),'canonicalValueDigest':canonical_value_digest(candidate),'trustedContextId':OWNER,'logicalOperationId':OWNER}
envelope=seal(candidate['bytes'],key,'synthetic-independent-key',metadata,'SECRET_IMMUTABLE_VERSION')
with open_snapshot(envelope,key,'synthetic-independent-key',metadata,lambda value:parse_profile(PROFILE,value),'SECRET_IMMUTABLE_VERSION')as view:check('actual-shared-canonical-opening-byte-preserving',bytes(view)==candidate['bytes'])
wrong={**metadata,'secretVersionId':'00000000-0000-4000-8000-000000000003'}
try:
 with open_snapshot(envelope,key,'synthetic-independent-key',wrong,lambda value:parse_profile(PROFILE,value),'SECRET_IMMUTABLE_VERSION'):check('other-immutable-version-denied',False)
except ValueError as e:check('other-immutable-version-denied',str(e)=='PROTECTED_INPUT_AUTHENTICATION_FAILED')
from synthetic_profile_fixtures import consumer
from datetime import datetime,timezone
use_metadata={'secretId':OWNER,'versionId':'00000000-0000-4000-8000-000000000002','type':'TOTP_SEED','representation':'PROFILE_JSON_V1','profileId':PROFILE,'schemaId':SCHEMA['$id']+'#/$defs/'+PROFILE,'schemaDigest':schema_digest(PROFILE),'plaintextByteLength':len(candidate['bytes']),'valueDigest':'sha256:'+hashlib.sha256(candidate['bytes']).hexdigest(),'canonicalValueDigest':canonical_value_digest(candidate),'payloadFormat':'EXACT_SECRET_BYTES_V1'}
expected_version={k:use_metadata[k]for k in ['secretId','versionId','type']};declaration=consumer(PROFILE)
for row in declaration['profiles']:row['schemaDigest']=schema_digest(row['profileId'])
check('actual-current-profile-use-domain-positive',load_use_profile(candidate['bytes'],use_metadata,expected_version,declaration,datetime(2026,9,30,tzinfo=timezone.utc))['status']=='REFERENCE_PREFLIGHT_PASSED')
def mismatch_use(metadata,selected):return load_use_profile(candidate['bytes'],metadata,selected,declaration,datetime(2026,9,30,tzinfo=timezone.utc))
negative('stored-schema-id-mismatch',lambda:mismatch_use({**use_metadata,'schemaId':'urn:kcml:wrong'},expected_version),'SECRET_PROFILE_SCHEMA_INVALID')
negative('stored-profile-type-mismatch-despite-matching-selectedtype',lambda:mismatch_use({**use_metadata,'type':'PRIVATE_KEY'},{**expected_version,'type':'PRIVATE_KEY'}),'SECRET_PROFILE_SCHEMA_INVALID')
# Preflight reports no secret material; explicit legacy RAW consumer, noformatguess.
legacy=b'  SYNTHETIC_LEGACY_RAW {"opaque":"not parsed"}\n'
raw_candidate={'type':'TOTP_SEED','representation':'RAW_UTF8','profileId':None,'bytes':legacy}
raw_metadata={**use_metadata,'representation':'RAW_UTF8','profileId':None,'schemaId':None,'schemaDigest':None,'plaintextByteLength':len(legacy),'valueDigest':'sha256:'+hashlib.sha256(legacy).hexdigest(),'canonicalValueDigest':canonical_value_digest(raw_candidate)}
raw_consumer={'consumerId':'SYNTHETIC_LEGACY','consumerRevision':'1','purposeKind':'SYNTHETIC_RAW_USE','rawTypes':['TOTP_SEED']}
check('legacy-immutable-complex-RAW-no-formatguess-positive',load_use_profile(legacy,raw_metadata,expected_version,raw_consumer,datetime(2026,9,30,tzinfo=timezone.utc))['status']=='RAW_REFERENCE_PREFLIGHT_PASSED')
negative('RAW-nonnull-profile-binding',lambda:load_use_profile(legacy,{**raw_metadata,'profileId':PROFILE},expected_version,raw_consumer,datetime(2026,9,30,tzinfo=timezone.utc)),'SECRET_PROFILE_SCHEMA_INVALID')
negative('RAW-wrong-byte-content-not-normalized',lambda:load_use_profile(legacy.strip(),raw_metadata,expected_version,raw_consumer,datetime(2026,9,30,tzinfo=timezone.utc)),'SECRET_STORED_BYTES_MISMATCH')
negative('profile-typed-canonical-digest-mismatch',lambda:mismatch_use({**use_metadata,'canonicalValueDigest':'sha256:'+'0'*64},expected_version),'SECRET_STORED_CANONICAL_DIGEST_MISMATCH')
report={'sourceDocumentSha256':SOURCE,'checked':len(checks),'failed':sum(not x['passed']for x in checks),'checks':checks,'status':'PASS'if all(x['passed']for x in checks)else'BLOCKED','scope':'Independent rootnativeHTTP-profile positive withspecificderivedviolations, exactorigspan/typedcanonical numeric relation andsyntheticcanonicalprimitive immutableversion binding. Registry/authcontext synthetic, notactualSecretacceptance/protectedDB/systemd proof.','wholeSecretOperationClosed':False,'sensitiveFixtureValuesInReport':False,'rootImplementationDigests':{n:hashlib.sha256((ROOT/'scripts'/n).read_bytes()).hexdigest()for n in ['secret_profile_parsers.py','secret_profile_reference.py','secret_profile_import.py','secret_profile_diagnostics.py','create_operation_contracts.py','generation_auth_crypto.py']},'sourceResourceSha256':{p:resource_index()[p]['sha256']for p in ['contracts/secrets/import.schema.json','contracts/secrets/profile-handoffs.schema.json','database/secret-profile-roots.sql']}}
assert SOURCE==hashlib.sha256(SSOT.read_bytes()).hexdigest(),'SOURCE_CHANGED'
(Path(__file__).parent/'secret-native-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':len(checks),'failed':report['failed'],'status':report['status']}))
