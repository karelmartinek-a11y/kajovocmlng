from pathlib import Path
import collections,copy,hashlib,json,sys
ROOT=Path('/workspace/kajovocmlng');OWN=Path(__file__).parent;SOURCE='116e2e50b80b29b957be97a7d89b0b6df959a13fc68e87d6260198e612768bb0';EXECUTION='2227d9d2458609fd0cfc78fff22f6ab1ab34c7709c77e4d3b2fc4c296981ef6a'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 source=ROOT/'00_SSOT/KajovoCMLNG_SSOT.md';assert sha(source)==SOURCE
 sys.path.insert(0,str(ROOT/'scripts'));from ssot_sources import resource_index
 rs=resource_index();mp=ROOT/'audit/phase1-operation-schema-matrix.json';up=ROOT/'audit/phase1-unresolved.json';m=read(mp);u=read(up);assert m['summary']==u['summary'];summary=m['summary'];assert summary['unresolvedOperationReferences']==238 and summary['operationsWithUnresolvedReferences']==119
 assert summary['genericRoutes']==498 and summary['genericBoundaryDefinitions']==1486
 roles=collections.Counter();allroles=collections.Counter();consumed={}
 for op in m['operations']:
  for route in op['routes']:
   for b in route['boundaries']:
    allroles[b['role']]+=1
    if b['concreteness']=='GENERIC_ENVELOPE':roles[b['role']]+=1
    p=b.get('target','').split('#')[0];h=(b.get('source')or{}).get('resourceSha256')
    if p in rs and h:
     assert rs[p]['sha256']==h,(p,h,rs[p]['sha256']);consumed[p]=h
 assert dict(roles)=={'request':494,'response':494,'event':498};assert sum(roles.values())==1486
 cp=OWN/'create-completion/completion-tests.json';completion=read(cp);assert completion['sourceDocumentSha256']==EXECUTION and completion['checked']==449 and completion['failed']==0
 for p,h in completion['resourceSha256'].items():assert rs[p]['sha256']==h
 for p,h in completion['supportSha256'].items():assert sha(ROOT/p)==h
 peer=OWN/'retained-masks/integrated-retained-mask-tests.json';assert read(peer)['sourceSha256']==EXECUTION and read(peer)['checked']==51 and read(peer)['failed']==0
 finite=read(OWN/'finite-package-scope-revalidation.json');assert finite['currentSourceSha256']==EXECUTION
 for entry in finite['comparedSupport']:
  actual=rs[entry['path']]['sha256']if entry['path']in rs else sha(ROOT/entry['path']);assert actual==entry['currentSha256']
 actualrows={x['operationId']:x for x in json.loads(rs['contracts/payload-contracts.json']['raw'])['records']}
 for op,schemas in finite['selectedBoundarySchemaDigests'].items():
  for key,h in schemas.items():assert hashlib.sha256(json.dumps(actualrows[op][key],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==h
 assert rs['contracts/owner-session-family.json']['sha256']==finite['ownerProfileSha256'] and rs['contracts/audit/core-read.schema.json']['sha256']==finite['auditProfileSha256']
 auth=read(ROOT/'audit/generated/closure-replan-84c/authority/classification-proposal.json');quotes=[]
 def walk(v):
  if isinstance(v,dict):
   if isinstance(v.get('quote'),str):quotes.append(v['quote'])
   for x in v.values():walk(x)
  elif isinstance(v,list):
   for x in v:walk(x)
 walk(auth);text=source.read_text();assert all(q in text for q in quotes)
 manifest=json.loads(rs['manifest.json']['raw']);assert manifest['resourceCount']==83
 proof={'status':'CURRENT_BLOCKED_STRUCTURAL_INVENTORY_BOUND_TO_SOURCE','sourceSha256':SOURCE,'sourceStable':sha(source)==SOURCE,'inventoryEvidence':{'matrix':{'path':str(mp.relative_to(ROOT)),'sha256':sha(mp)},'unresolved':{'path':str(up.relative_to(ROOT)),'sha256':sha(up)}},'summary':summary,'genericBoundaryCountsByRole':dict(roles),'actualBoundaryCountsByRole':dict(allroles),'denominatorLimitation':'Role denominators are actual present matrix boundaries, not every542route assumed to define all3 roles. Generic counters are overlapping structural inventories, not semanticclosure.','comparedConsumedResourceSha256':consumed,'freshCreateCompletion':{'path':str(cp.relative_to(ROOT)),'sha256':sha(cp),'executionSourceSha256':EXECUTION,'checked':449,'failed':0,'scope':'Current completion/reference witnesses only, no wholeoperation/persistence/runtime proof'},'freshIndependentRetainedMasks':{'path':str(peer.relative_to(ROOT)),'sha256':sha(peer),'executionSourceSha256':EXECUTION,'checked':51,'failed':0},'metadataScopeRevalidation':{'executionSourceSha256':EXECUTION,'currentSourceSha256':SOURCE,'reason':'Root globalembedded manifest resourceCount76→83 only; actual selected schema/SQL/helper/profile/sourcequote checks repeated','unchangedAuthorityQuotes':len(quotes),'unchangedSupportScopes':len(finite['comparedSupport']),'selectedSchemaHashesMatch':True,'currentManifestResourceCount':83,'noExecutionEvidenceRetag':True},'historicalEvidenceUntouched':True,'SSOT_CONTRACT_READY':'BLOCKED','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 assert proof['sourceStable'];pp=OWN/'current-structural-inventory-binding.json';pp.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');bind={'path':str(pp.relative_to(ROOT)),'sha256':sha(pp),'sourceSha256':SOURCE,'state':'CURRENT_STRUCTURAL_ONLY_NOT_SEMANTIC_CLOSURE'}
 cpath=ROOT/'audit/SSOT_CREATE_CLOSURE_CHECKLIST.json';rpath=ROOT/'audit/SSOT_COMPLETION_REGISTER.json';c=read(cpath);r=read(rpath);before={'checklist':sha(cpath),'register':sha(rpath)};original_entries=copy.deepcopy(r['obligations']);parentstates=[x['state']for x in c['obligations']]
 r.setdefault('historicalStructuralInventories',[]).append({'values':copy.deepcopy(r['structuralInventory']),'previousBinding':r.get('structuralInventoryBinding'),'reason':'Originalaggregate preserved before fresh2227 structuralbinding'})
 r.setdefault('historicalSourceBindings',[]).append({'sourceSha256':r['sourceDocumentSha256'],'reason':'2227→116e metadata scope revalidation; execution2227 proofs preserved'});c.setdefault('historicalSourceBindings',[]).append({'sourceSha256':c['sourceSha256'],'reason':'Globalmanifest resourceCount correction only; exact consumed scopes revalidated'});c['sourceSha256']=r['sourceDocumentSha256']=SOURCE
 for parent in c['obligations']:parent['sourceSha256']=SOURCE;parent['currentInventoryScopeRevalidation']=bind
 for doc,key in [(c,'layeredConditions'),(r,'createOperationLayeredDuties')]:
  doc[key]['sourceSha256']=SOURCE;doc[key]['currentInventoryScopeRevalidation']=bind
  for parent in doc[key]['parents']:
   for condition in parent['conditions']:condition['sourceBinding']['ssotSha256']=SOURCE;condition['sourceBinding']['currentInventoryScopeRevalidation']=bind
 r['structuralInventory']=copy.deepcopy(summary);r['structuralInventoryBinding']=bind;r['structuralInventoryRoleCounts']={'generic':dict(roles),'actualPresent':dict(allroles),'denominatorLimitation':proof['denominatorLimitation']};r['coverage']['unresolvedReferenceObligationsDeduplicatedByOperationAndReference']=238
 r['sourceSnapshot']='Current2227 structuralmatrix/resource scopes, current finite classified packages and14selectedinventory entries bound. Originalremaininginventory rows retain their historical semantic-review/source bindings; no full3897 semanticreview claimed.'
 c['currentStructuralInventory']={'summary':copy.deepcopy(summary),'genericBoundaryCountsByRole':dict(roles),'binding':bind,'notWholeOperationClosure':True}
 for package in r['workPackages']:
  package['sourceBinding']['previousSourceSha256']=package['sourceBinding']['ssotSha256'];package['sourceBinding']['ssotSha256']=SOURCE;package['sourceBinding']['currentInventoryScopeRevalidation']=bind
  if package['id']=='WORK.CREATE.RETAINED_MASKS':
   package['evidence'].append(proof['freshCreateCompletion']);package['coverage']['currentReferenceChecks']=449;package['outputs']['current449And51ExecutionSourceSha256']=EXECUTION;package['verificationMethod']='Freshcurrent449 createcompletion/reference witnesses plus51 independentmask/authoring checks; historicalad98 reports preserved; no retentionproducer/runtime/wholeoperationclosure.'
 r['changedBoundaryEvidenceRequirements'][0]['freshCurrentReferenceCompletion']=proof['freshCreateCompletion'];c['changedBoundaryEvidenceRequirements'][0]['freshCurrentReferenceCompletion']=proof['freshCreateCompletion']
 assert r['obligations']==original_entries and [x['state']for x in c['obligations']]==parentstates and len(c['obligations'])==36
 assert c['sourceSha256']==r['sourceDocumentSha256']==SOURCE and c['wholeOperationsClosed']==[]
 cb=(json.dumps(c,ensure_ascii=False,indent=2)+'\n').encode();r['currentFiniteChecklist']['sha256']=hashlib.sha256(cb).hexdigest();r['currentFiniteChecklist']['structuralInventoryBinding']=bind;cpath.write_bytes(cb);rpath.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 report={'status':'PASS_CURRENT_METRICS_SHARED_INTEGRATION','sourceSha256':SOURCE,'sourceStable':sha(source)==SOURCE,'before':before,'after':{'checklist':sha(cpath),'register':sha(rpath)},'same3897InventoryIdsAndStatesPreserved':True,'same36ParentStatesPreserved':True,'wholeOperationsClosed':0,'genericRoles':dict(roles),'actualRoles':dict(allroles),'references':238,'affectedOperations':119,'genericRoutes':498,'genericBoundaries':1486,'fresh449And51Execution2227ScopedRevalidated116e':True,'oldAggregateValuesAndExecutionProofsPreserved':True,'sharedWritesOnly':['audit/SSOT_CREATE_CLOSURE_CHECKLIST.json','audit/SSOT_COMPLETION_REGISTER.json']};assert report['sourceStable'];(OWN/'current-metrics-integration-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
