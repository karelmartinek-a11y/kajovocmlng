"""Bounded native frozen source→graph→child local specification consumer.

Owner approval/inherited commit and current dispatch guards stay independent.
A frozen source specification is immutable lineage, not child's approved receipt.
"""
import copy
from generation_native_graph import GraphValidator,project_inherited_specification
from generation_admission_contracts import fail,digest,canonical

def consume_inherited_basis(body,repository,domain_map,raw_kinds,child_job_id,frozen_inputs,frozen_schema_digests):
 kind=body.get('kind','CREATE')
 if kind not in ['UPDATE','RETRY','REPAIR']:fail('GENERATION_CONSUMER_OWN_KIND_REQUIRED')
 if len({r['recordId']for r in frozen_inputs})!=len(frozen_inputs):fail('GENERATION_CONSUMER_FROZEN_IDENTITY_DUPLICATE')
 frozen={r['recordId']:r for r in frozen_inputs}
 for r in frozen_inputs:
  actual=repository.records.get(r['recordId'])
  if actual is None:fail('GENERATION_CONSUMER_FROZEN_BYTES_UNAVAILABLE')
  if actual['schema']!=r['schema'] or actual.get('contentDigest')!=r['contentDigest']:fail('GENERATION_CONSUMER_FROZEN_SOURCE_DRIFT')
  if actual['schema']['bundleDigest'] not in frozen_schema_digests:fail('GENERATION_CONSUMER_FROZEN_SCHEMA_UNBOUND')
  # Recalculate actual bytes, validate actual stored schema; never use moving head.
  repository.hydrate(r['recordId'],r['contentDigest'],r['schema']['definition'])
 selector=body['generationBasis']
 if kind in ['RETRY','REPAIR']:
  sid=selector['approvedRevisionId'];sd=selector['expectedSpecificationDigest']
 else:
  target,_=repository.hydrate(selector['snapshotId'],selector['expectedDigest'],'TargetIdentitySnapshot')
  sid=target['lastApprovedSpecificationRevisionId'];sd=target['lastApprovedSpecificationDigest']
  if sid is None or sd is None:fail('GENERATION_UPDATE_SOURCE_SPECIFICATION_UNAVAILABLE_FOR_INHERITED_CONSUMER')
 if sid not in frozen or frozen[sid]['contentDigest']!=sd:fail('GENERATION_CONSUMER_SOURCE_NOT_FROZEN')
 spec,record=repository.hydrate(sid,sd,'ApprovedGenerationSpecification')
 if kind=='RETRY'and spec['jobId']!=body['parentJobId']:fail('GENERATION_CONSUMER_SOURCE_JOB_MISMATCH')
 validator=GraphValidator(repository,domain_map,raw_kinds)
 graph=validator.specification(spec)
 projection=project_inherited_specification(record['bytes'],spec['jobId'],child_job_id,sd,repository.registry)
 # Only source job identity changes in new local spec, source functional fields
 # and bytes are retained; this is NOT an OWNER/inherited execution commitment.
 return {'kind':kind,'sourceJobId':spec['jobId'],'childJobId':child_job_id,
  'sourceSpecificationRevisionId':sid,'sourceSpecificationDigest':sd,
  'childSpecificationBytes':projection['bytes'],'childSpecificationDigest':projection['contentDigest'],
  'graph':graph,'approvalCreated':False,'executionAuthorityCreated':False,
  'frozenLineageDigest':digest(canonical({'records':frozen_inputs,'schemaBundles':sorted(frozen_schema_digests)})),
  'dispatchPermitted':False,'runtimeAcceptance':'NOT_EVALUATED'}
