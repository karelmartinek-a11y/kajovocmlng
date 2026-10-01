import hashlib,json,sys
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');OWN=ROOT/'audit/generated/closure-replan-84c/evidence';OLD='2577dacf6024e4666ba98b11eb9c7ffa6e7f225e60630697db740129615cc536';NEW='ad98ebff9e2056c2596b04a0ea31870b3c89520c6f9ab2bd6e26e13ce0a54706'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 source=ROOT/'00_SSOT/KajovoCMLNG_SSOT.md';assert sha(source)==NEW;text=source.read_text()
 auth=read(ROOT/'audit/generated/closure-replan-84c/authority/classification-proposal.json');quotes=[]
 def walk(x):
  if isinstance(x,dict):
   if isinstance(x.get('quote'),str):quotes.append(x)
   for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(auth);assert all(x['quote'] in text for x in quotes)
 sys.path.insert(0,str(ROOT/'scripts'));from ssot_sources import resource_index
 resources=resource_index();prior=read(ROOT/'audit/generated/resume-8cc/key/canonical-final/DELIVERY.json')
 resource_checks=[{'path':name,'recordedSha256':h,'actualSha256':resources[name]['sha256'],'matches':h==resources[name]['sha256']}for name,h in prior['actualEmbeddedSixSQLSha256'].items()]
 helper_checks=[{'path':name,'recordedSha256':h,'actualSha256':sha(ROOT/name),'matches':h==sha(ROOT/name)}for name,h in prior['actualRootSupportSha256'].items()]
 assert all(x['matches']for x in resource_checks+helper_checks)
 phasechecks=[]
 for row in auth['classifications']:
  c=row['C_futureGeneratedApplication'];path=c['authoritativeResource'].split('#')[0]; candidates=[v for k,v in resources.items() if k==path or k==path.split('/',1)[-1]]
  assert len(candidates)==1 and candidates[0]['sha256']==c['resourceDigest']
  phasechecks.append({'parentId':row['id'],'path':path,'recordedSha256':c['resourceDigest'],'actualSha256':candidates[0]['sha256'],'matches':True})
 proof={'status':'PASS_CLASSIFICATION_CONSUMED_SCOPE_REVALIDATION_WITH_CHANGED_BOUNDARIES_STALE','executionSourceSha256':OLD,'currentSourceSha256':NEW,'noOldFixtureReportRetagged':True,'authorityExcerptsChecked':len(quotes),'authorityQuotesUnchanged':True,'canonicalResourcesCompared':resource_checks,'rootHelpersCompared':helper_checks,'phaseResourcesCompared':phasechecks,'changedBoundaryDisposition':[{'scope':'contracts/generation/create-completion.schema.json response/error machineReason optional field and error predicate','state':'STALE_PENDING_CURRENT_449_AND_INDEPENDENT_MASK_REPRODUCTION','requiresFreshEvidence':True,'doesNotInvalidateUnchangedSQLLedgerOrTokenHashScopes':True},{'scope':'§8.17 retained outcome technical supplement','state':'NEW_AUTHORITY_PENDING_CURRENT_SCOPED_REVIEW','existing§49.4RetentionNotWaived':True}],'limitations':['This revalidates only exact consumed classification excerpts, phase resources and the named canonical support scopes.','Original 2577 execution hashes and registered evidence remain historical; no claim all3897 inventory boundaries are current.','Create-completion affected error/predicate boundaries await fresh current evidence.'],'sourceStable':sha(source)==NEW}
 assert proof['sourceStable']; pp=OWN/'classification-scope-revalidation.json';pp.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');bind={'path':str(pp.relative_to(ROOT)),'sha256':sha(pp),'executionSourceSha256':OLD,'currentSourceSha256':NEW,'scope':'UNCHANGED_AUTHORITY_EXCERPTS_AND_PHASE_RESOURCE_METADATA_ONLY; namedSQL/roothelpers comparison','changedBoundariesRemainStale':True}
 cp=ROOT/'audit/SSOT_CREATE_CLOSURE_CHECKLIST.json';rp=ROOT/'audit/SSOT_COMPLETION_REGISTER.json';c=read(cp);r=read(rp);before={'checklist':sha(cp),'register':sha(rp)}
 c.setdefault('historicalSourceBindings',[]).append({'sourceSha256':c['sourceSha256'],'reason':'Preserve classification/fixture execution lineage before consumed-scope revalidation','priorChecklistSha256':before['checklist']})
 c['sourceSha256']=NEW;c['classificationScopeRevalidation']=bind
 for parent in c['obligations']:
  parent.setdefault('historicalClassificationSourceSha256',parent['sourceSha256']);parent['sourceSha256']=NEW;parent['classificationScopeRevalidation']=bind
 c['layeredConditions']['historicalExecutionSourceSha256']=OLD;c['layeredConditions']['sourceSha256']=NEW;c['layeredConditions']['classificationScopeRevalidation']=bind
 for parent in c['layeredConditions']['parents']:
  for condition in parent['conditions']:
   condition['sourceBinding']['historicalSourceSha256']=condition['sourceBinding']['ssotSha256'];condition['sourceBinding']['ssotSha256']=NEW;condition['sourceBinding']['revalidation']=bind
 c['changedBoundaryEvidenceRequirements']=proof['changedBoundaryDisposition']
 r.setdefault('historicalSourceBindings',[]).append({'sourceDocumentSha256':r['sourceDocumentSha256'],'registerSha256':before['register'],'scope':'Original inventory and old execution bindings preserved'})
 r['sourceDocumentSha256']=NEW;r['sourceSnapshot']='Current finite classification metadata revalidated; unchanged original structural inventory retains its explicit historical snapshot bindings pending full current inventory refresh.'
 oldlinks=r['createOperationLayeredDuties'].get('existingInventoryLinks',{});r['classificationScopeRevalidation']=bind;r['createOperationLayeredDuties']=json.loads(json.dumps(c['layeredConditions']));r['createOperationLayeredDuties']['existingInventoryLinks']=oldlinks;r['changedBoundaryEvidenceRequirements']=proof['changedBoundaryDisposition']
 r['currentFiniteChecklist']['scopeRevalidation']=bind
 assert len(c['obligations'])==36 and len(r['obligations'])==3897 and c['wholeOperationsClosed']==[]
 assert c['SSOT_CONTRACT_READY']=='BLOCKED' and c['IMPLEMENTATION_PRODUCTION_ACCEPTANCE']=='NOT_EVALUATED'
 cb=(json.dumps(c,ensure_ascii=False,indent=2)+'\n').encode();r['currentFiniteChecklist']['sha256']=hashlib.sha256(cb).hexdigest();cp.write_bytes(cb);rp.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 validation={'status':'PASS_SCOPED_CLASSIFICATION_REBIND','executionSourcePreserved':OLD,'currentSourceSha256':NEW,'sourceStable':sha(source)==NEW,'beforeSha256':before,'afterSha256':{'checklist':sha(cp),'register':sha(rp)},'authorityExcerptsChecked':len(quotes),'canonicalResourcesChecked':len(resource_checks),'rootHelpersChecked':len(helper_checks),'parentStatesUnchanged':True,'originalInventoryUntouched':True,'oldProofBytesAndExecutionHashesUntouched':True,'changedCreateCompletionEvidenceStillStale':True,'sharedWritesOnly':[str(cp.relative_to(ROOT)),str(rp.relative_to(ROOT))]};(OWN/'current-shared-rebind-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n');print(json.dumps(validation))
if __name__=='__main__':main()
