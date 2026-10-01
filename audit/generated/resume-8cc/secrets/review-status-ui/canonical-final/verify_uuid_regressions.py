from pathlib import Path
import sys,json,hashlib
OUT=Path(__file__).parent;ROOT=Path('/workspace/kajovocmlng');sys.path[:0]=[str(OUT),str(ROOT/'scripts')]
from ssot_sources import SSOT,resource_index
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
from secret_metadata_status_read import decode_metadata_read
from secret_value_read_transport import decode_value_read,decode_http_value_read
source=hashlib.sha256(SSOT.read_bytes()).hexdigest();resources=resource_index();checks=[];bindings={}
u='abcdef12-3456-4789-8abc-abcdef123456'
def ok(i,d=None):checks.append({'id':i,'status':'PASS','diagnostic':d})
def reject(v,x,i):
 try:v.validate(x)
 except ValidationError as e:assert e.validator in ('pattern','format');ok(i,e.validator);return
 raise AssertionError(i+' accepted')
for filename,res in [('secret-metadata-read.schema.json','contracts/secrets/metadata-read.schema.json'),('secret-value-read.schema.json','contracts/secrets/owner-value-read.schema.json')]:
 raw=(OUT/filename).read_bytes();assert raw==resources[res]['raw'];bindings[res]=hashlib.sha256(raw).hexdigest();s=json.loads(raw)
 def walk(x,p=''):
  if isinstance(x,dict):
   if x.get('format')=='uuid':
    v=Draft202012Validator({'$defs':s.get('$defs',{}),**x},format_checker=FormatChecker());v.validate(u);ok(filename+p+'/lowercase-positive')
    for label,bad in [('uppercase',u.upper()),('trailing-newline',u+'\n'),('leading-space',' '+u),('invalid-character',u[:-1]+'g')]:reject(v,bad,filename+p+'/'+label)
   if 'anyOf'in x and any(isinstance(t,dict)and t.get('format')=='uuid'for t in x['anyOf']) and any(t.get('type')=='null'for t in x['anyOf']if isinstance(t,dict)):
    v=Draft202012Validator({'$defs':s.get('$defs',{}),**x},format_checker=FormatChecker());v.validate(None);ok(filename+p+'/explicit-null-preserved')
   for k,z in x.items():walk(z,p+'/'+k)
  elif isinstance(x,list):
   for i,z in enumerate(x):walk(z,p+'/'+str(i))
 walk(s)
# Native decoders tested on the same valid domain-shaped request, changing only UUID spelling.
assert decode_metadata_read('GET',{'id':u},b'',b'')['secretId']==u;ok('native-metadata-lowercase-positive')
assert decode_value_read('GET',{'id':u},[('versionId',u)],b'')['selector']['versionId']==u;ok('native-value-history-lowercase-positive')
assert decode_http_value_read('GET',{'id':u},('versionId='+u).encode(),b'')['selector']['versionId']==u;ok('HTTP-value-history-lowercase-positive')
for label,bad in [('uppercase',u.upper()),('trailing-newline',u+'\n'),('leading-space',' '+u),('invalid-character',u[:-1]+'g')]:
 for name,call,code in [('metadata-path',lambda:decode_metadata_read('GET',{'id':bad},b'',b''),'SECRET_METADATA_READ_PATH_INVALID'),('value-path',lambda:decode_value_read('GET',{'id':bad},[],b''),'SECRET_VALUE_READ_PATH_INVALID'),('value-query',lambda:decode_value_read('GET',{'id':u},[('versionId',bad)],b''),'SECRET_VALUE_READ_VERSION_INVALID'),('HTTP-value-query',lambda:decode_http_value_read('GET',{'id':u},('versionId='+bad.replace('\n','%0A').replace(' ','%20')).encode(),b''),'SECRET_VALUE_READ_VERSION_INVALID')]:
  try:call()
  except ValueError as e:assert str(e)==code,(name,str(e));ok(name+'/'+label,code);continue
  raise AssertionError(name+'/'+label+' accepted')
assert source==hashlib.sha256(SSOT.read_bytes()).hexdigest()
report={'sourceSha256':source,'sourceUnchanged':True,'consumedSourceDigests':bindings,'checked':len(checks),'failed':0,'cases':checks,'scope':'All explicit UUID schema nodes in exact canonical metadata/value read schemas; positive-derived spelling violations, nullable fields and native HTTP/path/query agreement. No runtime application acceptance.','implementationAcceptance':'NOT_EVALUATED'}
(OUT/'uuid-regressions.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checks),'canonical UUID regressions PASS')
