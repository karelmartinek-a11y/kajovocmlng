"""Bounded OWNER rotation projection producer; full adapter remains BLOCKED.

Actual API verifier, canonical physical roots/crypto, exact CAS/epochs and actual
transaction completion. Missing effective dependent invalidation inventory and
real credential source are not substituted with an empty table or validity flag.
"""
import secrets,uuid,json
from generation_auth_crypto import canonical,sha,seal,verify_token,fingerprint,verifier_hash,fail
from create_operation_contracts import strict_json
from create_completion_contracts import semantic_result,canonical_digest
from secret_command_chain_eligible import lit,b,q,uid,validate_locked_credential_root

def rotate_owner_api_key(*args,**kwargs):fail('OWNER_ROTATION_EFFECTIVE_INVALIDATION_INVENTORY_UNRESOLVED')
def parse_request(raw):
 body=strict_json(raw)
 if type(body)is not dict or set(body)!={'expectedCredentialStateVersion','expectedSecretStateVersion'}:fail('OWNER_ROTATION_REQUEST_FIELDS_INVALID')
 import re
 for value in body.values():
  if type(value)is not str or re.fullmatch(r'0|[1-9][0-9]{0,18}',value)is None or int(value)>9223372036854775807:fail('OWNER_ROTATION_EXPECTED_VERSION_INVALID')
 return body

