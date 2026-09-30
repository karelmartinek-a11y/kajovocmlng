"""Authoring output only; does not modify the effective canonical SSOT."""
import copy,hashlib,json,subprocess
from pathlib import Path
D=Path(__file__).resolve().parent
ROOT=D.parents[3]
PIN='d362487999bd795d4723c2a930e93fc7aa8aa295'
p=json.loads(subprocess.check_output(['git','show',PIN+':audit/generated/create-review-authority/secret-variant-proposals.json']))
def obj(props,req=None):return {'type':'object','additionalProperties':False,'properties':props,'required':list(props) if req is None else req}
def arr(item):return {'type':'array','items':item}
def string(nonempty=False):return {'type':'string',**({'minLength':1} if nonempty else {})}
def const(x):return {'const':x}
def ref(n):return {'$ref':'#/$defs/'+n}
def uncap(v):
 if isinstance(v,dict):
  for key in ['maxLength','maxItems']:v.pop(key,None)
  for x in v.values():uncap(x)
 elif isinstance(v,list):
  for x in v:uncap(x)
variants=[];limits=[]
for c in p['contracts']:
 for s in c['schema']['oneOf']:
  s=copy.deepcopy(s);uncap(s)
  name=s['properties']['variant']['const']
  if name=='TOTP_BASE32_V1':
   s['properties']['seedBase32']['minLength']=1
   s['properties']['periodSeconds'].pop('maximum',None)
  variants.append({'secretType':c['secretType'],'profileId':name,'schema':s,'approval':'APPROVED_LIMITED_PROFILE_NAME','activation':'REQUIRES_NORMATIVE_INTEGRATION_AND_REVIEW','authority':c['authority']})
