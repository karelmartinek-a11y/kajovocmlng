"""Technical HTTP specialization from 12.18-23,26.1,32,49.4/27,51; no model-derived fields.

Schemas and case table are materialized into the authoritative SSOT by the
author script. Helpers are design validators, not deployed authentication/SQL.
"""
import copy,hashlib,json,re
from jsonschema import Draft202012Validator,FormatChecker
from referencing import Registry,Resource

PATH='contracts/generation/http-design.schema.json'
ID='urn:kcml:generation-http-design:1'
PAYLOAD='contracts/payload-contracts.json'
GEN='contracts/generation/generation-contracts.schema.json'
ROUTES={'route.0234':('generation.spec.approve','Approval'),
        'route.0232':('generation.spec.revision.read','SpecificationRead'),
        'route.0237':('generation.plan.read','PlanRead')}
READS={'route.0232','route.0237'}
# Each row: classification, HTTP, directive, action, applicability, evidence.
CASES={
 'API_AUTHENTICATION_FAILED':('AUTHENTICATION',401,'DO_NOT_RETRY','AUTHENTICATE','ALL',['7.2','21.2','26.1']),
 'API_REQUEST_INVALID':('VALIDATION',400,'DO_NOT_RETRY','CORRECT_REQUEST','ALL',['12.18','26.1']),
 'API_OBJECT_NOT_FOUND':('NOT_FOUND',404,'DO_NOT_RETRY','REVIEW_EXACT_TARGET','ALL',['12.19','12.23','12.44.1']),
 'STATE_VERSION_CONFLICT':('CONFLICT',409,'REFRESH_AND_RETRY_NEW_COMMAND','REVIEW_CURRENT_SNAPSHOT','APPROVAL',['49.3','49.27']),
 'SPECIFICATION_DIGEST_STALE':('CONFLICT',409,'REFRESH_AND_RETRY_NEW_COMMAND','REVIEW_CURRENT_SNAPSHOT','APPROVAL',['12.21','49.27']),
 'CAPABILITY_SNAPSHOT_STALE':('CONFLICT',409,'REFRESH_AND_RETRY_NEW_COMMAND','REVIEW_CURRENT_SNAPSHOT','APPROVAL',['12.20','12.21','49.27']),
 'SPECIFICATION_NOT_APPROVABLE':('VALIDATION',422,'DO_NOT_RETRY','REVIEW_PRECHECK','APPROVAL',['12.20','12.21']),
 'IDEMPOTENCY_CONFLICT':('CONFLICT',409,'DO_NOT_RETRY','LOOKUP_ORIGINAL_APPROVAL','APPROVAL',['49.4','49.27','51.12']),
 'API_READ_TIMEOUT':('TIMEOUT',504,'RETRY_SAME_OPERATION','RETRY_EXACT_READ','READ',['12.44.1','32.3']),
 'API_READ_CANCELLED':('CANCELLED',409,'DO_NOT_RETRY','NONE','READ',['12.44.1','32.1']),
 'API_IMMUTABLE_DOCUMENT_INVALID':('VALIDATION',500,'DO_NOT_RETRY','OPEN_AUDIT_DETAIL','READ',['12.19','12.23','51.10']),
 'API_COMMIT_UNCONFIRMED':('DEPENDENCY',503,'RECONCILE_THEN_RETRY','LOOKUP_ORIGINAL_APPROVAL','APPROVAL',['12.21','49.4','49.27','51.5']),
 'API_STORAGE_ROLLBACK':('DEPENDENCY',503,'RETRY_SAME_OPERATION','RETRY_ORIGINAL_REQUEST','ALL',['32.3','51.5','51.32']),
 'PLATFORM_RECOVERY_IN_PROGRESS':('DEPENDENCY',503,'RETRY_SAME_OPERATION','RETRY_ORIGINAL_REQUEST','APPROVAL',['32.7']),
 'PLATFORM_RECOVERY_BLOCKED':('MANUAL_REVIEW',503,'MANUAL_REVIEW','OPEN_AUDIT_DETAIL','APPROVAL',['32.7']),
 'QUEUE_CAPACITY_EXHAUSTED':('CAPACITY',503,'RETRY_SAME_OPERATION','RETRY_ORIGINAL_REQUEST','APPROVAL',['32.7','51.5']),
 'STORAGE_CAPACITY_EXHAUSTED':('CAPACITY',503,'RETRY_SAME_OPERATION','RETRY_ORIGINAL_REQUEST','ALL',['32.7','51.5']),
}

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(value):return 'sha256:'+hashlib.sha256(canonical(value)).hexdigest()
def obj(properties,required=None):return {'type':'object','additionalProperties':False,'properties':properties,'required':list(properties) if required is None else required}
def applicable(code,rid):return CASES[code][4] in ('ALL','READ' if rid in READS else 'APPROVAL')

