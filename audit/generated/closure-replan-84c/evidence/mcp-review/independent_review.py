from pathlib import Path
import copy,hashlib,json,sys
from jsonschema import Draft202012Validator,FormatChecker
from referencing import Registry,Resource
from referencing.jsonschema import DRAFT202012
ROOT=Path('/workspace/kajovocmlng');HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index
source=ROOT/'00_SSOT/KajovoCMLNG_SSOT.md';sourcehash=hashlib.sha256(source.read_bytes()).hexdigest();rs=resource_index();pack=json.loads((HERE/'native-read-reference-patch.json').read_text());native=json.loads(rs['contracts/mcp/native-2026-07-28.schema.json']['raw']);defs=json.loads((HERE/'native-read-schema-definitions.json').read_text());fx=json.loads((HERE/'positive-witnesses.json').read_text());checks=[]
registry=Registry().with_resource('urn:kcml:mcp-native:2026-07-28',Resource.from_contents(native,default_specification=DRAFT202012))
for s in defs.values():registry=registry.with_resource(s['$id'],Resource.from_contents(s))
v={k:Draft202012Validator(s,registry=registry,format_checker=FormatChecker())for k,s in defs.items()}
def test(id,condition):
 checks.append({'id':id,'status':'PASS'if condition else 'FAIL'});assert condition,id
for op in fx:
 test(op+'.baseline.actual_native_request',v[op+':command'].is_valid(fx[op]['request']));test(op+'.baseline.actual_native_response',v[op+':response'].is_valid(fx[op]['response']))
 test(op+'.single_wire.no_platform_wrapper',not v[op+':command'].is_valid({'request':fx[op]['request']}))
 test(op+'.single_wire.no_double_rpc_wrapper',not v[op+':response'].is_valid({'jsonrpc':'2.0','id':7,'result':fx[op]['response']}))
 bad=copy.deepcopy(fx[op]['response']);bad['result']['resultType']='task';test(op+'.task_not_negotiated_non_tool_rejected',not v[op+':response'].is_valid(bad))
