"""Own-kind generation basis design. Immutable repository fixtures, not production evidence.

Selectors are untrusted hints. Every payload is read from actual pinned bytes and
validated against native schemas. No validity/sufficiency flags are consumed.
"""
import copy, hashlib, json, sys
from functools import lru_cache
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from jsonschema_specifications import REGISTRY as SPECIFICATION_REGISTRY
from create_operation_contracts import ContractFailure, strict_json, schema as create_schema
from follow_up_contracts import request_schema as follow_up_schema

GEN='urn:kcml:generation-contracts:2'
UID={'type':'string','format':'uuid'}
DIGEST={'type':'string','pattern':'^sha256:[0-9a-f]{64}$(?![\\s\\S])'}
COUNTER={'$ref':GEN+'#/$defs/Counter'}

def closed(fields):
 return {'type':'object','additionalProperties':False,'required':list(fields),'properties':fields}
def digest(raw): return 'sha256:'+hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')
def fail(code,pointer=''): raise ContractFailure(code,pointer)
def source_json(raw):
 try:return strict_json(raw)
 except ContractFailure as e:
  codes={'DUPLICATE_JSON_KEY':'GENERATION_BASIS_DUPLICATE_JSON_KEY','INVALID_JSON':'GENERATION_BASIS_JSON_INVALID','INVALID_UTF8':'GENERATION_BASIS_UTF8_INVALID','INVALID_UNICODE':'GENERATION_BASIS_UNICODE_INVALID','NONFINITE_JSON_NUMBER':'GENERATION_BASIS_NONFINITE_JSON_NUMBER'}
  if e.code not in codes:raise
  fail(codes[e.code],e.pointer)
def validate(schema,value,registry=None,code='GENERATION_BASIS_SCHEMA_INVALID',pointer=''):
 try:
  errors=list(Draft202012Validator(schema,registry=registry or Registry(),format_checker=FormatChecker()).iter_errors(value))
 except Exception as e:
  from referencing.exceptions import Unresolvable
  from jsonschema.exceptions import _WrappedReferencingError
  if isinstance(e,(Unresolvable,_WrappedReferencingError)):fail('GENERATION_BASIS_SCHEMA_REFERENCE_UNRESOLVED',pointer)
  raise
 if errors:
  e=sorted(errors,key=lambda e:(list(map(str,e.absolute_path)),e.message))[0]
  at='/'+'/'.join(str(x).replace('~','~0').replace('/','~1') for x in e.absolute_path) if e.absolute_path else ''
  fail(code,pointer+at)
 return value

def selector_schema():
 approval={'approvedRevisionId':UID,'expectedSpecificationDigest':DIGEST,'authorityId':UID,'expectedAuthorityDigest':DIGEST}
 return {'oneOf':[
  closed({'basisKind':{'const':'UPDATE_TARGET_REVISION'},'snapshotId':UID,'expectedDigest':DIGEST}),
  closed({'basisKind':{'const':'RETRY_FAILED_TECHNICAL_PART'},'phaseRunId':UID,'expectedDigest':DIGEST,
          'planId':UID,'expectedPlanDigest':DIGEST,**approval}),
  closed({'basisKind':{'const':'REPAIR_MONITORING_EVIDENCE'},'monitoringArtifactId':UID,'expectedDigest':DIGEST,
          'snapshotId':UID,'expectedTargetDigest':DIGEST,**approval})]}

def request_schema():
 return copy.deepcopy(create_schema()['$defs']['GenerationJobCreateBody'])

TARGET_SCHEMA=closed({'snapshotId':UID,'objectId':UID,'targetKind':create_schema()['$defs']['GenerationJobCreateBody']['properties']['targetKind'],
 'componentId':UID,'runtimeInstanceIds':{'type':'array','uniqueItems':True,'items':UID},
 'revisionId':UID,'releaseId':{'anyOf':[UID,{'type':'null'}]},'bindingSetRevision':COUNTER,'activationEpoch':COUNTER,
 'lastApprovedAuthorityId':{'anyOf':[UID,{'type':'null'}]},'lastApprovedSpecificationRevisionId':{'anyOf':[UID,{'type':'null'}]},
 'lastApprovedSpecificationDigest':{'anyOf':[DIGEST,{'type':'null'}]}})