def definitions(bundle, payload):
    ref=lambda name:{'$ref':bundle['$id']+'#/$defs/'+name}
    local=lambda name:{'$ref':ID+'#/$defs/'+name}
    nullable=lambda value:{'oneOf':[{'type':'null'},value]}
    defs={}
    fields={'jobId':ref('Uuid'),'jobState':ref('SourceEnum034'),'stateVersion':ref('Counter'),
            'eventSequence':ref('Counter'),'specificationRevisionId':nullable(ref('Uuid')),
            'specificationDigest':nullable(ref('Digest')),'capabilitySnapshotId':nullable(ref('Uuid')),
            'capabilitySnapshotDigest':nullable(ref('Digest')),'currentTurnId':nullable(ref('Uuid')),
            'currentTurnStatus':nullable(ref('SourceEnum038'))}
    defs['CurrentSnapshot']=obj(fields)
    defs['CurrentSnapshot']['allOf']=[
        {'oneOf':[{'properties':{a:{'type':'null'},b:{'type':'null'}}},
                  {'properties':{a:{'not':{'type':'null'}},b:{'not':{'type':'null'}}}}]}
        for a,b in [('specificationRevisionId','specificationDigest'),
                    ('capabilitySnapshotId','capabilitySnapshotDigest'),('currentTurnId','currentTurnStatus')]]
    defs['ApprovalReceipt']=obj({'jobId':ref('Uuid'),'specificationRevisionId':ref('Uuid'),
        'specificationDigest':ref('Digest'),'executionAuthorityId':ref('Uuid'),
        'planningPhaseRunId':ref('Uuid'),'jobState':{'const':'ANALYZING'}})
    defs['FailureDetails']=obj({'fieldPaths':{'type':'array','items':ref('JsonPointer'),'maxItems':256,'uniqueItems':True},
        'reason':{'type':'string','minLength':1,'maxLength':8192}})
    for code,(classification,http,retry,action,scope,source) in CASES.items():
        snapshot=local('CurrentSnapshot') if code in ['STATE_VERSION_CONFLICT','SPECIFICATION_DIGEST_STALE','CAPABILITY_SNAPSHOT_STALE','SPECIFICATION_NOT_APPROVABLE'] else nullable(local('CurrentSnapshot'))
        if code=='API_AUTHENTICATION_FAILED':snapshot={'type':'null'}
        defs['Error.'+code]=obj({'stableCode':{'const':code},'classification':{'const':classification},
            'retryDirective':{'const':retry},'message':{'type':'string','minLength':1,'maxLength':8192},
            'detailsDigest':ref('Digest'),'details':local('FailureDetails'),
            'currentSnapshot':snapshot,'nextAction':{'const':action}})
        defs['Error.'+code]['description']='Technical materialization; authority SSOT '+','.join(source)+'. Diagnostic text never grants retry.'
    rows={r['routeId']:r for r in payload['records']}
    for rid,(operation,name) in ROUTES.items():
        props={'authorization':{'type':'string','pattern':'^Bearer [A-Za-z0-9\\-._~+/]+=*$','maxLength':8192},
               'cookie':{'type':'string','minLength':1,'maxLength':8192},
               'x-csrf-token':{'type':'string','minLength':1,'maxLength':4096},
               'accept':{'enum':['application/json','*/*']},
               'origin':{'const':'https://kaja.hcasc.cz'},
               'referer':{'type':'string','pattern':'^https://kaja\\.hcasc\\.cz/','maxLength':8192}}
        required=[]
        if rid=='route.0234':
            props.update({'idempotency-key':{'type':'string','minLength':1,'maxLength':512},
                'content-type':{'const':'application/json'},'if-match':{'type':'string','pattern':'^"(?:0|[1-9][0-9]{0,18})"$'}})
            required=['idempotency-key','content-type']
        headers=obj(props,required)
        headers['oneOf']=[{'required':['authorization'],'not':{'required':['cookie']}},
                          {'required':['cookie'],'not':{'required':['authorization']}}]
        if rid=='route.0234':headers['allOf']=[{'if':{'required':['cookie']},'then':{'required':['x-csrf-token','origin']}}]
        body={'type':'null'}
        if rid=='route.0234':
            body=copy.deepcopy(rows[rid]['requestSchema']['properties']['body']);body.pop('$id',None)
            body['properties']['expectedStateVersion']=ref('Counter')
        request=obj({'pathParameters':copy.deepcopy(rows[rid]['requestSchema']['properties']['pathParameters']),
                     'query':obj({}),'headers':headers,'body':body})
        if rid=='route.0234':request['anyOf']=[{'properties':{'headers':{'required':['if-match']}}},
                                                {'properties':{'body':{'required':['expectedStateVersion']}}}]
        defs[name+'WireRequest']=request
        defs[name+'Error']={'oneOf':[local('Error.'+code) for code in CASES if applicable(code,rid)]}
        defs[name+'HttpResponse']={'oneOf':[
            obj({'statusCode':{'const':200},'body':{'allOf':[{'$ref':f'urn:kcml:r9:route:{rid}:response'},
                                                         {'properties':{'status':{'const':'SUCCEEDED'}}}]}}),
            *[obj({'statusCode':{'const':CASES[code][1]},'body':{'allOf':[{'$ref':f'urn:kcml:r9:route:{rid}:response'},
                {'properties':{'error':local('Error.'+code)}}]}}) for code in CASES if applicable(code,rid)]]}
    return defs

