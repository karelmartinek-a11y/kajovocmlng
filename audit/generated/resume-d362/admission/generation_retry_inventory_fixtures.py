"""Read-only fixture builders; importing this module performs no writes or tests."""
import copy
from generation_admission_fixtures import *
from generation_retry_inventory import *
inventory_raw=canonical(bundle());ib=digest(inventory_raw)
CLASSIFIER=b'''def classify(observation, operation, attempt):
    if observation['requestDigest'] != operation['requestDigest'] or observation['targetIdempotencyKey'] != operation['targetIdempotencyKey']:
        return 'UNKNOWN'
    if observation['appliedOperationId'] is None and observation['beforeVersion'] == observation['afterVersion'] and observation['beforeValueDigest'] == observation['afterValueDigest']:
        return 'CONFIRMED_NOT_APPLIED'
    if observation['appliedOperationId'] == operation['operationId'] and int(observation['afterVersion']) > int(observation['beforeVersion']):
        return 'CONFIRMED_APPLIED'
    return 'UNKNOWN'
'''
CLASSIFIER_ID=ids(510);INVENTORY=ids(511);OBS_SCHEMA=ids(512);OBS_RECEIPT=ids(513)
obs_schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:synthetic-retry-cas-observation:1','type':'object','additionalProperties':False,
 'required':['requestDigest','targetIdempotencyKey','beforeVersion','afterVersion','beforeValueDigest','afterValueDigest','appliedOperationId'],
 'properties':{'requestDigest':DIGEST,'targetIdempotencyKey':{'type':'string','minLength':1},'beforeVersion':{'$ref':GEN+'#/$defs/Counter'},'afterVersion':{'$ref':GEN+'#/$defs/Counter'},'beforeValueDigest':DIGEST,'afterValueDigest':DIGEST,'appliedOperationId':{'anyOf':[UID,{'type':'null'}]}}}
