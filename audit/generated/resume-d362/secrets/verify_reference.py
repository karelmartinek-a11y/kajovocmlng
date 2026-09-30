"""Synthetic semantic evidence, values never appear in the report."""
import base64,copy,hashlib,importlib.metadata,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from profile_reference import *
checks=[]
def positive(name,fn):
 try:
  result=fn()
  if result is False:raise AssertionError('POSITIVE_PREDICATE_FALSE')
  checks.append({'id':name,'passed':True})
 except Exception as e:checks.append({'id':name,'passed':False,'code':getattr(e,'code',None),'pointer':getattr(e,'pointer',None),'unexpectedException':type(e).__name__})
def negative(name,fn,code,pointer=None):
 try:fn();checks.append({'id':name,'passed':False,'actual':'ACCEPTED','expectedCode':code})
 except Rejected as e:checks.append({'id':name,'passed':e.code==code and(pointer is None or e.pointer==pointer),'actualCode':e.code,'expectedCode':code,'pointer':e.pointer})
 except Exception as e:checks.append({'id':name,'passed':False,'unexpectedException':type(e).__name__})
p=json.loads(subprocess.check_output(['git','show',PIN+':audit/generated/create-review-authority/secret-variant-proposals.json']))
fixtures={}
for c in p['contracts']:
 for s in c['schema']['oneOf']:
  profile=s['properties']['variant']['const'];fixtures[profile]=next(copy.deepcopy(v['value'])for v in c['syntheticCases']if v['expected']=='SCHEMA_ACCEPT'and v['value']['variant']==profile)
floatv=lambda v:{'encoding':'IEEE754_BINARY64_BIG_ENDIAN_BASE64','base64':base64.b64encode(struct.pack('>d',v)).decode()}
key=serialization.load_pem_private_key(fixtures['PKCS8_PEM_PRIVATE_KEY_V1']['pem'].encode(),None)
der=base64.b64encode(key.private_bytes(serialization.Encoding.DER,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())).decode()
graph={'serializer':'ECMASCRIPT_AUTH_CLONE_GRAPH_V1','rootNodeId':'obj','nodes':[{'id':'obj','kind':'OBJECT','entries':[{'name':'self','valueNodeId':'obj'},{'name':'token','valueNodeId':'text'},{'name':'bytes','valueNodeId':'buf'}]},{'id':'text','kind':'STRING','value':' SYNTHETIC \u00e9\n'},{'id':'buf','kind':'ARRAY_BUFFER','base64':'AAEC/w=='}]}
full={'variant':'BROWSER_AUTH_STATE_GRAPH_V1','cookies':[{'name':'synthetic','value':' Exact +% \n','domain':'example.invalid','hostOnly':True,'path':'/','secure':True,'httpOnly':True,'sameSite':'None','expiry':{'kind':'ABSOLUTE','unixSeconds':floatv(1900000000.125)},'partition':{'kind':'TOP_LEVEL_SITE','topLevelSite':'https://top.example.invalid','hasCrossSiteAncestor':True}}],'origins':[{'origin':'https://example.invalid','localStorage':[{'name':'exact','value':' v\n'}],'indexedDB':[{'name':'auth','version':1,'objectStores':[{'name':'tokens','keyPath':None,'autoIncrement':False,'nextGeneratedKey':None,'indexes':[],'records':[{'key':{'kind':'STRING','value':'key'},'value':graph}]}]}]}],'pages':[{'pageKey':'login','origin':'https://example.invalid','sessionStorage':[{'name':'session','value':' exact '}]}],'permissions':[{'origin':'https://example.invalid','permission':'geolocation','state':'granted'}],'clientCertificateBindings':[{'kind':'OWNER_DEVICE_BRIDGE','origin':'https://example.invalid','bridgeBindingId':'b832b1c4-a1d7-4cc2-af57-c9a848cf733a','bridgeBindingRevision':'1'}],'virtualAuthenticators':[{'authenticatorKey':'automation','protocol':'ctap2','transport':'usb','hasResidentKey':True,'hasUserVerification':True,'automaticPresenceSimulation':True,'isUserVerified':True,'credentials':[{'kind':'VIRTUAL_AUTOMATION_ACCOUNT','credentialIdBase64':'AQID','rpId':'example.invalid','userHandleBase64':'AQ==','privateKeyPkcs8DerBase64':der,'signCount':0,'isResidentCredential':True,'backupEligible':False,'backupState':False}]}]}
fixtures[full['variant']]=full
now=datetime(2026,9,30,tzinfo=timezone.utc)
def consumer(profile):
 return {'consumerId':'SYNTHETIC_ADAPTER','consumerRevision':'1','purposeKind':'REFERENCE_TEST','profiles':[{'secretType':INVENTORY[profile]['secretType'],'profileId':profile,'schemaDigest':schema_digest(profile)}],'allowedOrigins':['https://example.invalid'],'cookieHosts':['example.invalid'],'tokenEndpoint':'https://oauth.example.invalid/token','database':'syntheticdb','keyAlgorithms':['RSA','EC','ED25519','ED448'],'browserMembers':['COOKIES','PARTITIONED_COOKIES','LOCAL_STORAGE','INDEXED_DB','SESSION_STORAGE','PERMISSIONS','CLIENT_CERTIFICATE_BINDINGS','VIRTUAL_WEBAUTHN'],'serializerIds':['ECMASCRIPT_AUTH_CLONE_GRAPH_V1','BROWSER_AUTH_STATE_GRAPH_V1','BROWSER_COOKIE_LOCAL_STORAGE_V1','HTTP_COOKIE_JAR_V1'],'engineBuild':'SYNTHETIC_REFERENCE_ONLY','keyAlgorithmPolicies':[{'algorithm':'RSA','minimumModulusBits':1024,'publicExponents':[65537]},{'algorithm':'EC','namedCurves':['secp256r1','secp384r1','secp521r1']},{'algorithm':'ED25519'},{'algorithm':'ED448'}],'totpPolicies':[{'algorithm':'SHA1','digits':6,'minimumSeedBytes':1,'minimumPeriodSeconds':1,'maximumPeriodSeconds':1000},{'algorithm':'SHA256','digits':8,'minimumSeedBytes':1,'minimumPeriodSeconds':1,'maximumPeriodSeconds':1000}],'oauthClientId':fixtures['OAUTH_CLIENT_SECRET_V1']['clientId'],'authorizedOAuthScopes':list(set(fixtures['OAUTH_CLIENT_SECRET_V1'].get('scopes',[])+fixtures['OAUTH_BEARER_TOKEN_SET_V1'].get('scopes',[])))}