AUTHORITY_SCHEMA=closed({'authorityId':UID,'sourceJobId':UID,'specificationRevisionId':UID,'specificationDigest':DIGEST,
 'kind':{'enum':['OWNER_APPROVED','INHERITED_TECHNICAL']},'ownerApprovalEventId':UID,
 'authority':{'$ref':GEN+'#/$defs/GenerationAuthority'},'targetSnapshotDigest':{'anyOf':[DIGEST,{'type':'null'}]},
 'frozenAt':{'$ref':GEN+'#/$defs/Timestamp'}})
PHASE_SCHEMA=closed({'phaseRunId':UID,'jobId':UID,'phase':{'$ref':GEN+'#/$defs/Phase'},'attempt':{'$ref':GEN+'#/$defs/PositiveCounter'},
 'state':{'const':'FAILED'},'resultDigest':DIGEST,'failedNodeIds':{'type':'array','minItems':1,'uniqueItems':True,'items':{'$ref':GEN+'#/$defs/Id'}},
 'planId':UID,'planDigest':DIGEST,'authorityId':UID,'authorityDigest':DIGEST,'specificationDigest':DIGEST,
 'pendingSideEffectIds':{'type':'array','maxItems':0},'completedAt':{'$ref':GEN+'#/$defs/Timestamp'}})
RESULT_SCHEMA=closed({'jobId':UID,'phaseRunId':UID,'failedNodeIds':{'type':'array','minItems':1,'uniqueItems':True,'items':{'$ref':GEN+'#/$defs/Id'}},
 'outcome':{'const':'KNOWN_FAILURE'},'errorCodes':{'type':'array','minItems':1,'uniqueItems':True,'items':{'$ref':GEN+'#/$defs/SourceEnum110'}}})
PUBLICATION_SCHEMA=closed({'receiptId':UID,'jobId':UID,'artifactId':UID,'contentDigest':DIGEST,'outcome':{'enum':['COMMITTED','FAILED','UNKNOWN']}})
APPROVAL_SCHEMA=closed({'receiptId':UID,'sourceJobId':UID,'revisionId':UID,'specificationDigest':DIGEST,'outcome':{'enum':['COMMITTED','FAILED','UNKNOWN']}})
LOCAL_DEFINITIONS={'JsonSchemaBundle':{'$ref':'https://json-schema.org/draft/2020-12/schema'},'PublicationReceipt':PUBLICATION_SCHEMA,'OwnerApprovalReceipt':APPROVAL_SCHEMA,'TargetIdentitySnapshot':TARGET_SCHEMA,'GenerationExecutionAuthoritySnapshot':AUTHORITY_SCHEMA,
 'FailedTechnicalPhaseRun':PHASE_SCHEMA,'KnownTechnicalFailureResult':RESULT_SCHEMA,'GenerationJobCreateBody':request_schema()}

def local_bundle():
 return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:generation-admission-basis:1','$defs':LOCAL_DEFINITIONS}

@lru_cache(maxsize=16)
def checked_bundle(raw):
 value=source_json(raw)
 try:Draft202012Validator.check_schema(value)
 except SchemaError:fail('GENERATION_SCHEMA_BUNDLE_INVALID')
 return value

@lru_cache(maxsize=2)
def _current_sources(raw):
 from ssot_sources import resource_index,resources
 rs=resource_index(resources(raw.decode('utf8')))
 return tuple(rs[p]['raw'] for p in ['contracts/generation/generation-contracts.schema.json','contracts/generation/admission-basis.schema.json','contracts/generation/artifact-schema-map.json','contracts/generation/domain-record-schema-map.json'])

