"""Isolated DESIGN REFERENCE. No broker authority, production cipher or live calls."""
import base64,copy,hashlib,json,math,os,re,struct,types
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
from jsonschema import Draft202012Validator,FormatChecker
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa,ec,ed25519,ed448,dsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
D=Path(__file__).resolve().parent
SCHEMA=json.loads((D/'secret-profile-handoffs.schema.json').read_text())
PIN='34d3a75c47a92ab7d8e0dac84f581549a15445ca'
import secret_value_parsers as legacy
Rejected=legacy.Rejected
reject=legacy.reject
INVENTORY={v['profileId']:v for v in SCHEMA['x-profileInventory']}
def digest(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()
def compiled_schema_bytes(profile):
 if profile not in SCHEMA['$defs']:reject('SECRET_VARIANT_UNSUPPORTED','/value/profileId')
 document={'$schema':SCHEMA['$schema'],'$id':SCHEMA['$id'],'$defs':SCHEMA['$defs'],'$ref':'#/$defs/'+profile}
 return json.dumps(document,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
def schema_digest(profile):return digest(compiled_schema_bytes(profile))
def strict_json(raw):
 if len(raw)>1048576:reject('SECRET_IMPORT_TRANSPORT_TOO_LARGE','')
 try:text=raw.decode('utf8',errors='strict')
 except UnicodeDecodeError:reject('SECRET_IMPORT_UTF8_INVALID','')
 class ObjectPairs(list):pass
 def convert(v,path=''):
  if isinstance(v,ObjectPairs):
   out={}
   for key,item in v:
    at=path+'/'+key.replace('~','~0').replace('/','~1')
    if key in out:reject('SECRET_IMPORT_DUPLICATE_JSON_KEY',at)
    out[key]=convert(item,at)
   return out
  if isinstance(v,list):return [convert(x,path+'/'+str(i))for i,x in enumerate(v)]
  if isinstance(v,float)and not math.isfinite(v):reject('SECRET_IMPORT_NONFINITE_NUMBER',path)
  if isinstance(v,str):
   try:v.encode('utf8')
   except UnicodeEncodeError:reject('SECRET_IMPORT_UTF8_INVALID',path)
  return v
 def exact_number(token):
  value=Decimal(token)
  return int(value) if value==value.to_integral_value() else value
 try:return convert(json.loads(text,object_pairs_hook=ObjectPairs,parse_float=exact_number))
 except Rejected:raise
 except (ValueError,TypeError,RecursionError):reject('SECRET_IMPORT_JSON_INVALID','')

def validate(schema_name,value):
 schema=json.loads(compiled_schema_bytes(schema_name))
 errors=list(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(value))
 if errors:reject('SECRET_PROFILE_SCHEMA_INVALID',errors[0].json_path)

def canonical_b64(value,at):
 try:raw=base64.b64decode(value,validate=True)
 except (ValueError,TypeError):reject('SECRET_PROFILE_ENCODING_INVALID',at)
 if base64.b64encode(raw).decode()!=value:reject('SECRET_PROFILE_ENCODING_INVALID',at)
 return raw

def float64(v,at,finite=True):
 raw=canonical_b64(v['base64'],at)
 if len(raw)!=8:reject('BROWSER_SERIALIZER_NUMBER_INVALID',at)
 n=struct.unpack('>d',raw)[0]
 if finite and not math.isfinite(n):reject('BROWSER_SERIALIZER_NUMBER_INVALID',at)
 return n

def unique(items,key,code,at):
 keys=[key(x) for x in items]
 if len(set(keys))!=len(keys):reject(code,at)

def algorithm(key):
 for cls,name in [(rsa.RSAPrivateKey,'RSA'),(ec.EllipticCurvePrivateKey,'EC'),(ed25519.Ed25519PrivateKey,'ED25519'),(ed448.Ed448PrivateKey,'ED448'),(dsa.DSAPrivateKey,'DSA')]:
  if isinstance(key,cls):return name
 reject('SECRET_KEY_ALGORITHM_UNSUPPORTED','/consumer/keyAlgorithms')

def candidate_consumer(profile,value):
 # Parser-only scope is derived for syntactic validation. It confers no target,
 # runtime binding, account postcondition or algorithm permission.
 hosts=[c['domain'].lstrip('.') for c in value.get('cookies',[])]
 origins=[o['origin'] for o in value.get('origins',[])]
 oauth=[legacy.urlsplit(value['tokenEndpoint']).hostname] if 'tokenEndpoint'in value else []
 return {'supported':{(INVENTORY[profile]['secretType'],profile)},'cookieHosts':hosts,'origins':origins,'oauthHosts':oauth,'database':value.get('database'),'keyAlgorithmAllowed':lambda key:True}

def clone(graph,at):
 nodes=graph['nodes'];unique(nodes,lambda n:n['id'],'BROWSER_STATE_DUPLICATE_NODE',at+'/nodes');by={n['id']:n for n in nodes}
 if graph['rootNodeId'] not in by:reject('BROWSER_STATE_GRAPH_REFERENCE_INVALID',at+'/rootNodeId')
 def same_value_zero(node_id):
  n=by.get(node_id)
  if n is None:reject('BROWSER_STATE_GRAPH_REFERENCE_INVALID',at+'/nodes')
  kind=n['kind']
  if kind in ['UNDEFINED','NULL']:return (kind,None)
  if kind in ['BOOLEAN','STRING']:return(kind,n['value'])
  if kind=='BIGINT':return(kind,'0'if n['decimal']=='-0'else n['decimal'])
  if kind=='NUMBER':
   value=float64(n['value'],at+'/nodes/'+node_id,finite=False)
   return(kind,'NaN'if math.isnan(value)else value)
  # All structured-clone objects, including Date and typed arrays, compare by
  # object identity rather than structurally equal contents.
  return('OBJECT_IDENTITY',node_id)
 links=[]
 for n in nodes:
  k=n['kind'];p=at+'/nodes/'+n['id']
  if k in ['NUMBER','DATE']:float64(n['value'] if k=='NUMBER' else n['epochMilliseconds'],p,finite=(k=='DATE'))
  if k in ['ARRAY_BUFFER','BLOB','FILE']:canonical_b64(n['base64'],p+'/base64')
  if k=='FILE':float64(n['lastModifiedMilliseconds'],p+'/lastModifiedMilliseconds')
  if k=='REGEXP' and ('u'in n['flags'] and 'v'in n['flags']):reject('BROWSER_STATE_REGEXP_FLAGS_INVALID',p+'/flags')
  if k=='OBJECT':
   unique(n['entries'],lambda x:x['name'],'BROWSER_STATE_DUPLICATE_STORAGE_KEY',p+'/entries');links += [e['valueNodeId']for e in n['entries']]
  elif k in ['ARRAY','SET']:
   if k=='ARRAY':
    unique(n['items'],lambda e:e['index'],'BROWSER_STATE_DUPLICATE_ARRAY_INDEX',p+'/items')
    if any(e['index']>=n['length']for e in n['items']):reject('BROWSER_STATE_ARRAY_INDEX_INVALID',p+'/items')
    unique(n['properties'],lambda e:e['name'],'BROWSER_STATE_DUPLICATE_STORAGE_KEY',p+'/properties')
    if any(e['name']=='length'or len(e['name'])<=10 and re.fullmatch(r'(0|[1-9][0-9]*)',e['name'])and int(e['name'])<4294967295 for e in n['properties']):reject('BROWSER_STATE_ARRAY_PROPERTY_INVALID',p+'/properties')
    links += [e['valueNodeId']for e in n['properties']]
   if k=='SET':unique(n['items'],lambda e:same_value_zero(e['nodeId']),'BROWSER_STATE_DUPLICATE_SET_VALUE',p+'/items')
   links += [e['nodeId']for e in n['items']]
  elif k=='MAP':
   unique(n['entries'],lambda e:same_value_zero(e['keyNodeId']),'BROWSER_STATE_DUPLICATE_MAP_KEY',p+'/entries')
   links += [e[f] for e in n['entries'] for f in ['keyNodeId','valueNodeId']]
  elif k=='TYPED_ARRAY':
   b=by.get(n['bufferNodeId'])
   if not b or b['kind']!='ARRAY_BUFFER':reject('BROWSER_STATE_GRAPH_REFERENCE_INVALID',p+'/bufferNodeId')
   raw=canonical_b64(b['base64'],p+'/buffer');width={'Int16Array':2,'Uint16Array':2,'Int32Array':4,'Uint32Array':4,'Float32Array':4,'Float64Array':8,'BigInt64Array':8,'BigUint64Array':8}.get(n['elementType'],1)
   if n['byteOffset']+n['byteLength']>len(raw) or n['byteOffset']%width or n['byteLength']%width:reject('BROWSER_STATE_TYPED_ARRAY_RANGE_INVALID',p)
   links.append(n['bufferNodeId'])
 if any(x not in by for x in links):reject('BROWSER_STATE_GRAPH_REFERENCE_INVALID',at+'/nodes')
 # Graph identity and original byte form preserved; no cycle flattening.
 return by

def idb_key(k,at):
 kind=k['kind']
 if kind in ['NUMBER','DATE']:
  n=float64(k['value']if kind=='NUMBER'else k['epochMilliseconds'],at)
  if kind=='DATE' and abs(n)>8640000000000000:reject('BROWSER_STATE_IDB_KEY_INVALID',at)
  return(kind,n)
 if kind=='BINARY':return(kind,canonical_b64(k['base64'],at))
 if kind=='STRING':return(kind,k['value'])
 return(kind,tuple(idb_key(x,at+'/items')for x in k['items']))

def full_browser(value):
 unique(value['origins'],lambda x:x['origin'],'BROWSER_STATE_DUPLICATE_ORIGIN','/origins')
 for oi,o in enumerate(value['origins']):
  at='/origins/'+str(oi);legacy.endpoint(o['origin'],'BROWSER_STATE_ORIGIN_INVALID',at+'/origin',True)
  unique(o['localStorage'],lambda x:x['name'],'BROWSER_STATE_DUPLICATE_STORAGE_KEY',at+'/localStorage')
  unique(o['indexedDB'],lambda x:x['name'],'BROWSER_STATE_IDB_DATABASE_DUPLICATE',at+'/indexedDB')
  for di,db in enumerate(o['indexedDB']):
   dp=at+'/indexedDB/'+str(di);unique(db['objectStores'],lambda x:x['name'],'BROWSER_STATE_IDB_STORE_DUPLICATE',dp+'/objectStores')
   for si,st in enumerate(db['objectStores']):
    sp=dp+'/objectStores/'+str(si)
    if st['autoIncrement']!=(st['nextGeneratedKey']is not None):reject('BROWSER_STATE_IDB_KEY_GENERATOR_INVALID',sp+'/nextGeneratedKey')
    if st['autoIncrement'] and (st['keyPath']=='' or isinstance(st['keyPath'],list)):reject('BROWSER_STATE_IDB_KEY_GENERATOR_INVALID',sp+'/keyPath')
    unique(st['indexes'],lambda x:x['name'],'BROWSER_STATE_IDB_INDEX_DUPLICATE',sp+'/indexes')
    for ix in st['indexes']:
     if ix['multiEntry'] and isinstance(ix['keyPath'],list):reject('BROWSER_STATE_IDB_INDEX_INVALID',sp+'/indexes')
    seen=set()
    for ri,rec in enumerate(st['records']):
     rp=sp+'/records/'+str(ri);key=idb_key(rec['key'],rp+'/key')
     if key in seen:reject('BROWSER_STATE_IDB_RECORD_DUPLICATE',rp+'/key')
     seen.add(key);clone(rec['value'],rp+'/value')
 origins={x['origin']for x in value['origins']}
 unique(value['pages'],lambda x:(x['pageKey'],x['origin']),'BROWSER_STATE_PAGE_DUPLICATE','/pages')
 for i,p in enumerate(value['pages']):
  if p['origin'] not in origins:reject('BROWSER_STATE_ORIGIN_INVENTORY_MISMATCH','/pages/'+str(i)+'/origin')
  unique(p['sessionStorage'],lambda x:x['name'],'BROWSER_STATE_DUPLICATE_STORAGE_KEY','/pages/'+str(i)+'/sessionStorage')
 unique(value['permissions'],lambda x:(x['origin'],x['permission']),'BROWSER_STATE_PERMISSION_DUPLICATE','/permissions')
 for p in value['permissions']:
  if p['origin'] not in origins:reject('BROWSER_STATE_ORIGIN_INVENTORY_MISMATCH','/permissions')
 for i,c in enumerate(value['clientCertificateBindings']):
  if c['origin'] not in origins:reject('BROWSER_STATE_ORIGIN_INVENTORY_MISMATCH','/clientCertificateBindings/'+str(i)+'/origin')
 keys=[]
 for i,c in enumerate(value['cookies']):
  at='/cookies/'+str(i);legacy.cookies([{f:c[f]for f in ['name','value','domain','path','secure','httpOnly','sameSite']}],{'cookieHosts':[c['domain'].lstrip('.')]})
  if c['hostOnly'] and c['domain'].startswith('.'):reject('COOKIE_HOST_ONLY_INVALID',at+'/domain')
  if c['expiry']['kind']=='ABSOLUTE':float64(c['expiry']['unixSeconds'],at+'/expiry/unixSeconds')
  part=c['partition'];partkey=None
  if part['kind']=='TOP_LEVEL_SITE':
   legacy.endpoint(part['topLevelSite'],'COOKIE_PARTITION_KEY_INVALID',at+'/partition/topLevelSite',True)
   if not c['secure']:reject('COOKIE_PARTITION_SECURE_REQUIRED',at+'/secure')
   partkey=(part['topLevelSite'],part['hasCrossSiteAncestor'])
  keys.append((c['name'],c['domain'].lower().lstrip('.'),c['hostOnly'],c['path'],partkey))
 if len(set(keys))!=len(keys):reject('COOKIE_DUPLICATE','/cookies')
 unique(value['virtualAuthenticators'],lambda x:x['authenticatorKey'],'BROWSER_VIRTUAL_AUTHENTICATOR_DUPLICATE','/virtualAuthenticators')
 for i,a in enumerate(value['virtualAuthenticators']):
  seen=set()
  for j,c in enumerate(a['credentials']):
   at='/virtualAuthenticators/'+str(i)+'/credentials/'+str(j)
   cid=canonical_b64(c['credentialIdBase64'],at+'/credentialIdBase64');uh=canonical_b64(c['userHandleBase64'],at+'/userHandleBase64')
   if not cid or len(uh)>64:reject('BROWSER_VIRTUAL_CREDENTIAL_INVALID',at)
   if cid in seen:reject('BROWSER_VIRTUAL_CREDENTIAL_DUPLICATE',at+'/credentialIdBase64')
   seen.add(cid)
   if c['backupState']and not c['backupEligible']:reject('BROWSER_VIRTUAL_CREDENTIAL_BACKUP_INVALID',at+'/backupState')
   try:serialization.load_der_private_key(canonical_b64(c['privateKeyPkcs8DerBase64'],at+'/privateKeyPkcs8DerBase64'),None)
   except (ValueError,TypeError):reject('BROWSER_VIRTUAL_CREDENTIAL_KEY_INVALID',at+'/privateKeyPkcs8DerBase64')

def parse_profile(profile,raw):
 if profile not in INVENTORY:reject('SECRET_VARIANT_UNSUPPORTED','/value/profileId')
 value=strict_json(raw);validate(profile,value)
 if profile=='BROWSER_AUTH_STATE_GRAPH_V1':full_browser(value)
 else:legacy.parse_candidate(INVENTORY[profile]['secretType'],value,candidate_consumer(profile,value))
 return value

def use_profile(profile,raw,consumer,now,account_observation=None):
 if profile not in INVENTORY:reject('SECRET_VARIANT_UNSUPPORTED','/value/profileId')
 validate('ConsumerDeclaration',consumer)
 matches=[x for x in consumer['profiles']if x['secretType']==INVENTORY[profile]['secretType']and x['profileId']==profile]
 if not matches:reject('SECRET_VARIANT_UNSUPPORTED','/consumer/profiles')
 if len(matches)!=1 or matches[0]['schemaDigest']!=schema_digest(profile):reject('SECRET_CONSUMER_SCHEMA_MISMATCH','/consumer/profiles')
 v=parse_profile(profile,raw)
 if profile=='OAUTH_CLIENT_SECRET_V1'and v['tokenEndpoint']!=consumer['tokenEndpoint']:reject('OAUTH_TOKEN_ENDPOINT_BINDING_MISMATCH','/tokenEndpoint')
 if profile=='OAUTH_CLIENT_SECRET_V1'and v['clientId']!=consumer['oauthClientId']:reject('OAUTH_CLIENT_BINDING_MISMATCH','/clientId')
 if profile in ['OAUTH_CLIENT_SECRET_V1','OAUTH_BEARER_TOKEN_SET_V1']and any(scope not in consumer['authorizedOAuthScopes']for scope in v.get('scopes',[])):reject('OAUTH_SCOPE_BINDING_MISMATCH','/scopes')
 if profile=='TOTP_BASE32_V1':
  seed=base64.b32decode(v['seedBase32']+'='*((-len(v['seedBase32']))%8),casefold=False)
  if not any(p['algorithm']==v['algorithm']and p['digits']==v['digits']and len(seed)>=p['minimumSeedBytes']and p['minimumPeriodSeconds']<=v['periodSeconds']<=p['maximumPeriodSeconds']for p in consumer['totpPolicies']):reject('TOTP_CONSUMER_PARAMETERS_UNSUPPORTED','/consumer/totpPolicies')
 if profile=='DATABASE_USER_PASSWORD_V1'and 'database'in v and v['database']!=consumer['database']:reject('DATABASE_CREDENTIAL_TARGET_MISMATCH','/database')
 if profile=='OAUTH_BEARER_TOKEN_SET_V1'and 'expiresAt'in v and datetime.fromisoformat(v['expiresAt'].replace('Z','+00:00'))<=now:reject('OAUTH_TOKEN_EXPIRED','/expiresAt')
 if profile in ['PKCS8_PEM_PRIVATE_KEY_V1','SSH_OPENSSH_PRIVATE_KEY_V1']:
  if profile=='PKCS8_PEM_PRIVATE_KEY_V1':key=serialization.load_pem_private_key(v['pem'].encode(),None)
  else:key=serialization.load_ssh_private_key(v['privateKeyPem'].encode(),v['passphrase'].encode()if'passphrase'in v else None)
  algo=algorithm(key)
  if algo not in consumer['keyAlgorithms']:reject('SECRET_KEY_ALGORITHM_UNSUPPORTED','/consumer/keyAlgorithms')
  policies=[p for p in consumer['keyAlgorithmPolicies']if p['algorithm']==algo]
  if len(policies)!=1:reject('SECRET_KEY_ALGORITHM_POLICY_INVALID','/consumer/keyAlgorithmPolicies')
  policy=policies[0];okay=True
  if algo=='RSA':okay=key.key_size>=policy['minimumModulusBits']and key.public_key().public_numbers().e in policy['publicExponents']
  elif algo=='EC':okay=key.curve.name in policy['namedCurves']
  elif algo=='DSA':
   params=key.parameters().parameter_numbers();okay=params.p.bit_length()>=policy['minimumPBits']and params.q.bit_length()>=policy['minimumQBits']
  if not okay:reject('SECRET_KEY_ALGORITHM_POLICY_REJECTED','/consumer/keyAlgorithmPolicies')
 if profile in ['HTTP_COOKIE_JAR_V1','BROWSER_COOKIE_LOCAL_STORAGE_V1','BROWSER_AUTH_STATE_GRAPH_V1']:
  if profile=='BROWSER_AUTH_STATE_GRAPH_V1':
   for c in v['cookies']:legacy.cookies([c],{'cookieHosts':consumer['cookieHosts']})
  else:legacy.cookies(v['cookies'],{'cookieHosts':consumer['cookieHosts']})
  members={'COOKIES'}
  if 'origins'in v:
   members.add('LOCAL_STORAGE')
   if any(o['origin']not in consumer['allowedOrigins']for o in v['origins']):reject('BROWSER_STATE_ORIGIN_SCOPE_MISMATCH','/origins')
  if profile=='BROWSER_AUTH_STATE_GRAPH_V1':
   for field,member in [('pages','SESSION_STORAGE'),('permissions','PERMISSIONS'),('clientCertificateBindings','CLIENT_CERTIFICATE_BINDINGS'),('virtualAuthenticators','VIRTUAL_WEBAUTHN')]:
    if v[field]:members.add(member)
   if any(o['indexedDB']for o in v['origins']):members.add('INDEXED_DB')
   if any(c['partition']['kind']!='UNPARTITIONED'for c in v['cookies']):members.add('PARTITIONED_COOKIES')
   if 'ECMASCRIPT_AUTH_CLONE_GRAPH_V1'not in consumer['serializerIds']and 'INDEXED_DB'in members:reject('BROWSER_STATE_SERIALIZER_UNSUPPORTED','/consumer/serializerIds')
  if not members<=set(consumer['browserMembers']):reject('BROWSER_STATE_MEMBER_UNSUPPORTED','/consumer/browserMembers')
  # Real account-marker evidence must be validated by the exact adapter; a
  # client/fixture boolean cannot stand in for semantic identity matching.
  if account_observation is not None:
   if not isinstance(account_observation,dict)or set(account_observation)!={'expectedAccount','expectedTenant','observedAccount','observedTenant'}:reject('BROWSER_STATE_AUTH_POSTCONDITION_FAILED','/consumer/account')
   if account_observation['observedAccount']!=account_observation['expectedAccount']or account_observation['observedTenant']!=account_observation['expectedTenant']:reject('BROWSER_STATE_AUTH_POSTCONDITION_FAILED','/consumer/account')
 return {'status':'REFERENCE_PREFLIGHT_PASSED','runtimeAuthenticated':False}

def original_profile_slice(raw):
 """Strict decoder plus source span: never reserialize the sensitive value."""
 strict_json(raw);text=raw.decode();decoder=json.JSONDecoder()
 def skip(i):
  while i<len(text)and text[i].isspace():i+=1
  return i
 def member(start,name):
  i=skip(start)
  if text[i]!='{':reject('SECRET_IMPORT_JSON_INVALID','')
  i=skip(i+1)
  while text[i]!='}':
   k,end=decoder.raw_decode(text,i);i=skip(end)
   if text[i]!=':':reject('SECRET_IMPORT_JSON_INVALID','')
   startvalue=skip(i+1);_,end=decoder.raw_decode(text,startvalue)
   if k==name:return startvalue,end
   i=skip(end)
   if text[i]==',':i=skip(i+1)
  reject('SECRET_IMPORT_PROFILE_MISSING','/value/profile')
 s,_=member(0,'value');s,e=member(s,'profile');return text[s:e].encode('utf8')

def import_body(raw):
 body=strict_json(raw);validate('SecretCreateBody',body);value=body['value']
 if 'encoding'in value:
  if body['type']in [c['secretType']for c in INVENTORY.values()]:reject('SECRET_PROFILE_REQUIRED','/value')
  original=value['text'].encode('utf8')if value['encoding']=='UTF8'else canonical_b64(value['base64'],'/value/base64')
  return {'type':body['type'],'representation':'RAW_UTF8'if value['encoding']=='UTF8'else'RAW_BINARY','profileId':None,'bytes':original}
 profile=value['profileId'];original=original_profile_slice(raw);parse_profile(profile,original)
 return {'type':body['type'],'representation':'PROFILE_JSON_V1','profileId':profile,'bytes':original}

def canonical_value_digest(candidate):
 profile=candidate['profileId'];payload=candidate['bytes']
 if profile:
  # Closed masks have string keys and integer-only direct numeric fields.
  # This explicitly named serializer is NOT an implicit RFC8785/JCS claim.
  payload=json.dumps(parse_profile(profile,payload),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')
 prefix=b'KCML_SECRET_VALUE_V1\0'+candidate['type'].encode()+b'\0'+candidate['representation'].encode()+b'\0'+(profile or 'RAW').encode()+b'\0'
 return digest(prefix+payload)

def store_reference(candidate,secret_id,version_id,key):
 # AES-GCM is isolated reference only, explicitly not a canonical cipher choice.
 profile=candidate['profileId'];metadata={'secretId':secret_id,'versionId':version_id,'type':candidate['type'],'representation':candidate['representation'],'profileId':profile,'schemaId':'urn:kcml:secret-profile-handoffs:1#/$defs/'+profile if profile else None,'schemaDigest':schema_digest(profile)if profile else None,'plaintextByteLength':len(candidate['bytes']),'valueDigest':digest(candidate['bytes']),'canonicalValueDigest':canonical_value_digest(candidate),'payloadFormat':'EXACT_SECRET_BYTES_V1'}
 aad=json.dumps(metadata,sort_keys=True,separators=(',',':')).encode();nonce=os.urandom(12);cipher=AESGCM(key).encrypt(nonce,candidate['bytes'],aad)
 return {'metadata':metadata,'aad':aad,'nonce':nonce,'ciphertext':cipher}

def load_reference(record,key,expected_secret_id,expected_version_id):
 if record['metadata'].get('secretId')!=expected_secret_id or record['metadata'].get('versionId')!=expected_version_id:reject('SECRET_STORED_REFERENCE_MISMATCH','/metadata')
 if record['aad']!=json.dumps(record['metadata'],sort_keys=True,separators=(',',':')).encode():reject('SECRET_STORED_IDENTITY_MISMATCH','/metadata')
 try:raw=AESGCM(key).decrypt(record['nonce'],record['ciphertext'],record['aad'])
 except __import__('cryptography.exceptions',fromlist=['InvalidTag']).InvalidTag:reject('SECRET_STORED_AUTHENTICATION_FAILED','/ciphertext')
 m=record['metadata'];validate('StoredVersionMetadata',m);profile=m['profileId']
 if len(raw)!=m['plaintextByteLength']or digest(raw)!=m['valueDigest']:reject('SECRET_STORED_BYTES_MISMATCH','/metadata')
 if m['representation']=='PROFILE_JSON_V1':
  if profile not in INVENTORY or m['schemaDigest']!=schema_digest(profile)or m['type']!=INVENTORY[profile]['secretType']:reject('SECRET_STORED_SCHEMA_MISMATCH','/metadata')
  parse_profile(profile,raw)
 candidate={'type':m['type'],'representation':m['representation'],'profileId':profile,'bytes':raw}
 if canonical_value_digest(candidate)!=m['canonicalValueDigest']:reject('SECRET_STORED_CANONICAL_DIGEST_MISMATCH','/metadata')
 return raw