for profile,value in fixtures.items():
 raw=(' \n'+json.dumps(value,ensure_ascii=True,indent=1)+' \t').encode()
 positive(profile+'/real-parser',lambda profile=profile,raw=raw:parse_profile(profile,raw))
 # Use tests start from an import-accepted positive and exact consumer mask.
 c=consumer(profile)
 if 'database'in value:c['database']=value['database']
 if 'tokenEndpoint'in value:c['tokenEndpoint']=value['tokenEndpoint']
 positive(profile+'/declared-consumer',lambda profile=profile,raw=raw,c=c:use_profile(profile,raw,c,now))
 wrong=copy.deepcopy(c);wrong['profiles']=[]
 negative(profile+'/unsupported-consumer',lambda profile=profile,raw=raw,wrong=wrong:use_profile(profile,raw,wrong,now),'SECRET_VARIANT_UNSUPPORTED','/consumer/profiles')
 extra=copy.deepcopy(value);extra['serverAuthority']='not-trusted'
 negative(profile+'/extra-field',lambda profile=profile,extra=extra:parse_profile(profile,json.dumps(extra).encode()),'SECRET_PROFILE_SCHEMA_INVALID')
 missing=copy.deepcopy(value);del missing['variant']
 negative(profile+'/required-field',lambda profile=profile,missing=missing:parse_profile(profile,json.dumps(missing).encode()),'SECRET_PROFILE_SCHEMA_INVALID')
 body={'stableName':'SYNTHETIC_'+profile,'displayName':'Synthetic fixture','type':INVENTORY[profile]['secretType'],'value':{'representation':'PROFILE_JSON_V1','profileId':profile,'profile':value}}
 # Sensitive profile span contains formatting and escaped code points; store
 # retains that exact span, rather than normalizing/reencoding parsed values.
 bodyraw=(' \n'+json.dumps(body,ensure_ascii=True,indent=2)+' \t').encode()
 def roundtrip(profile=profile,bodyraw=bodyraw):
  cand=import_body(bodyraw);expected=original_profile_slice(bodyraw);assert cand['bytes']==expected
  k=AESGCM.generate_key(bit_length=256);r=store_reference(cand,'aa4c859b-9bdc-4bf9-ab2c-543b3e61696f','27e7eed8-ef55-4a35-a2d2-bf6dad99adea',k);assert load_reference(r,k,'aa4c859b-9bdc-4bf9-ab2c-543b3e61696f','27e7eed8-ef55-4a35-a2d2-bf6dad99adea')==expected
  assert parse_profile(profile,load_reference(r,k,'aa4c859b-9bdc-4bf9-ab2c-543b3e61696f','27e7eed8-ef55-4a35-a2d2-bf6dad99adea'))==fixtures[profile]
 positive(profile+'/exact-import-store-load-bytes',roundtrip)
 def tamper(profile=profile,bodyraw=bodyraw):
  k=AESGCM.generate_key(bit_length=256);r=store_reference(import_body(bodyraw),'aa4c859b-9bdc-4bf9-ab2c-543b3e61696f','27e7eed8-ef55-4a35-a2d2-bf6dad99adea',k);r['metadata']['versionId']='forged';load_reference(r,k,'aa4c859b-9bdc-4bf9-ab2c-543b3e61696f','27e7eed8-ef55-4a35-a2d2-bf6dad99adea')
 negative(profile+'/stored-identity-tamper',tamper,'SECRET_STORED_REFERENCE_MISMATCH','/metadata')
 negative(profile+'/duplicate-import-key',lambda profile=profile,raw=raw:parse_profile(profile,raw.rstrip()[:-1]+b',"variant":"'+profile.encode()+b'"}'),'SECRET_IMPORT_DUPLICATE_JSON_KEY','/variant')