def document(bundle,payload):
    return {'$schema':bundle['$schema'],'$id':ID,'not':{},'$defs':definitions(bundle,payload),
        'authority':['12.18','12.19','12.20','12.21','12.23','12.44.1','26.1','32','49.4','49.27','51.5','51.10','51.12','51.13'],
        'errorBindings':{code:dict(zip(['classification','httpStatus','retryDirective','nextAction','scope','sourceSections'],v)) for code,v in CASES.items()},
        'transportBindings':{rid:{'operationId':op,'wireRequest':ID+'#/$defs/'+name+'WireRequest',
            'httpResponse':ID+'#/$defs/'+name+'HttpResponse','normalizedRequest':f'urn:kcml:r9:route:{rid}:request',
            'normalizedResponse':f'urn:kcml:r9:route:{rid}:response','authAuthority':'7.2/21.2/26.1',
            'readOnly':rid in READS} for rid,(op,name) in ROUTES.items()},
        'coverage':{'approval':'HTTP and approval-specific admission cases; coordinator/phase/checkpoint error dispatch remains a separate required design obligation, not a generic fallback',
                    'read':'transport, exact-selector lookup, immutable-content verification, timeout/cancellation and storage failure; no mutating phase guards'},
        'transportRules':{'headerNames':'lowercase, singleton after parsing; duplicate critical headers rejected',
            'headersScope':'application header projection; Host, User-Agent, Accept-Encoding, Connection, Content-Length and framing are HTTP adapter fields, not business arguments',
            'bodyEncoding':'UTF-8 application/json; duplicate object keys rejected; reads have no entity and normalize to null',
            'query':'no query parameters for these exact path-selected operations',
            'sessionCookieName':'__Host-kcml-owner','csrfHeader':'x-csrf-token',
            'auth':'Exactly one OWNER session or Bearer key; cookie requires valid CSRF for approval; authentication success is a trusted server result, not header presence',
            'cas':'If-Match quoted Counter or body expectedStateVersion; if both present they must agree',
            'derivedGuard':'clientRequestDigest is server SHA256 canonical {operationId,pathParameters,body,expectedStateVersion}; never supplied by caller',
            'reads':'no mutating command, idempotency claim, event or CAS; meta commandId/logicalOperationId are read trace identities only',
            'approval':'synchronous command linearizes at atomic approval commit; 200 confirms approval, not planning/job completion',
            'resultDigest':'SHA256 canonical {status,output,error}; excludes transport/meta, separate from immutable document digest',
            'replay':'fresh auth then stable locator lookup before any fresh guards; return frozen receipt/meta with idempotencyReplay=true and fresh response correlation/time; no new approval',
            'networkFailure':'no response is not an error outcome; read retries exact selector, approval resolves original idempotency locator; no new key or presumed rollback',
            'snapshot':'reads use CONSISTENT_READ snapshot for document + job metadata + activationEpoch; snapshot is not authority for a subsequent mutation',
            'cursor':'read meta.eventSequence is diagnostic snapshot metadata, never an instruction to skip stream events; only validated stream/replay snapshot advances consumer cursor',
            'mutationProfile':'ONLINE_MUTATION; B1/B2/B3 credential acceptance, C0/C1 locator/idempotency, E90 job, H35 command/H50 generation children/H900 queue/H910 outbox, I audit last; db_now after locks',
            'retryProfile':'ui/contracts/error-presentation.json#/defaultRetryProfile; only after explicit case authorization; known rollback or read-only; never unknown commit',
            'retention':'49.4 tombstone locator never reusable; retained outcome unavailable -> IDEMPOTENCY_CONFLICT details.reason=RESULT_RETAINED_AS_TOMBSTONE; currentSnapshot null permitted only when unavailable; never execute again'}}