# Every browser member is explicitly typed. Values use a closed tagged graph,
# including cycles/shared references, never an arbitrary JSON object/string.
b64={'type':'string','pattern':r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$'}
uuid={'type':'string','format':'uuid'}
origin={'type':'string','format':'uri','pattern':'^https?://'}
entry=obj({'name':string(),'value':string()})
key=obj({'nodeId':string(True)})
node=lambda kind,props:obj({'id':string(True),'kind':const(kind),**props})
defs={
 'StorageEntry':entry,
 'ExactFloat64':obj({'encoding':const('IEEE754_BINARY64_BIG_ENDIAN_BASE64'),'base64':b64}),
 'IDBKey':{'oneOf':[
  obj({'kind':const('STRING'),'value':string()}),obj({'kind':const('NUMBER'),'value':ref('ExactFloat64')}),
  obj({'kind':const('DATE'),'epochMilliseconds':ref('ExactFloat64')}),obj({'kind':const('BINARY'),'base64':b64}),
  obj({'kind':const('ARRAY'),'items':arr(ref('IDBKey'))})]},
 'CloneNode':{'oneOf':[
  node('UNDEFINED',{}),node('NULL',{}),node('BOOLEAN',{'value':{'type':'boolean'}}),node('STRING',{'value':string()}),
  node('NUMBER',{'value':ref('ExactFloat64')}),node('BIGINT',{'decimal':{'type':'string','pattern':'^(?:0|-?[1-9][0-9]*)$'}}),
  node('DATE',{'epochMilliseconds':ref('ExactFloat64')}),node('ARRAY_BUFFER',{'base64':b64}),
  node('TYPED_ARRAY',{'elementType':{'enum':['Int8Array','Uint8Array','Uint8ClampedArray','Int16Array','Uint16Array','Int32Array','Uint32Array','BigInt64Array','BigUint64Array','Float32Array','Float64Array','DataView']},'bufferNodeId':string(True),'byteOffset':{'type':'integer','minimum':0},'byteLength':{'type':'integer','minimum':0}}),
  node('ARRAY',{'items':arr(key)}),node('OBJECT',{'entries':arr(obj({'name':string(),'valueNodeId':string(True)}))}),
  node('MAP',{'entries':arr(obj({'keyNodeId':string(True),'valueNodeId':string(True)}))}),node('SET',{'items':arr(key)}),
  node('REGEXP',{'source':string(),'flags':{'type':'string','pattern':'^(?:d?g?i?m?s?u?v?y?)$'}}),
  node('BLOB',{'mediaType':string(),'base64':b64}),
  node('FILE',{'name':string(),'mediaType':string(),'lastModifiedMilliseconds':ref('ExactFloat64'),'base64':b64})]},
 'CloneGraph':obj({'serializer':const('ECMASCRIPT_AUTH_CLONE_GRAPH_V1'),'rootNodeId':string(True),'nodes':arr(ref('CloneNode'))}),
 'IDBIndex':obj({'name':string(),'keyPath':{'oneOf':[string(),arr(string())]},'unique':{'type':'boolean'},'multiEntry':{'type':'boolean'}}),
 'IDBStore':obj({'name':string(),'keyPath':{'oneOf':[string(),arr(string()),{'type':'null'}]},'autoIncrement':{'type':'boolean'},'nextGeneratedKey':{'oneOf':[{'type':'integer','minimum':1,'maximum':9007199254740992},{'type':'null'}]},'indexes':arr(ref('IDBIndex')),'records':arr(obj({'key':ref('IDBKey'),'value':ref('CloneGraph')}))}),
 'IDBDatabase':obj({'name':string(),'version':{'type':'integer','minimum':1,'maximum':9007199254740991},'objectStores':arr(ref('IDBStore'))}),
 'Cookie':obj({'name':string(True),'value':string(),'domain':string(True),'hostOnly':{'type':'boolean'},'path':{'type':'string','pattern':'^/'},'secure':{'type':'boolean'},'httpOnly':{'type':'boolean'},'sameSite':{'enum':['Strict','Lax','None']},'expiry':{'oneOf':[obj({'kind':const('SESSION')}),obj({'kind':const('ABSOLUTE'),'unixSeconds':ref('ExactFloat64')})]},'partition':{'oneOf':[obj({'kind':const('UNPARTITIONED')}),obj({'kind':const('TOP_LEVEL_SITE'),'topLevelSite':origin,'hasCrossSiteAncestor':{'type':'boolean'}})]}}),
 'SecretVersionRef':obj({'secretId':uuid,'versionId':uuid}),
 'ClientCertificate':{'oneOf':[obj({'kind':const('SECRET_PAIR'),'origin':origin,'certificate':ref('SecretVersionRef'),'privateKey':ref('SecretVersionRef')}),obj({'kind':const('OWNER_DEVICE_BRIDGE'),'origin':origin,'bridgeBindingId':uuid,'bridgeBindingRevision':string(True)})]},
 'VirtualCredential':obj({'kind':const('VIRTUAL_AUTOMATION_ACCOUNT'),'credentialIdBase64':b64,'rpId':string(True),'userHandleBase64':b64,'privateKeyPkcs8DerBase64':b64,'signCount':{'type':'integer','minimum':0,'maximum':4294967295},'isResidentCredential':{'type':'boolean'},'backupEligible':{'type':'boolean'},'backupState':{'type':'boolean'}}),
 'VirtualAuthenticator':obj({'authenticatorKey':string(True),'protocol':{'enum':['ctap2','u2f']},'transport':{'enum':['usb','nfc','ble','internal']},'hasResidentKey':{'type':'boolean'},'hasUserVerification':{'type':'boolean'},'automaticPresenceSimulation':{'type':'boolean'},'isUserVerified':{'type':'boolean'},'credentials':arr(ref('VirtualCredential'))}),
 'FullBrowserProfile':obj({'variant':const('BROWSER_AUTH_STATE_GRAPH_V1'),'cookies':arr(ref('Cookie')),'origins':arr(obj({'origin':origin,'localStorage':arr(ref('StorageEntry')),'indexedDB':arr(ref('IDBDatabase'))})),'pages':arr(obj({'pageKey':string(True),'origin':origin,'sessionStorage':arr(ref('StorageEntry'))})),'permissions':arr(obj({'origin':origin,'permission':{'enum':['geolocation','midi','midi-sysex','notifications','camera','microphone','background-sync','accelerometer','gyroscope','magnetometer','clipboard-read','clipboard-write','payment-handler','persistent-storage','idle-detection','local-fonts','window-management']},'state':{'enum':['granted','denied','prompt']}})),'clientCertificateBindings':arr(ref('ClientCertificate')),'virtualAuthenticators':arr(ref('VirtualAuthenticator'))}),
}
variants.append({'secretType':'SESSION_STATE','profileId':'BROWSER_AUTH_STATE_GRAPH_V1','schema':ref('FullBrowserProfile'),'approval':'TECHNICAL_PROFILE_AUTHORIZED_FOR_EXISTING_13_15_MEMBERS','activation':'REQUIRES_NORMATIVE_INTEGRATION_AND_REVIEW','authority':['SSOT §13.15 capture/restore/member inventory','SSOT §8.4 immutable encrypted bytes','SSOT §8.7/8.8 exact version and consumer authority']})
profiles=[]
for v in variants:
 n=v['profileId'];defs[n]=v['schema'];profiles.append(obj({'representation':const('PROFILE_JSON_V1'),'profileId':const(n),'profile':ref(n)}))
# Unchanged RAW values remain unchanged shapes. Their encoding discriminates
# explicitly; they are never inspected and promoted to profiles.
raw={'oneOf':[obj({'encoding':const('UTF8'),'text':string(True)}),obj({'encoding':const('BASE64'),'base64':b64})]}
defs['ProfileValue']={'oneOf':profiles};defs['RawValue']=raw
current=json.loads((D/'create-current.json').read_text())['record']['requestSchema']['properties']['body']
defs['RawValue']=copy.deepcopy(current['properties']['value']) # exact compatibility, including original nonempty BASE64
body=copy.deepcopy(current);body.pop('$id',None);body.pop('$comment',None);body['properties']['value']={'oneOf':[ref('RawValue'),ref('ProfileValue')]};body.pop('allOf',None)
for v in variants:
 body.setdefault('allOf',[]).append({'if':{'properties':{'value':{'properties':{'profileId':const(v['profileId'])},'required':['profileId']}},'required':['value']},'then':{'properties':{'type':const(v['secretType'])}}})
body['allOf'].append({'if':{'properties':{'value':{'required':['encoding']}},'required':['value']},'then':{'if':{'properties':{'type':const('GENERIC_BINARY')}},'then':{'properties':{'value':{'properties':{'encoding':const('BASE64')}}}},'else':{'properties':{'value':{'properties':{'encoding':const('UTF8')}}}}}})
defs['SecretCreateBody']=body
# Trusted declarations are server-produced/pinned, not import authority.
defs['ConsumerProfileSupport']=obj({'secretType':{'enum':[c['secretType']for c in p['contracts']]},'profileId':{'enum':[v['profileId']for v in variants]},'schemaDigest':{'type':'string','pattern':'^sha256:[0-9a-f]{64}$'}})
defs['ConsumerDeclaration']=obj({'consumerId':string(True),'consumerRevision':string(True),'purposeKind':string(True),'profiles':arr(ref('ConsumerProfileSupport')),'allowedOrigins':arr(origin),'cookieHosts':arr(string(True)),'tokenEndpoint':{'oneOf':[{'type':'string','format':'uri','pattern':'^https://'},{'type':'null'}]},'database':{'oneOf':[string(),{'type':'null'}]},'keyAlgorithms':arr({'enum':['RSA','EC','ED25519','ED448','DSA']}),'browserMembers':arr({'enum':['COOKIES','PARTITIONED_COOKIES','LOCAL_STORAGE','INDEXED_DB','SESSION_STORAGE','PERMISSIONS','CLIENT_CERTIFICATE_BINDINGS','VIRTUAL_WEBAUTHN']}),'serializerIds':arr({'enum':['ECMASCRIPT_AUTH_CLONE_GRAPH_V1','BROWSER_AUTH_STATE_GRAPH_V1','BROWSER_COOKIE_LOCAL_STORAGE_V1','HTTP_COOKIE_JAR_V1']}),'engineBuild':{'oneOf':[string(True),{'type':'null'}]}})
defs['StoredVersionPayload']=obj({'payloadVersion':const('SECRET_IMMUTABLE_PAYLOAD_V1'),'secretType':{'enum':current['properties']['type']['enum']},'representation':{'enum':['RAW_UTF8','RAW_BINARY','PROFILE_JSON_V1']},'profileId':{'oneOf':[{'enum':[v['profileId']for v in variants]},{'type':'null'}]},'schemaId':{'oneOf':[string(True),{'type':'null'}]},'schemaDigest':{'oneOf':[{'type':'string','pattern':'^sha256:[0-9a-f]{64}$'},{'type':'null'}]},'originalPlaintextBytesBase64':b64})
defs['KeyAlgorithmPolicy']={'oneOf':[obj({'algorithm':const('RSA'),'minimumModulusBits':{'type':'integer','minimum':1},'publicExponents':arr({'type':'integer','minimum':3})}),obj({'algorithm':const('EC'),'namedCurves':arr({'enum':['secp256r1','secp384r1','secp521r1','secp256k1']})}),obj({'algorithm':const('ED25519')}),obj({'algorithm':const('ED448')}),obj({'algorithm':const('DSA'),'minimumPBits':{'type':'integer','minimum':1},'minimumQBits':{'type':'integer','minimum':1}})]}
defs['ConsumerDeclaration']['properties']['keyAlgorithmPolicies']=arr(ref('KeyAlgorithmPolicy'))
defs['ConsumerDeclaration']['properties']['totpPolicies']=arr(obj({'algorithm':{'enum':['SHA1','SHA256','SHA512']},'digits':{'enum':[6,8]},'minimumSeedBytes':{'type':'integer','minimum':1},'minimumPeriodSeconds':{'type':'integer','minimum':1},'maximumPeriodSeconds':{'type':'integer','minimum':1}}))
defs['ConsumerDeclaration']['properties']['oauthClientId']={'oneOf':[string(True),{'type':'null'}]}
defs['ConsumerDeclaration']['properties']['authorizedOAuthScopes']=arr(string(True))
defs['ConsumerDeclaration']['required'] += ['keyAlgorithmPolicies','totpPolicies','oauthClientId','authorizedOAuthScopes']
# Exact compatible pairs are structural, not merely reviewer prose.
defs['ConsumerProfileSupport']['allOf']=[{'if':{'properties':{'profileId':const(v['profileId'])}},'then':{'properties':{'secretType':const(v['secretType'])}}}for v in variants]
defs.pop('StoredVersionPayload')
defs['StoredVersionMetadata']=obj({'secretId':uuid,'versionId':uuid,'type':{'enum':current['properties']['type']['enum']},'representation':{'enum':['RAW_UTF8','RAW_BINARY','PROFILE_JSON_V1']},'profileId':{'oneOf':[{'enum':[v['profileId']for v in variants]},{'type':'null'}]},'schemaId':{'oneOf':[string(True),{'type':'null'}]},'schemaDigest':{'oneOf':[{'type':'string','pattern':'^sha256:[0-9a-f]{64}$'},{'type':'null'}]},'plaintextByteLength':{'type':'integer','minimum':0},'valueDigest':{'type':'string','pattern':'^sha256:[0-9a-f]{64}$'},'payloadFormat':const('EXACT_SECRET_BYTES_V1')})
defs['StoredVersionMetadata']['allOf']=[{'if':{'properties':{'representation':const('PROFILE_JSON_V1')}},'then':{'properties':{'profileId':{'enum':[v['profileId']for v in variants]},'schemaId':string(True),'schemaDigest':{'type':'string','pattern':'^sha256:[0-9a-f]{64}$'}}},'else':{'properties':{'profileId':{'type':'null'},'schemaId':{'type':'null'},'schemaDigest':{'type':'null'}}}}]+[{'if':{'properties':{'profileId':const(v['profileId'])}},'then':{'properties':{'type':const(v['secretType']),'schemaId':const('urn:kcml:secret-profile-handoffs:1#/$defs/'+v['profileId'])}}}for v in variants]
defs['StoredVersionMetadata']['properties']['canonicalValueDigest']={'type':'string','pattern':'^sha256:[0-9a-f]{64}$'}
defs['StoredVersionMetadata']['required'].append('canonicalValueDigest')
out={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:secret-profile-handoffs:1','$defs':defs,'x-profileInventory':variants,'x-inputCommit':PIN,'x-sourceSha256':json.loads((D/'source-bindings.json').read_text())['sourceSha256'],'x-status':'DESIGN_PROPOSAL_REQUIRES_COORDINATOR_INTEGRATION_REVIEW','x-limits':[{'scope':'Entire HTTP body UTF8 bytes','maximum':1048576,'authority':'SSOT §12.18 current transport parser boundary; per-value char/item caps removed'},{'scope':'IDB database version / key generator','maximum':9007199254740991,'authority':'IndexedDB unsigned long long represented as ECMAScript safe integer; next key exhaustion sentinel 2^53 explicitly supported'},{'scope':'WebAuthn signCount','maximum':4294967295,'authority':'WebAuthn authenticatorData uint32 field'}]}
(D/'secret-profile-handoffs.schema.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'profiles':len(variants),'types':len(p['contracts']),'definitions':len(defs)}))
if __name__=='__main__':pass
