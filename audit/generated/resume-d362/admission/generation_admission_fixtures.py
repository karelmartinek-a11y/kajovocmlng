"""Positive-derived own-kind basis checks; pinned document bytes, no network."""
import copy,hashlib,json,re,subprocess,sys
from pathlib import Path
from generation_admission_reference import *
from ssot_sources import resources,resource_index
from verify_phase2_handoffs import witness
PIN='d362487999bd795d4723c2a930e93fc7aa8aa295'
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
source=subprocess.check_output(['git','show',PIN+':00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT)
assert hashlib.sha256(source).hexdigest()=='22256baa17729b7577ca4e2498b74b7dfc2b3e6bab57f3b88c338a059557a0ee'
rs=resource_index(resources(source.decode()));gen_raw=rs['contracts/generation/generation-contracts.schema.json']['raw'];gen=json.loads(gen_raw)
artifact_map=json.loads(rs['contracts/generation/artifact-schema-map.json']['raw'])
local_raw=canonical(local_bundle());gb=digest(gen_raw);lb=digest(local_raw)
ids=lambda n:'00000000-0000-4000-8000-'+str(n).zfill(12)
JOB=ids(1);REV=ids(2);AUTH=ids(3);TARGET=ids(4);SNAP=ids(5);RUN=ids(6);PLAN=ids(7);APP=ids(8);MON=ids(9);MREC=ids(10);SCHEMA=ids(11);SREC=ids(12);INITIAL=ids(13);SPEC=ids(14)
defs=copy.deepcopy(gen['$defs'])
for k,v in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-30T00:00:00.000Z','RelPath':'synthetic.json','JsonPointer':'','NonemptyJsonPointer':'/synthetic'}.items():defs[k]={'const':v}
records={}
def put(key,value,definition,job=JOB,native=False,**metadata):
 raw=canonical(value)
 records[key]={'recordId':key,'jobId':job,'owner':'synthetic-owner','contentDigest':digest(raw),'bytes':raw,
 'schema':{'schemaId':GEN if native else 'urn:kcml:generation-admission-basis:1','bundleDigest':gb if native else lb,'definition':definition},**metadata}
 return records[key]['contentDigest']
native_authority=witness(defs['GenerationAuthority'],defs)
NATIVE_AUTHORITY=ids(44);nadig=put(NATIVE_AUTHORITY,native_authority,'GenerationAuthority',native=True)
spec=witness(defs['GenerationSpecification'],defs);spec['jobId']=JOB;spec['openQuestions']=[]
spec['authorityModel'].update(recordKind='GENERATION_AUTHORITY',recordId='SyntheticAuthority',recordDigest=nadig,schema=records[NATIVE_AUTHORITY]['schema'])
spec['authorityModel']['artifact'].update(artifactId=NATIVE_AUTHORITY,kind='GENERATION_AUTHORITY',contentDigest=nadig,schema=records[NATIVE_AUTHORITY]['schema'],sizeBytes=len(records[NATIVE_AUTHORITY]['bytes']))
records[NATIVE_AUTHORITY]['artifactRef']=copy.deepcopy(spec['authorityModel']['artifact'])
specdig=put(REV,spec,'ApprovedGenerationSpecification',native=True)
put(SPEC,spec,'GenerationSpecification',native=True)
target={'snapshotId':SNAP,'objectId':TARGET,'targetKind':'PLATFORM_COMPONENT','componentId':ids(40),'runtimeInstanceIds':[ids(41)],'revisionId':ids(42),'releaseId':ids(43),'bindingSetRevision':'2','activationEpoch':'7','lastApprovedAuthorityId':AUTH,'lastApprovedSpecificationRevisionId':REV,'lastApprovedSpecificationDigest':specdig}
targetdig=put(SNAP,target,'TargetIdentitySnapshot')
authority={'authorityId':AUTH,'sourceJobId':JOB,'specificationRevisionId':REV,'specificationDigest':specdig,'kind':'OWNER_APPROVED','ownerApprovalEventId':APP,'authority':native_authority,'targetSnapshotDigest':targetdig,'frozenAt':'2026-09-30T00:00:00.000Z'}
authdig=put(AUTH,authority,'GenerationExecutionAuthoritySnapshot')
put(APP,{'receiptId':APP,'sourceJobId':JOB,'revisionId':REV,'specificationDigest':specdig,'outcome':'COMMITTED'},'OwnerApprovalReceipt')
plan=witness(defs['GenerationPlan'],defs);plan['jobId']=JOB;plan['planId']=PLAN;plan['specificationDigest']=specdig;plan['scopeLock']['approvedSpecificationDigest']=specdig
plan['nodes'][0]['nodeId']='SyntheticBuild';plan['nodes'][0]['kind']='BUILD';plan['nodes'][0]['phase']='IMPLEMENTING';plan['nodes'][0]['executionRole']='WORKSPACE_WORKER';plan['nodes'][0]['purpose']='Compile synthetic immutable implementation input'
plandig=put(PLAN,plan,'GenerationPlan',native=True)
result={'jobId':JOB,'phaseRunId':RUN,'failedNodeIds':['SyntheticBuild'],'outcome':'KNOWN_FAILURE','errorCodes':['LEASE_EXPIRED']}
resultdig=digest(canonical(result));put(resultdig,result,'KnownTechnicalFailureResult')
run={'phaseRunId':RUN,'jobId':JOB,'phase':'IMPLEMENTING','attempt':'3','state':'FAILED','resultDigest':resultdig,'failedNodeIds':['SyntheticBuild'],'planId':PLAN,'planDigest':plandig,'authorityId':AUTH,'authorityDigest':authdig,'specificationDigest':specdig,'pendingSideEffectIds':[],'completedAt':'2026-09-30T00:00:00.000Z'}
rundig=put(RUN,run,'FailedTechnicalPhaseRun')
obs_schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:synthetic-monitoring-observation:1','type':'object','additionalProperties':False,'required':['measurement','failureCount'],'properties':{'measurement':{'const':'SYNTHETIC_HEALTH_CHECK'},'failureCount':{'type':'integer','minimum':1}}}
obsraw=canonical(obs_schema);obsdig=digest(obsraw)
records[SCHEMA]={'recordId':SCHEMA,'jobId':JOB,'owner':'synthetic-owner','artifactKind':'JSON_SCHEMA_BUNDLE','publicationReceiptId':SREC,'contentDigest':obsdig,'bytes':obsraw,'schema':{'schemaId':'urn:kcml:generation-admission-basis:1','bundleDigest':lb,'definition':'JsonSchemaBundle'}}
put(SREC,{'receiptId':SREC,'jobId':JOB,'artifactId':SCHEMA,'contentDigest':obsdig,'outcome':'COMMITTED'},'PublicationReceipt')
evidence=witness(defs['EvidenceRecord'],defs);evidence.update({'evidenceId':MON,'kind':'SYNTHETIC_HEALTH_FAILURE','subjectDigest':targetdig,'observations':{'measurement':'SYNTHETIC_HEALTH_CHECK','failureCount':2}})
evidence['observationSchema']={'schemaId':obs_schema['$id'],'dialect':'https://json-schema.org/draft/2020-12/schema','rootPointer':'','bundle':witness(defs['ArtifactRef'],defs),'nativeSchemaDigest':obsdig}
evidence['observationSchema']['bundle'].update({'artifactId':SCHEMA,'kind':'JSON_SCHEMA_BUNDLE','contentDigest':obsdig,'schema':records[SCHEMA]['schema'],'sizeBytes':len(obsraw)})
mondig=put(MON,evidence,'EvidenceRecord',native=True,artifactKind='MONITORING_EVIDENCE',publicationReceiptId=MREC)
put(MREC,{'receiptId':MREC,'jobId':JOB,'artifactId':MON,'contentDigest':mondig,'outcome':'COMMITTED'},'PublicationReceipt')
put(INITIAL,{'intent':'Synthetic immutable discussion request','kind':'CREATE'},'GenerationJobCreateBody')
common={'approvedRevisionId':REV,'expectedSpecificationDigest':specdig,'authorityId':AUTH,'expectedAuthorityDigest':authdig}
bodies={
 'UPDATE':{'kind':'UPDATE','intent':'Discuss compatible synthetic implementation update','targetKind':'PLATFORM_COMPONENT','targetObjectId':TARGET,'generationBasis':{'basisKind':'UPDATE_TARGET_REVISION','snapshotId':SNAP,'expectedDigest':targetdig}},
 'RETRY':{'kind':'RETRY','intent':'Repeat the exact failed synthetic technical compile','parentJobId':JOB,'generationBasis':{'basisKind':'RETRY_FAILED_TECHNICAL_PART','phaseRunId':RUN,'expectedDigest':rundig,'planId':PLAN,'expectedPlanDigest':plandig,**common}},
 'REPAIR':{'kind':'REPAIR','intent':'Repair synthetic health failure within approved functional lineage','targetKind':'PLATFORM_COMPONENT','targetObjectId':TARGET,'generationBasis':{'basisKind':'REPAIR_MONITORING_EVIDENCE','monitoringArtifactId':MON,'expectedDigest':mondig,'snapshotId':SNAP,'expectedTargetDigest':targetdig,**common}}}
def repo(rs=None,bs=None):return Repository(rs or copy.deepcopy(records),bs or {gb:gen_raw,lb:local_raw},artifact_map,'synthetic-owner',{TARGET:{'snapshotId':SNAP,'contentDigest':targetdig}})
