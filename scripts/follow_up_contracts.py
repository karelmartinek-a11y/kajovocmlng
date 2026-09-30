"""Approved FOLLOW_UP admission projection; reference design, never runtime evidence.

Client selectors/digest hints select persisted immutable inputs. They do not confer
ownership, execution authority, publication status, or byte authenticity.
"""
import copy, hashlib, json, uuid
from jsonschema import Draft202012Validator, FormatChecker

STATES = ['ACTIVATING','ANALYZING','BLOCKED','CANCELLED','CML_CONFORMANCE','COMPLETED','DISCUSSING','FAILED','IMPLEMENTING','INTEGRATING','VALIDATING']
KINDS = ['CREATE','UPDATE','FOLLOW_UP','RETRY','REPAIR']
AVAILABILITY = ['AVAILABLE_IMMUTABLE','MISSING','INCONSISTENT','INSUFFICIENT','UNPUBLISHED']
BASIS_KINDS = ['INITIAL_REQUEST','SPECIFICATION_REVISION','PUBLISHED_FINAL_OUTPUT']
AUTHORITY = ['SSOT §12.41','SSOT §25.11 generation_job/generation_spec_revision/generation_execution_authority','SSOT §49.4','SSOT §49.5','USER_APPROVED_FOLLOW_UP_2026_09_30_CONDITIONS_1_TO_7']
DIGEST = {'type':'string','pattern':'^sha256:[0-9a-f]{64}$(?![\\s\\S])'}
UID = {'type':'string','format':'uuid'}

def request_schema():
    variants=[]
    for kind,key in [('INITIAL_REQUEST',None),('SPECIFICATION_REVISION','revisionId'),('PUBLISHED_FINAL_OUTPUT','artifactId')]:
        props={'basisKind':{'const':kind},'expectedDigest':copy.deepcopy(DIGEST)}
        if key: props[key]=copy.deepcopy(UID)
        variants.append({'type':'object','additionalProperties':False,'properties':props,'required':list(props)})
    return {'oneOf':variants,'$comment':'Explicit caller selector and digest precondition only; server verifies owned immutable persisted bytes and required publication evidence atomically. Approved FOLLOW_UP rule 2026-09-30.'}

def frozen_basis_schema():
    """Server-created persisted/hydrated descriptor, containing no source bytes."""
    variants=[]
    for kind,key in [('INITIAL_REQUEST',None),('SPECIFICATION_REVISION','revisionId'),('PUBLISHED_FINAL_OUTPUT','artifactId')]:
        props={'sourceJobId':copy.deepcopy(UID),'snapshotId':copy.deepcopy(UID),'basisKind':{'const':kind},'contentDigest':copy.deepcopy(DIGEST),'lineageDigest':copy.deepcopy(DIGEST)}
        if key: props[key]=copy.deepcopy(UID)
        if kind=='PUBLISHED_FINAL_OUTPUT': props['publicationReceiptId']=copy.deepcopy(UID)
        variants.append({'type':'object','additionalProperties':False,'properties':props,'required':list(props)})
    return {'oneOf':variants,'$comment':'Server-owned immutable persisted reference; actual bytes hydration and lineage digest verification mandatory. No plaintext or execution authority in descriptor.'}

def _fail(code,pointer=''):
    from create_operation_contracts import ContractFailure
    raise ContractFailure(code,pointer)

def _digest(raw): return 'sha256:'+hashlib.sha256(raw).hexdigest()

def _uuid(value):
    try: return isinstance(value,str) and str(uuid.UUID(value))==value.lower()
    except (ValueError,AttributeError): return False