def decode_json(raw):
    def unique(pairs):
        out={}
        for key,value in pairs:
            if key in out:raise ValueError('API_REQUEST_INVALID:duplicate key')
            out[key]=value
        return out
    return json.loads(raw.decode('utf8'),object_pairs_hook=unique,
        parse_constant=lambda value:(_ for _ in ()).throw(ValueError('API_REQUEST_INVALID:non-JSON number')))

def application_headers(pairs):
    projected={};ignored={'host','user-agent','accept-encoding','accept-language','connection','content-length',
        'sec-fetch-site','sec-fetch-mode','sec-fetch-dest','sec-ch-ua','sec-ch-ua-mobile','sec-ch-ua-platform'}
    allowed={'authorization','cookie','x-csrf-token','accept','idempotency-key','content-type','if-match','origin','referer'}
    for name,value in pairs:
        key=name.lower()
        if key in ignored:continue
        if key not in allowed or key in projected:raise ValueError('API_REQUEST_INVALID:unknown/duplicate application header')
        if not isinstance(value,str) or '\r' in value or '\n' in value:raise ValueError('API_REQUEST_INVALID:header')
        if key=='content-type':
            parts=[p.strip().lower() for p in value.split(';')]
            if parts[0]!='application/json' or any(x not in ('charset=utf-8','charset="utf-8"') for x in parts[1:]):raise ValueError('API_REQUEST_INVALID:content-type')
            value='application/json'
        projected[key]=value
    return projected