# Actual malformed current import JSON, not an obsolete field rejection.
negative('malformed-http-json',lambda:import_body(bodyraw.rstrip()[:-1]),'SECRET_IMPORT_JSON_INVALID','')
negative('nonfinite-http-json',lambda:import_body(bodyraw.rstrip()[:-1]+b',"extra":NaN}'),'SECRET_IMPORT_NONFINITE_NUMBER','/extra')
positive('unchanged-raw-password-whitespace',lambda:import_body(json.dumps({'stableName':'S','displayName':'D','type':'PASSWORD','value':{'encoding':'UTF8','text':' \u00e9\n'}}).encode())['bytes']==b' \xc3\xa9\n')
negative('complex-legacy-value-not-sniffed',lambda:import_body(json.dumps({'stableName':'S','displayName':'D','type':'OAUTH_CLIENT','value':{'encoding':'UTF8','text':json.dumps(fixtures['OAUTH_CLIENT_SECRET_V1'])}}).encode()),'SECRET_PROFILE_REQUIRED','/value')
token=copy.deepcopy(fixtures['OAUTH_BEARER_TOKEN_SET_V1']);token['expiresAt']='2020-01-01T00:00:00Z';raw=json.dumps(token).encode()
positive('expired-token-import-is-candidate',lambda:parse_profile(token['variant'],raw))
negative('expired-token-use-is-rejected',lambda:use_profile(token['variant'],raw,consumer(token['variant']),now),'OAUTH_TOKEN_EXPIRED','/expiresAt')
v=fixtures['OAUTH_CLIENT_SECRET_V1'];c=consumer(v['variant']);c['tokenEndpoint']=v['tokenEndpoint']+'?different=1'
negative('endpoint-full-binding-not-host-only',lambda:use_profile(v['variant'],json.dumps(v).encode(),c,now),'OAUTH_TOKEN_ENDPOINT_BINDING_MISMATCH','/tokenEndpoint')
f=copy.deepcopy(full);f['origins'][0]['indexedDB'][0]['objectStores'][0]['records'][0]['value']['nodes'][0]['entries'][0]['valueNodeId']='missing'
negative('actual-IDB-graph-reference',lambda:parse_profile(f['variant'],json.dumps(f).encode()),'BROWSER_STATE_GRAPH_REFERENCE_INVALID')
f=copy.deepcopy(full);f['cookies'][0]['partition']['hasCrossSiteAncestor']=None
negative('partition-exact-type',lambda:parse_profile(f['variant'],json.dumps(f).encode()),'SECRET_PROFILE_SCHEMA_INVALID')
f=copy.deepcopy(full);f['virtualAuthenticators'][0]['credentials'][0]['backupState']=True
negative('virtual-WebAuthn-backup-relation',lambda:parse_profile(f['variant'],json.dumps(f).encode()),'BROWSER_VIRTUAL_CREDENTIAL_BACKUP_INVALID')
c=consumer(full['variant']);c['browserMembers'].remove('INDEXED_DB')
negative('mandatory-member-no-silent-fallback',lambda:use_profile(full['variant'],json.dumps(full).encode(),c,now),'BROWSER_STATE_MEMBER_UNSUPPORTED','/consumer/browserMembers')
c=consumer(full['variant']);c['serializerIds'].remove('ECMASCRIPT_AUTH_CLONE_GRAPH_V1')
negative('missing-IDB-serializer-rejected',lambda:use_profile(full['variant'],json.dumps(full).encode(),c,now),'BROWSER_STATE_SERIALIZER_UNSUPPORTED','/consumer/serializerIds')
negative('account-boolean-not-proof',lambda:use_profile(full['variant'],json.dumps(full).encode(),consumer(full['variant']),now,True),'BROWSER_STATE_AUTH_POSTCONDITION_FAILED','/consumer/account')
# Semantic account mismatch from concrete adapter marker fields, no validity flag.
negative('account-identity-mismatch',lambda:use_profile(full['variant'],json.dumps(full).encode(),consumer(full['variant']),now,{'expectedAccount':'synthetic-A','expectedTenant':'T','observedAccount':'synthetic-B','observedTenant':'T'}),'BROWSER_STATE_AUTH_POSTCONDITION_FAILED','/consumer/account')
# Additional exact semantic mutants always retain the corresponding valid base.
f=copy.deepcopy(full);f['origins'][0]['indexedDB'][0]['objectStores'][0]['records'][0]['value']['nodes'].append(copy.deepcopy(f['origins'][0]['indexedDB'][0]['objectStores'][0]['records'][0]['value']['nodes'][0]))
negative('duplicate-clone-node-identity',lambda:parse_profile(f['variant'],json.dumps(f).encode()),'BROWSER_STATE_DUPLICATE_NODE')
f=copy.deepcopy(full);f['origins'][0]['indexedDB'][0]['objectStores'][0]['records'][0]['value']['nodes'].append({'id':'view','kind':'TYPED_ARRAY','elementType':'Uint32Array','bufferNodeId':'buf','byteOffset':0,'byteLength':8})
negative('typed-array-buffer-range',lambda:parse_profile(f['variant'],json.dumps(f).encode()),'BROWSER_STATE_TYPED_ARRAY_RANGE_INVALID')
f=copy.deepcopy(full);f['origins'][0]['indexedDB'][0]['objectStores'][0]['records'][0]['value']['nodes'].append({'id':'rx','kind':'REGEXP','source':'a','flags':'uv'})
negative('regexp-u-v-conflict',lambda:parse_profile(f['variant'],json.dumps(f).encode()),'BROWSER_STATE_REGEXP_FLAGS_INVALID')
c=consumer('OAUTH_CLIENT_SECRET_V1');c['profiles'][0]['secretType']='PRIVATE_KEY'
negative('incompatible-type-profile-consumer-pair',lambda:use_profile('OAUTH_CLIENT_SECRET_V1',json.dumps(fixtures['OAUTH_CLIENT_SECRET_V1']).encode(),c,now),'SECRET_PROFILE_SCHEMA_INVALID')
# Whole endpoint equality already tested; target host or same origin alone is insufficient.
basebody={'stableName':'FIXTURE','displayName':'Fixture','type':'DATABASE_CREDENTIAL','value':{'representation':'PROFILE_JSON_V1','profileId':'DATABASE_USER_PASSWORD_V1','profile':fixtures['DATABASE_USER_PASSWORD_V1']}}
def tamper_cipher():
 k=AESGCM.generate_key(bit_length=256);r=store_reference(import_body(json.dumps(basebody).encode()),'aa4c859b-9bdc-4bf9-ab2c-543b3e61696f','27e7eed8-ef55-4a35-a2d2-bf6dad99adea',k)
 r['ciphertext']=bytes([r['ciphertext'][0]^1])+r['ciphertext'][1:];load_reference(r,k,'aa4c859b-9bdc-4bf9-ab2c-543b3e61696f','27e7eed8-ef55-4a35-a2d2-bf6dad99adea')
