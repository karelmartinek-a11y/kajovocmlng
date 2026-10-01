"""Trusted repository -> closed create-read consumer; no fake auth/crypto claim."""
import json,hashlib
from pathlib import Path
from generation_create_consumer_archive import *
HERE=Path(__file__).parent

def digest(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()

def hydrate_storage(row,*,selected_job_id,authenticated_owner_id,open_snapshot,archive_binding=None,archive_bundles=None,policy_implementations=None,previous=None):
    """owner and open_snapshot come from trusted service, never client JSON.

    open_snapshot(snapshotId, expected) must perform canonical authenticated
    decryption and actual record identity/schema/profile/AAD verification.
    This module proves consumer use of returned actual bytes, NOT the crypto
    or OWNER token verifier. No callback valid flags are consumed.
    Internal SQL row is kept internal; no whole-job-read replacement intended.
    """
    if row is None:fail('GENERATION_READ_STORAGE_UNAVAILABLE')
    if set(row)!={'root','creation','initialRequestRef','event','links'}:fail('GENERATION_READ_STORAGE_SHAPE_INVALID')
    root=row['root'];creation=row['creation'];ref=row['initialRequestRef'];event=row['event'];links=row['links']
    validate_schema(json.loads(__import__('ssot_sources').resource_index()['contracts/generation/root-storage-read.schema.json']['raw']),root,'GENERATION_READ_ROOT_SCHEMA_INVALID')
    if root['ownerId']!=authenticated_owner_id:fail('GENERATION_READ_OWNER_MISMATCH')
    if root['jobId']!=selected_job_id:fail('READ_JOB_IDENTITY_MISMATCH')
    if root['initialRequestSnapshotId']!=ref['snapshotId']or root['jobId']!=ref['jobId']:fail('INITIAL_SNAPSHOT_IDENTITY_MISMATCH')
    if root['initialRequestDigest']!=ref['contentDigest']:fail('GENERATION_READ_SNAPSHOT_ROOT_DIGEST_MISMATCH')
    if len({creation['logicalOperationId'],ref['logicalOperationId'],event['logicalOperationId'],links['logicalOperationId']})!=1:fail('GENERATION_READ_COMMAND_IDENTITY_MISMATCH')
    if event['id']!=creation['eventId']or event['aggregateId']!=selected_job_id or event['sequence']!=creation['eventSequence']:fail('GENERATION_READ_EVENT_IDENTITY_MISMATCH')
    if int(root['eventSequence'])<int(event['sequence']):fail('GENERATION_READ_EVENT_SEQUENCE_REGRESSION')
    if not all(links.get(x)for x in ['outboxId','auditId','locatorId']):fail('GENERATION_READ_ATOMIC_LINKS_MISSING')
    try:receipt_raw=bytes.fromhex(creation['receiptHex']);semantic_raw=bytes.fromhex(creation['semanticResponseHex']);event_raw=bytes.fromhex(event['payloadHex'])
    except (TypeError,ValueError,KeyError):fail('GENERATION_READ_STORED_BYTES_ENCODING_INVALID')
    if digest(receipt_raw)!=creation['receiptDigest']or digest(event_raw)!=event['payloadDigest']:fail('GENERATION_READ_RECEIPT_BYTES_DIGEST_MISMATCH')
    if receipt_raw!=event_raw:fail('GENERATION_READ_RECEIPT_EVENT_BYTES_MISMATCH')
    if digest(semantic_raw)!=creation['resultDigest']or links['canonicalOutcomeDigest']!=creation['resultDigest']:fail('GENERATION_READ_RETAINED_RESULT_DIGEST_MISMATCH')
    semantic=strict_json(semantic_raw);receipt=strict_json(receipt_raw)
    if semantic.get('status')!='SUCCEEDED'or semantic.get('terminal')is not True or semantic.get('output')!=receipt or semantic.get('error')is not None:fail('GENERATION_READ_RETAINED_OUTCOME_INVALID')
    retained={**semantic,'resultDigest':creation['resultDigest'],'idempotencyReplay':False}
    retry_action(retained,'internal-read','internal-read')
    for key,rk in [('jobId','jobId'),('kind','kind'),('createdAt','createdAt')]:
        # Native PostgreSQL timestamps may use +00:00 rather than Z.
        if key=='createdAt':
            from datetime import datetime
            if datetime.fromisoformat(receipt[key].replace('Z','+00:00'))!=datetime.fromisoformat(root[rk].replace('Z','+00:00')):fail('IMMUTABLE_CREATE_LINK_MISMATCH','/'+key)
        elif receipt[key]!=root[rk]:fail('IMMUTABLE_CREATE_LINK_MISMATCH','/'+key)
    if receipt['stateVersion']!=creation['stateVersion']:fail('GENERATION_READ_COMMITTED_VERSION_MISMATCH')
    projection={**receipt,'state':root['state'],'stateVersion':root['stateVersion'],'eventSequence':root['eventSequence'],
        'initialRequestRef':{'snapshotId':ref['snapshotId'],'contentDigest':ref['contentDigest'],'mediaType':'application/json'}}
    from generation_frozen_archive import compile_archived_request
    if archive_binding is None:fail('FROZEN_DOMAIN_POLICY_UNAVAILABLE')
    if archive_binding['schemaId']!=ref['schemaId']or archive_binding['schemaDigest']!=ref['schemaDigest']:fail('FROZEN_POLICY_SNAPSHOT_BINDING_MISMATCH')
    validator=compile_archived_request(archive_binding,archive_bundles or {},policy_implementations=policy_implementations or {})
    if not callable(open_snapshot):fail('GENERATION_READ_AUTHENTICATED_OPEN_UNAVAILABLE')
    raw=open_snapshot(ref['snapshotId'],dict(ref))
    if not isinstance(raw,bytes):fail('INITIAL_REQUEST_BYTES_UNAVAILABLE')
    stored={'jobId':ref['jobId'],'snapshotId':ref['snapshotId'],'bytes':raw}
    return consume(receipt,projection,stored,selected_job_id=selected_job_id,
      producer=('CANONICAL_OWNER_API','generation.job.read',selected_job_id),previous=previous,request_validator=validator)