class Repository:
 """Trusted fixture repository. Server must hydrate these records under SQL locks.

Records are keyed by immutable primary key; bytes and schema addresses are
persisted metadata, not HTTP authority. Fixture mutability is deliberate solely
for negative tests. Production needs immutable columns/FK/crypto/roles.
 """
 def __init__(self, records, bundles, artifact_map, owner, target_heads=None):
  self.records=records;self.bundles=bundles;self.artifact_map=artifact_map;self.owner=owner
  self.consulted={};self.usedBundles=set();self.targetHeads=target_heads or {}
  self.registry=SPECIFICATION_REGISTRY
  self.decoded={}
  ids={}
  for expected,raw in bundles.items():
   if not isinstance(raw,bytes) or digest(raw)!=expected:fail('GENERATION_SCHEMA_BUNDLE_DIGEST_MISMATCH')
   value=checked_bundle(raw)
   schema_id=value.get('$id')
   if not isinstance(schema_id,str) or not schema_id:fail('GENERATION_SCHEMA_BUNDLE_ID_MISSING')
   if schema_id in ids and ids[schema_id]!=expected:fail('GENERATION_SCHEMA_BUNDLE_ID_AMBIGUOUS')
   ids[schema_id]=expected;self.decoded[expected]=value
   self.registry=self.registry.with_resource(schema_id,Resource.from_contents(value))
 @classmethod
 def from_current_ssot(cls,records,owner,target_heads=None):
  """Resolve complete authoritative current embedded schemas; no proposal fallback."""
  from ssot_sources import SSOT
  try:native,local,kindmap,domainmap=_current_sources(SSOT.read_bytes())
  except (ValueError,KeyError):fail('GENERATION_ADMISSION_CONTRACT_UNRESOLVED')
  mapping=source_json(domainmap)
  if mapping.get('GENERATION_AUTHORITY')!='GenerationAuthority':fail('GENERATION_ADMISSION_AUTHORITY_MAP_UNRESOLVED')
  return cls(records,{digest(native):native,digest(local):local},source_json(kindmap),owner,target_heads)
 def hydrate(self,key,expected_digest,definition=None,job_id=None):
  record=self.records.get(key)
  if record is None:fail('GENERATION_BASIS_UNAVAILABLE')
  if record.get('recordId')!=key:fail('GENERATION_BASIS_IDENTITY_MISMATCH')
  if record.get('owner')!=self.owner:fail('GENERATION_BASIS_OWNER_MISMATCH')
  if job_id is not None and record.get('jobId')!=job_id:fail('GENERATION_BASIS_JOB_MISMATCH')
  raw=record.get('bytes')
  if not isinstance(raw,bytes):fail('GENERATION_BASIS_BYTES_UNAVAILABLE')
  actual=digest(raw)
  if record.get('contentDigest')!=actual:fail('GENERATION_BASIS_BYTES_DIGEST_MISMATCH')
  if expected_digest!=actual:fail('GENERATION_BASIS_DIGEST_CONFLICT')
  address=record.get('schema')
  if not isinstance(address,dict) or set(address)!={'bundleDigest','schemaId','definition'}:fail('GENERATION_BASIS_SCHEMA_ADDRESS_INVALID')
  bundle=self.decoded.get(address['bundleDigest'])
  if bundle is None:fail('GENERATION_BASIS_SCHEMA_BUNDLE_UNAVAILABLE')
  if bundle['$id']!=address['schemaId']:fail('GENERATION_BASIS_SCHEMA_ID_MISMATCH')
  if definition is not None and address['definition']!=definition:fail('GENERATION_BASIS_DEFINITION_MISMATCH')
  if address['definition'] not in bundle.get('$defs',{}):fail('GENERATION_BASIS_DEFINITION_UNRESOLVED')
  value=source_json(raw)
  validate({'$ref':address['schemaId']+'#/$defs/'+address['definition']},value,self.registry)
  if 'jobId' in value and value['jobId']!=record.get('jobId'):fail('GENERATION_BASIS_DOCUMENT_JOB_MISMATCH')
  if 'sourceJobId' in value and value['sourceJobId']!=record.get('jobId'):fail('GENERATION_BASIS_DOCUMENT_JOB_MISMATCH')
  # Canonical domain snapshots/specification revisions use exactly frozen bytes.
  if raw!=canonical(value):fail('GENERATION_BASIS_NONCANONICAL_JSON')
  self.consulted[key]=record;self.usedBundles.add(address['bundleDigest'])
  return value,record
 def publication(self,record):
  receipt_id=record.get('publicationReceiptId');receipt=self.records.get(receipt_id)
  if receipt is None:fail('GENERATION_BASIS_PUBLICATION_UNAVAILABLE')
  payload,_=self.hydrate(receipt_id,receipt['contentDigest'],'PublicationReceipt',record['jobId'])
  if payload['outcome']!='COMMITTED':fail('GENERATION_BASIS_UNPUBLISHED')
  if payload['receiptId']!=receipt_id:fail('GENERATION_BASIS_PUBLICATION_IDENTITY_MISMATCH')
  if (payload['artifactId'],payload['contentDigest'])!=(record['recordId'],record['contentDigest']):fail('GENERATION_BASIS_PUBLICATION_MISMATCH')
  return payload
 def artifact(self,key,expected_digest,required_kind=None,job_id=None):
  record=self.records.get(key)
  if record is None:fail('GENERATION_BASIS_UNAVAILABLE')
  kind=record.get('artifactKind')
  if required_kind is not None and kind!=required_kind:fail('GENERATION_BASIS_ARTIFACT_KIND_MISMATCH')
  definition=self.artifact_map.get(kind)
  if definition is None:fail('GENERATION_BASIS_ARTIFACT_KIND_UNSUPPORTED')
  value,record=self.hydrate(key,expected_digest,definition,job_id)
  self.publication(record)
  return value,record
 def observation(self,evidence):
  # Native EvidenceRecord observations are only meaningful under its exact schema.
  descriptor=evidence['observationSchema'];ref=descriptor['bundle']
  record=self.records.get(ref['artifactId'])
  if record is None:fail('MONITORING_OBSERVATION_SCHEMA_UNAVAILABLE')
  if record.get('recordId')!=ref['artifactId'] or record.get('artifactKind')!='JSON_SCHEMA_BUNDLE':fail('MONITORING_OBSERVATION_SCHEMA_IDENTITY_MISMATCH')
  if record.get('owner')!=self.owner:fail('GENERATION_BASIS_OWNER_MISMATCH')
  raw=record.get('bytes')
  if not isinstance(raw,bytes):fail('GENERATION_BASIS_BYTES_UNAVAILABLE')
  if digest(raw)!=ref['contentDigest'] or record.get('contentDigest')!=ref['contentDigest']:fail('MONITORING_OBSERVATION_SCHEMA_BYTES_DIGEST_MISMATCH')
  schema_value,record=self.hydrate(ref['artifactId'],ref['contentDigest'],'JsonSchemaBundle')
  try:Draft202012Validator.check_schema(schema_value)
  except SchemaError:fail('MONITORING_OBSERVATION_SCHEMA_INVALID')
  self.publication(record)
  if descriptor['schemaId']!=schema_value.get('$id'):fail('MONITORING_OBSERVATION_SCHEMA_ID_MISMATCH')
  if ref['schema']!=record['schema']:fail('MONITORING_OBSERVATION_SCHEMA_ADDRESS_MISMATCH')
  selected=schema_value
  for escaped in descriptor['rootPointer'].split('/')[1:]:
   token=escaped.replace('~1','/').replace('~0','~')
   if not isinstance(selected,dict) or token not in selected:fail('MONITORING_OBSERVATION_SCHEMA_POINTER_UNRESOLVED')
   selected=selected[token]
  if digest(canonical(selected))!=descriptor['nativeSchemaDigest']:fail('MONITORING_OBSERVATION_SCHEMA_DIGEST_MISMATCH')
  try:Draft202012Validator.check_schema(selected)
  except SchemaError:fail('MONITORING_OBSERVATION_SCHEMA_INVALID')
  validate(selected,evidence['observations'],self.registry,'MONITORING_OBSERVATION_INVALID','/observations')
  return evidence['observations']