def admit_follow_up(body,server):
    """Read an atomic server snapshot and return an isolated frozen descriptor.

The integrating transaction must persist this descriptor, a new child identity,
request/idempotency receipt, audit and outbox together. This reference function
has no side effects and cannot itself prove locks, commits or runtime ownership.
"""
    if body.get('kind')!='FOLLOW_UP': _fail('FOLLOW_UP_KIND_REQUIRED','$.kind')
    if not _uuid(body.get('parentJobId')): _fail('FOLLOW_UP_PARENT_REQUIRED','$.parentJobId')
    basis=body.get('followUpBasis')
    if list(Draft202012Validator(request_schema(),format_checker=FormatChecker()).iter_errors(basis)):
        _fail('FOLLOW_UP_BASIS_INVALID','$.followUpBasis')
    if server.get('actor')!='OWNER' or server.get('authenticated') is not True or not isinstance(server.get('owner'),str) or not server['owner']:
        _fail('AUTHENTICATION_REQUIRED')
    if server.get('atomicGenerationAdmission') is not True:
        _fail('FOLLOW_UP_ATOMIC_ADMISSION_UNVERIFIED')
    parent=server.get('jobs',{}).get(body['parentJobId'])
    if parent is None: _fail('PARENT_JOB_UNRESOLVED','$.parentJobId')
    if parent.get('jobId')!=body['parentJobId']: _fail('PARENT_JOB_IDENTITY_MISMATCH','$.parentJobId')
    if parent.get('owner')!=server.get('owner'): _fail('FOLLOW_UP_SOURCE_OWNER_MISMATCH','$.parentJobId')
    if parent.get('state') not in STATES: _fail('FOLLOW_UP_SOURCE_STATE_INVALID','$.parentJobId')
    selector=basis.get('revisionId',basis.get('artifactId',''))
    source=server.get('sourceSnapshots',{}).get((body['parentJobId'],basis['basisKind'],selector))
    if source is None or source.get('available') is not True:
        _fail('FOLLOW_UP_BASIS_UNAVAILABLE','$.followUpBasis')
    if source.get('jobId')!=parent['jobId'] or source.get('basisKind')!=basis['basisKind']:
        _fail('FOLLOW_UP_BASIS_IDENTITY_MISMATCH','$.followUpBasis')
    if source.get('owner')!=server['owner']: _fail('FOLLOW_UP_SOURCE_OWNER_MISMATCH','$.followUpBasis')
    if not _uuid(source.get('snapshotId')): _fail('FOLLOW_UP_SNAPSHOT_IDENTITY_INVALID','$.followUpBasis')
    for key in ['revisionId','artifactId']:
        if key in basis and source.get(key)!=basis[key]: _fail('FOLLOW_UP_BASIS_IDENTITY_MISMATCH','$.followUpBasis.'+key)
    if source.get('immutable') is not True: _fail('FOLLOW_UP_BASIS_NOT_IMMUTABLE','$.followUpBasis')
    raw=source.get('bytes')
    if not isinstance(raw,bytes): _fail('FOLLOW_UP_BASIS_BYTES_UNAVAILABLE','$.followUpBasis')
    actual=_digest(raw)
    if source.get('contentDigest')!=actual: _fail('FOLLOW_UP_BASIS_BYTES_DIGEST_MISMATCH','$.followUpBasis')
    if basis['expectedDigest']!=actual: _fail('FOLLOW_UP_BASIS_DIGEST_CONFLICT','$.followUpBasis.expectedDigest')
    if basis['basisKind']=='PUBLISHED_FINAL_OUTPUT':
        if not _uuid(source.get('publicationReceiptId')): _fail('FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED','$.followUpBasis')
        receipt=server.get('publicationReceipts',{}).get(source.get('publicationReceiptId'))
        if receipt is None or receipt.get('outcome')!='COMMITTED': _fail('FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED','$.followUpBasis')
        if receipt.get('receiptId')!=source.get('publicationReceiptId') or receipt.get('jobId')!=parent['jobId'] or receipt.get('artifactId')!=basis['artifactId'] or receipt.get('contentDigest')!=actual:
            _fail('FOLLOW_UP_PUBLICATION_RECEIPT_MISMATCH','$.followUpBasis')
    _validate_content(body,source,server)
    descriptor={'sourceJobId':parent['jobId'],'snapshotId':source['snapshotId'],'basisKind':basis['basisKind'],'contentDigest':actual}
    for key in ['revisionId','artifactId']:
        if key in basis: descriptor[key]=basis[key]
    if basis['basisKind']=='PUBLISHED_FINAL_OUTPUT': descriptor['publicationReceiptId']=source['publicationReceiptId']
    # The lineage excludes mutable parent state/current pointers. Later source
    # progress, failure, cancellation or deletion cannot reinterpret these inputs.
    descriptor['lineageDigest']=_digest(json.dumps(descriptor,sort_keys=True,separators=(',',':')).encode())
    return {'frozenBasis':descriptor,'sourceStateObserved':parent['state'],'decision':'ALLOW_FOLLOW_UP','sourceMutationAllowed':False}

def matrix():
    rows=[]
    for kind in KINDS:
        for state in STATES:
            for availability in AVAILABILITY:
                if kind=='FOLLOW_UP':
                    allow=availability=='AVAILABLE_IMMUTABLE'
                    errors={'MISSING':'FOLLOW_UP_BASIS_UNAVAILABLE','INCONSISTENT':'FOLLOW_UP_BASIS_INCONSISTENT','INSUFFICIENT':'FOLLOW_UP_BASIS_INSUFFICIENT','UNPUBLISHED':'FOLLOW_UP_FINAL_OUTPUT_UNPUBLISHED'}
                    decision='ALLOW_IF_ATOMIC_IDENTITY_AUTHORITY_BYTES_AND_REQUIRED_PUBLICATION_VERIFIED' if allow else 'REJECT'
                    reason='Approved independent branch uses frozen sufficient basis; source terminality is not an admission prerequisite.' if allow else errors[availability]
                    status='SPECIFIED'
                else:
                    decision='BLOCKED_SEPARATE_KIND_ADMISSION_REVIEW';status='OPEN'
                    reason={'CREATE':'No parent is required for baseline CREATE; parent-linked CREATE semantics must not be inferred from FOLLOW_UP.', 'UPDATE':'Own target snapshot, preserved component/runtime identity, compatibility and migration plan per §12.41.', 'RETRY':'Retained approved functional authority and failed technical part only per §12.41; source lifecycle eligibility needs its own exact admission rule.', 'REPAIR':'Monitoring evidence and last approved functional lineage with preserved identity per §12.41; own source eligibility needs independent review.'}[kind]
                rows.append({'kind':kind,'sourceState':state,'basisAvailability':availability,'decision':decision,'reason':reason,'status':status,'authorityRefs':AUTHORITY if kind=='FOLLOW_UP' else ['SSOT §12.41']})
    return {'scope':'FOLLOW_UP product decision only; no closure claim for other kinds','rows':rows,'rowCount':len(rows),'followUpRowCount':len(STATES)*len(AVAILABILITY),'implementationProductionAcceptance':'NOT_EVALUATED'}

