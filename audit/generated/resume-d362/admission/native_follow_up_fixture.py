"""Synthetic native FOLLOW_UP fixtures. Real bytes/addresses, no validity flags.

ARTIFACT_MANIFEST finalness is declared by an immutable source result contract,
not inferred from its name, monitoring status, or a publishedFinal boolean.
"""
import copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'scripts'))
from ssot_sources import load_resource,SSOT
from verify_phase2_handoffs import witness
from generation_admission_contracts import Repository,canonical,digest,GEN

_templates={}
def _current_template():
 # Template reuse is keyed by actual whole-SSOT bytes. All schema/domain maps
 # are checked by the real from_current_ssot loader once for that source.
 key=hashlib.sha256(SSOT.read_bytes()).hexdigest()
 if key not in _templates:
  genraw=load_resource('contracts/generation/generation-contracts.schema.json')['raw'];gen=json.loads(genraw)
  localraw=load_resource('contracts/generation/admission-basis.schema.json')['raw'];local=json.loads(localraw)
  template=Repository.from_current_ssot({},'synthetic-template-owner')
  if hashlib.sha256(SSOT.read_bytes()).hexdigest()!=key:raise ValueError('FIXTURE_SOURCE_CHANGED_DURING_LOAD')
  _templates.clear();_templates[key]=(genraw,gen,localraw,local,template)
 return _templates[key]

def factory(basis_kind,owner,job,snapshot,revision,artifact,receipt,state='DISCUSSING'):
 genraw,gen,localraw,local,template=_current_template();gd=digest(genraw);ld=digest(localraw)
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
 repository=copy.copy(template);repository.records=records;repository.owner=owner;repository.consulted={};repository.usedBundles=set();repository.targetHeads={}
 repository.decoded=copy.deepcopy(template.decoded);repository.bundles=copy.copy(template.bundles);repository.artifact_map=copy.copy(template.artifact_map)
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
 if record.get('artifactRef')!=reference['artifact'] or record['schema']!=reference['schema']:fail('GENERATION_FINAL_RESULT_CONTRACT_LEDGER_MISMATCH')
 output,out_record=repository.artifact(artifact,selector['expectedDigest'],job_id=job)
 if out_record.get('publicationReceiptId')!=declaration['publicationReceiptId']:fail('GENERATION_FINAL_OUTPUT_PUBLICATION_REFERENCE_MISMATCH')
 schema=result['outputSchema'];bundle_ref=schema['bundle'];bundle_record=repository.records.get(bundle_ref['artifactId'])
 if bundle_record is None:fail('GENERATION_FINAL_OUTPUT_SCHEMA_UNAVAILABLE')
 if bundle_record.get('owner')!=repository.owner or bundle_record.get('recordId')!=bundle_ref['artifactId'] or bundle_record.get('artifactRef')!=bundle_ref:fail('GENERATION_FINAL_OUTPUT_SCHEMA_LEDGER_MISMATCH')
 raw=bundle_record.get('bytes')
 if not isinstance(raw,bytes) or len(raw)!=bundle_ref['sizeBytes'] or digest(raw)!=bundle_ref['contentDigest'] or bundle_record.get('contentDigest')!=bundle_ref['contentDigest']:fail('GENERATION_FINAL_OUTPUT_SCHEMA_BYTES_MISMATCH')
 parsed=source_json(raw)
 if parsed.get('$id')!=schema['schemaId']:fail('GENERATION_FINAL_OUTPUT_SCHEMA_ID_MISMATCH')
 selected=parsed
 for token in schema['rootPointer'].split('/')[1:]:
  key=token.replace('~1','/').replace('~0','~')
  if not isinstance(selected,dict) or key not in selected:fail('GENERATION_FINAL_OUTPUT_SCHEMA_POINTER_UNRESOLVED')
  selected=selected[key]
 if digest(canonical(selected))!=schema['nativeSchemaDigest']:fail('GENERATION_FINAL_OUTPUT_SCHEMA_DIGEST_MISMATCH')
 compiled=copy.deepcopy(parsed)
 if schema['rootPointer']:compiled['$ref']='#'+schema['rootPointer']
 else:compiled.pop('$ref',None)
 validate(compiled,output,repository.registry,'GENERATION_FINAL_OUTPUT_CONSUMER_SCHEMA_INVALID')
 repository.consulted[bundle_ref['artifactId']]=bundle_record
 return {'decision':'DECLARED_FINAL_OUTPUT_CONTENT_VALIDATED','sourceRevisionId':declaration['sourceRevisionId'],
 'resultContractArtifactId':declaration['resultContractArtifactId'],'contentDigest':selector['expectedDigest'],
 'closurePredicateId':result['closurePredicateId'],'acceptanceCriterionIds':result['acceptanceCriterionIds'],
 'producerPublicationClosure':'SQL_PRODUCER_COMMIT_CONTRACT_REQUIRED','runtimeAcceptance':'NOT_EVALUATED'}