negative('actual-AEAD-authentication-tamper',tamper_cipher,'SECRET_STORED_AUTHENTICATION_FAILED','/ciphertext')
# No unjustified username/item-count limit remains in the approved limited mask.
v=copy.deepcopy(fixtures['DATABASE_USER_PASSWORD_V1']);v['username']='S'*5000
positive('no-unjustified-4096-username-limit',lambda:parse_profile(v['variant'],json.dumps(v).encode()))
v=copy.deepcopy(fixtures['TOTP_BASE32_V1']);v['seedBase32']='MY';v['periodSeconds']=301
positive('seed-and-period-no-invented-global-policy',lambda:parse_profile(v['variant'],json.dumps(v).encode()))
# Independent reviewer mutants: Map/Set deduplication would be lossy and must
# reject prior to hydration, including SameValueZero primitive equivalence.
for kind,code in [('MAP','BROWSER_STATE_DUPLICATE_MAP_KEY'),('SET','BROWSER_STATE_DUPLICATE_SET_VALUE')]:
 f=copy.deepcopy(full);g=f['origins'][0]['indexedDB'][0]['objectStores'][0]['records'][0]['value']
 g['nodes'].append({'id':'second-text','kind':'STRING','value':g['nodes'][1]['value']})
 g['nodes'].append({'id':'collection','kind':kind,**({'entries':[{'keyNodeId':'text','valueNodeId':'obj'},{'keyNodeId':'second-text','valueNodeId':'buf'}]}if kind=='MAP'else{'items':[{'nodeId':'text'},{'nodeId':'second-text'}]})})
 negative('reviewer-'+kind+'-SameValueZero-primitive-duplicate',lambda f=f:parse_profile(f['variant'],json.dumps(f).encode()),code)