def hydrate_frozen_basis(descriptor,server):
    """Consumer-side reference hydration; returned bytes are internal, never logs/API.

Parent current pointers/state and mutable eligibility flags are intentionally not
read. Consumer rechecks the frozen identity, retained receipt and actual bytes.
"""
    if list(Draft202012Validator(frozen_basis_schema(),format_checker=FormatChecker()).iter_errors(descriptor)):
        _fail('FOLLOW_UP_FROZEN_DESCRIPTOR_INVALID')
    canonical={k:v for k,v in descriptor.items() if k!='lineageDigest'}
    if descriptor['lineageDigest']!=_digest(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()):
        _fail('FOLLOW_UP_FROZEN_LINEAGE_DIGEST_MISMATCH')
    records=[v for v in server.get('sourceSnapshots',{}).values() if v.get('snapshotId')==descriptor['snapshotId']]
    if len(records)!=1: _fail('FOLLOW_UP_FROZEN_SNAPSHOT_UNAVAILABLE')
    source=records[0]
    if not isinstance(server.get('owner'),str) or not server['owner'] or source.get('owner')!=server['owner']:
        _fail('FOLLOW_UP_SOURCE_OWNER_MISMATCH')
    for sourcekey,key in [('jobId','sourceJobId'),('basisKind','basisKind'),('contentDigest','contentDigest'),('revisionId','revisionId'),('artifactId','artifactId'),('publicationReceiptId','publicationReceiptId')]:
        if key in descriptor and source.get(sourcekey)!=descriptor[key]: _fail('FOLLOW_UP_FROZEN_IDENTITY_MISMATCH')
    if source.get('immutable') is not True: _fail('FOLLOW_UP_BASIS_NOT_IMMUTABLE')
    if not isinstance(source.get('bytes'),bytes): _fail('FOLLOW_UP_BASIS_BYTES_UNAVAILABLE')
    if _digest(source['bytes'])!=descriptor['contentDigest']: _fail('FOLLOW_UP_BASIS_BYTES_DIGEST_MISMATCH')
    if descriptor['basisKind']=='PUBLISHED_FINAL_OUTPUT':
        receipt=server.get('publicationReceipts',{}).get(descriptor['publicationReceiptId'])
        if receipt is None or receipt.get('outcome')!='COMMITTED': _fail('FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED')
        if receipt.get('receiptId')!=descriptor['publicationReceiptId'] or receipt.get('jobId')!=descriptor['sourceJobId'] or receipt.get('artifactId')!=descriptor['artifactId'] or receipt.get('contentDigest')!=descriptor['contentDigest']:
            _fail('FOLLOW_UP_PUBLICATION_RECEIPT_MISMATCH')
    body={'kind':'FOLLOW_UP','parentJobId':descriptor['sourceJobId'],'followUpBasis':{'basisKind':descriptor['basisKind'],'expectedDigest':descriptor['contentDigest']}}
    for key in ['revisionId','artifactId']:
        if key in descriptor:body['followUpBasis'][key]=descriptor[key]
    _validate_content(body,source,server)
    return source['bytes']

def _validate_content(body,source,server):
    from generation_admission_contracts import Repository,validate_follow_up_content,validate_declared_final_output
    repository=server.get('generationBasisRepository')
    if not isinstance(repository,Repository):_fail('GENERATION_ADMISSION_CONTRACT_UNRESOLVED')
    if repository.owner!=server['owner']:_fail('GENERATION_BASIS_OWNER_MISMATCH')
    kind=body['followUpBasis']['basisKind']
    identity=source['snapshotId'] if kind=='INITIAL_REQUEST' else body['followUpBasis']['revisionId' if kind=='SPECIFICATION_REVISION' else 'artifactId']
    if source.get('recordId')!=identity:_fail('GENERATION_BASIS_IDENTITY_MISMATCH')
    validated=validate_follow_up_content(body,identity,repository)
    if kind=='PUBLISHED_FINAL_OUTPUT':validate_declared_final_output(body,repository,server.get('finalOutputDeclarations',{}))
    return validated
