"""Precise create completion design; never a runtime/server receipt implementation."""
import copy, hashlib, json
from functools import lru_cache

PATH='contracts/create-completion.json'
UID={'type':'string','format':'uuid'}
DIGEST={'type':'string','pattern':'^sha256:[0-9a-f]{64}$(?![\\s\\S])'}
COUNTER={'type': 'string', 'minLength': 1, 'maxLength': 19, 'pattern': '^(?:0|[1-9][0-9]{0,17}|[1-8][0-9]{18}|9[0-1][0-9]{17}|92[0-1][0-9]{16}|922[0-2][0-9]{15}|9223[0-2][0-9]{14}|92233[0-6][0-9]{13}|922337[0-1][0-9]{12}|92233720[0-2][0-9]{10}|922337203[0-5][0-9]{9}|9223372036[0-7][0-9]{8}|92233720368[0-4][0-9]{7}|922337203685[0-3][0-9]{6}|9223372036854[0-6][0-9]{5}|92233720368547[0-6][0-9]{4}|922337203685477[0-4][0-9]{3}|9223372036854775[0-7][0-9]{2}|922337203685477580[0-6]|9223372036854775807)$(?![\\s\\S])'}
TIME={'type':'string','format':'date-time'}
OPERATIONS={'generation.job.create':('GenerationCreated','generation.job.created','jobId'),
            'secret.create':('SecretCreated','OPERATION_TERMINAL','secretId')}

def obj(properties):return {'type':'object','additionalProperties':False,'properties':properties,'required':list(properties)}
def nullable(schema):return {'oneOf':[copy.deepcopy(schema),{'type':'null'}]}
def canonical_digest(value):return 'sha256:'+hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