def specialize(payload,bundle):
    d=copy.deepcopy(payload);ref=lambda name:{'$ref':ID+'#/$defs/'+name}
    for row in d['records']:
        rid=row['routeId']
        if rid not in ROUTES:continue
        name=ROUTES[rid][1];row['transportContractRef']=ID+'#/transportBindings/'+rid
        row['requestSchema']['properties']['query']['maxItems']=0
        if rid in READS:row['requestSchema']['properties']['body']={'$schema':bundle['$schema'],
            '$id':f'urn:kcml:r9:semantic:{rid}:body','type':'null'}
        response=row['responseSchema'];p=response['properties']
        p['meta']={'oneOf':[{'type':'null'},{'$ref':bundle['$id']+'#/$defs/ApiConcurrencyEnvelope'}]}
        if 'meta' not in response['required']:response['required'].append('meta')
        if rid=='route.0234':p['output']={'oneOf':[{'type':'null'},{'$schema':bundle['$schema'],
            '$id':'urn:kcml:r9:semantic:route.0234:output',**ref('ApprovalReceipt')}]}
        p['error']={'oneOf':[{'type':'null'},ref(name+'Error')]}
        p['status']['enum']=['SUCCEEDED','FAILED']+(['CANCELLED'] if rid in READS else ['UNCONFIRMED'])
        response['allOf']=[
            {'if':{'properties':{'status':{'const':'SUCCEEDED'}}},'then':{'properties':{
                'output':ref('ApprovalReceipt') if rid=='route.0234' else {'$ref':bundle['$id']+'#/$defs/'+('GenerationSpecification' if rid=='route.0232' else 'GenerationPlan')},
                'error':{'type':'null'},'terminal':{'const':True},'meta':{'$ref':bundle['$id']+'#/$defs/ApiConcurrencyEnvelope'}}}},
            {'if':{'properties':{'status':{'not':{'const':'SUCCEEDED'}}}},'then':{'properties':{'output':{'type':'null'},'error':ref(name+'Error'),'meta':{'type':'null'}}}},
            {'if':{'properties':{'status':{'enum':['FAILED','CANCELLED']}}},'then':{'properties':{'terminal':{'const':True}}}}]
        if rid=='route.0234':
            response['allOf'] += [{'if':{'properties':{'status':{'const':'UNCONFIRMED'}}},'then':{'properties':{'terminal':{'const':False},'error':ref('Error.API_COMMIT_UNCONFIRMED')}}},
                {'if':{'properties':{'error':{'type':'object','properties':{'stableCode':{'const':'API_COMMIT_UNCONFIRMED'}},'required':['stableCode']}},'required':['error']},'then':{'properties':{'status':{'const':'UNCONFIRMED'}}}}]
        else:
            response['allOf'] += [{'if':{'properties':{'status':{'const':'CANCELLED'}}},'then':{'properties':{'error':ref('Error.API_READ_CANCELLED')}}},
                {'if':{'properties':{'error':{'type':'object','properties':{'stableCode':{'const':'API_READ_CANCELLED'}},'required':['stableCode']}},'required':['error']},'then':{'properties':{'status':{'const':'CANCELLED'}}}}]
    from phase1_repair_contracts import canonical_digest
    d['canonicalDigest']=canonical_digest({**d,'canonicalDigest':None});return d

def validators(bundle,contract,payload):
    registry=Registry().with_resource(bundle['$id'],Resource.from_contents(bundle)).with_resource(ID,Resource.from_contents(contract))
    for row in payload['records']:
        if row['routeId'] in ROUTES:
            for key in ['requestSchema','responseSchema','eventSchema']:
                s=row[key];registry=registry.with_resource(s['$id'],Resource.from_contents(s))
    return lambda schema:Draft202012Validator(schema,registry=registry,format_checker=FormatChecker())

def normalize(rid,wire,*,authenticated,csrf_valid,validator):
    if authenticated is not True:raise ValueError('API_AUTHENTICATION_FAILED')
    validator({'$ref':ID+'#/$defs/'+ROUTES[rid][1]+'WireRequest'}).validate(wire)
    headers=wire['headers'];body=copy.deepcopy(wire['body']);version=None
    if 'cookie' in headers:
        cookies=[x.strip().split('=',1) for x in headers['cookie'].split(';')]
        owner=[v for k,*v in cookies if k=='__Host-kcml-owner']
        if len(owner)!=1 or len(owner[0])!=1 or not owner[0][0]:raise ValueError('API_AUTHENTICATION_FAILED')
        if rid=='route.0234' and csrf_valid is not True:raise ValueError('API_AUTHENTICATION_FAILED')
    if rid=='route.0234':
        version=body.pop('expectedStateVersion',None)
        if 'if-match' in headers:
            header_version=headers['if-match'][1:-1]
            if version is not None and version!=header_version:raise ValueError('API_REQUEST_INVALID')
            version=header_version
        validator({'$ref':'urn:kcml:generation-contracts:2#/$defs/Counter'}).validate(version)
    inputs={'operationId':ROUTES[rid][0],'pathParameters':wire['pathParameters'],'body':body,'expectedStateVersion':version}
    guards={k:None for k in ['idempotencyKey','expectedStateVersion','expectedRevisionId','expectedReleaseId','expectedBindingSetRevision','expectedActivationEpoch','deadlineAt']}
    guards.update(idempotencyKey=headers.get('idempotency-key'),expectedStateVersion=version,clientRequestDigest=digest(inputs))
    return {'routeId':rid,'operationId':ROUTES[rid][0],'pathParameters':wire['pathParameters'],'query':[],'body':body,'guards':guards}

