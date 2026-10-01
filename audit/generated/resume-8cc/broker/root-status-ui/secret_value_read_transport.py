"""Closed transport/native OWNER value read; plaintext only on authorized reveal.
Authority/authenticated SQL/open/audit transaction is a required upstream stage.
No client owner/context/guard creates read authority. No value normalization.
"""
import base64,hashlib,json,re
from secret_profile_reference import parse_profile,strict_json,canonical_value_digest,INVENTORY
UUID=re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
def fail(code):raise ValueError(code)
def decode_value_read(method,path_parameters,query_pairs,body):
 if method!='GET':fail('SECRET_VALUE_READ_METHOD_INVALID')
 if type(path_parameters)is not dict or set(path_parameters)!={'id'} or not isinstance(path_parameters['id'],str) or not UUID.fullmatch(path_parameters['id']):fail('SECRET_VALUE_READ_PATH_INVALID')
 if body not in (None,b''):fail('SECRET_VALUE_READ_BODY_NOT_ALLOWED')
 if type(query_pairs)is not list:fail('SECRET_VALUE_READ_QUERY_INVALID')
 seen={}
 for pair in query_pairs:
  if not isinstance(pair,(tuple,list)) or len(pair)!=2 or not all(isinstance(x,str)for x in pair):fail('SECRET_VALUE_READ_QUERY_INVALID')
  name,value=pair
  if name!='versionId':fail('SECRET_VALUE_READ_QUERY_UNKNOWN')
  if name in seen:fail('SECRET_VALUE_READ_QUERY_DUPLICATE')
  if not UUID.fullmatch(value):fail('SECRET_VALUE_READ_VERSION_INVALID')
  seen[name]=value
 return {'operationId':'secret.value.read','secretId':path_parameters['id'],'selector':{'kind':'IMMUTABLE_VERSION','versionId':seen['versionId']}if seen else {'kind':'CURRENT'}}
def decode_http_value_read(method,path_parameters,raw_query,body):
 # Standard URI query percent-decoding is transport-only; it never touches
 # the Secret's immutable plaintext bytes. Preserve duplicate decoded names.
 from urllib.parse import parse_qsl
 if not isinstance(raw_query,bytes):fail('SECRET_VALUE_READ_QUERY_ENCODING_INVALID')
 try:text=raw_query.decode('ascii',errors='strict')
 except UnicodeDecodeError:fail('SECRET_VALUE_READ_QUERY_ENCODING_INVALID')
 if re.search(r'%(?![0-9A-Fa-f]{2})',text):fail('SECRET_VALUE_READ_QUERY_ENCODING_INVALID')
 try:pairs=parse_qsl(text,keep_blank_values=True,strict_parsing=True,encoding='utf8',errors='strict',separator='&') if text else []
 except (ValueError,UnicodeDecodeError):fail('SECRET_VALUE_READ_QUERY_ENCODING_INVALID')
 return decode_value_read(method,path_parameters,pairs,body)
def selected_version_argument(native):
 s=native['selector'];return None if s['kind']=='CURRENT' else s['versionId']
def reveal_response(snapshot,original_bytes):
 # This function has no authority: invoke only AFTER actual fresh verifier,
 # canonical open/content check and same-transaction retained audit commit.
 if snapshot['diagnostic']!='VALUE_READ_READY':fail('SECRET_VALUE_READ_NOT_AUTHORIZED_STAGE')
 protected=snapshot['protectedRow'];status=protected.get('recordStatus');state=protected.get('recordStateVersion')
 if status not in ('INACTIVE','ACTIVE'):fail('SECRET_REVEAL_ROOT_STATUS_INVALID')
 if not isinstance(state,str) or not re.fullmatch(r'0|[1-9][0-9]*',state) or int(state)>9223372036854775807:fail('SECRET_REVEAL_ROOT_STATE_VERSION_INVALID')
 v=protected['version'];raw=bytes(original_bytes)
 if len(raw)!=v['plaintext_byte_length'] or 'sha256:'+hashlib.sha256(raw).hexdigest()!='sha256:'+v['original_import_bytes_digest'][2:]:fail('SECRET_REVEAL_ORIGINAL_BYTES_MISMATCH')
 candidate={'type':v['secret_type'],'representation':v['value_representation'],'profileId':v['profile_id'],'bytes':raw}
 if canonical_value_digest(candidate)!='sha256:'+v['canonical_value_digest'][2:]:fail('SECRET_REVEAL_CANONICAL_DIGEST_MISMATCH')
 representation=v['value_representation']
 if representation=='RAW_UTF8':value={'representation':representation,'text':raw.decode('utf8',errors='strict')}
 elif representation=='RAW_BINARY':value={'representation':representation,'base64':base64.b64encode(raw).decode('ascii')}
 elif representation=='PROFILE_JSON_V1':
  if v['profile_id']=='BROWSER_AUTH_STATE_GRAPH_V1':fail('SECRET_REVEAL_PROFILE_NOT_ACTIVATED')
  if v['profile_id'] not in INVENTORY or INVENTORY[v['profile_id']]['secretType']!=v['secret_type']:fail('SECRET_REVEAL_PROFILE_TYPE_MISMATCH')
  parse_profile(v['profile_id'],raw)
  value={'representation':representation,'profileId':v['profile_id'],'profile':strict_json(raw),'originalBytesBase64':base64.b64encode(raw).decode('ascii')}
 else:fail('SECRET_REVEAL_REPRESENTATION_UNSUPPORTED')
 return {'recordStatus':status,'recordStateVersion':state,'secretId':v['secret_id'],'versionId':v['id'],'secretType':v['secret_type'],'byteLength':len(raw),'originalImportBytesDigest':'sha256:'+v['original_import_bytes_digest'][2:],'canonicalValueDigest':'sha256:'+v['canonical_value_digest'][2:],'value':value}
def copy_revealed_bytes(response):
 # Existing UI COPY is a client interaction with the same revealed version,
 # not another server command or re-resolution to current activation.
 v=response['value']
 if v['representation']=='RAW_UTF8':raw=v['text'].encode('utf8')
 else:
  field='base64' if v['representation']=='RAW_BINARY' else 'originalBytesBase64'
  raw=base64.b64decode(v[field],validate=True)
  if base64.b64encode(raw).decode('ascii')!=v[field]:fail('SECRET_REVEAL_BYTES_ENCODING_INVALID')
 if v['representation']=='PROFILE_JSON_V1':
  parse_profile(v['profileId'],raw)
  if strict_json(raw)!=v['profile']:fail('SECRET_REVEAL_PROFILE_BYTES_MISMATCH')
 if len(raw)!=response['byteLength'] or 'sha256:'+hashlib.sha256(raw).hexdigest()!=response['originalImportBytesDigest']:fail('SECRET_REVEAL_ORIGINAL_BYTES_MISMATCH')
 return raw
