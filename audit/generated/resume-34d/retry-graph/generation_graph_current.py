"""Native source graph/reference design. Does not execute arbitrary implementations.

An exact DesignArtifactExpectation is a declared future output contract, not
missing generated application bytes. Existing ArtifactRef always requires bytes.
"""
import copy
from generation_admission_contracts import *

CR_FIELDS={'artifact','recordDigest','recordId','recordKind','schema'}
AR_FIELDS={'artifactId','kind','schema','mediaType','path','contentDigest','sizeBytes','producerNodeId','provenanceDigest'}
SA_FIELDS={'schemaId','dialect','rootPointer','bundle','nativeSchemaDigest'}

class GraphValidator:
 def __init__(self,repo,domain_map,raw_kinds,stage='PRE_GENERATION_DESIGN'):
  self.repo=repo;self.domain_map=domain_map;self.raw_kinds=set(raw_kinds);self.stage=stage
  self.active=set();self.cache={};self.records={};self.expectations={};self.vectors=[];self.requirementIds=set()
 def _native(self,definition,value):
  return validate({'$ref':GEN+'#/$defs/'+definition},value,self.repo.registry,'GENERATION_GRAPH_SCHEMA_INVALID')
 def _stored(self,ref):
  self._native('ArtifactRef',ref);r=self.repo.records.get(ref['artifactId'])
  if r is None:fail('GENERATION_GRAPH_ARTIFACT_UNAVAILABLE','/artifactId')
  if r.get('owner')!=self.repo.owner:fail('GENERATION_GRAPH_ARTIFACT_OWNER_MISMATCH','/artifactId')
  if r.get('recordId')!=ref['artifactId'] or r.get('artifactRef')!=ref:fail('GENERATION_GRAPH_ARTIFACT_LEDGER_MISMATCH','/artifactId')
  raw=r.get('bytes')
  if not isinstance(raw,bytes):fail('GENERATION_GRAPH_ARTIFACT_BYTES_UNAVAILABLE','/artifactId')
  if len(raw)!=ref['sizeBytes'] or digest(raw)!=ref['contentDigest'] or r.get('contentDigest')!=ref['contentDigest']:fail('GENERATION_GRAPH_ARTIFACT_BYTES_MISMATCH','/contentDigest')
  self.repo.consulted[ref['artifactId']]=r
  return raw,r
 def artifact(self,ref):
  key=(ref['artifactId'],ref['contentDigest']);raw,record=self._stored(ref)
  if key in self.active:fail('GENERATION_GRAPH_HYDRATION_CYCLE','/artifactId')
  if key in self.cache:return self.cache[key]
  self.active.add(key)
  try:
   kind=ref['kind']
   if kind=='JSON_SCHEMA_BUNDLE':
    value=source_json(raw)
    try:Draft202012Validator.check_schema(value)
    except SchemaError:fail('GENERATION_GRAPH_NATIVE_SCHEMA_INVALID','/bundle')
    if ref['schema'] is not None:
     self.repo.hydrate(ref['artifactId'],ref['contentDigest'])
    # Null SchemaAddress is explicitly allowed for JSON_SCHEMA_BUNDLE by native
    # ArtifactResolver.get; official 2020-12 meta-schema provides the contract.
    self._local_refs(value)
   elif kind in self.repo.artifact_map:
    definition=self.repo.artifact_map[kind]
    value,_=self.repo.hydrate(ref['artifactId'],ref['contentDigest'],definition)
    self.walk(value)
    if definition=='TypedDocument':self.typed(value['documentSchema'],value['document'])
    if definition=='TypedValue':
     self.typed(value['schema'],value['value'])
     if digest(canonical(value['value']))!=value['valueDigest']:fail('GENERATION_GRAPH_TYPED_VALUE_DIGEST_MISMATCH','/valueDigest')
    if definition=='EvidenceRecord':self.typed(value['observationSchema'],value['observations'])
    if definition=='ContractVector':self._vector(value)
   elif kind in self.raw_kinds:
    # Raw declared kinds preserve exact bytes; no trim/decode/reinterpretation.
    value=raw
   else:fail('GENERATION_GRAPH_ARTIFACT_KIND_UNDECLARED','/kind')
   self.cache[key]=value;return value
  finally:self.active.remove(key)
 def _local_refs(self,schema):
  def walk(v):
   if isinstance(v,dict):
    for k,c in v.items():
     if k=='$ref' and isinstance(c,str) and c.startswith('#'):
      self.pointer(schema,c[1:],'GENERATION_GRAPH_SCHEMA_LOCAL_REF_UNRESOLVED')
     walk(c)
   elif isinstance(v,list):
    for c in v:walk(c)
  walk(schema)
 @staticmethod
 def pointer(value,path,error):
  if path=='':return value
  if not path.startswith('/'):fail(error,'/rootPointer')
  for part in path.split('/')[1:]:
   token=part.replace('~1','/').replace('~0','~')
   if isinstance(value,dict) and token in value:value=value[token]
   elif isinstance(value,list) and token.isdecimal() and str(int(token))==token and int(token)<len(value):value=value[int(token)]
   else:fail(error,'/rootPointer')
  return value
 def schema(self,reference):
  self._native('SchemaArtifact',reference);bundle=self.artifact(reference['bundle'])
  if bundle.get('$id')!=reference['schemaId']:fail('GENERATION_GRAPH_SCHEMA_IDENTITY_MISMATCH','/schemaId')
  selected=self.pointer(bundle,reference['rootPointer'],'GENERATION_GRAPH_SCHEMA_POINTER_UNRESOLVED')
  if digest(canonical(selected))!=reference['nativeSchemaDigest']:fail('GENERATION_GRAPH_SCHEMA_DIGEST_MISMATCH','/nativeSchemaDigest')
  compiled=copy.deepcopy(bundle)
  if reference['rootPointer']:compiled['$ref']='#'+reference['rootPointer']
  else:compiled.pop('$ref',None)
  return compiled
 def typed(self,schema_reference,value):
  compiled=self.schema(schema_reference)
  validate(compiled,value,self.repo.registry,'GENERATION_GRAPH_TYPED_CONTENT_INVALID','/value')
 def record(self,ref):
  self._native('ContractRecordRef',ref);definition=self.domain_map.get(ref['recordKind'])
  if definition is None:fail('GENERATION_GRAPH_RECORD_KIND_UNDECLARED','/recordKind')
  value=self.artifact(ref['artifact']);self._native(definition,value)
  normalized=copy.deepcopy(value)
  if 'canonicalDigest' in normalized:normalized['canonicalDigest']=None
  if digest(canonical(normalized))!=ref['recordDigest']:fail('GENERATION_GRAPH_RECORD_DIGEST_MISMATCH','/recordDigest')
  if ref['schema']!=ref['artifact']['schema']:fail('GENERATION_GRAPH_RECORD_SCHEMA_MISMATCH','/schema')
  key=(ref['recordKind'],ref['recordId'])
  if key in self.records and canonical(self.records[key])!=canonical(value):fail('GENERATION_GRAPH_RECORD_IDENTITY_CONFLICT','/recordId')
  self.records[key]=value;return value
 def expectation(self,value):
  self._native('DesignArtifactExpectation',value);kind=value['artifactKind']
  if kind not in self.raw_kinds and kind not in self.repo.artifact_map and kind!='JSON_SCHEMA_BUNDLE':fail('GENERATION_GRAPH_EXPECTATION_KIND_UNDECLARED','/artifactKind')
  if kind in self.repo.artifact_map:
   address=value['expectedSchema']
   if address is None or address['definition']!=self.repo.artifact_map[kind]:fail('GENERATION_GRAPH_EXPECTATION_SCHEMA_REQUIRED','/expectedSchema')
   bundle=self.repo.decoded.get(address['bundleDigest'])
   if bundle is None or bundle['$id']!=address['schemaId']:fail('GENERATION_GRAPH_EXPECTATION_SCHEMA_UNRESOLVED','/expectedSchema')
   self.repo.usedBundles.add(address['bundleDigest'])
  if not set(value['producerRequirementIds'])<=self.requirementIds:fail('GENERATION_GRAPH_EXPECTATION_REQUIREMENT_UNRESOLVED','/producerRequirementIds')
  eid=value['expectationId']
  if eid in self.expectations and self.expectations[eid]!=value:fail('GENERATION_GRAPH_EXPECTATION_IDENTITY_CONFLICT','/expectationId')
  self.expectations[eid]=copy.deepcopy(value)
  if self.stage=='IMPLEMENTATION_ACCEPTANCE':fail('GENERATION_GRAPH_IMPLEMENTATION_EXPECTATION_UNMATERIALIZED','/repositoryPath')
 def _vector(self,value):
  compiled=self.schema(value['targetSchema'])
  errors=list(Draft202012Validator(compiled,registry=self.repo.registry,format_checker=FormatChecker()).iter_errors(value['input']))
  if (not errors)!=value['expectedValid']:fail('GENERATION_GRAPH_VECTOR_RESULT_MISMATCH','/expectedValid')
  pointers={'/'+'/'.join(str(p).replace('~','~0').replace('/','~1') for p in e.absolute_path) if e.absolute_path else '' for e in errors}
  if not set(value['expectedFailurePointers'])<=pointers:fail('GENERATION_GRAPH_VECTOR_FAILURE_POINTER_MISMATCH','/expectedFailurePointers')
  self.vectors.append({'vectorId':value['vectorId'],'actualValid':not errors,'testedSchemaDigest':value['targetSchema']['nativeSchemaDigest']})
 def walk(self,value):
  if isinstance(value,dict):
   keys=set(value)
   if keys==CR_FIELDS:self.record(value);return
   if keys==AR_FIELDS:self.artifact(value);return
   if keys==SA_FIELDS:self.schema(value);return
   if value.get('recordKind')=='DESIGN_ARTIFACT_EXPECTATION':self.expectation(value);return
   for v in value.values():self.walk(v)
  elif isinstance(value,list):
   for v in value:self.walk(v)
 def specification(self,spec):
  self._native('GenerationSpecification',spec)
  reqs=spec['behavioralRequirements'];ids=[r['requirementId'] for r in reqs]
  if len(ids)!=len(set(ids)):fail('GENERATION_GRAPH_DUPLICATE_REQUIREMENT','/behavioralRequirements')
  self.requirementIds=set(ids);dependencies={r['requirementId']:set(r['dependsOn']) for r in reqs}
  for rid,deps in dependencies.items():
   if not deps<=self.requirementIds:fail('GENERATION_GRAPH_REQUIREMENT_DEPENDENCY_UNRESOLVED','/behavioralRequirements')
  self.dag(dependencies,'GENERATION_GRAPH_REQUIREMENT_CYCLE')
  if any(q['blocking'] for q in spec['openQuestions']):fail('GENERATION_GRAPH_BLOCKING_OPEN_QUESTION','/openQuestions')
  self.walk(spec)
  criteria={}
  for ref in spec['acceptanceCriteria']:
   item=self.record(ref);cid=item['criterionId']
   if cid in criteria:fail('GENERATION_GRAPH_DUPLICATE_ACCEPTANCE','/acceptanceCriteria')
   if not set(item['requirementIds'])<=self.requirementIds:fail('GENERATION_GRAPH_ACCEPTANCE_REQUIREMENT_UNRESOLVED','/acceptanceCriteria')
   criteria[cid]=item
  for req in reqs:
   for cid in req['acceptanceIds']:
    if cid not in criteria:fail('GENERATION_GRAPH_ACCEPTANCE_UNRESOLVED','/behavioralRequirements/acceptanceIds')
    if req['requirementId'] not in criteria[cid]['requirementIds']:fail('GENERATION_GRAPH_ACCEPTANCE_COVERAGE_MISMATCH','/behavioralRequirements/acceptanceIds')
   if not req['domainContractRefs']:fail('GENERATION_GRAPH_DOMAIN_CONTRACT_COVERAGE_MISSING','/behavioralRequirements/domainContractRefs')
  coverage=spec['capabilityDecision']['coverage'];covered=[c['requirementId'] for c in coverage]
  if len(covered)!=len(set(covered)):fail('GENERATION_GRAPH_CAPABILITY_DUPLICATE','/capabilityDecision/coverage')
  if set(covered)!=self.requirementIds:fail('GENERATION_GRAPH_CAPABILITY_COVERAGE_MISSING','/capabilityDecision/coverage')
  if not set(spec['capabilityDecision']['uncoveredRequirementIds'])<=self.requirementIds:fail('GENERATION_GRAPH_CAPABILITY_UNKNOWN_REQUIREMENT','/capabilityDecision/uncoveredRequirementIds')
  if spec['capabilityDecision']['decision']=='FULL_REUSE' and spec['capabilityDecision']['uncoveredRequirementIds']:fail('GENERATION_GRAPH_FULL_REUSE_UNCOVERED','/capabilityDecision/uncoveredRequirementIds')
  return {'status':'VERIFIED_BOUNDED_NATIVE_GRAPH','hydratedArtifactCount':len(self.cache),'hydratedRecordCount':len(self.records),
   'schemaVectorsExecuted':len(self.vectors),'expectedArtifacts':copy.deepcopy(list(self.expectations.values())),
   'implementationAcceptance':'NOT_EVALUATED','unverified':['Semantic predicate implementation behavior and broad business requirement truth are not established by schema vectors','Source/delegation/Secret-use/current target-state execution predicates require exact consumer implementations and authority context']}
 @staticmethod
 def dag(graph,error):
  active=set();done=set()
  def visit(node):
   if node in active:fail(error)
   if node in done:return
   active.add(node)
   for dep in graph[node]:visit(dep)
   active.remove(node);done.add(node)
  for node in graph:visit(node)