def fixture():
 rs2=copy.deepcopy(records);p=copy.deepcopy(plan);p['nodes'][0]['sideEffectClass']='LOCAL_STATE_IDEMPOTENT'
 current_run=copy.deepcopy(run);current_run['planDigest']=digest(canonical(p));rd=digest(canonical(current_run))
 rs2[RUN]['bytes']=canonical(current_run);rs2[RUN]['contentDigest']=rd
 def put(key,value,definition,local=False,**metadata):
  raw=canonical(value);rs2[key]={'recordId':key,'jobId':JOB,'owner':'synthetic-owner','bytes':raw,'contentDigest':digest(raw),'schema':{'schemaId':'urn:kcml:generation-admission-basis:1' if local else INVENTORY_SCHEMA_ID,'bundleDigest':lb if local else ib,'definition':definition},**metadata};return digest(raw)
 rs2[CLASSIFIER_ID]={'recordId':CLASSIFIER_ID,'owner':'synthetic-owner','bytes':CLASSIFIER,'contentDigest':digest(CLASSIFIER)}
 put(OBS_SCHEMA,obs_schema,'JsonSchemaBundle',True,artifactKind='JSON_SCHEMA_BUNDLE',publicationReceiptId=OBS_RECEIPT)
 put(OBS_RECEIPT,{'receiptId':OBS_RECEIPT,'jobId':JOB,'artifactId':OBS_SCHEMA,'contentDigest':rs2[OBS_SCHEMA]['contentDigest'],'outcome':'COMMITTED'},'PublicationReceipt',True)
 obs_ref=witness(defs['ArtifactRef'],defs);obs_ref.update({'artifactId':OBS_SCHEMA,'kind':'JSON_SCHEMA_BUNDLE','schema':rs2[OBS_SCHEMA]['schema'],'contentDigest':rs2[OBS_SCHEMA]['contentDigest'],'sizeBytes':len(rs2[OBS_SCHEMA]['bytes'])})
 descriptor={'schemaId':obs_schema['$id'],'dialect':obs_schema['$schema'],'rootPointer':'','bundle':obs_ref,'nativeSchemaDigest':digest(canonical(obs_schema))}
 operation=ids(520);attempt=ids(521);stateid=ids(522);evidenceid=ids(523);reqdigest=digest(b'synthetic immutable compare-and-set request')
 op={'operationId':operation,'jobId':JOB,'phaseRunId':RUN,'nodeId':'SyntheticBuild','currentAttemptId':attempt,'currentAttemptSequence':'1','currentAttemptStateId':stateid,'currentAttemptStateVersion':'2','state':'CONFIRMED_NOT_APPLIED','requestDigest':reqdigest,
 'retryClass':p['nodes'][0]['retryClass'],'sideEffectClass':p['nodes'][0]['sideEffectClass'],'targetBindingId':ids(524),'targetBindingRevisionId':ids(525),'targetIdempotencyKey':'synthetic-fixed-target-key'}
 od=put(operation,op,'SourceSideEffectOperation')
 a={'attemptId':attempt,'operationId':operation,'jobId':JOB,'phaseRunId':RUN,'attemptSequence':'1','requestDigest':reqdigest,'targetBindingId':op['targetBindingId'],'targetBindingRevisionId':op['targetBindingRevisionId'],'targetIdempotencyKey':op['targetIdempotencyKey']};ad=put(attempt,a,'SourceSideEffectAttempt')
 observed={'requestDigest':reqdigest,'targetIdempotencyKey':op['targetIdempotencyKey'],'beforeVersion':'7','afterVersion':'7','beforeValueDigest':digest(b'old-synthetic-value'),'afterValueDigest':digest(b'old-synthetic-value'),'appliedOperationId':None}
 e={'evidenceId':evidenceid,'operationId':operation,'attemptId':attempt,'jobId':JOB,'phaseRunId':RUN,'requestDigest':reqdigest,'targetBindingId':op['targetBindingId'],'targetBindingRevisionId':op['targetBindingRevisionId'],'targetIdempotencyKey':op['targetIdempotencyKey'],'outcome':op['state'],'recordedAt':'2026-09-30T00:00:00.000Z','classifierId':'SyntheticCASReadBack','classifierDigest':digest(CLASSIFIER),'observationSchema':descriptor,'observations':observed};ed=put(evidenceid,e,'SourceSideEffectOutcomeEvidence')
 state={'attemptStateId':stateid,'operationId':operation,'attemptId':attempt,'attemptSequence':'1','state':op['state'],'stateVersion':'2','evidenceId':evidenceid,'evidenceDigest':ed};sd=put(stateid,state,'SourceSideEffectAttemptState')
 # Independently valid retained history: same operation/attempt/outcome and
 # evidence, older projection version. It is not the current JOIN selector.
 historic={**state,'attemptStateId':ids(530),'stateVersion':'1'}
 put(ids(530),historic,'SourceSideEffectAttemptState')
 inv={'inventoryId':INVENTORY,'jobId':JOB,'phaseRunId':RUN,'phaseRunDigest':rd,'capturedAt':'2026-09-30T00:00:00.000Z','operations':[{'operationId':operation,'operationDigest':od,'attemptId':attempt,'attemptDigest':ad,'attemptStateId':stateid,'attemptStateDigest':sd}]};ind=put(INVENTORY,inv,'PhaseSideEffectInventory')
 repo=Repository(rs2,{gb:gen_raw,lb:local_raw,ib:inventory_raw},artifact_map,'synthetic-owner')
 namespace={'__builtins__':{'int':int}};exec(compile(CLASSIFIER,'synthetic-pinned-cas-classifier','exec'),namespace)
 return repo,current_run,rd,p,ind,{operation:od},{'SyntheticCASReadBack':{'sourceRecordId':CLASSIFIER_ID,'activeSourceDigest':digest(CLASSIFIER),'evaluate':namespace['classify']}}
def call(f):return verify_retry_inventory(f[0],f[1],f[2],f[3],INVENTORY,f[4],f[5],f[6])