for label,a,b in [('signed-zero',-0.0,0.0),('NaN',float('nan'),float('nan'))]:
 f=copy.deepcopy(full);g=f['origins'][0]['indexedDB'][0]['objectStores'][0]['records'][0]['value']
 g['nodes'] += [{'id':'a','kind':'NUMBER','value':floatv(a)},{'id':'b','kind':'NUMBER','value':floatv(b)},{'id':'set','kind':'SET','items':[{'nodeId':'a'},{'nodeId':'b'}]}]
 negative('SameValueZero-'+label,lambda f=f:parse_profile(f['variant'],json.dumps(f).encode()),'BROWSER_STATE_DUPLICATE_SET_VALUE')
negative('unknown-use-profile-structured-error',lambda:use_profile('UNSUPPORTED_PROFILE',json.dumps(full).encode(),consumer(full['variant']),now),'SECRET_VARIANT_UNSUPPORTED','/value/profileId')
def swap_valid_record():
 k=AESGCM.generate_key(bit_length=256);r=store_reference(import_body(json.dumps(basebody).encode()),'aa4c859b-9bdc-4bf9-ab2c-543b3e61696f','11111111-1111-4111-8111-111111111111',k)
 # Authentic ciphertext and internally consistent metadata belong to another
 # immutable version. This is reference substitution, not AEAD corruption.
 load_reference(r,k,'aa4c859b-9bdc-4bf9-ab2c-543b3e61696f','27e7eed8-ef55-4a35-a2d2-bf6dad99adea')
negative('valid-AEAD-other-version-substitution',swap_valid_record,'SECRET_STORED_REFERENCE_MISMATCH','/metadata')
# Keep sensitive runtime fixtures off disk; only schema and identifier outcomes persist.
report={'inputCommit':PIN,'sourceSha256':SCHEMA['x-sourceSha256'],'currentWorkingRepairInput':json.loads((D/'active-join-repair-source.json').read_text()),'schemaSha256':hashlib.sha256((D/'secret-profile-handoffs.schema.json').read_bytes()).hexdigest(),'supportSha256':{n:hashlib.sha256((D/n).read_bytes()).hexdigest()for n in ['profile_reference.py','verify_reference.py']},'dependencies':{n:importlib.metadata.version(n)for n in ['cryptography','jsonschema']},'checked':len(checks),'failed':sum(not x['passed']for x in checks),'checks':checks,'sensitiveValuesInReport':False,'status':'REFERENCE_VERIFIED_BOUNDED_MASK_PARSER_STORAGE','activation':'NOT_ACTIVATED','runtimeAcceptance':'NOT_EVALUATED','excluded':['Real canonical systemd master key and production crypto implementation','Actual broker/context/database authorization','Actual TLS/OAuth/DB/SSH authentication','Full browser engine capture/restore implementation','IndexedDB keyPath/index/uniqueness postconditions','Client-certificate bridge and WebAuthn attestation/signature assertions']}
(D/'reference-tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checked':report['checked'],'failed':report['failed']}))
for check in checks:
 if not check['passed']:print(json.dumps(check))
raise SystemExit(bool(report['failed']))
