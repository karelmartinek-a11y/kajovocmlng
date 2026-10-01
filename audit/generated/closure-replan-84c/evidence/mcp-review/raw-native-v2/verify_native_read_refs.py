from pathlib import Path
import json,sys,copy,hashlib
ROOT=Path('/workspace/kajovocmlng');sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resources,resource_index
from jsonschema import Draft202012Validator,FormatChecker
from referencing import Registry,Resource
from referencing.jsonschema import DRAFT202012
from native_byte_format import install_native_byte_checker
install_native_byte_checker()
HERE=Path(__file__).parent;rs=resource_index(list(resources()));base=json.loads(rs['contracts/operation-contracts.json']['raw']);pack=json.loads((HERE/'native-read-reference-patch.json').read_text());defs=json.loads((HERE/'native-read-schema-definitions.json').read_text())
native=base['$defs']['mcp.native.2026-07-28'];registry=Registry().with_resource('urn:kcml:mcp-native:2026-07-28',Resource.from_contents(native,default_specification=DRAFT202012))
for k,s in defs.items():registry=registry.with_resource(s['$id'],Resource.from_contents(s))
v={k:Draft202012Validator(s,registry=registry,format_checker=FormatChecker()) for k,s in defs.items()};checks=[]
def check(name,condition):
 checks.append({'id':name,'status':'PASS' if condition else 'FAIL'})
 if not condition:raise AssertionError(name)
def mutate(value,path,new=None,remove=False):
 value=copy.deepcopy(value);p=value
 for k in path[:-1]:p=p[k]
 if remove:del p[path[-1]]
 else:p[path[-1]]=new
 return value
meta={'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientCapabilities':{}}
fixtures={}
for op,method,key,target,result in [('mcp.prompts.get','prompts/get','name','fixture-prompt',{'resultType':'complete','_meta':{'io.modelcontextprotocol/serverInfo':{'name':'synthetic-server','version':'fixture-1'}},'messages':[{'role':'user','content':{'type':'text','text':'synthetic: preserve whitespace  '}}]}),('mcp.resources.read','resources/read','uri','fixture://synthetic/resource',{'resultType':'complete','_meta':{},'contents':[{'uri':'fixture://synthetic/resource','mimeType':'text/plain','text':'  synthetic\n'}],'ttlMs':0,'cacheScope':'private'})]:
 req={'jsonrpc':'2.0','id':7,'method':method,'params':{'_meta':copy.deepcopy(meta),key:target}};resp={'jsonrpc':'2.0','id':7,'result':result};fixtures[op]={'request':req,'response':resp}
 check(op+'.positive.request',v[op+':command'].is_valid(req));check(op+'.positive.complete',v[op+':response'].is_valid(resp))
 mrtr={'jsonrpc':'2.0','id':7,'result':{'resultType':'input_required','_meta':{},'requestState':'synthetic-opaque-exact-token'}}
 check(op+'.positive.MRTR',v[op+':response'].is_valid(mrtr))
 check(op+'.positive.raw_complete_without_meta',v[op+':response'].is_valid(mutate(resp,['result','_meta'],remove=True)))
 check(op+'.positive.raw_MRTR_without_meta',v[op+':response'].is_valid(mutate(mrtr,['result','_meta'],remove=True)))
 check(op+'.negative.raw_MRTR_invalid_present_meta',not v[op+':response'].is_valid(mutate(mrtr,['result','_meta'],None)))
 err={'jsonrpc':'2.0','id':7,'error':{'code':-32602,'message':'Synthetic invalid parameter'}}
 check(op+'.positive.error',v[op+':response'].is_valid(err))
 for label,path,value,remove in [('missing_target',['params',key],None,True),('null_target',['params',key],None,False),('numeric_target',['params',key],1,False),('unknown_param',['params','extra'],True,False),('unknown_envelope',['extra'],True,False),('missing_metadata',['params','_meta'],None,True),('missing_capabilities',['params','_meta','io.modelcontextprotocol/clientCapabilities'],None,True),('boolean_ID',['id'],True,False),('wrong_method',['method'],'tools/list',False)]:
  check(op+'.negative.'+label,not v[op+':command'].is_valid(mutate(req,path,value,remove)))
 for label,path,value,remove in [('missing_resultType',['result','resultType'],None,True),('unknown_resultType',['result','resultType'],'future_unknown',False),('task_for_non_tool',['result','resultType'],'task',False),('unknown_output',['result','extra'],True,False),('both_result_error',['error'],{'code':-32602,'message':'bad'},False),('invalid_present_result_meta',['result','_meta'],None,False)]:
  check(op+'.negative.'+label,not v[op+':response'].is_valid(mutate(resp,path,value,remove)))
 check(op+'.negative.MRTR_missing_state_and_requests',not v[op+':response'].is_valid(mutate(mrtr,['result','requestState'],remove=True)))
 check(op+'.negative.reserved_undefined_error',not v[op+':response'].is_valid(mutate(err,['error','code'],-32023)))