def project_inherited_specification(source_raw,source_job_id,child_job_id,expected_source_digest,registry):
 """Identity-only derivation: source immutable bytes stay retained, all other fields equal.

New local revision/digest belongs to child job; source approval remains lineage.
This function never creates an OWNER approval or execution authority receipt.
 """
 validate(UID,source_job_id);validate(UID,child_job_id)
 if source_job_id==child_job_id:fail('GENERATION_CHILD_JOB_IDENTITY_NOT_DISTINCT','/jobId')
 if not isinstance(source_raw,bytes) or digest(source_raw)!=expected_source_digest:fail('GENERATION_CHILD_SOURCE_DIGEST_MISMATCH')
 source=source_json(source_raw)
 validate({'$ref':GEN+'#/$defs/ApprovedGenerationSpecification'},source,registry,'GENERATION_CHILD_SOURCE_SCHEMA_INVALID')
 if source['jobId']!=source_job_id:fail('GENERATION_CHILD_SOURCE_JOB_MISMATCH','/jobId')
 if source_raw!=canonical(source):fail('GENERATION_CHILD_SOURCE_NONCANONICAL')
 child=copy.deepcopy(source);child['jobId']=child_job_id
 validate({'$ref':GEN+'#/$defs/ApprovedGenerationSpecification'},child,registry,'GENERATION_CHILD_SCHEMA_INVALID')
 if {k:v for k,v in child.items() if k!='jobId'}!={k:v for k,v in source.items() if k!='jobId'}:fail('GENERATION_CHILD_FUNCTIONAL_FIELDS_CHANGED')
 raw=canonical(child)
 return {'bytes':raw,'contentDigest':digest(raw),'sourceJobId':source_job_id,'childJobId':child_job_id,
 'sourceSpecificationDigest':expected_source_digest,'sourceRetained':True,'allowedChangedPointers':['/jobId'],
 'approvalCreated':False,'executionAuthorityCreated':False}