def approved(repo,selector,job_id=None):
 spec,revision=repo.hydrate(selector['approvedRevisionId'],selector['expectedSpecificationDigest'],'ApprovedGenerationSpecification',job_id)
 authority,record=repo.hydrate(selector['authorityId'],selector['expectedAuthorityDigest'],'GenerationExecutionAuthoritySnapshot',job_id)
 if authority['authorityId']!=selector['authorityId']:fail('GENERATION_AUTHORITY_IDENTITY_MISMATCH')
 if (authority['specificationRevisionId'],authority['specificationDigest'],authority['sourceJobId'])!=(selector['approvedRevisionId'],selector['expectedSpecificationDigest'],revision['jobId']):fail('GENERATION_APPROVED_LINEAGE_MISMATCH')
 # Actual OWNER approval receipt is immutable and must bind revision/digest.
 approval_record=repo.records.get(authority['ownerApprovalEventId'])
 if approval_record is None:fail('GENERATION_OWNER_APPROVAL_UNAVAILABLE')
 approval,_=repo.hydrate(authority['ownerApprovalEventId'],approval_record['contentDigest'],'OwnerApprovalReceipt',revision['jobId'])
 if approval['receiptId']!=authority['ownerApprovalEventId']:fail('GENERATION_OWNER_APPROVAL_IDENTITY_MISMATCH')
 if (approval['revisionId'],approval['specificationDigest'],approval['sourceJobId'],approval['outcome'])!=(selector['approvedRevisionId'],selector['expectedSpecificationDigest'],revision['jobId'],'COMMITTED'):fail('GENERATION_OWNER_APPROVAL_MISMATCH')
 authority_ref=spec['authorityModel']
 if authority_ref['recordKind']!='GENERATION_AUTHORITY':fail('GENERATION_APPROVED_AUTHORITY_RECORD_KIND_MISMATCH')
 if authority_ref['artifact']['kind']!='GENERATION_AUTHORITY' or repo.artifact_map.get('GENERATION_AUTHORITY')!='GenerationAuthority':fail('GENERATION_APPROVED_AUTHORITY_ARTIFACT_KIND_UNRESOLVED')
 authority_content,authority_record=repo.hydrate(authority_ref['artifact']['artifactId'],authority_ref['artifact']['contentDigest'],'GenerationAuthority',revision['jobId'])
 if authority_record.get('artifactRef')!=authority_ref['artifact']:fail('GENERATION_APPROVED_AUTHORITY_ARTIFACT_REF_MISMATCH')
 if len(authority_record['bytes'])!=authority_ref['artifact']['sizeBytes']:fail('GENERATION_APPROVED_AUTHORITY_ARTIFACT_SIZE_MISMATCH')
 if authority_ref['schema']!=authority_record['schema'] or authority_ref['artifact']['schema']!=authority_record['schema']:fail('GENERATION_APPROVED_AUTHORITY_SCHEMA_MISMATCH')
 if authority_ref['recordDigest']!=authority_record['contentDigest']:fail('GENERATION_APPROVED_AUTHORITY_RECORD_DIGEST_MISMATCH')
 if canonical(authority_content)!=canonical(authority['authority']):fail('GENERATION_APPROVED_AUTHORITY_CONTENT_MISMATCH')
 return spec,authority

