"""Authorized bounded integration; writes only the two delegated audit registers."""
import copy,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng'); OWN=ROOT/'audit/generated/closure-replan-84c/evidence'
SOURCE='2577dacf6024e4666ba98b11eb9c7ffa6e7f225e60630697db740129615cc536'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 assert sha(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md')==SOURCE
 cp=ROOT/'audit/SSOT_CREATE_CLOSURE_CHECKLIST.json';rp=ROOT/'audit/SSOT_COMPLETION_REGISTER.json'
 oldc=read(cp);oldr=read(rp); c=copy.deepcopy(oldc);r=copy.deepcopy(oldr)
 assert c['sourceSha256']==r['sourceDocumentSha256']==SOURCE
 auth=read(ROOT/'audit/generated/closure-replan-84c/authority/classification-proposal.json')
 evidence=read(OWN/'36-duty-layer-review.json');review={x['id']:x for x in evidence['obligations']}
 assert auth['sourceSha256']==SOURCE and len(auth['classifications'])==36
 spec=importlib.util.spec_from_file_location('proposals',OWN/'apply_audit_proposals.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 proposals=read(OWN/'integration-patch-proposals.json')
 # Exact checklist precondition is scoped to input bytes, never a contract failure.
 c=m.patch_checklist(c,next(x for x in proposals['patches'] if x['target']=='audit/SSOT_CREATE_CLOSURE_CHECKLIST.json'))
 cby={x['id']:x for x in c['obligations']};assert set(cby)==set(review)
 parents=[]
 for a in auth['classifications']:
  id=a['id'];parent=cby[id];v=review[id];deps=list(parent.get('dependencies',[]))
  layer_ids={l:id+'.LAYER.'+l for l in 'ABCD'}
  refs=[{'path':'audit/generated/closure-replan-84c/authority/classification-proposal.json','sha256':sha(ROOT/'audit/generated/closure-replan-84c/authority/classification-proposal.json'),'rowId':id,'scope':'NORMATIVE_TIMING_AND_DEPENDENCY_REVIEW'}, {'path':'audit/generated/closure-replan-84c/evidence/36-duty-layer-review.json','sha256':sha(OWN/'36-duty-layer-review.json'),'rowId':id,'scope':'SCOPED_EVIDENCE_DEPENDENCY_REVIEW'}]
  env=v['environmentD'];actual=a['B_fixture']['mandatoryActualMechanism'];conditions=[]
  for l in 'ABCD':
   condition={'id':layer_ids[l],'parentId':id,'layer':l,'origin':'DERIVED_EXISTING_DUTY_SPLIT_NOT_NEW_PRODUCT_REQUIREMENT','sourceBinding':{'ssotSha256':SOURCE},'authority':a['A_definitionBeforeGeneration']['authorityQuotes'] if l=='A' else a['B_fixture']['exactExecutableProducerOrBeforeGenerationAuthority'] if l=='B' else [a['C_futureGeneratedApplication']['precedenceQuote']] if l=='C' else ([a['D_environment']['quote']] if a['D_environment']['applicable'] else []),'dependencies':deps if l=='A' else [layer_ids['A']]+deps if l=='B' else [layer_ids['A'],layer_ids['B']] if l=='C' else [],'consumer':a['proposedScope'],'output':v['definitionA']['exit'] if l=='A' else v['fixtureB']['exit'] if l=='B' else a['C_futureGeneratedApplication']['exactDeliverables'] if l=='C' else 'Actual supported isolated environment for specifically required mechanism; no mock provider substitute','method': 'Semantic review against exact authority and producer/consumer definitions' if l=='A' else v['fixtureB']['namedMethod'] if l=='B' else a['C_futureGeneratedApplication']['exactExitGates'] if l=='C' else 'Capability observation and authoritative actual-mechanism fixture; do not repeat unavailable attempts unchanged','state':('IN_PROGRESS' if parent['state']=='IN_PROGRESS' else 'OPEN') if l=='A' else ('IN_PROGRESS' if v['fixtureB']['provedConditions'] else 'OPEN') if l=='B' else 'NOT_EVALUATED' if l=='C' else ('BLOCKED' if env['state']=='ENV_BLOCKED' else 'NOT_APPLICABLE'),'evidence':refs+(v['fixtureB']['provedConditions'] if l=='B' else []),'requiredBeforeGeneration':l in 'AB','blocksDefinitionA':False if l in 'CD' else None,'wholeConditionVerified':False}
   if l=='B':condition.update({'explicitBeforeGenerationExecutionTiming':a['B_fixture']['timingClassification'] in ['PREGEN_HANDOFF','EXPLICIT_PREGEN_ACTUAL_MECHANISM','FINAL_UI_FAMILY'],'requiredBeforeGeneration':a['B_fixture']['timingClassification']!='REFERENCE_NOT_TIMED_EXPLICITLY','timingDisposition': 'EXISTING_NAMED_REFERENCE_PROOF_PRESERVED_NO_NEW_ACTUAL_PRODUCER_EXECUTION_GATE_INFERRED' if a['B_fixture']['timingClassification']=='REFERENCE_NOT_TIMED_EXPLICITLY' else 'BEFORE_ACTIVE_PROFILE_USE_KEEP_ACTIVATION_GATE' if a['B_fixture']['timingClassification']=='PROFILE_ACTIVATION' else 'EXACT_UI_DESIGN_REFERENCE_AND_ACTIVATION_GATE_KEEP_GENERATED_BACKEND_EXECUTION_IN_C' if a['B_fixture']['timingClassification']=='UI_CONTRACT_REFERENCE' else 'EXPLICIT_PREGEN_OR_FINAL_FAMILY_GATE','notWaiverOfExactDefinitionOrExistingFixtureRequirement':True,'timingClassification':a['B_fixture']['timingClassification'],'timingLimit':a['B_fixture']['timingLimit'],'mandatoryActualMechanism':actual,'missingExactRemainder':v['fixtureB']['missingExactRemainder'],'provedSubconditionsDoNotCloseParent':True,'environmentDependency':layer_ids['D'] if env['state']=='ENV_BLOCKED' else None,'environmentDependencyScope':env['scope'],'existingNamedFixtureRequirementsPreserved':True})
   if l=='C':condition.update({'implementationAcceptance':'NOT_EVALUATED','blocksAorB':False,'phase':a['C_futureGeneratedApplication']['phase'],'authoritativeResource':a['C_futureGeneratedApplication']['authoritativeResource'],'resourceDigest':a['C_futureGeneratedApplication']['resourceDigest'],'notReplacementForAorB':True})
   if l=='D':condition.update({'blocksOnlyNamedActualMechanismFixture':env.get('blocksOnlyNamedActualMechanismFixture',False),'dependencyScope':env['scope'],'blockerType':'ENVIRONMENT' if env['state']=='ENV_BLOCKED' else None,'notOwnerProductDecision':True,'noRequirementRemoved':True})
   conditions.append(condition)
  parent['layerConditionIds']=layer_ids
  parent['classificationReview']={'path':'audit/generated/closure-replan-84c/authority/classification-proposal.json','sourceSha256':SOURCE,'preservesOriginalParentState':True,'scope':'NORMATIVE_LAYER_AND_TIMING_ONLY_NOT_FULL_PARENT_VERIFICATION'}
  parents.append({'id':id,'originalParentState':parent['state'],'originalMissingTextPreserved':a['originalMissingTextPreserved'],'scope':a['proposedScope'],'conditions':conditions,'wholeParentVerified':False})
 c['layeredConditions']={'format':'KCML-CREATE-LAYERED-CONDITIONS/1','sourceSha256':SOURCE,'parentDenominator':36,'conditionCount':144,'countingLimitation':'A/B/C/D splits overlap existing parent duties; not 144 new independent project requirements or completion units.','parents':parents,'newRequirementsAdopted':0,'speculativeProposalsNotAdopted':evidence['speculationDisposition']}
 r['createOperationLayeredDuties']=copy.deepcopy(c['layeredConditions'])
 r['currentFiniteChecklist'].update({'path':'audit/SSOT_CREATE_CLOSURE_CHECKLIST.json','parentDenominator':36,'layeredConditionCount':144,'layeredConditionsOverlapExistingDuties':True,'wholeOperationsClosed':len(c['wholeOperationsClosed']),'limitation':'36 parent A/B/C/D dependency classifications, no parent state upgrade; 144 overlapping splits are not independent project obligations.'})
 r['createOperationLayeredDuties']['existingInventoryLinks']={x['id']:[o['id'] for o in r['obligations'] if o.get('scope',{}).get('operationId')==cby[x['id']]['area'] or o['id']=='ui-exposure:'+({'UI.DASHBOARD_START.JOIN':'dashboard.start','UI.DASHBOARD_STOP.JOIN':'dashboard.stop','UI.GEN_EDIT_SPEC.JOIN':'gen.editSpec'}.get(x['id'],''))] for x in parents}
 assert len(r['obligations'])==len(oldr['obligations']) and r['obligations']==oldr['obligations']
 assert [x['state'] for x in c['obligations']]==[x['state'] for x in oldc['obligations']]
 assert [x['proofRequirements'] for x in c['obligations']]==[x['proofRequirements'] for x in oldc['obligations']]
 assert c['SSOT_CONTRACT_READY']=='BLOCKED' and c['IMPLEMENTATION_PRODUCTION_ACCEPTANCE']=='NOT_EVALUATED'
 assert r['readiness']==oldr['readiness'] and c['wholeOperationsClosed']==[]
 before={'checklist':sha(cp),'register':sha(rp)}
 cbytes=(json.dumps(c,ensure_ascii=False,indent=2)+'\n').encode();r['currentFiniteChecklist']['sha256']=hashlib.sha256(cbytes).hexdigest()
 cp.write_bytes(cbytes);rp.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 validation={'status':'PASS_BOUNDED_SHARED_AUDIT_INTEGRATION','sourceSha256':SOURCE,'authorizedWrites':[str(cp.relative_to(ROOT)),str(rp.relative_to(ROOT))],'beforeSha256':before,'afterSha256':{'checklist':sha(cp),'register':sha(rp)},'parentsClassified':36,'layerConditions':144,'newIndependentObligations':0,'originalInventoryEntriesPreserved':len(oldr['obligations']),'parentStatesPreserved':True,'mandatoryNamedProofRequirementsPreserved':True,'historyPreserved':True,'futureRuntimeCannotBlockDefinition':True,'readinessUnchanged':True,'wholeOperationsClosed':0,'currentStagePointerUpdatedWithHistoricalEvidencePreserved':True,'secretUIAuthorityCorrected':'§72.21','noCanonicalOrCheckpointOrGitWrites':True}
 (OWN/'shared-integration-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(validation))
if __name__=='__main__':main()
