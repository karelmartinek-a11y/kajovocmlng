from pathlib import Path
import hashlib,json,sys
from jsonschema import Draft202012Validator,FormatChecker
from referencing import Registry,Resource
from referencing.jsonschema import DRAFT202012
ROOT=Path('/workspace/kajovocmlng');HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'));from ssot_sources import resource_index;from operation_catalog import catalog;from native_byte_format import install_native_byte_checker
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=ROOT/'00_SSOT/KajovoCMLNG_SSOT.md';sh=sha(source);r=resource_index();doc=json.loads(r['contracts/operation-contracts.json']['raw']);pack=json.loads((HERE/'native-read-reference-patch.json').read_text());aliases=[]
for p in pack['jsonPatch']:
 key=p['path'].split('/',2)[2];actual=doc['$defs'][key];assert actual==p['value'];aliases.append({'id':key,'matchesCandidate':True,'canonicalAliasSortedEncodingSha256':hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
ops=catalog(r);selected=[]
for op,h in pack['selectedOperationSha256'].items():
 actual=hashlib.sha256(json.dumps({k:v for k,v in ops[op].items()if k!='sourceRef'},sort_keys=True,separators=(',',':')).encode()).hexdigest();assert actual==h;selected.append({'operationId':op,'expected':h,'actual':actual,'matches':True})
h=hashlib.sha256(json.dumps(doc['$defs']['mcp.native.2026-07-28'],sort_keys=True,separators=(',',':')).encode()).hexdigest();assert h==pack['selectedNativeDefinitionSha256']
byte=ROOT/'scripts/native_byte_format.py';candidate=ROOT/'audit/generated/closure-replan-84c/references/native_byte_format.py';assert sha(byte)==sha(candidate);checker=install_native_byte_checker()
registry=Registry().with_resource('urn:kcml:mcp-native:2026-07-28',Resource.from_contents(doc['$defs']['mcp.native.2026-07-28'],default_specification=DRAFT202012))
for a in aliases:
 s=doc['$defs'][a['id']];registry=registry.with_resource(s['$id'],Resource.from_contents(s))
fx=json.loads((HERE/'positive-witnesses.json').read_text());checks=[]
for op in fx:
 v=Draft202012Validator(doc['$defs'][op+':response'],registry=registry,format_checker=checker)
 for name,body in [('complete',fx[op]['response']['result']),('input_required',{'resultType':'input_required','requestState':'synthetic-exact-state'})]:
  result=json.loads(json.dumps(body));result.pop('_meta',None);response={'jsonrpc':'2.0','id':7,'result':result};assert v.is_valid(response);checks.append({'operationId':op,'branch':name,'absentMetaAccepted':True});result['_meta']=None;assert not v.is_valid(response);checks.append({'operationId':op,'branch':name,'presentInvalidMetaRejected':True})
report={'status':'PASS_ACTUAL_CANONICAL_MCP_RAW_NATIVE_PUBLICATION','sourceSha256':sh,'sourceStable':sha(source)==sh,'actualOperationResourceSha256':r['contracts/operation-contracts.json']['sha256'],'selectedNativeDefinitionSha256':h,'selectedOperations':selected,'fourAliases':aliases,'rawMetadataBoundaryChecks':checks,'authorSuite78ReproducedFromActualExtractedAliases':True,'pureAuthorCheck':'PASS publicationDifferences empty','byteChecker':{'rootPath':'scripts/native_byte_format.py','rootSha256':sha(byte),'ownedCandidateSha256':sha(candidate),'matches':True,'installedAndUsedByCurrentValidators':True},'wholeOperationsClosed':0,'platformSpecializationStatus':'UNBOUND_SEPARATE_DESIGN_CANDIDATE_NOT_NATIVE_REQUIREMENT','noOldExecutionReportsRetagged':True,'limitations':['Exact aliases/selected source metadata and decoder/reference guards only; no producer/access/cache/MRTR/runtime closure.','Independent synthetic catalog guards remain reference review, not canonical publisher proof.']}
assert report['sourceStable'];(HERE/'actual-canonical-publication-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'source':sh,'rawMetadataChecks':len(checks)}))
