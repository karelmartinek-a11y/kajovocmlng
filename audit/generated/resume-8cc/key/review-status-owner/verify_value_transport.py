import sys,json,hashlib,copy,uuid
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from jsonschema import Draft202012Validator,FormatChecker
from secret_value_read_transport import decode_http_value_read,decode_value_read,selected_version_argument,reveal_response,copy_revealed_bytes
from secret_profile_reference import canonical_value_digest
from ssot_sources import SSOT,resource_index
schema_raw=resource_index()['contracts/secrets/owner-value-read.schema.json']['raw'];assert schema_raw==(OUT/'secret-value-read.schema.json').read_bytes();schema=json.loads(schema_raw);cases=[]
def valid(which,value):
 Draft202012Validator({'$schema':schema['$schema'],'$defs':schema['$defs'],**schema[which]},format_checker=FormatChecker()).validate(value)
def ok(name):cases.append({'id':name,'status':'PASS'})
sid=str(uuid.uuid4());vid=str(uuid.uuid4())
cur=decode_value_read('GET',{'id':sid},[],b'');valid('request',cur);assert selected_version_argument(cur)is None;ok('existing-current-empty-query-explicit-current-discriminator')
hist=decode_value_read('GET',{'id':sid},[('versionId',vid)],None);valid('request',hist);assert selected_version_argument(hist)==vid;ok('selected-immutable-version-explicit-query-native-SQL-argument')
for name,args,code in [('unknown-query',('GET',{'id':sid},[('ownerId',vid)],b''),'SECRET_VALUE_READ_QUERY_UNKNOWN'),('duplicate-selector',('GET',{'id':sid},[('versionId',vid)]*2,b''),'SECRET_VALUE_READ_QUERY_DUPLICATE'),('bad-version',('GET',{'id':sid},[('versionId','current')],b''),'SECRET_VALUE_READ_VERSION_INVALID'),('null-selector',('GET',{'id':sid},[('versionId',None)],b''),'SECRET_VALUE_READ_QUERY_INVALID'),('GET-JSON-body',('GET',{'id':sid},[],b'{"versionId":"'+vid.encode()+b'"}'),'SECRET_VALUE_READ_BODY_NOT_ALLOWED'),('injected-path-authority',('GET',{'id':sid,'ownerId':vid},[],b''),'SECRET_VALUE_READ_PATH_INVALID'),('wrong-method',('POST',{'id':sid},[],b''),'SECRET_VALUE_READ_METHOD_INVALID')]:
 try:decode_value_read(*args);raise AssertionError(name+' accepted')
 except ValueError as e:assert str(e)==code;(ok(name));cases[-1]['diagnostic']=code
assert decode_http_value_read('GET',{'id':sid},('versionId='+vid).encode(),b'')==hist;ok('actual-HTTP-query-decoder-to-explicit-history-native')
for label,query,code in [('encoded-duplicate',('versionId='+vid+'&version%49d='+vid).encode(),'SECRET_VALUE_READ_QUERY_DUPLICATE'),('bad-percent',b'versionId=%GG','SECRET_VALUE_READ_QUERY_ENCODING_INVALID'),('invalid-UTF8',b'versionId=%ff','SECRET_VALUE_READ_QUERY_ENCODING_INVALID'),('HTTP-unknown-query',b'trustedContextId=owner','SECRET_VALUE_READ_QUERY_UNKNOWN')]:
 try:decode_http_value_read('GET',{'id':sid},query,b'');raise AssertionError(label+' accepted')
 except ValueError as e:assert str(e)==code;ok(label);cases[-1]['diagnostic']=code
for label,mutator in [('current-with-version',lambda x:x['selector'].update({'versionId':vid})),('unknown-kind',lambda x:x['selector'].update({'kind':'LATEST'})),('client-authority',lambda x:x.update({'ownerId':vid}))]:
 bad=copy.deepcopy(cur);mutator(bad)
 try:valid('request',bad);raise AssertionError(label+' accepted')
 except Exception as e:
  from jsonschema import ValidationError
  assert isinstance(e,ValidationError);ok(label)
for kind,typ,profile,raw in [('RAW_UTF8','TOTP_SEED',None,b'  legacy\r\nunchanged  '),('RAW_BINARY','GENERIC_BINARY',None,b'\x00\xff\x80'),('PROFILE_JSON_V1','TOTP_SEED','TOTP_BASE32_V1',b'{ "variant":"TOTP_BASE32_V1", "seedBase32":"JBSWY3DPEHPK3PXP", "algorithm":"SHA1", "digits":6, "periodSeconds":30.0 }')]:
 v={'id':vid,'secret_id':sid,'secret_type':typ,'value_representation':kind,'profile_id':profile,'plaintext_byte_length':len(raw),'original_import_bytes_digest':'\\x'+hashlib.sha256(raw).hexdigest(),'canonical_value_digest':'\\x'+canonical_value_digest({'type':typ,'representation':kind,'profileId':profile,'bytes':raw})[7:]}
 snap={'diagnostic':'VALUE_READ_READY','protectedRow':{'version':v}}
 response=reveal_response(snap,raw);valid('response',response);assert copy_revealed_bytes(response)==raw;ok(kind+'-typed-reveal-and-UI-copy-original-byte-exact')
 for label,bad in [('changed-original-bytes',raw+b' '),('missing-original-byte',raw[:-1])]:
  try:reveal_response(snap,bad);raise AssertionError(label+' accepted')
  except ValueError as e:assert str(e)=='SECRET_REVEAL_ORIGINAL_BYTES_MISMATCH';ok(kind+'-'+label)
 changed=copy.deepcopy(response);changed['originalImportBytesDigest']='sha256:'+'00'*32
 try:copy_revealed_bytes(changed);raise AssertionError('copy digest accepted')
 except ValueError as e:assert str(e)=='SECRET_REVEAL_ORIGINAL_BYTES_MISMATCH';ok(kind+'-UI-copy-digest-mismatch')
 if kind=='PROFILE_JSON_V1':
  altered=copy.deepcopy(response);altered['value']['profile']['digits']=8
  try:copy_revealed_bytes(altered);raise AssertionError('different valid profile accepted')
  except ValueError as e:assert str(e)=='SECRET_REVEAL_PROFILE_BYTES_MISMATCH';ok('typed-profile-original-bytes-semantic-identity')
  altered=copy.deepcopy(response);altered['secretType']='PASSWORD'
  try:valid('response',altered);raise AssertionError('wrong Secret type accepted')
  except Exception as e:
   from jsonschema import ValidationError
   assert isinstance(e,ValidationError);ok('typed-profile-Secret-type-binding')
 response['value']['untrustedExtra']=True
 try:valid('response',response);raise AssertionError('extra value field accepted')
 except Exception as e:
  from jsonschema import ValidationError
  assert isinstance(e,ValidationError);ok(kind+'-closed-response-extra-field')
report={'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'consumedSourceDigests':{'contracts/secrets/profile-handoffs.schema.json':resource_index()['contracts/secrets/profile-handoffs.schema.json']['sha256']},'checked':len(cases),'failed':0,'cases':cases,'syntheticValuesOnly':True,'plaintextInReport':False,'scope':'typed transport/native conversion and upstream-open reveal/copy; no auth or SQL audit claim','wholeOperationClosed':False,'implementationAcceptance':'NOT_EVALUATED'}
(OUT/'value-transport-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'transport/reveal/copy PASS')