def select_generation_basis(body,repo):
 validate(request_schema(),body,repo.registry,'GENERATION_REQUEST_INVALID')
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

def validate_follow_up_content(body,source_record_id,repo):
 """Supplement existing identity/digest/publication/atomic FOLLOW_UP checks.

Exact source content is verified here. Requested semantic sufficiency is only
claimed for the explicitly selected source class; arbitrary downstream workflow
requirements remain separate declared input contracts, never guessed from intent.
 """
 basis=body['followUpBasis'];validate(follow_up_schema(),basis)
 kind=basis['basisKind'];job_id=body['parentJobId']
 if kind=='INITIAL_REQUEST':
  value,record=repo.hydrate(source_record_id,basis['expectedDigest'],'GenerationJobCreateBody',job_id)
  from create_operation_contracts import validate_body
  try:validate_body('generation.job.create',value)
  except ContractFailure:fail('GENERATION_BASIS_DOMAIN_INVALID')
 elif kind=='SPECIFICATION_REVISION':
  if source_record_id!=basis['revisionId']:fail('GENERATION_BASIS_IDENTITY_MISMATCH')
  value,record=repo.hydrate(source_record_id,basis['expectedDigest'],'GenerationSpecification',job_id)
 else:
  if source_record_id!=basis['artifactId']:fail('GENERATION_BASIS_IDENTITY_MISMATCH')
  value,record=repo.artifact(source_record_id,basis['expectedDigest'],job_id=job_id)
 return {'contentValidated':True,'validatedDefinition':record['schema']['definition'],
  'contentDigest':record['contentDigest'],'sourceJobId':job_id,'requiredWorkflowContracts':'SEPARATE_EXPLICIT_CONSUMER_INPUTS'}