platform_schema={'$schema':'https://json-schema.org/draft/2020-12/schema','allOf':[{'$ref':'urn:kcml:r9:operation:mcp.prompts.get:response'},{'properties':{'result':{'properties':{'resultType':{'const':'complete'},'_meta':{'required':['io.modelcontextprotocol/serverInfo']}},'required':['_meta','resultType']}},'required':['result']}]}
platform=Draft202012Validator(platform_schema,registry=registry,format_checker=FormatChecker())
check('prompt.platform_producer.positive_serverInfo',platform.is_valid(fixtures['mcp.prompts.get']['response']))
missing_metadata=mutate(fixtures['mcp.prompts.get']['response'],['result','_meta','io.modelcontextprotocol/serverInfo'],remove=True)
check('prompt.native_wire.positive_omitted_optional_serverInfo',v['mcp.prompts.get:response'].is_valid(missing_metadata))
check('prompt.platform_producer.negative_missing_serverInfo',not platform.is_valid(missing_metadata))
check('prompt.platform_producer.negative_missing_meta',not platform.is_valid(mutate(fixtures['mcp.prompts.get']['response'],['result','_meta'],remove=True)))
resource_platform_schema=copy.deepcopy(platform_schema)
resource_platform_schema['allOf'][0]['$ref']='urn:kcml:r9:operation:mcp.resources.read:response'
resource_platform_schema['allOf'][1]['properties']['result']['properties']['_meta']={'$ref':'urn:kcml:mcp-native:2026-07-28#/$defs/ResultMetaObject'}
resource_platform=Draft202012Validator(resource_platform_schema,registry=registry,format_checker=FormatChecker())
check('resource.platform_producer.positive_metadata',resource_platform.is_valid(fixtures['mcp.resources.read']['response']))
check('resource.platform_producer.negative_missing_metadata',not resource_platform.is_valid(mutate(fixtures['mcp.resources.read']['response'],['result','_meta'],remove=True)))
(HERE/'platform-complete.specializations.proposed.schema.json').write_text(json.dumps({'specializations':{'mcp.prompts.get':platform_schema,'mcp.resources.read':resource_platform_schema},'authority':['SSOT10.4','SSOT10.14'],'status':'UNBOUND_PRODUCER_SPECIALIZATION_FOR_COORDINATOR_REVIEW','nativeExternalCompatibility':'UNCHANGED_OPTIONAL_RESULT_METADATA','changesNativeAliases':False},indent=2)+'\n')
# Exercise actual binary resource content boundary; byte checker cannot silently ignore format.
resource=fixtures['mcp.resources.read']['response'];blob=mutate(resource,['result','contents'],[{'uri':'fixture://synthetic/resource','blob':'AAE=','mimeType':'application/octet-stream'}])
check('resource.positive.base64_blob',v['mcp.resources.read:response'].is_valid(blob))
for label,value in [('malformed','%%%'),('bad_padding','a'),('whitespace','AA E='),('nonascii','ž')]:
 check('resource.negative.base64_'+label,not v['mcp.resources.read:response'].is_valid(mutate(blob,['result','contents',0,'blob'],value)))
