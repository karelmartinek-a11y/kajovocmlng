"""Exact create request projections and strict HTTP decoder; reference design only."""
import base64,copy,hashlib,io,json,re,math
from urllib.parse import urlsplit
from jsonschema import Draft202012Validator,FormatChecker
ID='urn:kcml:create-operation-design:1'
PATH='contracts/create-operation-design.schema.json'
PAYLOAD='contracts/payload-contracts.json'
OPERATIONS={'generation.job.create':'GenerationJobCreateBody','secret.create':'SecretCreateBody'}
UID={'type':'string','format':'uuid'}
DIGEST={'type':'string','pattern':'^sha256:[0-9a-f]{64}$(?![\\s\\S])'}
TEXT={'type':'string','minLength':1,'maxLength':1048576}
SHORT={'type':'string','minLength':1,'maxLength':256}
TYPES=['PASSWORD','API_KEY','BEARER_TOKEN','OAUTH_CLIENT','OAUTH_TOKEN_SET','TOTP_SEED','CERTIFICATE','PRIVATE_KEY','WEBHOOK_SECRET','DATABASE_CREDENTIAL','SESSION_STATE','COOKIE_JAR','SSH_CREDENTIAL','GENERIC_TEXT','GENERIC_BINARY']
TARGETS=['MCP_SERVER','MCP_TOOL','MCP_RESOURCE','MCP_PROMPT','AI_AGENT','AGENT_TOOL_ADAPTER','AGENT_AS_TOOL','AGENT_HANDOFF','PLATFORM_COMPONENT','MANAGED_RUNTIME','EXTERNAL_API_CONNECTOR','WEBHOOK_HANDLER','PULSE_INTEGRATION','BROWSER_AUTOMATION','OWNER_UI']

def obj(props,required=None):return {'type':'object','additionalProperties':False,'properties':props,'required':list(props) if required is None else required}
def array(item):return {'type':'array','items':item,'maxItems':4096,'uniqueItems':True}
def schema():
    source={'oneOf':[
        obj({'kind':{'const':'TEXT'},'text':TEXT}),
        obj({'kind':{'enum':['FILE','IMAGE','API_DOC']},'artifactId':UID}),
        obj({'kind':{'const':'URL'},'url':{'type':'string','format':'uri','maxLength':1048576,'pattern':'^https?://'}}),
        obj({'kind':{'const':'CREDENTIAL_REF'},'stableName':SHORT}),
        obj({'kind':{'const':'OBJECT_REF'},'objectId':UID})]}
    generation=obj({'intent':TEXT,'kind':{'type':'string','enum':['CREATE','UPDATE','FOLLOW_UP','RETRY','REPAIR']},
        'targetKind':{'type':'string','enum':TARGETS},'targetObjectId':UID,'parentJobId':UID,
        'requestedModel':SHORT,'credential':TEXT,'sources':array(source),'followUpBasis':__import__('follow_up_contracts').request_schema()},['intent'])
    generation['allOf']=[
        {'if':{'required':['kind'],'properties':{'kind':{'const':'FOLLOW_UP'}}},'then':{'required':['parentJobId','followUpBasis']},'else':{'not':{'required':['followUpBasis']}}},
        {'if':{'required':['targetObjectId']},'then':{'required':['targetKind']}},
        {'if':{'required':['kind'],'properties':{'kind':{'const':'UPDATE'}}},'then':{'required':['targetObjectId','targetKind']}}]
    generation=__import__('generation_basis_selectors').apply(generation)
    value={'oneOf':[obj({'encoding':{'const':'UTF8'},'text':TEXT}),
        obj({'encoding':{'const':'BASE64'},'base64':{'type':'string','minLength':4,'maxLength':1398104,
            'pattern':'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$(?![\\s\\S])'}})]}
    secret=obj({'stableName':SHORT,'displayName':{'type':'string','minLength':1,'maxLength':1048576},
        'type':{'type':'string','enum':TYPES},'value':value,
        'description':{'type':'string','maxLength':1048576},'purposeKind':SHORT,'targetObjectId':UID,
        'tags':array(SHORT),'group':SHORT,'url':{'type':'string','format':'uri','maxLength':1048576},
        'username':{'type':'string','maxLength':1048576},'notes':{'type':'string','maxLength':1048576},
        'expiration':{'type':'string','format':'date-time'}},['stableName','displayName','type','value'])
    secret['allOf']=[{'if':{'properties':{'type':{'const':'GENERIC_BINARY'}},'required':['type']},
        'then':{'properties':{'value':{'properties':{'encoding':{'const':'BASE64'}}}}},
        'else':{'properties':{'value':{'properties':{'encoding':{'const':'UTF8'}}}}}}]
    from secret_profile_import import active_import_document
    profiles=active_import_document();secret=copy.deepcopy(profiles['$defs']['SecretCreateBody'])
    needed={}
    def collect(node):
        if isinstance(node,dict):
            ref=node.get('$ref','')
            if ref.startswith('#/$defs/'):
                name=ref.split('/')[2]
                if name not in needed:
                    needed[name]=copy.deepcopy(profiles['$defs'][name]);collect(needed[name])
            for value in node.values():collect(value)
        elif isinstance(node,list):
            for value in node:collect(value)
    collect(secret);secret['$defs']=needed
    secret['$id']='urn:kcml:secret-create-native-body:1'
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':ID,
        '$comment':'Technical field spelling/encoding per 12.18; authority 8.2-8.6.1, 12.1-12.3, 25.6/25.11, 26.7/26.9, 72.11/72.21. Limits inherit the prior 1 MiB transport value ceiling; no UI row count is a business length cap.',
        '$defs':{'GenerationJobCreateBody':generation,'SecretCreateBody':secret,**needed,**__import__('create_completion_contracts').definitions()}}