r=copy.deepcopy(fx['mcp.resources.read']['request']);r['params']['uri']='not a URI';test('resource.bad_uri_encoding.native_format_rejected',not v['mcp.resources.read:command'].is_valid(r))
r['params']['uri']='fixture://synthetic/foreign';test('resource.unknown_registered_uri.shape_only_accepts',v['mcp.resources.read:command'].is_valid(r))
p=copy.deepcopy(fx['mcp.prompts.get']['request']);p['params']['name']='unknown-prompt';test('prompt.unknown_name.shape_only_accepts',v['mcp.prompts.get:command'].is_valid(p))
# Independent bounded review guards load actual immutable catalog/schema bytes.
# These are review fixtures, not authoritative publisher/admission/runtime implementations.
schema={'type':'object','properties':{'topic':{'type':'string','minLength':1}},'required':['topic'],'additionalProperties':False}
catalog={'promptName':'fixture-prompt','resourceUri':'fixture://synthetic/resource','mimeType':'text/plain','argumentSchema':schema,'revision':3}
raw=json.dumps(catalog,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode();digest=hashlib.sha256(raw).hexdigest()
def load(bytes_,expected):
 if hashlib.sha256(bytes_).hexdigest()!=expected:raise ValueError('MCP_REGISTRY_REVISION_DIGEST_MISMATCH')
 return json.loads(bytes_)
def prompt(req,bytes_=raw,expected=digest):
 c=load(bytes_,expected)
 if req['params']['name']!=c['promptName']:raise ValueError('MCP_PROMPT_NOT_FOUND')
 if not Draft202012Validator(c['argumentSchema']).is_valid(req['params'].get('arguments',{})):raise ValueError('MCP_PROMPT_ARGUMENT_INVALID')
def resource(req,response,bytes_=raw,expected=digest):
 c=load(bytes_,expected)
 if req['params']['uri']!=c['resourceUri']:raise ValueError('MCP_RESOURCE_NOT_FOUND')
 for content in response['result']['contents']:
  if content['uri']!=c['resourceUri']:raise ValueError('MCP_RESOURCE_CONTENT_URI_MISMATCH')
  if content['mimeType']!=c['mimeType']:raise ValueError('MCP_RESOURCE_CONTENT_MIME_MISMATCH')
def identity(req,resp):
 if type(req['id'])is not type(resp.get('id'))or req['id']!=resp.get('id'):raise ValueError('MCP_RESPONSE_ID_MISMATCH')
def rejects(id,expected,fn):
 try:fn()
 except ValueError as e:test(id,str(e)==expected)
 else:test(id,False)
p=copy.deepcopy(fx['mcp.prompts.get']['request']);p['params']['arguments']={'topic':'  synthetic exact whitespace  '};prompt(p);test('review.prompt.valid_domain_witness',True)
r=copy.deepcopy(fx['mcp.resources.read']['request']);resp=copy.deepcopy(fx['mcp.resources.read']['response']);resource(r,resp);test('review.resource.valid_domain_witness',True)
b=copy.deepcopy(p);b['params']['name']='unknown-prompt';rejects('review.unknown_prompt.exact_rejection','MCP_PROMPT_NOT_FOUND',lambda:prompt(b))
b=copy.deepcopy(r);b['params']['uri']='fixture://synthetic/foreign';rejects('review.wrong_uri.exact_rejection','MCP_RESOURCE_NOT_FOUND',lambda:resource(b,resp))
for name,args in [('missing',{}),('unknown',{'topic':'ok','extra':'x'}),('wrong_type',{'topic':False}),('null',{'topic':None})]:
 b=copy.deepcopy(p);b['params']['arguments']=args;rejects('review.prompt.arguments.'+name,'MCP_PROMPT_ARGUMENT_INVALID',lambda:prompt(b))
rejects('review.digest.actual_bytes_mutation','MCP_REGISTRY_REVISION_DIGEST_MISMATCH',lambda:prompt(p,raw+b' '))
for name,value in [('wrong_uri','fixture://synthetic/foreign'),('wrong_mime','text/html')]:
 b=copy.deepcopy(resp);b['result']['contents'][0]['uri'if name=='wrong_uri'else'mimeType']=value;rejects('review.resource.'+name,'MCP_RESOURCE_CONTENT_URI_MISMATCH'if name=='wrong_uri'else'MCP_RESOURCE_CONTENT_MIME_MISMATCH',lambda:resource(r,b))
for name,value in [('different_type','7'),('different_value',8),('bool',True)]:
 b=copy.deepcopy(resp);b['id']=value;rejects('review.message_identity.'+name,'MCP_RESPONSE_ID_MISMATCH',lambda:identity(r,b))
for field,value in [('ttlMs',-1),('ttlMs',True),('cacheScope','shared')]:
 b=copy.deepcopy(resp);b['result'][field]=value;test('resource.cache_invalid.'+field+'.'+str(value),not v['mcp.resources.read:response'].is_valid(b))
test('resource.exact_text_preserved',resp['result']['contents'][0]['text']=='  synthetic\n')
report={'status':'PASS_BOUNDED_ALIAS_REVIEW','sourceSha256':sourcehash,'sourceStable':hashlib.sha256(source.read_bytes()).hexdigest()==sourcehash,'author61Reproduced':True,'checks':checks,'passed':len(checks),'consumedResources':{k:{'candidateRecordedSha256':h,'actualSha256':rs[k]['sha256'],'matches':h==rs[k]['sha256']}for k,h in pack['consumedResources'].items()},'nativeAliasDecision':'APPROVE_FOUR_IDENTITY_AND_WIRE_SHAPE_ALIASES_ONLY','nativeDefinitionsDirectlyReferenced':True,'wholeOperationsClosed':0,'technicalMappingClassification':'EXISTING_PREVIOUSLY_UNCAPTURED_NATIVE_MAPPING_NOT_NEW_PRODUCT_SCOPE','remaining':['Dynamic trusted catalog/access publisher and exact registered prompt/resource identities; unknown names/registered URIs are intentionally outside shape aliases','Prompt renderer must emit required server identity metadata under platform §10.14; external native parser diagnostic metadata optionality is not authority','Actual MRTR state producer/capability negotiation and cache/access-context consumer persistence remain open','Review catalog guards are isolated synthetic domain witnesses, not canonical publisher/runtime proof'],'oldFixtureRetagged':False}
assert report['sourceStable'];(HERE/'independent-alias-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'independentChecks':len(checks),'sourceStable':report['sourceStable']}))