@lru_cache(maxsize=16)
def _checked_final_bundle(raw):
 from jsonschema.validators import validator_for
 parsed=source_json(raw);validator=validator_for(parsed,default=None)
 if validator is None:fail('GENERATION_FINAL_OUTPUT_SCHEMA_DIALECT_UNRESOLVED')
 try:validator.check_schema(parsed)
 except SchemaError:fail('GENERATION_FINAL_OUTPUT_SCHEMA_INVALID')
 return parsed,validator

@lru_cache(maxsize=16)
def _compiled_final_schema(raw,root):
 parsed,validator=_checked_final_bundle(raw);compiled=copy.deepcopy(parsed)
 if root:compiled['$ref']='#'+root
 else:compiled.pop('$ref',None)
 try:validator.check_schema(compiled)
 except SchemaError:fail('GENERATION_FINAL_OUTPUT_SCHEMA_INVALID')
 return compiled

def validate_declared_final_output(body,repository,declarations):
 """Verify concrete source result declaration and its actual output schema/bytes.

`declarations` is the immutable server publication-slot relation. SQL/producer
closure predicate evidence is separate; it must never be assembled from HTTP.
 """
 from generation_admission_contracts import closed,UID,DIGEST,validate,source_json,fail
 job=body['parentJobId'];selector=body['followUpBasis'];artifact=selector['artifactId']
 declaration=declarations.get((job,artifact))
 if declaration is None:fail('GENERATION_FINAL_OUTPUT_DECLARATION_UNAVAILABLE')
 validate(closed({'sourceRevisionId':UID,'sourceSpecificationDigest':DIGEST,'resultContractArtifactId':UID,'resultContractDigest':DIGEST,'artifactId':UID,'contentDigest':DIGEST,'publicationReceiptId':UID}),declaration,repository.registry,'GENERATION_FINAL_OUTPUT_DECLARATION_INVALID')
 if (declaration['artifactId'],declaration['contentDigest'])!=(artifact,selector['expectedDigest']):fail('GENERATION_FINAL_OUTPUT_DECLARATION_MISMATCH')
 specification,_=repository.hydrate(declaration['sourceRevisionId'],declaration['sourceSpecificationDigest'],'GenerationSpecification',job)
 reference=specification['resultContract']
 if reference['recordKind']!='GENERATION_RESULT':fail('GENERATION_FINAL_RESULT_CONTRACT_KIND_MISMATCH')
 if (reference['artifact']['artifactId'],reference['artifact']['contentDigest'],reference['recordDigest'])!=(declaration['resultContractArtifactId'],declaration['resultContractDigest'],declaration['resultContractDigest']):fail('GENERATION_FINAL_RESULT_CONTRACT_REFERENCE_MISMATCH')
 result,record=repository.hydrate(declaration['resultContractArtifactId'],declaration['resultContractDigest'],'GenerationResult',job)
 if reference['recordId']!=result['resultId']:fail('GENERATION_FINAL_RESULT_CONTRACT_IDENTITY_MISMATCH')
 if record.get('artifactRef')!=reference['artifact'] or record['schema']!=reference['schema']:fail('GENERATION_FINAL_RESULT_CONTRACT_LEDGER_MISMATCH')
 output,out_record=repository.artifact(artifact,selector['expectedDigest'],job_id=job)
 if out_record.get('publicationReceiptId')!=declaration['publicationReceiptId']:fail('GENERATION_FINAL_OUTPUT_PUBLICATION_REFERENCE_MISMATCH')
 schema=result['outputSchema'];bundle_ref=schema['bundle'];bundle_record=repository.records.get(bundle_ref['artifactId'])
 if bundle_record is None:fail('GENERATION_FINAL_OUTPUT_SCHEMA_UNAVAILABLE')
 if bundle_record.get('owner')!=repository.owner or bundle_record.get('recordId')!=bundle_ref['artifactId'] or bundle_record.get('artifactRef')!=bundle_ref:fail('GENERATION_FINAL_OUTPUT_SCHEMA_LEDGER_MISMATCH')
 raw=bundle_record.get('bytes')
 if not isinstance(raw,bytes) or len(raw)!=bundle_ref['sizeBytes'] or digest(raw)!=bundle_ref['contentDigest'] or bundle_record.get('contentDigest')!=bundle_ref['contentDigest']:fail('GENERATION_FINAL_OUTPUT_SCHEMA_BYTES_MISMATCH')
 parsed,validator=_checked_final_bundle(raw)
 if parsed.get('$schema')!=schema['dialect']:fail('GENERATION_FINAL_OUTPUT_SCHEMA_DIALECT_MISMATCH')
 if parsed.get('$id')!=schema['schemaId']:fail('GENERATION_FINAL_OUTPUT_SCHEMA_ID_MISMATCH')
 selected=parsed
 for token in schema['rootPointer'].split('/')[1:]:
  key=token.replace('~1','/').replace('~0','~')
  if not isinstance(selected,dict) or key not in selected:fail('GENERATION_FINAL_OUTPUT_SCHEMA_POINTER_UNRESOLVED')
  selected=selected[key]
 if digest(canonical(selected))!=schema['nativeSchemaDigest']:fail('GENERATION_FINAL_OUTPUT_SCHEMA_DIGEST_MISMATCH')
 compiled=_compiled_final_schema(raw,schema['rootPointer'])
 try:errors=list(validator(compiled,registry=repository.registry,format_checker=FormatChecker()).iter_errors(output))
 except Exception as e:
  from referencing.exceptions import Unresolvable
  from jsonschema.exceptions import _WrappedReferencingError
  if isinstance(e,(Unresolvable,_WrappedReferencingError)):fail('GENERATION_FINAL_OUTPUT_SCHEMA_REFERENCE_UNRESOLVED')
  raise
 if errors:fail('GENERATION_FINAL_OUTPUT_CONSUMER_SCHEMA_INVALID','/'+ '/'.join(str(x).replace('~','~0').replace('/','~1') for x in errors[0].absolute_path) if errors[0].absolute_path else '')
 repository.consulted[bundle_ref['artifactId']]=bundle_record
 return {'decision':'DECLARED_FINAL_OUTPUT_CONTENT_VALIDATED','sourceRevisionId':declaration['sourceRevisionId'],
 'resultContractArtifactId':declaration['resultContractArtifactId'],'contentDigest':selector['expectedDigest'],
 'closurePredicateId':result['closurePredicateId'],'acceptanceCriterionIds':result['acceptanceCriterionIds'],
 'producerPublicationClosure':'SQL_PRODUCER_COMMIT_CONTRACT_REQUIRED','runtimeAcceptance':'NOT_EVALUATED'}
