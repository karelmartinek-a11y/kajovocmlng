import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_schema_closure import Inventory
from author_native_read_refs import apply
from native_byte_format import install_native_byte_checker
install_native_byte_checker()
HERE=Path(__file__).parent
baseline=json.loads((ROOT/'audit/phase1-unresolved.json').read_text());refs=[x for x in baseline['items'] if x.get('resolution')=='UNRESOLVED'];text=SSOT.read_text();rs=resource_index(list(resources(text)));doc=json.loads(rs['contracts/operation-contracts.json']['raw']);pack=json.loads((HERE/'native-read-reference-patch.json').read_text());reconstructed=False
for p in pack['jsonPatch']:
 key=p['path'].split('/',2)[2]
 if key in doc['$defs']:
  if doc['$defs'][key]!=p['value'] and doc['$defs'][key]!=pack.get('previousPublishedDefinitions',{}).get(key):raise ValueError('ALIAS_RECONSTRUCTION_CONFLICT:'+key)
  del doc['$defs'][key];reconstructed=True
before_text=rewrite(text,list(resources(text)),{'contracts/operation-contracts.json':(json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode()}) if reconstructed else text
before=Inventory(before_text);after=Inventory(apply(text));records=[]
for x in refs:
 row={'operationId':x['operationId'],'role':x['role'],'reference':x['reference']}
 for name,inv in [('before',before),('after',after)]:
  try:p,q,s=inv.resolve(x['reference']);row[name]={'resolution':'RESOLVED','pointer':p+'#'+q}
  except ValueError as e:row[name]={'resolution':'UNRESOLVED','reason':str(e)}
 records.append(row)
changed=[r for r in records if r['before']['resolution']!=r['after']['resolution']];expected={'mcp.prompts.get','mcp.resources.read'}
assert len(changed)==4 and {r['operationId'] for r in changed}==expected
boundaries=[after.boundary(r['role'],r['reference'],'native alias') for r in changed]
assert all(b['resolution']=='RESOLVED' and not b.get('nestedReferenceFailures') for b in boundaries)
report={'status':'PASS','sourceSha256':hashlib.sha256(text.encode()).hexdigest(),'baselineMode':'RECONSTRUCTED_PRE_PUBLICATION_REMOVES_ONLY_FOUR_KNOWN_ALIASES' if reconstructed else 'ACTUAL_PRE_PUBLICATION_SOURCE','referenceUniverse':len(refs),'beforeUnresolved':sum(r['before']['resolution']=='UNRESOLVED' for r in records),'afterUnresolved':sum(r['after']['resolution']=='UNRESOLVED' for r in records),'changes':changed,'resolvedBoundaries':boundaries,'unchangedReferenceCount':len(refs)-len(changed),'semanticClosureCount':0,'limitations':'Resolve/integrity/structure only, no semantic certification; excludes concurrent coordinator family edits by exact target resource precondition'}
(HERE/'inventory-delta.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','referenceUniverse','beforeUnresolved','afterUnresolved','semanticClosureCount']}))