def specialize(payload):
    result=copy.deepcopy(payload);defs=schema()['$defs']
    for row in result['records']:
        oid=row['operationId']
        if oid not in OPERATIONS:continue
        body=copy.deepcopy(defs[OPERATIONS[oid]])
        body.update({'$id':f'urn:kcml:r9:semantic:{row["routeId"]}:body','$schema':schema()['$schema'],
          '$comment':f'Exact {oid} domain request, not a schemaId/values/canonicalJson container. Authoritative definition: {ID}#/$defs/{OPERATIONS[oid]}'})
        p=row['requestSchema']['properties'];p['body']=body;p['query']={'type':'array','maxItems':0}
        p['pathParameters']=obj({})
        # These calls create new roots. Snapshots belong to referenced target
        # resolution, not a caller-created root/receipt or new-root CAS.
        for key in ['expectedStateVersion','expectedRevisionId','expectedReleaseId','expectedBindingSetRevision','expectedActivationEpoch']:
            p['guards']['properties'][key]={'type':'null'}
        row['semanticRules']=[s for s in row['semanticRules'] if s not in ['DUPLICATE_SLOT_REJECT','CANONICAL_JSON_MUST_MATCH_VALUE_WHEN_NON_NULL','VALUE_DIGEST_OVER_CANONICAL_VALUE']]+[
            'STRICT_UTF8_JSON_DUPLICATE_KEYS_AND_NONFINITE_REJECT','NO_QUERY_PARAMETERS','NO_PATH_PARAMETERS',
            'EXACT_CREATE_DOMAIN_BODY','SERVER_RESOLVES_REFERENCES_AND_RECOMPUTES_REQUEST_DIGEST',
            'CLIENT_SNAPSHOT_OR_AUTHORITY_FIELDS_ARE_NOT_TRUSTED','IDEMPOTENCY_REPLAY_EXACT_OWNER_OPERATION_KEY_DIGEST']
        row['semanticRules']=list(dict.fromkeys(row['semanticRules']))
    result=__import__('create_completion_contracts').specialize(result)
    result['canonicalDigest']='sha256:'+hashlib.sha256(json.dumps({**result,'canonicalDigest':None},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return result

class ContractFailure(ValueError):
    def __init__(self,code,pointer=''):
        self.code=code;self.pointer=pointer;super().__init__(code+':'+pointer)

def digest(value):return 'sha256:'+hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def strict_json(raw):
    class ObjectPairs(list):pass
    def convert(v,path=''):
        if isinstance(v,ObjectPairs):
            result={}
            for key,item in v:
                at=path+'/'+key.replace('~','~0').replace('/','~1')
                if key in result:raise ContractFailure('DUPLICATE_JSON_KEY',at)
                result[key]=convert(item,at)
            return result
        if isinstance(v,list):return [convert(item,path+'/'+str(i)) for i,item in enumerate(v)]
        if isinstance(v,float) and not math.isfinite(v):raise ContractFailure('NONFINITE_JSON_NUMBER',path)
        return v
    try:
        value=convert(json.loads(raw.decode('utf8'),object_pairs_hook=ObjectPairs))
        def unicode_check(v):
            if isinstance(v,str):
                try:v.encode('utf8')
                except UnicodeEncodeError:raise ContractFailure('INVALID_UNICODE')
            elif isinstance(v,dict):
                for key,item in v.items():unicode_check(key);unicode_check(item)
            elif isinstance(v,list):
                for item in v:unicode_check(item)
        unicode_check(value)
        return value
    except ContractFailure:raise
    except UnicodeDecodeError:raise ContractFailure('INVALID_UTF8')
    except (ValueError,TypeError,RecursionError):raise ContractFailure('INVALID_JSON')

def decode_http(operation,method,path,query,headers,body):
    expected='/generation/jobs' if operation=='generation.job.create' else '/secrets' if operation=='secret.create' else None
    if expected is None:raise ContractFailure('UNKNOWN_OPERATION')
    if method!='POST' or path!=expected:raise ContractFailure('TRANSPORT_ROUTE_MISMATCH')
    if query:raise ContractFailure('UNKNOWN_QUERY_PARAMETER','/query')
    normalized={}
    for key,value in headers:
        key=key.lower()
        if key in normalized:raise ContractFailure('DUPLICATE_HEADER','/headers/'+key)
        normalized[key]=value
    if normalized.get('content-type','').lower() not in ['application/json','application/json; charset=utf-8']:
        raise ContractFailure('CONTENT_TYPE_MISMATCH','/headers/content-type')
    key=normalized.get('idempotency-key')
    if not isinstance(key,str) or not 1<=len(key)<=512:raise ContractFailure('IDEMPOTENCY_KEY_REQUIRED','/headers/idempotency-key')
    if any(k in normalized for k in ['if-match','x-authority-id','x-execution-authority-id','x-state-version']):
        raise ContractFailure('UNDECLARED_CREATE_GUARD_OR_AUTHORITY','/headers')
    if len(body)>1048576:raise ContractFailure('REQUEST_TOO_LARGE','/body')
    value=strict_json(body)
    if operation=='secret.create':
        from secret_profile_import import strict_json as parse_secret,candidate_from_http,request_digest,Rejected
        try:
            value=parse_secret(body);validate_body(operation,value);candidate=candidate_from_http(body)
        except Rejected as e:raise ContractFailure(e.code,e.pointer)
        computed=request_digest(body) if candidate['representation']=='PROFILE_JSON_V1' else digest({'operationId':operation,'body':value})
    else:
        value=strict_json(body);validate_body(operation,value)
        computed=digest({'operationId':operation,'body':value})
    hint=normalized.get('x-kcml-request-digest')
    if hint is not None and hint!=computed:raise ContractFailure('CLIENT_DIGEST_MISMATCH','/headers/x-kcml-request-digest')
    native={'operationId':operation,'body':value,'idempotencyKey':key,'requestDigest':computed}
    if operation=='secret.create':native['secretImportCandidate']=candidate
    return native

def validate_body(operation,value):
    v=Draft202012Validator(schema()['$defs'][OPERATIONS[operation]],format_checker=FormatChecker())
    errors=sorted(v.iter_errors(value),key=lambda e:(e.json_path,0 if e.validator=='type' else 1))
    if errors:
        e=errors[0];raise ContractFailure('SCHEMA_'+e.validator.upper(),e.json_path)
    if operation=='generation.job.create':
        if not value['intent'].strip():raise ContractFailure('EMPTY_INTENT','$.intent')
        ids=[s['artifactId'] for s in value.get('sources',[]) if 'artifactId' in s]
        if len(ids)!=len(set(ids)):raise ContractFailure('DUPLICATE_ARTIFACT_REFERENCE','$.sources')
    if operation=='secret.create':
        for field in ['stableName','displayName']:
            if not value[field].strip():raise ContractFailure('EMPTY_'+field.upper(),'$.'+field)
        val=value['value']
        if val.get('representation')=='PROFILE_JSON_V1':
            from secret_profile_reference import parse_profile,Rejected
            try:parse_profile(val['profileId'],json.dumps(val['profile'],ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
            except Rejected as e:raise ContractFailure(e.code,e.pointer)
        elif val['encoding']=='BASE64':
            try:raw=base64.b64decode(val['base64'],validate=True)
            except ValueError:raise ContractFailure('INVALID_BASE64','$.value.base64')
            if base64.b64encode(raw).decode()!=val['base64']:raise ContractFailure('NONCANONICAL_BASE64','$.value.base64')
        else:
            try:val['text'].encode('utf8')
            except UnicodeEncodeError:raise ContractFailure('INVALID_UNICODE','$.value.text')
    return value

def admit(request,server,replay=None):
    # The server argument represents a trusted repository/authority snapshot.
    # It is never merged from HTTP fields. This is an executable reference model.
    if server.get('actor')!='OWNER' or not server.get('authenticated'):raise ContractFailure('AUTHENTICATION_REQUIRED')
    if server.get('recovery')!='READY':raise ContractFailure('RECOVERY_BARRIER')
    if replay:
        if replay['owner']!=server['owner'] or replay['operationId']!=request['operationId'] or replay['key']!=request['idempotencyKey']:
            raise ContractFailure('REPLAY_SCOPE_MISMATCH')
        if replay['requestDigest']!=request['requestDigest']:raise ContractFailure('IDEMPOTENCY_CONFLICT')
        from create_replay_contract import verify_record
        verify_record(request,server,replay)
        if replay['outcome']=='UNKNOWN':return {'action':'RECONCILE_ORIGINAL_OPERATION','dispatchNew':False}
        if replay['outcome']=='FAILED':return {'action':'REPLAY_FAILURE','dispatchNew':False}
        if replay['outcome']=='COMMITTED':return {'action':'REPLAY_RECEIPT','dispatchNew':False}
        raise ContractFailure('INVALID_REPLAY_OUTCOME')
    body=request['body']
    frozen=None
    selected=None
    if request['operationId']=='generation.job.create':
        if body.get('kind')=='FOLLOW_UP':
            from follow_up_contracts import admit_follow_up
            frozen=admit_follow_up(body,server)['frozenBasis']
        if body.get('credential') and not server.get('ephemeralCredentialPolicyVerified'):raise ContractFailure('EPHEMERAL_CREDENTIAL_POLICY_UNVERIFIED','$.credential')
        if body.get('targetObjectId') and body['targetObjectId'] not in server.get('targets',{}):raise ContractFailure('TARGET_UNRESOLVED','$.targetObjectId')
        if body.get('targetObjectId') and server['targets'][body['targetObjectId']].get('kind')!=body['targetKind']:raise ContractFailure('TARGET_KIND_MISMATCH','$.targetKind')
        if body.get('targetObjectId') and server['targets'][body['targetObjectId']].get('objectId')!=body['targetObjectId']:raise ContractFailure('TARGET_IDENTITY_MISMATCH','$.targetObjectId')
        if body.get('parentJobId') and body['parentJobId'] not in server.get('jobs',{}):raise ContractFailure('PARENT_JOB_UNRESOLVED','$.parentJobId')
        if body.get('parentJobId') and server['jobs'][body['parentJobId']].get('jobId')!=body['parentJobId']:raise ContractFailure('PARENT_JOB_IDENTITY_MISMATCH','$.parentJobId')
        # Own kind policies from12.41 are not interchangeable with parent state.
        # Until exact persisted selectors/validators are authored, existence or
        # caller/trusted fixture flags must never authorize these transitions.
        if body.get('kind','CREATE') in ('UPDATE','RETRY','REPAIR'):
            from generation_admission_contracts import Repository,select_generation_basis
            repository=server.get('generationBasisRepository')
            if not isinstance(repository,Repository):raise ContractFailure('PARENT_TARGET_ADMISSION_POLICY_UNVERIFIED','$.kind')
            if repository.owner!=server['owner']:raise ContractFailure('GENERATION_BASIS_OWNER_MISMATCH')
            selected=select_generation_basis(body,repository)
        if body.get('requestedModel') and body['requestedModel'] not in server.get('openaiModels',[]):raise ContractFailure('MODEL_UNAVAILABLE','$.requestedModel')
        for i,source in enumerate(body.get('sources',[])):
            if 'artifactId' in source:
                artifact=server.get('artifacts',{}).get(source['artifactId'])
                if artifact is None:raise ContractFailure('ARTIFACT_UNRESOLVED',f'$.sources[{i}].artifactId')
                if artifact.get('immutable') is not True:raise ContractFailure('ARTIFACT_LINEAGE_UNVERIFIED',f'$.sources[{i}]')
                if artifact.get('owner')!=server['owner']:raise ContractFailure('ARTIFACT_OWNER_MISMATCH',f'$.sources[{i}]')
                if not isinstance(artifact.get('bytes'),bytes):raise ContractFailure('ARTIFACT_BYTES_UNAVAILABLE',f'$.sources[{i}]')
                if artifact.get('artifactId')!=source['artifactId']:raise ContractFailure('ARTIFACT_IDENTITY_MISMATCH',f'$.sources[{i}].artifactId')
                if not isinstance(artifact.get('contentSha256'),str):raise ContractFailure('ARTIFACT_DIGEST_UNAVAILABLE',f'$.sources[{i}]')
                if hashlib.sha256(artifact['bytes']).hexdigest()!=artifact['contentSha256']:raise ContractFailure('ARTIFACT_BYTES_DIGEST_MISMATCH',f'$.sources[{i}]')
                if source['kind']=='IMAGE':
                    if not isinstance(artifact.get('mediaType'),str) or not artifact['mediaType'].startswith('image/'):raise ContractFailure('ARTIFACT_MEDIA_TYPE_MISMATCH',f'$.sources[{i}]')
                    from PIL import Image,UnidentifiedImageError
                    try:
                        with Image.open(io.BytesIO(artifact['bytes'])) as image:image.verify()
                    except (UnidentifiedImageError,OSError,SyntaxError):raise ContractFailure('ARTIFACT_BYTES_MEDIA_INVALID',f'$.sources[{i}]')
            if source['kind']=='OBJECT_REF':
                record=server.get('targets',{}).get(source['objectId'])
                if record is None:raise ContractFailure('OBJECT_REFERENCE_UNRESOLVED',f'$.sources[{i}].objectId')
                if record.get('objectId')!=source['objectId']:raise ContractFailure('OBJECT_REFERENCE_IDENTITY_MISMATCH',f'$.sources[{i}].objectId')
            if source['kind']=='CREDENTIAL_REF':
                if source['stableName'] not in server.get('stableNames',[]):raise ContractFailure('SECRET_REFERENCE_UNRESOLVED',f'$.sources[{i}].stableName')
                if source['stableName'] not in server.get('credentialSourceContexts',[]):raise ContractFailure('SECRET_USE_CONTEXT_UNVERIFIED',f'$.sources[{i}]')
            if source['kind']=='URL':
                origin=urlsplit(source['url']);origin=origin.scheme+'://'+origin.netloc
                if origin not in server.get('sourceOrigins',[]):raise ContractFailure('SOURCE_NAVIGATION_POLICY_REJECT',f'$.sources[{i}].url')
    else:
        if body.get('targetObjectId') and body['targetObjectId'] not in server.get('targets',{}):raise ContractFailure('TARGET_UNRESOLVED','$.targetObjectId')
        if body['stableName'] in server.get('stableNames',[]):raise ContractFailure('STABLE_NAME_UNAVAILABLE','$.stableName')
        if body['stableName'] in ['KCML_OWNER_API_KEY','PASS']:raise ContractFailure('RESERVED_CREDENTIAL_REQUIRES_SPECIAL_CONTRACT','$.stableName')
        if body['value'].get('representation')=='PROFILE_JSON_V1':
            from secret_profile_import import registry_profile,Rejected
            try:registry_profile(body['value']['profileId'],server.get('secretProfileRegistryReader'),server.get('secretProfileNormativeSourceDigest'),server.get('secretProfileReviewReceiptDigest'))
            except Rejected as e:raise ContractFailure(e.code,e.pointer)
        elif body['type'] not in ['PASSWORD','API_KEY','BEARER_TOKEN','WEBHOOK_SECRET','GENERIC_TEXT','GENERIC_BINARY']:raise ContractFailure('SECRET_PROFILE_REQUIRED','/value')
        # Type name flags cannot replace a value grammar. Structured/crypto types
        # stay blocked until their exact authoritative formats are resolved.
    result={'action':'RESERVE_ATOMIC_CREATE','dispatchNew':True,'serverWriter':'generation-orchestrator' if request['operationId']=='generation.job.create' else 'secret'}

    if selected is not None: result['generationAdmission']=selected
    if frozen is not None: result['frozenBasis']=frozen
    return result
