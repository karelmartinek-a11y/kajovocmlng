from pathlib import Path
import sys,json,hashlib,copy
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resources,resource_index,SSOT
from operation_catalog import catalog
OUT=Path(__file__).parent
rs=resource_index(list(resources()));doc=json.loads(rs['contracts/operation-contracts.json']['raw']);ops=catalog(rs)
N='urn:kcml:mcp-native:2026-07-28#/$defs/'
def exact(properties,required):return {'type':'object','properties':properties,'required':required,'additionalProperties':False}
def branch(native,properties,required):return {'allOf':[{'$ref':N+native},exact(properties,required)]}
def alias(op,request,result):
 cp={'jsonrpc':{'const':'2.0'},'id':{'$ref':N+'RequestId'},'method':{'const':request[1]},'params':{'allOf':[{'$ref':N+request[0]+'Params'},exact({k:{} for k in ['_meta',request[2],'inputResponses','requestState']+(['arguments'] if request[2]=='name' else [])},['_meta',request[2]])]}}
 req={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':f'urn:kcml:r9:operation:{op}:command','allOf':[{'$ref':N+request[0]},exact(cp,['jsonrpc','id','method','params'])]}
 common={'jsonrpc':{'const':'2.0'},'id':{'$ref':N+'RequestId'},'result':{}}
 resultkeys=['_meta','resultType']+(['description','messages'] if result=='GetPromptResult' else ['contents','ttlMs','cacheScope'])
 complete={'allOf':[{'$ref':N+result},exact({k:({'const':'complete'} if k=='resultType' else {'$ref':N+'ResultMetaObject'} if k=='_meta' else {}) for k in resultkeys},['resultType']+(['messages'] if result=='GetPromptResult' else ['contents','ttlMs','cacheScope']))]}
 mrtr={'allOf':[{'$ref':N+'InputRequiredResult'},exact({'_meta':{'$ref':N+'ResultMetaObject'},'resultType':{'const':'input_required'},'inputRequests':{},'requestState':{}},['resultType']),{'anyOf':[{'required':['inputRequests']},{'required':['requestState']}]}]}
 err=branch('JSONRPCErrorResponse',{'jsonrpc':{'const':'2.0'},'id':{'$ref':N+'RequestId'},'error':{'properties':{'code':{'not':{'type':'integer','minimum':-32099,'maximum':-32023}}}}},['jsonrpc','error'])
 resp={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':f'urn:kcml:r9:operation:{op}:response','oneOf':[exact({**common,'result':complete},['jsonrpc','id','result']),exact({**common,'result':mrtr},['jsonrpc','id','result']),err]}
 return req,resp
patch=[];defs={};records=[];previous={}
prior=json.loads((OUT/'native-read-schema-definitions.json').read_text()) if (OUT/'native-read-schema-definitions.json').exists() else {}
approved_prior=json.loads((OUT/'native-read-reference-patch.json').read_text()).get('previousPublishedDefinitions',{}) if (OUT/'native-read-reference-patch.json').exists() else {}
for op,request,result in [('mcp.prompts.get',('GetPromptRequest','prompts/get','name'),'GetPromptResult'),('mcp.resources.read',('ReadResourceRequest','resources/read','uri'),'ReadResourceResult')]:
 req,resp=alias(op,request,result)
 for role,s in [('command',req),('response',resp)]:
  key=f'{op}:{role}'
  if key in doc['$defs']:
   if doc['$defs'][key]!=prior.get(key) and doc['$defs'][key]!=s and doc['$defs'][key]!=approved_prior.get(key):raise ValueError('ALIAS_IDENTITY_CONFLICT:'+key)
   previous[key]=doc['$defs'][key]
  defs[key]=s
  patch.append({'op':'add','path':'/$defs/'+key,'value':s})
 records.append({'operationId':op,'operationSourcePointer':ops[op]['sourceRef'],'requestReference':req['$id'],'responseReference':resp['$id'],'nativeRequestPointer':'contracts/mcp/native-2026-07-28.schema.json#/$defs/'+request[0],'nativeCompletePointer':'contracts/mcp/native-2026-07-28.schema.json#/$defs/'+result,'boundaryKind':'RAW_NATIVE_PROTOCOL_2026_07_28_WITH_KNOWN_CORE_RESULT_DISCRIMINATORS','responseMetadataPolicy':'OPTIONAL_NATIVE_METADATA_VALIDATED_IF_PRESENT; separate platform producer specialization','eventApplicability':'UNCHANGED_OPERATION_ADMITTED_STATE_CHANGED_TERMINAL','sourceSections':['10.3','10.4','10.10','10.11','10.14'],'semanticClosure':'NOT_CLOSED','remaining':['Trusted authenticated source/access producer and lifecycle/persistence','Dynamic revision-specific prompt arguments/resource access/MIME binding','MRTR persistent state/context/consume producer and capability negotiation','Event/outbox/audit and consumer fixtures']})
pack={'format':'KCML-MCP-READ-NATIVE-REFERENCE-PATCH/1','pinnedHead':'5ac0a33f3058d9159cf01d7a2168919dea732fea','sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'consumedResources':{p:rs[p]['sha256'] for p in ['contracts/mcp/native-2026-07-28.schema.json','contracts/mcp-native-schema-artifact.json']},'selectedNativeDefinitionSha256':hashlib.sha256(json.dumps(doc['$defs']['mcp.native.2026-07-28'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'selectedOperationSha256':{o:hashlib.sha256(json.dumps({k:v for k,v in ops[o].items() if k!='sourceRef'},sort_keys=True,separators=(',',':')).encode()).hexdigest() for o in ['mcp.prompts.get','mcp.resources.read']},'targetResource':'contracts/operation-contracts.json','jsonPatch':patch,'previousPublishedDefinitions':previous,'previousPublishedDefinitionSha256':{k:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest() for k,v in previous.items()},'operations':records,'entryUnresolvedReferenceUniverse':242,'originalReferenceCorrection':{'before':242,'after':238,'structuralOnly':True},'currentSelectedFamilyMissingAliases':sum(p['path'].split('/',2)[2] not in doc['$defs'] for p in patch),'currentAfterSelectedFamilyMissingAliases':0,'optionalMetadataCorrection':{'affectedResponseSchemas':2,'unresolvedReferenceDelta':0},'operationClosureCount':0,'classification':'EXISTING_PREVIOUSLY_UNCAPTURED_NATIVE_MAPPING','newProductDecision':False,'limits':'Four identity/shape references resolved, no whole operation semantic/runtime closure; no Tasks capability invented, native input_required retained.'}
(OUT/'native-read-reference-patch.json').write_text(json.dumps(pack,indent=2)+'\n')
(OUT/'native-read-schema-definitions.json').write_text(json.dumps(defs,indent=2)+'\n')
