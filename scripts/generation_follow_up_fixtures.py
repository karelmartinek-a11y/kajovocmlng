"""Synthetic native FOLLOW_UP fixtures. Real bytes/addresses, no validity flags.

ARTIFACT_MANIFEST finalness is declared by an immutable source result contract,
not inferred from its name, monitoring status, or a publishedFinal boolean.
"""
import copy,hashlib,json,sys
from pathlib import Path
from ssot_sources import SSOT,resource_index,resources
from functools import lru_cache
@lru_cache(maxsize=2)
def _snapshot(raw):return resource_index(resources(raw.decode()))
def load_resource(name):return _snapshot(SSOT.read_bytes())[name]
from verify_phase2_handoffs import witness
from generation_admission_contracts import Repository,canonical,digest,GEN

@lru_cache(maxsize=16)
def _template(basis_kind,owner,job,snapshot,revision,artifact,receipt):
 state='DISCUSSING'
 genraw=load_resource('contracts/generation/generation-contracts.schema.json')['raw'];gen=json.loads(genraw);gd=digest(genraw)
 localraw=load_resource('contracts/generation/admission-basis.schema.json')['raw'];local=json.loads(localraw);ld=digest(localraw)
 defs=copy.deepcopy(gen['$defs'])
 for k,v in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-30T00:00:00.000Z','RelPath':'synthetic.json','JsonPointer':'','NonemptyJsonPointer':'/synthetic'}.items():defs[k]={'const':v}
 records={}
 def put(key,value,definition,native=True,**metadata):
  raw=canonical(value);address={'schemaId':GEN if native else local['$id'],'definition':definition,'bundleDigest':gd if native else ld}
  record={'recordId':key,'jobId':job,'owner':owner,'bytes':raw,'contentDigest':digest(raw),'schema':address,**metadata};records[key]=record;return record
 initial={'intent':'Create the synthetic component that returns the documented exact string.','kind':'CREATE'}
 specification=witness(defs['GenerationSpecification'],defs);specification['jobId']=job;specification['openQuestions']=[]
 specification['behavioralRequirements'][0]['statement']='Return the exact synthetic text without trimming or normalization.'
 final=witness(defs['ArtifactManifest'],defs);final['jobId']=job
 # Schema is actual complete native bundle, selected by exact frozen address.
 bundle_id='10000000-0000-4000-8000-000000000001'
 schema_record={'recordId':bundle_id,'jobId':job,'owner':owner,'bytes':genraw,'contentDigest':gd,'schema':None,'artifactKind':'JSON_SCHEMA_BUNDLE'}
 records[bundle_id]=schema_record
 bundle_ref=witness(defs['ArtifactRef'],defs);bundle_ref.update({'artifactId':bundle_id,'kind':'JSON_SCHEMA_BUNDLE','schema':None,'contentDigest':gd,'sizeBytes':len(genraw)})
 schema_record['artifactRef']=copy.deepcopy(bundle_ref)
 output_schema={'schemaId':GEN,'dialect':gen['$schema'],'rootPointer':'/$defs/ArtifactManifest','bundle':bundle_ref,'nativeSchemaDigest':digest(canonical(gen['$defs']['ArtifactManifest']))}
 result_id='10000000-0000-4000-8000-000000000002'
 result_contract={'resultId':'SyntheticPublishedArtifactManifest','outputSchema':output_schema,'targetKeys':['SyntheticComponent'],'acceptanceCriterionIds':['SyntheticManifestAcceptance'],'closurePredicateId':'SyntheticManifestClosure'}
 result_record=put(result_id,result_contract,'GenerationResult')
 result_ref=witness(defs['ContractRecordRef'],defs);result_ref.update({'recordId':'SyntheticPublishedArtifactManifest','recordKind':'GENERATION_RESULT','recordDigest':result_record['contentDigest'],'schema':result_record['schema']})
 result_ref['artifact'].update({'artifactId':result_id,'kind':'GENERATION_RESULT','schema':result_record['schema'],'contentDigest':result_record['contentDigest'],'sizeBytes':len(result_record['bytes'])})
 result_record['artifactRef']=copy.deepcopy(result_ref['artifact']);specification['resultContract']=result_ref
 spec_record=put(revision,specification,'GenerationSpecification')
 selector=''
 if basis_kind=='INITIAL_REQUEST':record=put(snapshot,initial,'GenerationJobCreateBody',False)
 elif basis_kind=='SPECIFICATION_REVISION':selector=revision;record=spec_record
 elif basis_kind=='PUBLISHED_FINAL_OUTPUT':
  selector=artifact;record=put(artifact,final,'ArtifactManifest',artifactKind='ARTIFACT_MANIFEST',publicationReceiptId=receipt)
 else:raise ValueError('Unsupported basis kind')
 record.update({'snapshotId':snapshot,'basisKind':basis_kind,'immutable':True,'available':True})
 if selector:record['revisionId' if basis_kind=='SPECIFICATION_REVISION' else 'artifactId']=selector
 basis={'basisKind':basis_kind,'expectedDigest':record['contentDigest']}
 if selector:basis['revisionId' if basis_kind=='SPECIFICATION_REVISION' else 'artifactId']=selector
 body={'intent':'Discuss an independent synthetic FOLLOW_UP using its immutable declared source.','kind':'FOLLOW_UP','parentJobId':job,'followUpBasis':basis}
 repository=Repository.from_current_ssot(records,owner)
 server={'owner':owner,'actor':'OWNER','authenticated':True,'recovery':'READY','atomicGenerationAdmission':True,
 'jobs':{job:{'jobId':job,'owner':owner,'state':state}},'sourceSnapshots':{(job,basis_kind,selector):record},'generationBasisRepository':repository}
 if basis_kind=='PUBLISHED_FINAL_OUTPUT':
  record['publicationReceiptId']=receipt
  receipt_value={'receiptId':receipt,'jobId':job,'artifactId':artifact,'contentDigest':record['contentDigest'],'outcome':'COMMITTED'}
  put(receipt,receipt_value,'PublicationReceipt',False)
  server['publicationReceipts']={receipt:copy.deepcopy(receipt_value)}
  # Explicit final slot binding freezes both source revision and its result
  # declaration. It is not a model/client claim or a generic final=true flag.
  server['finalOutputDeclarations']={(job,artifact):{'sourceRevisionId':revision,'sourceSpecificationDigest':spec_record['contentDigest'],
   'resultContractArtifactId':result_id,'resultContractDigest':result_record['contentDigest'],'artifactId':artifact,'contentDigest':record['contentDigest'],'publicationReceiptId':receipt}}
 return body,server,(job,basis_kind,selector)



def factory(basis_kind,owner,job,snapshot,revision,artifact,receipt,state='DISCUSSING'):
 """Fresh mutable records per test, pinned immutable registry reused by identity."""
 template=_template(basis_kind,owner,job,snapshot,revision,artifact,receipt)
 repository=template[1]['generationBasisRepository']
 immutable=[repository.registry,repository.decoded,repository.bundles,repository.artifact_map]
 result=copy.deepcopy(template,{id(v):v for v in immutable})
 result[1]['jobs'][job]['state']=state
 return result