# Cross-message ID binding is outside JSON Schema: exact type matters.
def echo(request,response):
 if 'id' not in response:raise ValueError('MCP_RESPONSE_ID_MISSING_FOR_KNOWN_REQUEST')
 if type(request['id']) is not type(response['id']) or request['id']!=response['id']:raise ValueError('MCP_RESPONSE_ID_MISMATCH')
for op,fx in fixtures.items():
 echo(fx['request'],fx['response']);check(op+'.positive.exact_ID',True)
 for label,value in [('string_ID','7'),('different_ID',8)]:
  bad=mutate(fx['response'],['id'],value)
  check(op+'.mismatch_schema_still_valid.'+label,v[op+':response'].is_valid(bad))
  try:echo(fx['request'],bad)
  except ValueError as e:check(op+'.negative.'+label,str(e)=='MCP_RESPONSE_ID_MISMATCH')
  else:check(op+'.negative.'+label,False)
# No query/body wire inference: this package addresses JSON-RPC native bodies only.
# Actual registry bytes enforce exact revision-specific prompt arguments, never a caller flag.
prompt_schema={'type':'object','properties':{'topic':{'type':'string'}},'required':['topic'],'additionalProperties':False}
artifact=json.dumps(prompt_schema,sort_keys=True,separators=(',',':')).encode();expected=hashlib.sha256(artifact).hexdigest()
def arguments(raw,digest,args):
 if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('PROMPT_REVISION_DIGEST_MISMATCH')
 if not Draft202012Validator(json.loads(raw)).is_valid(args):raise ValueError('PROMPT_ARGUMENT_CONTRACT_INVALID')
arguments(artifact,expected,{'topic':' synthetic '});check('prompt.positive.loaded_immutable_schema',True)
for label,args in [('missing',{}),('unknown',{'topic':'ok','extra':'x'}),('null',{'topic':None})]:
 try:arguments(artifact,expected,args)
 except ValueError as e:check('prompt.negative.'+label,str(e)=='PROMPT_ARGUMENT_CONTRACT_INVALID')
 else:check('prompt.negative.'+label,False)
try:arguments(artifact+b' ',expected,{'topic':'ok'})
except ValueError as e:check('prompt.negative.changed_bytes',str(e)=='PROMPT_REVISION_DIGEST_MISMATCH')
# Actual JSON decoder rejects duplicate keys before native schema validation.
def decode(raw):
 def pairs(values):
  out={}
  for key,value in values:
   if key in out:raise ValueError('MCP_DUPLICATE_JSON_KEY')
   out[key]=value
  return out
 return json.loads(raw,object_pairs_hook=pairs)
check('decoder.positive',decode(json.dumps(fixtures['mcp.prompts.get']['request']))==fixtures['mcp.prompts.get']['request'])
for name,raw in [('duplicate_ID','{"id":1,"id":2}'),('duplicate_argument','{"params":{"arguments":{"topic":"a","topic":"b"}}}')]:
 try:decode(raw)
 except ValueError as e:check('decoder.negative.'+name,str(e)=='MCP_DUPLICATE_JSON_KEY')
try:decode('{')
except json.JSONDecodeError:check('decoder.negative.malformed_JSON',True)
report={'status':'PASS','scope':'REFERENCE_SCHEMA_AND_CROSS_MESSAGE_GUARDS_ONLY','checks':checks,'passed':len(checks),'failed':0,'consumedResources':pack['consumedResources'],'schemaDefinitionSha256':hashlib.sha256((HERE/'native-read-schema-definitions.json').read_bytes()).hexdigest(),'operationClosureCount':0,'limitations':['Synthetic prompt registry is not runtime registry publisher evidence','No transport HTTP, access-authority, persistence, MRTR cryptography or external runtime proof','Four reference definitions only; event and whole-operation obligations unchanged']}
(HERE/'native-read-reference-tests.json').write_text(json.dumps(report,indent=2)+'\n');(HERE/'positive-witnesses.json').write_text(json.dumps(fixtures,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(checks),'wholeOperationClosureCount':0}))
