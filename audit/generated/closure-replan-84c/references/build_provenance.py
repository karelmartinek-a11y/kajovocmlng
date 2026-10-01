from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resources,resource_index,SSOT
from operation_catalog import catalog
HERE=Path(__file__).parent;rs=resource_index(list(resources()));c=catalog(rs);native=json.loads(rs['contracts/operation-contracts.json']['raw'])['$defs']['mcp.native.2026-07-28']['$defs'];ls=SSOT.read_text().splitlines();sections={}
for sec in ['10.3','10.4','10.10','10.11','10.14','10.16.1']:
 starts=[i for i,l in enumerate(ls) if l.startswith(('### '+sec+' ','#### '+sec+' '))]
 assert len(starts)==1,(sec,starts)
 i=starts[0];j=next((j for j in range(i+1,len(ls)) if ls[j].startswith(('## ','### ','#### '))),len(ls));text='\n'.join(ls[i:j])+'\n'
 sections[sec]={'sourcePointer':'00_SSOT/KajovoCMLNG_SSOT.md#section.'+sec,'startLine':i+1,'endLine':j,'sha256':hashlib.sha256(text.encode()).hexdigest(),'text':text}
fields=[]
for name in ['GetPromptRequest','GetPromptRequestParams','GetPromptResult','ReadResourceRequest','ReadResourceRequestParams','ReadResourceResult','InputRequiredResult','RequestMetaObject','ResultMetaObject','JSONRPCErrorResponse']:
 d=native[name]
 for k,schema in d.get('properties',{}).items():fields.append({'definition':name,'field':k,'sourcePointer':'contracts/mcp/native-2026-07-28.schema.json#/$defs/'+name+'/properties/'+k,'required':k in d.get('required',[]),'schema':schema,'origin':'NATIVE_PINNED_2026_07_28','semanticAuthority':'10.4' if k in ['id','_meta'] else '10.11' if k in ['inputRequests','inputResponses','requestState'] else '10.14'})
inv=json.loads((ROOT/'audit/phase1-unresolved.json').read_text());unres=[i for i in inv['items'] if i.get('resolution')=='UNRESOLVED'];groups={}
for i in unres:
 op=i['operationId'];family=c[op]['operationFamily'];g=groups.setdefault(family,{'operations':{},'references':0,'status':'BLOCKED','blocker':'EXACT_OPERATION_BOUNDARY_MASK_ABSENT; native artifact or similar entity schema is not interchangeable without producer/consumer mapping'})
 g['references']+=1;g['operations'].setdefault(op,{'source':c[op]['sourceRef'],'authoritySourceRefs':c[op]['authoritySourceRefs'],'references':[]})['references'].append({'role':i['role'],'ref':i['reference']})
json.dump({'status':'STRUCTURAL_INVENTORY','referenceCount':len(unres),'operationCount':len({i['operationId'] for i in unres}),'families':groups},open(HERE/'unresolved-family-packages.json','w'),indent=2)
json.dump({'sections':sections,'fields':fields,'schemaCount':10,'fieldCount':len(fields),'technicalOverlayRules':[{'rule':'Envelope and params permit exactly named native fields; vendor extensions remain _meta','authority':['10.3','10.4'],'classification':'TECHNICAL_EXPLICIT_MASK_DERIVATION'}, {'rule':'Result complete/input_required distinct discriminator, MRTR retains its continuation fields','authority':['10.11','10.14'],'classification':'EXISTING_PREVIOUSLY_UNCAPTURED'}, {'rule':'No task result for resources/read or prompts/get','authority':['10.16.1'],'classification':'EXISTING_PREVIOUSLY_UNCAPTURED'}, {'rule':'Exact request ID JSON type/value and safe no-id parse errors remain distinct','authority':['10.4','10.10'],'classification':'EXISTING_PREVIOUSLY_UNCAPTURED'}]},open(HERE/'source-provenance.json','w'),indent=2)
