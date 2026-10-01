"""Versioned existing own-kind discussion selector; actual frozen request validator."""
from generation_admission_contracts import approved,fail,digest,canonical
import copy
REVISION='GENERATION_OWN_KIND_DISCUSSION_V1'
def evaluate(body,repo,request_validator):
 request_validator(body)
 kind=body.get('kind','CREATE')
 if kind not in ['UPDATE','RETRY','REPAIR']:fail('GENERATION_KIND_OWN_BASIS_NOT_APPLICABLE')
 selector=body['generationBasis'];identities=[]
 if kind=='UPDATE':
  target,record=repo.hydrate(selector['snapshotId'],selector['expectedDigest'],'TargetIdentitySnapshot')
  if (target['snapshotId'],target['objectId'],target['targetKind'])!=(selector['snapshotId'],body['targetObjectId'],body['targetKind']):fail('GENERATION_TARGET_SNAPSHOT_MISMATCH')
  identities=[record]
  result={'decision':'ADMIT_DISCUSSION','executionAuthority':'REQUIRES_OWNER_APPROVAL',
   'preserveComponentId':target['componentId'],'preserveRuntimeInstanceIds':target['runtimeInstanceIds'],
   'executionRequirements':['COMPATIBILITY_PLAN','MIGRATION_PLAN','APPROVED_CURRENT_SPECIFICATION'],
   'activationRequirements':['CURRENT_FENCE_AND_DEPENDENCY_SNAPSHOT','VALIDATION_AND_REGRESSION']}
 elif kind=='RETRY':
  spec,authority=approved(repo,selector,body['parentJobId'])
  run,record=repo.hydrate(selector['phaseRunId'],selector['expectedDigest'],'FailedTechnicalPhaseRun',body['parentJobId'])
  plan,plan_record=repo.hydrate(selector['planId'],selector['expectedPlanDigest'],'GenerationPlan',body['parentJobId'])
  if (run['phaseRunId'],run['planId'],run['planDigest'],run['authorityId'],run['authorityDigest'],run['specificationDigest'])!=(selector['phaseRunId'],selector['planId'],selector['expectedPlanDigest'],selector['authorityId'],selector['expectedAuthorityDigest'],selector['expectedSpecificationDigest']):fail('GENERATION_RETRY_LINEAGE_MISMATCH')
  if plan['specificationDigest']!=selector['expectedSpecificationDigest']:fail('GENERATION_RETRY_PLAN_SPECIFICATION_MISMATCH')
  failed=set(run['failedNodeIds']);nodes={n['nodeId']:n for n in plan['nodes']}
  if len(nodes)!=len(plan['nodes']):fail('GENERATION_RETRY_DUPLICATE_PLAN_NODE')
  if not failed<=set(nodes) or any(nodes[n]['phase']!=run['phase'] for n in failed):fail('GENERATION_RETRY_FAILED_PART_MISMATCH')
  if run['phase']=='DISCUSSING':fail('GENERATION_RETRY_NONTECHNICAL_PART')
  # The failed run is terminal, but the parent job need not be terminal.
  evidence=repo.records.get(run['resultDigest'])
  if evidence is None:fail('GENERATION_RETRY_TERMINAL_RESULT_UNAVAILABLE')
  result_doc,_=repo.hydrate(run['resultDigest'],run['resultDigest'],'KnownTechnicalFailureResult',body['parentJobId'])
  if (result_doc['phaseRunId'],set(result_doc['failedNodeIds']))!=(run['phaseRunId'],failed):fail('GENERATION_RETRY_TERMINAL_RESULT_MISMATCH')
  identities=[record,plan_record,repo.records[selector['approvedRevisionId']],repo.records[selector['authorityId']]]
  result={'decision':'ADMIT_DISCUSSION','executionAuthority':'REQUIRES_INHERITED_TECHNICAL_COMMIT',
   'approvedSpecificationDigest':selector['expectedSpecificationDigest'],'technicalNodeIds':sorted(failed),
   'sourceAttempt':run['attempt'],'functionalChangesAllowed':False,
   'executionRequirements':['INHERITED_AUTHORITY_COMMIT','NEW_ATTEMPT_RECORD','CURRENT_FENCE_AND_DEPENDENCY_SNAPSHOT'],
   'activationRequirements':['VALIDATION_AND_REGRESSION']}
 else:
  spec,authority=approved(repo,selector)
  target,target_record=repo.hydrate(selector['snapshotId'],selector['expectedTargetDigest'],'TargetIdentitySnapshot')
  if (target['snapshotId'],target['objectId'],target['targetKind'])!=(selector['snapshotId'],body['targetObjectId'],body['targetKind']):fail('GENERATION_TARGET_SNAPSHOT_MISMATCH')
  if repo.targetHeads.get(body['targetObjectId'])!={'snapshotId':selector['snapshotId'],'contentDigest':selector['expectedTargetDigest']}:fail('GENERATION_REPAIR_CURRENT_TARGET_SNAPSHOT_MISMATCH')
  if (target['lastApprovedAuthorityId'],target['lastApprovedSpecificationRevisionId'],target['lastApprovedSpecificationDigest'])!=(selector['authorityId'],selector['approvedRevisionId'],selector['expectedSpecificationDigest']):fail('GENERATION_REPAIR_LAST_APPROVED_LINEAGE_MISMATCH')
  if authority['targetSnapshotDigest'] is not None:
   historical=[r for r in repo.records.values() if r.get('contentDigest')==authority['targetSnapshotDigest'] and r.get('schema',{}).get('definition')=='TargetIdentitySnapshot']
   if len(historical)!=1:fail('GENERATION_REPAIR_APPROVED_TARGET_UNAVAILABLE')
   prior,_=repo.hydrate(historical[0]['recordId'],authority['targetSnapshotDigest'],'TargetIdentitySnapshot')
   if (prior['objectId'],prior['targetKind'],prior['componentId'],set(prior['runtimeInstanceIds']))!=(target['objectId'],target['targetKind'],target['componentId'],set(target['runtimeInstanceIds'])):fail('GENERATION_REPAIR_PRESERVED_IDENTITY_MISMATCH')
  evidence,record=repo.artifact(selector['monitoringArtifactId'],selector['expectedDigest'],'MONITORING_EVIDENCE')
  if evidence['subjectDigest']!=selector['expectedTargetDigest']:fail('GENERATION_REPAIR_MONITORING_TARGET_MISMATCH')
  repo.observation(evidence)
  identities=[record,target_record,repo.records[selector['approvedRevisionId']],repo.records[selector['authorityId']]]
  result={'decision':'ADMIT_DISCUSSION','executionAuthority':'REQUIRES_INHERITED_TECHNICAL_COMMIT',
   'approvedSpecificationDigest':selector['expectedSpecificationDigest'],'functionalChangesAllowed':False,
   'preserveComponentId':target['componentId'],'preserveRuntimeInstanceIds':target['runtimeInstanceIds'],
   'executionRequirements':['INHERITED_AUTHORITY_COMMIT','TECHNICAL_REPAIR_PLAN','CURRENT_FENCE_AND_DEPENDENCY_SNAPSHOT'],
   'activationRequirements':['COMPLETE_REGRESSION_VALIDATION']}
 result['frozenInputs']=[{'recordId':r['recordId'],'contentDigest':r['contentDigest'],'schema':copy.deepcopy(r['schema'])} for _,r in sorted(repo.consulted.items())]
 result['frozenSchemaBundleDigests']=sorted(repo.usedBundles)
 result['lineageDigest']=digest(canonical({'records':result['frozenInputs'],'schemaBundles':result['frozenSchemaBundleDigests']}))
 return result

