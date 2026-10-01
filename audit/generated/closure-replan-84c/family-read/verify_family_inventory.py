import sys,json,hashlib,copy
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');O=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resources,resource_index
from phase1_schema_closure import Inventory
from operation_catalog import catalog
source=SSOT.read_text();delta=json.loads((O/'authorable-delta.json').read_text());rs=resource_index(resources(source));payload=json.loads(rs['contracts/payload-contracts.json']['raw'])
for p in delta['patches']:
 matches=[x for x in payload['records']if x['routeId']==p['routeId']and x['operationId']==p['operationId']];assert len(matches)==1;matches[0].update(p['replace'])
def envelope(path,doc,family='KCML-EMBEDDED'):
 raw=(json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode();return '<!-- '+family+' path="'+path+'" kind="JSON" bytes="'+str(len(raw))+'" sha256="'+hashlib.sha256(raw).hexdigest()+'" encoding="plain" -->\n```json\n'+raw.decode()+'```\n<!-- '+family+'-END -->'
m=rs['contracts/payload-contracts.json']['match'];virtual=source[:m.start()]+envelope('contracts/payload-contracts.json',payload,rs['contracts/payload-contracts.json']['family'])+source[m.end():]+'\n\n'+envelope(delta['newResource'],delta['resource'])+'\n'
reports={}
for name,text in [('before',source),('candidate',virtual)]:
 inv=Inventory(text);ops=catalog(inv.rs);rows=[];operation_refs=[]
 for patch in delta['patches']:
  i=next(i for i,x in enumerate(inv.docs['contracts/payload-contracts.json']['records'])if x['routeId']==patch['routeId'])
  rows.append({'routeId':patch['routeId'],'operationId':patch['operationId'],'boundaries':[inv.boundary(role,'contracts/payload-contracts.json#/records/'+str(i)+'/'+field,'inline')for role,field in [('request','requestSchema'),('response','responseSchema'),('event','eventSchema')]]})
 for oid in sorted({x['operationId']for x in delta['patches']}):
  op=ops[oid]
  for namefield in ['commandSchemaRef','requestSchemaRef','responseSchemaRef','eventSchemaRef']:
   ref=op.get(namefield)
   if isinstance(ref,str):operation_refs.append({'operationId':oid,'field':namefield,'boundary':inv.boundary('native',ref,namefield)})
   elif isinstance(ref,dict)and'schemaId'in ref:operation_refs.append({'operationId':oid,'field':namefield,'boundary':inv.boundary('native',ref['schemaId'],namefield)})
 reports[name]={'routes':rows,'operationNativeRefs':operation_refs,'genericBoundaries':sum(b.get('concreteness')=='GENERIC_ENVELOPE'for row in rows for b in row['boundaries']),'genericRoutes':sum(any(b.get('concreteness')=='GENERIC_ENVELOPE'for b in row['boundaries'])for row in rows),'unresolvedRouteBoundaries':sum(b.get('resolution')!='RESOLVED'for row in rows for b in row['boundaries']),'unresolvedOperationRefs':sum(x['boundary'].get('resolution')!='RESOLVED'for x in operation_refs)}
report={'currentSourceSha256':hashlib.sha256(source.encode()).hexdigest(),'virtualCandidateOnly':True,'canonicalUnchanged':source==SSOT.read_text(),'familyDenominator':{'operations':4,'routes':6,'routeBoundaries':18},'before':reports['before'],'candidate':reports['candidate'],'semanticClosureClaim':False,'eventAuthoritiesNotChanged':True}
(O/'family-inventory-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print({k:{p:v[p]for p in ['genericBoundaries','genericRoutes','unresolvedRouteBoundaries','unresolvedOperationRefs']}for k,v in reports.items()})