def check_response(rid,response,*,validator,persisted_receipt=None,persisted_meta=None):
    validator({'$ref':f'urn:kcml:r9:route:{rid}:response'}).validate(response)
    expected=digest({k:response[k] for k in ['status','output','error']})
    if response['resultDigest']!=expected:raise ValueError('RESULT_DIGEST_MISMATCH')
    if response['status']=='SUCCEEDED':
        meta=response['meta']
        if any(meta[k]!=response[k] for k in ['logicalOperationId','correlationId','resultDigest']):raise ValueError('META_MISMATCH')
        if rid=='route.0234':
            if response['output']!=persisted_receipt or not isinstance(persisted_meta,dict):raise ValueError('PERSISTED_RECEIPT_REQUIRED')
            for k in ['logicalOperationId','commandId','stateVersion','eventSequence','activationEpoch','resultDigest']:
                if meta[k]!=persisted_meta.get(k):raise ValueError('FROZEN_META_MISMATCH')
        return 200
    error=response['error']
    if error['detailsDigest']!=digest(error['details']):raise ValueError('DETAILS_DIGEST_MISMATCH')
    return CASES[error['stableCode']][1]


def check_error_context(rid,response,*,validator,effect,dispatched,current_snapshot):
    """Trusted repository/transaction observations, never caller-provided retry permission.

    An error's text/status cannot prove rollback. Unknown local commit is resolved
    against the original locator; it must never enter the bounded retry branch.
    """
    status=check_response(rid,response,validator=validator)
    if response['status']=='SUCCEEDED':raise ValueError('ERROR_REQUIRED')
    if effect not in {'READ_ONLY','CONFIRMED_ROLLBACK','UNKNOWN_COMMIT','NO_DISPATCH'} or type(dispatched) is not bool:
        raise ValueError('EXACT_EFFECT_OBSERVATION_REQUIRED')
    code=response['error']['stableCode'];error=response['error']
    if rid in READS and effect!='READ_ONLY':raise ValueError('READ_CANNOT_MUTATE')
    if effect=='UNKNOWN_COMMIT' and code!='API_COMMIT_UNCONFIRMED':raise ValueError('UNKNOWN_COMMIT_CANNOT_BE_FAILURE')
    if code=='API_COMMIT_UNCONFIRMED' and effect!='UNKNOWN_COMMIT':raise ValueError('UNKNOWN_COMMIT_REQUIRED')
    if code=='API_STORAGE_ROLLBACK' and effect not in {'CONFIRMED_ROLLBACK','READ_ONLY'}:
        raise ValueError('CONFIRMED_ROLLBACK_REQUIRED')
    if code=='PLATFORM_RECOVERY_IN_PROGRESS' and (dispatched or effect!='NO_DISPATCH'):
        raise ValueError('RECOVERY_RETRY_ONLY_BEFORE_DISPATCH')
    if error['retryDirective']=='RETRY_SAME_OPERATION' and effect not in {'READ_ONLY','CONFIRMED_ROLLBACK','NO_DISPATCH'}:
        raise ValueError('RETRY_WITHOUT_KNOWN_NO_EFFECT')
    if error['currentSnapshot']!=current_snapshot:raise ValueError('CURRENT_SNAPSHOT_PROVENANCE')
    if code=='IDEMPOTENCY_CONFLICT' and current_snapshot is None and error['details']['reason']!='RESULT_RETAINED_AS_TOMBSTONE':
        raise ValueError('CONFLICT_SNAPSHOT_REQUIRED')
    return status


def check_read_response(rid,response,*,validator,native,document,path_parameters,
                        persisted_job_id,persisted_document_id,persisted_document_digest,snapshot_meta):
    """Compose wire response, exact immutable lookup and one consistent read snapshot."""
    if rid not in READS:raise ValueError('READ_ROUTE_REQUIRED')
    status=check_response(rid,response,validator=validator)
    if response['status']=='SUCCEEDED':
        if response['meta']!=snapshot_meta:raise ValueError('READ_SNAPSHOT_META_MISMATCH')
        if response['meta']['idempotencyReplay'] is not False:raise ValueError('READ_HAS_NO_IDEMPOTENCY_REPLAY')
    native.validate_generation_read_handoff(document,ROUTES[rid][0],path_parameters,response,
        persisted_job_id=persisted_job_id,persisted_document_id=persisted_document_id,
        persisted_document_digest=persisted_document_digest)
    return status
