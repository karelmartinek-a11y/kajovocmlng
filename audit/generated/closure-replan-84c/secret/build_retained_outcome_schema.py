from pathlib import Path
import json,copy
OUT=Path(__file__).parent
j=json.loads((OUT/'effective-contracts.json').read_text());response=j['response'];uid={'type':'string','format':'uuid','pattern':r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$(?![\s\S])'};digest={'type':'string','pattern':r'^sha256:[0-9a-f]{64}$(?![\s\S])'}
error=next(x for x in response['properties']['error']['oneOf']if x.get('type')!='null')
from contract_delta import retained_error_reason
error=retained_error_reason(error)
nullable=lambda s:{'oneOf':[s,{'type':'null'}]}
states=['RESERVED','EXECUTING','WAITING_FOR_INPUT','WAITING_FOR_RECONCILIATION','MANUAL_REVIEW','FAILED_FINAL','CANCELLED_FINAL']
def obj(p):return {'type':'object','additionalProperties':False,'properties':p,'required':list(p)}
properties={'operationId':{'const':'secret.create'},'logicalOperationId':uid,'acceptedContextId':uid,'operationContractRevision':{'type':'string','minLength':1},'requestDigest':digest,'schemaArchiveDigest':digest,'policyArchiveDigest':digest,'outcomeSequence':{**copy.deepcopy(response['properties']['eventSequence']['oneOf'][0]),'not':{'const':'0'}},'state':{'enum':states},'terminal':{'type':'boolean'},'secretId':{'type':'null'},'output':{'type':'null'},'error':nullable(error),'evidenceDigest':digest,'recordedAt':{'type':'string','format':'date-time'}}
payload=obj(properties);payload['allOf']=[{'if':{'properties':{'state':{'enum':['FAILED_FINAL','CANCELLED_FINAL']}}},'then':{'properties':{'terminal':{'const':True},'error':error}},'else':{'properties':{'terminal':{'const':False}}}},{'if':{'properties':{'state':{'const':'CANCELLED_FINAL'}}},'then':{'properties':{'error':{'properties':{'stableCode':{'const':'CREATE_CANCELLED'}}}}}},{'if':{'properties':{'error':{'type':'object','properties':{'classification':{'const':'UNKNOWN'}},'required':['classification']}}},'then':{'properties':{'state':{'enum':['WAITING_FOR_RECONCILIATION','MANUAL_REVIEW']},'terminal':{'const':False}}}}]
payload['allOf'].append({'if':{'properties':{'state':{'const':'FAILED_FINAL'}}},'then':{'properties':{'error':{'properties':{'stableCode':{'not':{'const':'CREATE_CANCELLED'}},'classification':{'not':{'const':'UNKNOWN'}},'retryDirective':{'const':'DO_NOT_RETRY'}}}}}})
# This proposed stream is explicitly COMMAND-owned; no invented Secret aggregate.
event=obj({'eventType':{'const':'domain.command.outcome.updated'},'immutableEventId':uid,'logicalOperationId':uid,'correlationId':uid,'causationId':nullable(uid),'sequence':properties['outcomeSequence'],'occurredAt':properties['recordedAt'],'payload':payload,'payloadDigest':digest})
schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:proposed:secret-create-retained-command:1','$comment':'Inactive technical definition proposal for49.3/49.4/49.5/49.25/51.12. Command-owned pre-root evidence/stream only; exact physical producer and publication must be authoritatively integrated before dispatch. SUCCEEDED uses existing SecretCreated boundary, not rootless payload.','payload':payload,'event':event}
(OUT/'retained-command-outcome.proposed.schema.json').write_text(json.dumps(schema,indent=2)+'\n');print('Exact proposed rootless command outcome mask; inactive, no producer proof')
