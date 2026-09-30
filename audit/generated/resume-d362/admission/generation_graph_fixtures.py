"""One exact synthetic native source graph at pinned 6ac0e89, no live services."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
from generation_graph_reference import *
from ssot_sources import resources,resource_index
from verify_phase2_handoffs import witness
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
PIN='6ac0e89921ad73e1dae7054ef78d0d4880c67e60'
source=subprocess.check_output(['git','show',PIN+':00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT)
assert hashlib.sha256(source).hexdigest()=='9bf5510b189ef4f71216d56bf293599ac129d200ec92e90ff7c2c22f6b15e57b'
rs=resource_index(resources(source.decode()));gen_raw=rs['contracts/generation/generation-contracts.schema.json']['raw'];gen=json.loads(gen_raw);gb=digest(gen_raw)
artifact_map=json.loads(rs['contracts/generation/artifact-schema-map.json']['raw']);domain_map=json.loads(rs['contracts/generation/domain-record-schema-map.json']['raw']);raw_kinds=json.loads(rs['contracts/execution/raw-artifact-kinds.json']['raw'])
if isinstance(raw_kinds,dict):raw_kinds=list(raw_kinds)
JOB='00000000-0000-4000-8000-000000000001';CHILD='00000000-0000-4000-8000-000000000002';REQ='SyntheticRequirement';CRIT='SyntheticAcceptance'
expectation={'recordKind':'DESIGN_ARTIFACT_EXPECTATION','expectationId':'SyntheticPredicateImplementation','artifactKind':'SOURCE','repositoryPath':'synthetic-predicate.py','ownerModule':'synthetic-module','producerRequirementIds':[REQ],'verificationObligationIds':['SyntheticPredicatePositive','SyntheticPredicateNegative'],'expectedSchema':None,'generationRuleId':'SyntheticDeclaredRule'}
defs=copy.deepcopy(gen['$defs'])
for k,v in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-30T00:00:00.000Z','RelPath':'synthetic.json','JsonPointer':'','NonemptyJsonPointer':'/synthetic','ImplementationRef':expectation}.items():defs[k]={'const':v}
records={};artifact_cache={};record_cache={};count=100
schema_doc={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:synthetic-native-graph-schema:1','type':'object','additionalProperties':False,'required':['syntheticValue'],'properties':{'syntheticValue':{'type':'string','minLength':1}}}
def address(definition):return {'schemaId':GEN,'bundleDigest':gb,'definition':definition}
def persist(kind,value,definition=None):
 global count
 count+=1;key='00000000-0000-4000-8000-'+str(count).zfill(12)
 raw=value if isinstance(value,bytes) else canonical(value)
 ref={'artifactId':key,'kind':kind,'schema':address(definition) if definition else None,'mediaType':'application/octet-stream' if isinstance(value,bytes) else 'application/json','path':'synthetic-'+str(count)+'.json','contentDigest':digest(raw),'sizeBytes':len(raw),'producerNodeId':'SyntheticProducer','provenanceDigest':digest(b'synthetic-owned-source')}
 records[key]={'recordId':key,'jobId':JOB,'owner':'synthetic-owner','artifactRef':ref,'bytes':raw,'contentDigest':digest(raw),'schema':ref['schema']}
 return ref
schema_ref=persist('JSON_SCHEMA_BUNDLE',schema_doc)
def schema_artifact():return {'schemaId':schema_doc['$id'],'dialect':schema_doc['$schema'],'rootPointer':'','bundle':copy.deepcopy(schema_ref),'nativeSchemaDigest':digest(canonical(schema_doc))}
def transform(value):
 if isinstance(value,dict):
  keys=set(value)
  if keys==CR_FIELDS:
   kind=value['recordKind'] if value['recordKind'] in domain_map else 'ACCEPTANCE_CRITERION'
   return contract_record(kind)
  if keys==SA_FIELDS:return schema_artifact()
  if keys==AR_FIELDS:
   kind=value['kind'] if value['kind'] in artifact_map or value['kind'] in raw_kinds or value['kind']=='JSON_SCHEMA_BUNDLE' else 'SOURCE'
   return artifact(kind)
  out={k:transform(v) for k,v in value.items()}
  if out.get('recordKind')=='DESIGN_ARTIFACT_EXPECTATION':return copy.deepcopy(expectation)
  if 'documentSchema' in out and 'document' in out:out['document']={'syntheticValue':'ok'}
  if 'observationSchema' in out and 'observations' in out:out['observations']={'syntheticValue':'ok'}
  return out
 if isinstance(value,list):return [transform(v) for v in value]
 return value

def artifact(kind):
 if kind=='JSON_SCHEMA_BUNDLE':return copy.deepcopy(schema_ref)
 if kind in raw_kinds:return persist(kind,b'Synthetic exact raw source\n')
 if kind in artifact_cache:return copy.deepcopy(artifact_cache[kind])
 definition=artifact_map[kind]
 value=transform(witness(defs[definition],defs))
 ref=persist(kind,value,definition);artifact_cache[kind]=ref;return copy.deepcopy(ref)

def vector(valid):
 v={'schemaVersion':'1.0','vectorId':'SyntheticPositive' if valid else 'SyntheticNegative','fixtureOnly':True,'targetSchema':schema_artifact(),'input':{'syntheticValue':'ok'} if valid else {},'expectedValid':valid,'expectedFailurePointers':[] if valid else ['']}
 return persist('CONTRACT_VECTOR',v,'ContractVector')

def contract_record(kind):
 if kind in record_cache:return copy.deepcopy(record_cache[kind])
 definition=domain_map[kind]
 value=transform(witness(defs[definition],defs))
 if definition=='AcceptanceCriterion':value['criterionId']=CRIT;value['requirementIds']=[REQ]
 # Every PredicateContract includes actual schema-positive/negative vectors,
 # while its generated implementation remains an exact typed expectation.
 def finish(v):
  if isinstance(v,dict):
   if set(v)=={'predicateId','inputSchema','implementation','expectedBoolean','positiveVectorRefs','negativeVectorRefs'}:
    v['implementation']=copy.deepcopy(expectation);v['positiveVectorRefs']=[vector(True)];v['negativeVectorRefs']=[vector(False)]
   for x in v.values():finish(x)
  elif isinstance(v,list):
   for x in v:finish(x)
 finish(value)
 # TargetGraph/requirement-specific semantic field links are set afterhydration.
 normalized=copy.deepcopy(value)
 if 'canonicalDigest' in normalized:normalized['canonicalDigest']=None
 ref=persist(kind,value,definition)
 record={'recordId':'Synthetic'+kind.replace('_',''),'recordKind':kind,'recordDigest':digest(canonical(normalized)),'schema':ref['schema'],'artifact':ref}
 record_cache[kind]=record;return copy.deepcopy(record)

spec=transform(witness(defs['GenerationSpecification'],defs));spec['jobId']=JOB;spec['openQuestions']=[]
spec['behavioralRequirements']=[{'requirementId':REQ,'kind':'BUSINESS','statement':'Produce the exact synthetic nonempty string result','sourceRefs':[{'section':'12.20','anchor':'SyntheticOwnerRequirement','sourceDigest':digest(b'synthetic owner decision'),'relation':'AUTHORITY'}],'ownerDecisionIds':[],'dependsOn':[],'acceptanceIds':[CRIT],'domainContractRefs':[contract_record('ACCEPTANCE_CRITERION')]}]
coverage=spec['capabilityDecision']['coverage'][0];coverage['requirementId']=REQ;coverage['verificationContractRefs']=[contract_record('ACCEPTANCE_CRITERION')]
spec['capabilityDecision']['coverage']=[coverage];spec['capabilityDecision']['uncoveredRequirementIds']=[]
# Fixproducerrequirementmetadata in every alreadygeneratedtypedexpectation.
source_raw=canonical(spec)
def repo(rs_override=None):return Repository(copy.deepcopy(rs_override if rs_override is not None else records),{gb:gen_raw},artifact_map,'synthetic-owner')
def validator(rs_override=None,stage='PRE_GENERATION_DESIGN'):return GraphValidator(repo(rs_override),domain_map,raw_kinds,stage)