# These are technical stable codes with explicit predicates, not exception names
# assumed to have an existing meaning. Existing stable codes keep their meaning.
ERRORS=[
 {'stableCode':'CREATE_CANCELLED','classification':'CANCELLED','retryDirective':'DO_NOT_RETRY','httpStatus':409,'predicate':'Cancellation won before create commit; no created root; after commit only canonical completed receipt may replay','sources':['49.11','49.25']},
 {'stableCode':'CREATE_INPUT_INVALID','classification':'VALIDATION','retryDirective':'DO_NOT_RETRY','httpStatus':400,'predicate':'Strict HTTP/UTF8/JSON/schema input rejected before domain mutation','sources':['12.47','8.11']},
 {'stableCode':'CREATE_AUTHENTICATION_REQUIRED','classification':'AUTHENTICATION','retryDirective':'DO_NOT_RETRY','httpStatus':401,'predicate':'No current authenticated OWNER context','sources':['21','26','49.4']},
 {'stableCode':'CREATE_REFERENCE_INVALID','classification':'VALIDATION','retryDirective':'DO_NOT_RETRY','httpStatus':422,'predicate':'Referenced artifact/object/parent is missing, wrong identity/kind, or bytes/digest/media evidence is invalid','sources':['25.11','12.47']},
 {'stableCode':'CREATE_POLICY_UNRESOLVED','classification':'DEPENDENCY','retryDirective':'DO_NOT_RETRY','httpStatus':503,'predicate':'Mandatory exact Secret type, ephemeral credential or parent/target admission policy is not resolved; dispatch remains blocked','sources':['8.11','12.47','55.2']},
 {'stableCode':'CREATE_RECOVERY_BARRIER','classification':'CONFLICT','retryDirective':'DO_NOT_RETRY','httpStatus':423,'predicate':'Platform recovery is not READY; no fresh create admission','sources':['49.33','51.12']},
 {'stableCode':'CREATE_STABLE_NAME_CONFLICT','classification':'CONFLICT','retryDirective':'DO_NOT_RETRY','httpStatus':409,'predicate':'secret stableName already exists, including soft-deleted records','sources':['25.6']},
 {'stableCode':'IDEMPOTENCY_CONFLICT','classification':'CONFLICT','retryDirective':'DO_NOT_RETRY','httpStatus':409,'predicate':'Same stable business locator, different caller request digest','sources':['49.4']},
 {'stableCode':'CREATE_PERSISTENCE_FAILED','classification':'INTERNAL','retryDirective':'RETRY_SAME_OPERATION','httpStatus':500,'predicate':'Positive evidence proves the entire create transaction rolled back; no committed root/event/outbox/outcome','sources':['49.25','51.12']},
 {'stableCode':'SIDE_EFFECT_OUTCOME_UNKNOWN','classification':'UNKNOWN','retryDirective':'RECONCILE_THEN_RETRY','httpStatus':503,'predicate':'Create commit/outcome cannot yet be established from persisted canonical evidence; never classify as rolled back','sources':['49.25','32.6']},
 {'stableCode': 'FOLLOW_UP_ATOMIC_ADMISSION_UNVERIFIED', 'classification': 'DEPENDENCY', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 503, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_ATOMIC_ADMISSION_UNVERIFIED; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_BASIS_BYTES_DIGEST_MISMATCH', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_BASIS_BYTES_DIGEST_MISMATCH; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_BASIS_BYTES_UNAVAILABLE', 'classification': 'DEPENDENCY', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 503, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_BASIS_BYTES_UNAVAILABLE; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_BASIS_DIGEST_CONFLICT', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_BASIS_DIGEST_CONFLICT; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_BASIS_IDENTITY_MISMATCH', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_BASIS_IDENTITY_MISMATCH; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_BASIS_INCONSISTENT', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_BASIS_INCONSISTENT; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_BASIS_INSUFFICIENT', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_BASIS_INSUFFICIENT; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_BASIS_INVALID', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_BASIS_INVALID; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_BASIS_NOT_IMMUTABLE', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_BASIS_NOT_IMMUTABLE; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_BASIS_UNAVAILABLE', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_BASIS_UNAVAILABLE; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_FINAL_OUTPUT_UNPUBLISHED', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_FINAL_OUTPUT_UNPUBLISHED; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_FROZEN_DESCRIPTOR_INVALID', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_FROZEN_DESCRIPTOR_INVALID; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_FROZEN_IDENTITY_MISMATCH', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_FROZEN_IDENTITY_MISMATCH; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_FROZEN_LINEAGE_DIGEST_MISMATCH', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_FROZEN_LINEAGE_DIGEST_MISMATCH; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_FROZEN_SNAPSHOT_UNAVAILABLE', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_FROZEN_SNAPSHOT_UNAVAILABLE; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_KIND_REQUIRED', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 400, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_KIND_REQUIRED; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_PARENT_REQUIRED', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_PARENT_REQUIRED; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_PUBLICATION_RECEIPT_MISMATCH', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_PUBLICATION_RECEIPT_MISMATCH; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED', 'classification': 'DEPENDENCY', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 503, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_SNAPSHOT_IDENTITY_INVALID', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_SNAPSHOT_IDENTITY_INVALID; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_SOURCE_OWNER_MISMATCH', 'classification': 'AUTHORIZATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 403, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_SOURCE_OWNER_MISMATCH; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
 {'stableCode': 'FOLLOW_UP_SOURCE_STATE_INVALID', 'classification': 'VALIDATION', 'retryDirective': 'DO_NOT_RETRY', 'httpStatus': 422, 'predicate': 'Exact FOLLOW_UP admission diagnostic FOLLOW_UP_SOURCE_STATE_INVALID; evaluated against atomically captured server-owned immutable basis, never caller authority', 'sources': ['12.49', '49.4', '49.5'], 'operationIds': ['generation.job.create']},
]
from close_create_error_presentation import FOLLOW_UP_REASON
for _error in ERRORS:
 if _error['stableCode'].startswith('FOLLOW_UP_'):
  _error['predicate']=FOLLOW_UP_REASON[_error['stableCode'][10:]][2]+'; evaluated only against trusted atomic admission/persisted hydration, not client assertions'

def definitions():
 from create_operation_contracts import TYPES
 gen=obj({'jobId':UID,'state':{'const':'DISCUSSING'},'stateVersion':COUNTER,
          'initialRequestDigest':DIGEST,'createdAt':TIME,'kind':{'enum':['CREATE','UPDATE','FOLLOW_UP','RETRY','REPAIR']},'frozenBasis':nullable(__import__('follow_up_contracts').frozen_basis_schema())})
 gen['allOf']=[{'if':{'properties':{'kind':{'const':'FOLLOW_UP'}}},'then':{'properties':{'frozenBasis':__import__('follow_up_contracts').frozen_basis_schema()}},'else':{'properties':{'frozenBasis':{'type':'null'}}}}]
 secret=obj({'secretId':UID,'stableName':{'type':'string','minLength':1,'maxLength':256},
             'type':{'type':'string','enum':TYPES},'versionId':UID,'versionNumber':COUNTER,
             'versionState':{'const':'CREATED'},'recordStatus':{'type':'string','const':'INACTIVE','readOnly':True},'activeVersionId':{'type':'null'},
             'stateVersion':COUNTER,'createdAt':TIME})
 # Number allocation is server-owned; there is no invented constant "first=1".
 secret['properties']['versionNumber']={**COUNTER,'not':{'const':'0'}}
 admission_error=obj({'stableCode':{'type':'string'},'classification':{'type':'string'},
                      'retryDirective':{'type':'string'},'message':{'type':'string','maxLength':8192},'detailsDigest':nullable(DIGEST)})
 http=obj({'operationId':{'enum':list(OPERATIONS)},'requestId':UID,'correlationId':UID,
           'logicalOperationId':nullable(UID),'statusCode':{'type':'integer'},'error':admission_error})
 http['oneOf']=[{'properties':{'statusCode':{'const':e['httpStatus']},'error':{'properties':{k:{'const':e[k]} for k in ['stableCode','classification','retryDirective']}}}} for e in ERRORS]
 http['allOf']=[{'if':{'properties':{'operationId':{'const':'generation.job.create'}}},'then':{'properties':{'error':{'properties':{'stableCode':{'not':{'const':'CREATE_STABLE_NAME_CONFLICT'}}}}}}}]
 http['allOf'].append({'if':{'properties':{'operationId':{'const':'secret.create'}}},'then':{'properties':{'error':{'properties':{'stableCode':{'not':{'enum':['FOLLOW_UP_ATOMIC_ADMISSION_UNVERIFIED', 'FOLLOW_UP_BASIS_BYTES_DIGEST_MISMATCH', 'FOLLOW_UP_BASIS_BYTES_UNAVAILABLE', 'FOLLOW_UP_BASIS_DIGEST_CONFLICT', 'FOLLOW_UP_BASIS_IDENTITY_MISMATCH', 'FOLLOW_UP_BASIS_INCONSISTENT', 'FOLLOW_UP_BASIS_INSUFFICIENT', 'FOLLOW_UP_BASIS_INVALID', 'FOLLOW_UP_BASIS_NOT_IMMUTABLE', 'FOLLOW_UP_BASIS_UNAVAILABLE', 'FOLLOW_UP_FINAL_OUTPUT_UNPUBLISHED', 'FOLLOW_UP_FROZEN_DESCRIPTOR_INVALID', 'FOLLOW_UP_FROZEN_IDENTITY_MISMATCH', 'FOLLOW_UP_FROZEN_LINEAGE_DIGEST_MISMATCH', 'FOLLOW_UP_FROZEN_SNAPSHOT_UNAVAILABLE', 'FOLLOW_UP_KIND_REQUIRED', 'FOLLOW_UP_PARENT_REQUIRED', 'FOLLOW_UP_PUBLICATION_RECEIPT_MISMATCH', 'FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED', 'FOLLOW_UP_SNAPSHOT_IDENTITY_INVALID', 'FOLLOW_UP_SOURCE_OWNER_MISMATCH', 'FOLLOW_UP_SOURCE_STATE_INVALID']}}}}}}})
 return {'GenerationCreated':gen,'SecretCreated':secret,'HttpCreateFailure':http}

def specialize(payload):
 result=copy.deepcopy(payload);defs=definitions()
 for row in result['records']:
  operation=row['operationId']
  if operation not in OPERATIONS:continue
  definition,event_type,identity=OPERATIONS[operation];receipt=copy.deepcopy(defs[definition])
  receipt.update({'$id':f'urn:kcml:r9:semantic:{row["routeId"]}:output','$schema':'https://json-schema.org/draft/2020-12/schema'})
  response=row['responseSchema'];p=response['properties'];p['output']=nullable(receipt);p['resultDigest']=copy.deepcopy(DIGEST)
  # Operation completion is distinct from the newly created job's lifecycle.
  p['stateVersion']=nullable(COUNTER);p['eventSequence']=nullable(COUNTER)
  p['activationEpoch']=nullable(COUNTER);p['idempotencyReplay']={'type':'boolean'}
  response['required']=list(dict.fromkeys(response['required']+['stateVersion','eventSequence','activationEpoch','idempotencyReplay']))
  applicable=[e for e in ERRORS if operation in e.get('operationIds', ['secret.create'] if e['stableCode']=='CREATE_STABLE_NAME_CONFLICT' else list(OPERATIONS))]
  error=obj({'stableCode':{'type':'string','enum':[e['stableCode'] for e in applicable]},
             'classification':{'type':'string'},'retryDirective':{'type':'string'},
             'message':{'type':'string','maxLength':8192},'detailsDigest':nullable(DIGEST)})
  error['oneOf']=[{'properties':{k:{'const':e[k]} for k in ['stableCode','classification','retryDirective']}} for e in applicable]
  p['error']=nullable(error)
  response['allOf']=[
   {'if':{'properties':{'status':{'const':'SUCCEEDED'}}},'then':{'properties':{'terminal':{'const':True},'output':receipt,'error':{'type':'null'},'stateVersion':COUNTER,'eventSequence':COUNTER}}},
   {'if':{'properties':{'status':{'const':'ACCEPTED'}}},'then':{'properties':{'terminal':{'const':False},'output':{'type':'null'},'error':{'type':'null'}}}},
   {'if':{'properties':{'status':{'enum':['FAILED','CANCELLED']}}},'then':{'properties':{'output':{'type':'null'},'error':error}}},
   {'if':{'properties':{'error':{'type':'object','properties':{'classification':{'const':'UNKNOWN'}}}}},'then':{'properties':{'terminal':{'const':False}}}},
  ]
  response['allOf'].append({'if':{'properties':{'status':{'const':'CANCELLED'}}},'then':{'properties':{'terminal':{'const':True},'error':{'properties':{'stableCode':{'const':'CREATE_CANCELLED'}}}}}})
  response['allOf'].append({'if':{'properties':{'error':{'type':'object','properties':{'stableCode':{'const':'CREATE_CANCELLED'}}}}},'then':{'properties':{'status':{'const':'CANCELLED'},'terminal':{'const':True}}}})
  response['allOf'].append({'if':{'properties':{'status':{'const':'FAILED'},'error':{'type':'object','properties':{'classification':{'not':{'const':'UNKNOWN'}},'retryDirective':{'not':{'const':'RETRY_SAME_OPERATION'}}}}}},'then':{'properties':{'terminal':{'const':True}}}})
  response['allOf'].append({'if':{'properties':{'status':{'const':'FAILED'},'error':{'type':'object','properties':{'retryDirective':{'const':'RETRY_SAME_OPERATION'}}}}},'then':{'properties':{'terminal':{'const':False}}}})
  # The response union retains pending/failure/unknown transport states; local
  # create completion emits its own typed committed event, not job COMPLETED.
  event=row['eventSchema'];ep=event['properties'];ep['eventType']={'const':event_type};ep['payloadDigest']=copy.deepcopy(DIGEST)
  ep['sequence']={**COUNTER,'not':{'const':'0'}}
  ep['immutableEventId']=UID;ep['aggregateId']=UID;ep['occurredAt']=TIME
  ep['payload']=copy.deepcopy(receipt)
  ep['payload']['$id']=f'urn:kcml:r9:semantic:{row["routeId"]}:event-payload'
  event['required']=list(dict.fromkeys(event['required']+['immutableEventId','aggregateId','occurredAt']))
  row['eventApplicability']='AGGREGATE_STREAM'
  row['semanticRules']=list(dict.fromkeys(row['semanticRules']+[
   'CREATE_COMPLETION_NOT_CHILD_WORKFLOW_COMPLETION','FROZEN_RESULT_REPLAY_NO_NEW_EVENT',
   'CREATE_ROOT_RECEIPT_EVENT_AUDIT_OUTBOX_ATOMIC','EVENT_PUBLISH_ONLY_AFTER_COMMIT',
   'SERVER_RECEIPT_IDENTITY_DIGEST_RELATIONS','CREATE_ERRORS_EXACT_PREDICATE_AND_RETRY']))
 result['canonicalDigest']=canonical_digest({**result,'canonicalDigest':None})
 return result

def contract():
 return {'format':'KCML-CREATE-COMPLETION/1','authority':['12.48','25.6','25.11','49.4','49.5','49.22.1','51.9','51.12','72.11','72.21'],
  'operations':{oid:{'outputDefinition':definition,'eventType':event,'aggregateIdentityField':field,
   'eventApplicability':'AGGREGATE_STREAM','requestPolicyClosure':'PARTIAL',
   'runtimeAcceptance':'NOT_EVALUATED'} for oid,(definition,event,field) in OPERATIONS.items()},
  'errorPredicates':[{**e,'operationIds':e.get('operationIds',['secret.create'] if e['stableCode']=='CREATE_STABLE_NAME_CONFLICT' else list(OPERATIONS))} for e in ERRORS],
  'httpFailureDefinition':'urn:kcml:create-operation-design:1#/$defs/HttpCreateFailure',
  'transactions':['Authenticate/freeze OWNER context and lock current platform/deployment heads','Stable locator lookup before fresh admission; matching request digest pins old frozen execution descriptor','Reserve one canonical root identity; verify referenced target/parent policy under its current locks','Persist immutable caller request and references; Secret encrypted version CREATED under master-key policy, generation job DISCUSSING','Allocate aggregate-local contiguous sequence; persist typed event, audit and outbox with root and canonical outcome in one commit','Publish only after commit; immutable receipt replay never mutates root or emits another event'],
  'postconditions':['Receipt identity belongs to exact committed aggregate','Result digest recomputed from frozen semantic response excluding transport replay marker','Event receipt equals frozen response output; payload digest covers exact canonical receipt','Read/hydration selects persisted root/version by server ID and verifies immutable initial/version linkage; current state may evolve without rewriting frozen receipt','Unknown commit outcome reconciles the same locator; no new root or side effect'],
  'open':['Nine structured/cryptographic Secret type value grammars','Exact parent/target lifecycle admission matrix','SQL physical/helper executable proof','Full UI and consumer runtime implementation']}

def semantic_result(response):
 """Replay transport marker never changes the frozen operation result."""
 return {k:v for k,v in response.items() if k not in ['resultDigest','idempotencyReplay']}

def http_failure(operation,failure,*,request_id,correlation_id,logical_operation_id=None):
 """Deterministic projection of known reference diagnostics; no HTTP server."""
 from create_operation_contracts import ContractFailure
 code=failure.code
 if code in ['FOLLOW_UP_ATOMIC_ADMISSION_UNVERIFIED', 'FOLLOW_UP_BASIS_BYTES_DIGEST_MISMATCH', 'FOLLOW_UP_BASIS_BYTES_UNAVAILABLE', 'FOLLOW_UP_BASIS_DIGEST_CONFLICT', 'FOLLOW_UP_BASIS_IDENTITY_MISMATCH', 'FOLLOW_UP_BASIS_INCONSISTENT', 'FOLLOW_UP_BASIS_INSUFFICIENT', 'FOLLOW_UP_BASIS_INVALID', 'FOLLOW_UP_BASIS_NOT_IMMUTABLE', 'FOLLOW_UP_BASIS_UNAVAILABLE', 'FOLLOW_UP_FINAL_OUTPUT_UNPUBLISHED', 'FOLLOW_UP_FROZEN_DESCRIPTOR_INVALID', 'FOLLOW_UP_FROZEN_IDENTITY_MISMATCH', 'FOLLOW_UP_FROZEN_LINEAGE_DIGEST_MISMATCH', 'FOLLOW_UP_FROZEN_SNAPSHOT_UNAVAILABLE', 'FOLLOW_UP_KIND_REQUIRED', 'FOLLOW_UP_PARENT_REQUIRED', 'FOLLOW_UP_PUBLICATION_RECEIPT_MISMATCH', 'FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED', 'FOLLOW_UP_SNAPSHOT_IDENTITY_INVALID', 'FOLLOW_UP_SOURCE_OWNER_MISMATCH', 'FOLLOW_UP_SOURCE_STATE_INVALID']:stable=code
 elif code in ['SCHEMA_'+keyword for keyword in ['ADDITIONALPROPERTIES','ALLOF','ANYOF','CONST','ENUM','FORMAT','MAXIMUM','MINIMUM','MULTIPLEOF','MINLENGTH','MAXLENGTH','MINITEMS','MAXITEMS','MINPROPERTIES','MAXPROPERTIES','NOT','ONEOF','PATTERN','REQUIRED','TYPE','UNIQUEITEMS']] or code in ['INVALID_UTF8','INVALID_JSON','INVALID_UNICODE','DUPLICATE_JSON_KEY','NONFINITE_JSON_NUMBER','INVALID_BASE64','NONCANONICAL_BASE64','UNKNOWN_QUERY_PARAMETER','DUPLICATE_HEADER','CONTENT_TYPE_MISMATCH','IDEMPOTENCY_KEY_REQUIRED','UNDECLARED_CREATE_GUARD_OR_AUTHORITY','REQUEST_TOO_LARGE','CLIENT_DIGEST_MISMATCH','EMPTY_INTENT','EMPTY_STABLENAME','EMPTY_DISPLAYNAME','DUPLICATE_ARTIFACT_REFERENCE','RESERVED_CREDENTIAL_REQUIRES_SPECIAL_CONTRACT']:
  stable='CREATE_INPUT_INVALID'
 elif code in __import__('generation_admission_diagnostics').codes():
  if operation!='generation.job.create':raise ContractFailure('HTTP_FAILURE_OPERATION_MISMATCH','/operationId')
  stable=__import__('generation_admission_diagnostics').codes()[code]
 elif code in __import__('secret_profile_diagnostics').CODES:
  if operation!='secret.create':raise ContractFailure('HTTP_FAILURE_OPERATION_MISMATCH','/operationId')
  stable=__import__('secret_profile_diagnostics').CODES[code]
 elif code=='AUTHENTICATION_REQUIRED':stable='CREATE_AUTHENTICATION_REQUIRED'
 elif code=='RECOVERY_BARRIER':stable='CREATE_RECOVERY_BARRIER'
 elif code=='IDEMPOTENCY_CONFLICT':stable=code
 elif code=='STABLE_NAME_UNAVAILABLE':stable='CREATE_STABLE_NAME_CONFLICT'
 elif code in ['TYPE_SPECIFIC_POLICY_UNVERIFIED','EPHEMERAL_CREDENTIAL_POLICY_UNVERIFIED','PARENT_TARGET_ADMISSION_POLICY_UNVERIFIED','REPLAY_LOCATOR_UNVERIFIED','REPLAY_DESCRIPTOR_UNVERIFIED','REPLAY_DESCRIPTOR_DIGEST_MISMATCH','REPLAY_FROZEN_SCOPE_MISMATCH']:stable='CREATE_POLICY_UNRESOLVED'
 elif code in ['ARTIFACT_UNRESOLVED','ARTIFACT_LINEAGE_UNVERIFIED','ARTIFACT_OWNER_MISMATCH','ARTIFACT_BYTES_UNAVAILABLE','ARTIFACT_IDENTITY_MISMATCH','ARTIFACT_DIGEST_UNAVAILABLE','ARTIFACT_BYTES_DIGEST_MISMATCH','ARTIFACT_MEDIA_TYPE_MISMATCH','ARTIFACT_BYTES_MEDIA_INVALID','TARGET_UNRESOLVED','TARGET_KIND_MISMATCH','TARGET_IDENTITY_MISMATCH','PARENT_JOB_UNRESOLVED','PARENT_JOB_IDENTITY_MISMATCH','OBJECT_REFERENCE_UNRESOLVED','OBJECT_REFERENCE_IDENTITY_MISMATCH','SECRET_REFERENCE_UNRESOLVED','MODEL_UNAVAILABLE','SOURCE_NAVIGATION_POLICY_REJECT','SECRET_USE_CONTEXT_UNVERIFIED']:stable='CREATE_REFERENCE_INVALID'
 else:raise ContractFailure('HTTP_FAILURE_PROJECTION_UNRESOLVED','/error')
 if operation not in OPERATIONS or operation not in next(e for e in ERRORS if e['stableCode']==stable).get('operationIds',['secret.create'] if stable=='CREATE_STABLE_NAME_CONFLICT' else list(OPERATIONS)):
  raise ContractFailure('HTTP_FAILURE_OPERATION_MISMATCH','/operationId')
 definition=next(e for e in ERRORS if e['stableCode']==stable)
 return {'operationId':operation,'requestId':request_id,'correlationId':correlation_id,
         'logicalOperationId':logical_operation_id,'statusCode':definition['httpStatus'],
         'error':{k:definition[k] for k in ['stableCode','classification','retryDirective']}|
                 {'message':stable,'detailsDigest':canonical_digest({'reason':code,'pointer':failure.pointer})}}

@lru_cache(maxsize=2)
def _rows(source_digest):
 from ssot_sources import SSOT,resource_index,resources
 from create_operation_contracts import ContractFailure
 raw=SSOT.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=source_digest:raise ContractFailure('CREATE_SOURCE_CHANGED','/source')
 rs=resource_index(resources(raw.decode('utf8')))
 return {r['operationId']:r for r in json.loads(rs['contracts/payload-contracts.json']['raw'])['records'] if r['operationId'] in OPERATIONS}

def validate_completion(operation,response,event,*,committed,persisted,hydrated):
 """Executable DESIGN relations over trusted persisted inputs; no runtime claim.

 Hydrated bytes are the stored frozen creation receipt, not a fabricated full
 generation document or a current-state read snapshot. Full consumers remain
 separately obligated by the completion register.
 """
 from jsonschema import Draft202012Validator,FormatChecker
 from create_operation_contracts import ContractFailure,strict_json
 from ssot_sources import SSOT
 row=_rows(hashlib.sha256(SSOT.read_bytes()).hexdigest())[operation]
 errors=list(Draft202012Validator(row['responseSchema'],format_checker=FormatChecker()).iter_errors(response))
 if errors:raise ContractFailure('CREATE_RESPONSE_SCHEMA_INVALID',errors[0].json_path)
 if canonical_digest(semantic_result(response))!=response['resultDigest']:raise ContractFailure('RESULT_DIGEST_MISMATCH','/response/resultDigest')
 if response['status']!='SUCCEEDED':
  if event is not None:raise ContractFailure('UNCOMMITTED_CREATE_EVENT','/event')
  return {'action':'RECONCILE_ORIGINAL_OPERATION' if (response.get('error') or {}).get('classification')=='UNKNOWN' else 'NO_CREATE_RECEIPT'}
 errors=list(Draft202012Validator(row['eventSchema'],format_checker=FormatChecker()).iter_errors(event))
 if errors:raise ContractFailure('CREATE_EVENT_SCHEMA_INVALID',errors[0].json_path)
 if committed is not True:raise ContractFailure('COMMIT_NOT_VERIFIED','/commit')
 definition,event_type,key=OPERATIONS[operation];output=response['output']
 if operation=='generation.job.create' and output['kind']=='FOLLOW_UP':
  descriptor=output['frozenBasis']
  if descriptor['lineageDigest']!=canonical_digest({k:v for k,v in descriptor.items() if k!='lineageDigest'}):raise ContractFailure('FOLLOW_UP_RECEIPT_LINEAGE_MISMATCH','/response/output/frozenBasis/lineageDigest')
 if response['stateVersion']!=output['stateVersion']:raise ContractFailure('RESPONSE_STATE_VERSION_MISMATCH','/response/stateVersion')
 if response['activationEpoch'] is not None:raise ContractFailure('CREATE_ACTIVATION_FORBIDDEN','/response/activationEpoch')
 if event['sequence']!=response['eventSequence']:raise ContractFailure('EVENT_SEQUENCE_MISMATCH','/event/sequence')
 if event['aggregateId']!=output[key]:raise ContractFailure('EVENT_AGGREGATE_ID_MISMATCH','/event/aggregateId')
 if event['logicalOperationId']!=response['logicalOperationId']:
  raise ContractFailure('EVENT_OPERATION_CONTEXT_MISMATCH','/event/logicalOperationId')
 if event['correlationId']!=response['correlationId']:raise ContractFailure('EVENT_OPERATION_CONTEXT_MISMATCH','/event/correlationId')
 if event['payload']!=output:raise ContractFailure('EVENT_PAYLOAD_RECEIPT_MISMATCH','/event/payload')
 if event['payloadDigest']!=canonical_digest(output):raise ContractFailure('EVENT_PAYLOAD_DIGEST_MISMATCH','/event/payloadDigest')
 if not isinstance(persisted,dict) or not isinstance(persisted.get('response'),dict) or not isinstance(persisted.get('event'),dict):
  raise ContractFailure('PERSISTED_COMPLETION_UNAVAILABLE','/persisted')
 def frozen(r):return {k:v for k,v in r.items() if k!='idempotencyReplay'}
 if frozen(persisted['response'])!=frozen(response):raise ContractFailure('PERSISTED_RESPONSE_MISMATCH','/persisted/response')
 if persisted['event']!=event:raise ContractFailure('PERSISTED_EVENT_MISMATCH','/persisted/event')
 if not isinstance(hydrated,dict) or not isinstance(hydrated.get('bytes'),bytes):raise ContractFailure('HYDRATION_BYTES_UNAVAILABLE','/hydrated/bytes')
 if not isinstance(hydrated.get('contentDigest'),str):raise ContractFailure('HYDRATION_DIGEST_UNAVAILABLE','/hydrated/contentDigest')
 raw=hydrated['bytes']
 if 'sha256:'+hashlib.sha256(raw).hexdigest()!=hydrated['contentDigest']:raise ContractFailure('HYDRATION_CONTENT_DIGEST_MISMATCH','/hydrated/contentDigest')
 try:value=strict_json(raw)
 except ContractFailure as exc:raise ContractFailure('HYDRATION_'+exc.code,'/hydrated/bytes')
 if value!=output:raise ContractFailure('HYDRATION_RECEIPT_MISMATCH','/hydrated/bytes')
 return {key:output[key],**({'versionId':output['versionId']} if operation=='secret.create' else {})}