def fixture_rotate_projection(db,token,raw,client_key,key,key_id,retention_until):
 if db.transaction_status()!=2:fail('OWNER_ROTATION_TRANSACTION_REQUIRED')
 body=parse_request(raw);request=sha(canonical({'operationId':'ownerApiKey.rotate','body':body}));key_digest=sha(client_key.encode())
 q(db,'SELECT pg_advisory_xact_lock_shared(1000,0)')
 pi=q(db,'SELECT platform_incarnation_id FROM platform_incarnation WHERE singleton_key=1 FOR SHARE')
 dh=q(db,'SELECT platform_incarnation_id,application_deployment_epoch FROM application_deployment_head WHERE singleton_key=1 FOR SHARE')
 if len(pi)!=1 or len(dh)!=1 or pi[0][0]!=dh[0][0]:fail('SECRET_DEPLOYMENT_CONTEXT_MISMATCH')
 c=q(db,'SELECT verifier_hash,fingerprint,credential_version,credential_activation_epoch,secret_id,secret_version_id,state_version FROM owner_api_credential WHERE singleton_key=1 FOR UPDATE')
 if len(c)!=1:fail('OWNER_API_CREDENTIAL_UNRESOLVED')
 c=c[0];fp=verify_token(token,c[0],4096)
 if fp!=c[1]:fail('OWNER_API_VERIFIER_FINGERPRINT_MISMATCH')
 owner=q(db,'SELECT id FROM owner_identity WHERE singleton_key=1')[0][0]
 pins=q(db,"SELECT operation_revision FROM kcml_secret_v1.operation_contract_publication WHERE operation_id='ownerApiKey.rotate' AND application_deployment_epoch="+dh[0][1])
 if len(pins)!=1:fail('OWNER_ROTATION_CONTRACT_UNAVAILABLE')
 auth={'owner':owner,'fingerprint':fp,'credentialSecretId':c[4],'credentialSecretVersionId':c[5]}
 descriptor=canonical({'callerAuthorityKind':'OWNER_FULL','clientKeyDigest':'sha256:'+key_digest.hex(),'operationContractId':'ownerApiKey.rotate','operationContractRevision':pins[0][0],'stableBusinessTargetKey':'KCML_OWNER_API_KEY','stableCallerObjectId':owner,'stableCallerRevisionId':None});scope=sha(descriptor);op=uid();sid=c[4]
 q(db,'INSERT INTO idempotency_locator(locator_id,operation_family,caller_authority_kind,caller_stable_id,business_target_kind,business_target_id,client_key_digest,logical_operation_id,client_request_digest,execution_descriptor_digest,frozen_revision_digest,created_at,terminal_at,retention_until)VALUES('+','.join([lit(uid()),"'SECRET'","'OWNER_FULL'",lit(owner),"'OWNER_API_CREDENTIAL'",lit(sid),b(key_digest),lit(op),b(request),b(scope),b(scope),'clock_timestamp()','NULL',lit(retention_until)])+')ON CONFLICT ON CONSTRAINT uq_idempotency_locator_scope DO NOTHING')
 locator=q(db,"SELECT logical_operation_id,encode(client_request_digest,'hex'),encode(frozen_revision_digest,'hex')FROM idempotency_locator WHERE operation_family='SECRET'AND caller_authority_kind='OWNER_FULL'AND caller_stable_id="+lit(owner)+"AND business_target_kind='OWNER_API_CREDENTIAL'AND business_target_id="+lit(sid)+'AND client_key_digest='+b(key_digest)+' FOR UPDATE')[0]
 if locator[0]!=op:
  import hmac
  if not hmac.compare_digest(bytes.fromhex(locator[1]),request):fail('IDEMPOTENCY_CONFLICT')
  old=q(db,'SELECT logical_operation_id FROM domain_idempotency_record WHERE scope_digest='+b(bytes.fromhex(locator[2]))+'AND key_digest='+b(key_digest)+' FOR UPDATE')
  if len(old)!=1 or old[0][0]!=locator[0]:fail('OWNER_ROTATION_RETAINED_COMMAND_UNAVAILABLE')
  q(db,'SELECT id FROM owner_identity WHERE id='+lit(owner)+' FOR UPDATE');q(db,'SELECT id FROM kcml_secret_v1.secret_record WHERE id='+lit(sid)+' FOR UPDATE');validate_locked_credential_root(db,auth)
  receipt=q(db,"SELECT convert_from(output_receipt_bytes,'UTF8')FROM kcml_secret_v1.rotation_projection_completion WHERE logical_operation_id="+lit(locator[0]))
  if len(receipt)!=1:fail('OWNER_ROTATION_RETAINED_OUTCOME_UNAVAILABLE')
  return {'output':json.loads(receipt[0][0]),'logicalOperationId':locator[0],'replay':True}
 q(db,'INSERT INTO domain_idempotency_record VALUES('+','.join([b(scope),b(key_digest),b(request),lit(op),"'RESERVED'",'0','NULL'])+')')
 q(db,'SELECT logical_operation_id FROM domain_idempotency_record WHERE scope_digest='+b(scope)+'AND key_digest='+b(key_digest)+' FOR UPDATE')
 q(db,'SELECT id FROM owner_identity WHERE id='+lit(owner)+' FOR UPDATE')
 root=q(db,'SELECT state_version,secret_activation_epoch,active_version_id FROM kcml_secret_v1.secret_record WHERE id='+lit(sid)+' FOR UPDATE')[0];validate_locked_credential_root(db,auth)
 if int(c[6])!=int(body['expectedCredentialStateVersion']):fail('OWNER_ROTATION_CREDENTIAL_STATE_CAS_CONFLICT')
 if int(root[0])!=int(body['expectedSecretStateVersion']):fail('OWNER_ROTATION_SECRET_STATE_CAS_CONFLICT')
 if max(int(c[2]),int(c[3]),int(c[6]),int(root[0]),int(root[1]))>=9223372036854775807:fail('OWNER_ROTATION_VERSION_EXHAUSTED')
 ctx=uid();vid=uid();event=uid();correlation=uid();newtoken=secrets.token_urlsafe(32).encode('ascii');newfp=fingerprint(newtoken)
 now=q(db,"SELECT to_char(clock_timestamp()AT TIME ZONE'UTC','YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')")[0][0]
 number=int(q(db,'SELECT COALESCE(max(version_number),0)+1 FROM kcml_secret_v1.secret_version WHERE secret_id='+lit(sid))[0][0])
 q(db,'INSERT INTO kcml_secret_v1.owner_api_context VALUES('+','.join([lit(ctx),lit(owner),"'ownerApiKey.rotate'","'ROTATE_OWNER_API_CREDENTIAL'","'OWNER_API_KEY'",b(request),b(descriptor),b(scope),lit(pi[0][0]),dh[0][1],lit(pins[0][0]),c[2],c[3],lit(fp),lit(now)])+')')
 metadata={'ownerId':owner,'secretId':sid,'secretVersionId':vid,'secretType':'API_KEY','representation':'RAW_UTF8','profileId':None,'schemaId':None,'schemaDigest':None,'plaintextByteLength':len(newtoken),'originalImportBytesDigest':'sha256:'+sha(newtoken).hex(),'canonicalValueDigest':'sha256:'+sha(newtoken).hex(),'trustedContextId':ctx,'logicalOperationId':op}
 envelope=seal(newtoken,key,key_id,metadata,purpose='SECRET_IMMUTABLE_VERSION')
 q(db,'INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,creator_context_id)VALUES('+','.join([lit(vid),lit(sid),str(number),"'API_KEY'","'RAW_UTF8'","'EXACT_SECRET_BYTES_V1'",str(len(newtoken)),b(envelope['ciphertext']),b(envelope['nonce']),lit(envelope['algorithm']),lit(key_id),lit(newfp),b(sha(newtoken)),b(sha(newtoken)),"'CREATED'",lit(now),lit(ctx)])+')')
 q(db,"UPDATE kcml_secret_v1.secret_version SET lifecycle='RETIRED',retired_at="+lit(now)+'WHERE id='+lit(c[5])+"AND lifecycle='ACTIVE'")
 q(db,"UPDATE kcml_secret_v1.secret_version SET lifecycle='ACTIVE',activated_at="+lit(now)+',activation_logical_operation_id='+lit(op)+"WHERE id="+lit(vid)+"AND lifecycle='CREATED'")
 updated=q(db,'UPDATE kcml_secret_v1.secret_record SET active_version_id='+lit(vid)+',state_version=state_version+1,secret_activation_epoch=secret_activation_epoch+1,updated_at='+lit(now)+' WHERE id='+lit(sid)+'AND state_version='+body['expectedSecretStateVersion']+' RETURNING id')
 if len(updated)!=1:fail('OWNER_ROTATION_SECRET_STATE_CAS_CONFLICT')
 output={'secretId':sid,'activeVersionId':vid,'versionNumber':str(number),'recordStatus':'ACTIVE','secretStateVersion':str(int(root[0])+1),'secretActivationEpoch':str(int(root[1])+1),'credentialVersion':str(int(c[2])+1),'credentialStateVersion':str(int(c[6])+1),'credentialActivationEpoch':str(int(c[3])+1),'fingerprint':newfp,'rotatedAt':now}
 receipt=canonical(output);response={'routeId':'route.0024','operationId':'ownerApiKey.rotate','logicalOperationId':op,'correlationId':correlation,'status':'SUCCEEDED','terminal':True,'output':output,'error':None,'stateVersion':output['credentialStateVersion'],'eventSequence':output['secretActivationEpoch'],'activationEpoch':output['secretActivationEpoch'],'idempotencyReplay':False};result=bytes.fromhex(canonical_digest(semantic_result(response))[7:])
 q(db,'UPDATE owner_api_credential SET secret_version_id='+lit(vid)+',verifier_hash='+lit(verifier_hash(newtoken))+',fingerprint='+lit(newfp)+',credential_version=credential_version+1,state_version=state_version+1,credential_activation_epoch=credential_activation_epoch+1,last_rotate_logical_operation_id='+lit(op)+',last_rotate_outcome_digest='+b(result)+',rotated_at='+lit(now)+'WHERE singleton_key=1 AND state_version='+body['expectedCredentialStateVersion'])
 q(db,'INSERT INTO domain_command(logical_operation_id,operation_id,owner_id,request_digest,execution_descriptor_bytes,execution_descriptor_digest,state,terminal,state_version,result_digest,platform_incarnation_id,application_deployment_epoch,created_at,updated_at,command_id,operation_contract_revision,caller_channel,execution_context_id,target_aggregate_kind,target_aggregate_id,canonical_arguments_snapshot_id,scope_digest,client_key_digest,correlation_id,accepted_at,terminal_at)VALUES('+','.join([lit(op),"'ownerApiKey.rotate'",lit(owner),b(request),b(descriptor),b(scope),"'SUCCEEDED'",'true','1',b(result),lit(pi[0][0]),dh[0][1],lit(now),lit(now),lit(uid()),lit(pins[0][0]),"'OWNER_API_KEY'",lit(ctx),"'SECRET_RECORD'",lit(sid),lit(vid),b(scope),b(key_digest),lit(correlation),lit(now),lit(now)])+')')
 q(db,'INSERT INTO domain_event VALUES('+','.join([lit(event),lit(sid),"'SECRET_RECORD'",lit(op),output['secretActivationEpoch'],"'OPERATION_TERMINAL'","'urn:kcml:r9:route:route.0024:event'",b(sha(canonical(json.loads((__import__('pathlib').Path(__file__).parent/'rotation-event-projection-proposal.schema.json').read_bytes())))),b(receipt),b(sha(receipt)),lit(correlation),'NULL',lit(now)])+')')
 q(db,'INSERT INTO kcml_secret_v1.rotation_projection_completion VALUES('+','.join([lit(op),lit(ctx),lit(sid),lit(vid),lit(event),b(receipt),b(canonical(semantic_result(response))),b(result),c[6],root[0],c[2],c[3],root[1]])+')')
 q(db,"UPDATE domain_idempotency_record SET state='SUCCEEDED',state_version=state_version+1,canonical_outcome_digest="+b(result)+'WHERE logical_operation_id='+lit(op)+"AND state='RESERVED';UPDATE idempotency_locator SET terminal_at="+lit(now)+'WHERE logical_operation_id='+lit(op))
 q(db,'INSERT INTO transactional_outbox(id,event_id,logical_operation_id,aggregate_id,purpose,consumer_scope,available_at,state,payload_digest)VALUES('+','.join([lit(uid()),lit(event),lit(op),lit(sid),"'DOMAIN_EVENT'","'BOUNDED_ROTATION_PROJECTION_ONLY'",lit(now),"'READY'",b(sha(receipt))])+')')
 head=q(db,"SELECT last_sequence,encode(last_hash,'hex')FROM audit_head WHERE singleton_key=1 FOR UPDATE")[0];seq=int(head[0])+1;prev=bytes.fromhex(head[1]);auditbytes=canonical({'logicalOperationId':op,'eventId':event,'objectId':sid,'actorId':owner,'beforeDigest':None,'afterDigest':'sha256:'+sha(receipt).hex(),'correlationId':correlation,'causationId':None,'traceId':correlation,'occurredAt':now,'chainSequence':str(seq),'previousHash':'sha256:'+prev.hex()})
 q(db,'INSERT INTO audit_event VALUES('+','.join([lit(uid()),str(seq),b(prev),'kcml_audit_hash_v1(1,'+b(prev)+','+str(seq)+','+b(auditbytes)+')','1',lit(op),lit(event),b(auditbytes),'false'])+');UPDATE audit_head SET last_sequence='+str(seq)+',last_hash=kcml_audit_hash_v1(1,'+b(prev)+','+str(seq)+','+b(auditbytes)+'),state_version=state_version+1 WHERE singleton_key=1')
 return {'output':output,'logicalOperationId':op,'replay':False,'fixtureGeneratedToken':newtoken,'metadata':metadata,'envelope':envelope}
