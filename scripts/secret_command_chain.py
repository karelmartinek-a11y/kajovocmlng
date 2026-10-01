"""Actual native Secret OWNER API acceptance and SQL commit producer candidate.

Own immutable context; no generation receipt, caller authorized flag, or token
expiry/scope is introduced. Caller owns one transaction until canonical commit.
The fixture key argument is explicitly not a systemd credential-source proof.
"""
import uuid,json,hashlib
from generation_auth_crypto import verify_token,fingerprint,canonical,sha,seal,fail
from create_operation_contracts import decode_http
from secret_profile_reference import canonical_value_digest,SCHEMA,schema_digest
def lit(v):
 if not isinstance(v,str) or '\x00' in v:raise ValueError('SECRET_SQL_STRING_INVALID')
 return "'"+v.replace("'","''")+"'"
def b(v):return "decode('"+v.hex()+"','hex')"
def q(db,sql):return db.query(sql)
def uid():return str(uuid.uuid4())

def authenticate_api(db,token,request_digest,operation='secret.create',ceiling=4096):
 if db.transaction_status()!=2:fail('SECRET_ACCEPTANCE_TRANSACTION_REQUIRED')
 q(db,'SELECT pg_advisory_xact_lock_shared(1000,0)')
 pi=q(db,'SELECT platform_incarnation_id FROM platform_incarnation WHERE singleton_key=1 FOR SHARE')
 dh=q(db,'SELECT platform_incarnation_id,application_deployment_epoch FROM application_deployment_head WHERE singleton_key=1 FOR SHARE')
 if len(pi)!=1 or len(dh)!=1 or pi[0][0]!=dh[0][0]:fail('SECRET_DEPLOYMENT_CONTEXT_MISMATCH')
 rows=q(db,'SELECT verifier_hash,fingerprint,credential_version,credential_activation_epoch,secret_id,secret_version_id FROM owner_api_credential WHERE singleton_key=1 FOR SHARE')
 if len(rows)!=1:fail('OWNER_API_CREDENTIAL_UNRESOLVED')
 fp=verify_token(token,rows[0][0],ceiling)
 if fp!=rows[0][1]:fail('OWNER_API_VERIFIER_FINGERPRINT_MISMATCH')
 owners=q(db,'SELECT id FROM owner_identity WHERE singleton_key=1')
 if len(owners)!=1:fail('OWNER_IDENTITY_UNRESOLVED')
 pins=q(db,"SELECT operation_revision,encode(request_schema_digest,'hex'),encode(request_schema_bytes,'hex'),encode(source_ssot_digest,'hex') FROM kcml_secret_v1.operation_contract_publication WHERE operation_id="+lit(operation)+' AND application_deployment_epoch='+dh[0][1])
 if len(pins)!=1:fail('SECRET_OPERATION_CONTRACT_UNRESOLVED')
 schema_bytes=bytes.fromhex(pins[0][2])
 if sha(schema_bytes).hex()!=pins[0][1]:fail('SECRET_OPERATION_CONTRACT_SCHEMA_DRIFT')
 if operation=='secret.create':
  from ssot_sources import resource_index
  if schema_bytes!=resource_index()['contracts/secrets/import.schema.json']['raw']:fail('SECRET_OPERATION_CONTRACT_SCHEMA_DRIFT')
 return {'owner':owners[0][0],'operation':operation,'incarnation':pi[0][0],'deployment':int(dh[0][1]),'credentialVersion':int(rows[0][2]),'credentialEpoch':int(rows[0][3]),'fingerprint':fp,'requestDigest':request_digest,'revision':pins[0][0],'credentialSecretId':rows[0][4],'credentialSecretVersionId':rows[0][5]}

def validate_locked_credential_root(db,auth):
 # Caller has B credential and sorted E root locks. No new caller authority.
 rows=q(db,"SELECT r.id,r.stable_name,r.secret_type,r.active_version_id,v.secret_id,v.id,v.secret_type,v.lifecycle,v.fingerprint,kcml_secret_v1.record_status_v1(r.id) FROM kcml_secret_v1.secret_record r LEFT JOIN kcml_secret_v1.secret_version v ON v.id=r.active_version_id WHERE r.id="+lit(auth['credentialSecretId']))
 if len(rows)!=1:fail('OWNER_API_CREDENTIAL_ROOT_UNAVAILABLE')
 r=rows[0]
 if r[1:3]!=['KCML_OWNER_API_KEY','API_KEY'] or r[3]!=auth['credentialSecretVersionId'] or r[4:8]!=[r[0],auth['credentialSecretVersionId'],'API_KEY','ACTIVE'] or r[8]!=auth['fingerprint']:
  fail('OWNER_API_CREDENTIAL_ROOT_BINDING_MISMATCH')
 if r[9]!='ACTIVE':fail('OWNER_API_CREDENTIAL_ROOT_NOT_ACTIVE')

def lock_replay_roots_and_validate(db,auth,target):
 own=q(db,'SELECT id FROM owner_identity WHERE singleton_key=1 AND id='+lit(auth['owner'])+' FOR UPDATE')
 if len(own)!=1:fail('SECRET_OWNER_IDENTITY_CHANGED')
 for root in sorted({auth['credentialSecretId'],target}):
  rows=q(db,'SELECT id FROM kcml_secret_v1.secret_record WHERE id='+lit(root)+' FOR UPDATE')
  if len(rows)!=1:fail('SECRET_REPLAY_ROOT_UNAVAILABLE')
 validate_locked_credential_root(db,auth)

def create_secret(*args,**kwargs):
 # Real adapter stays closed until exact root-status and retention authority
 # producer is normatively supplied. No caller string authorizes that policy.
 fail('SECRET_RETENTION_AUTHORITY_UNRESOLVED')

def fixture_create_secret(db,token,raw_body,client_key,key,key_id,root_status,retention_until,*,omit=()):
 """Finite import→auth→claim→cipher→root/event/audit/locator chain.

 root_status is intentionally supplied by a separate *server* policy. Its
 normative status is approved INACTIVE; this bounded producer does not
 borrow version.CREATED as record lifecycle. No optional target authority is
 silently accepted. Fixture omissions exercise atomic closure rollback only.
 """
 if root_status!='INACTIVE':fail('SECRET_CREATE_RECORD_MUST_BE_INACTIVE')
 native=decode_http('secret.create','POST','/secrets',[],[('Content-Type','application/json'),('Idempotency-Key',client_key)],raw_body)
 request=bytes.fromhex(native['requestDigest'][7:]);auth=authenticate_api(db,token,request)
 body=native['body'];candidate=native['secretImportCandidate']
 if candidate['representation']=='PROFILE_JSON_V1':
  candidate={**candidate,'schemaId':SCHEMA['$id']+'#/$defs/'+candidate['profileId'],'schemaDigest':schema_digest(candidate['profileId'])}
 if body['stableName'] in ('KCML_OWNER_API_KEY','PASS'):fail('RESERVED_CREDENTIAL_REQUIRES_SPECIAL_CONTRACT')
 if body.get('targetObjectId') is not None:fail('SECRET_TARGET_AUTHORITY_PRODUCER_REQUIRED')
 # Actual trusted PROFILE DB registry reader is checked separately by producer
 # integration; never turn registry existence into a boolean validity flag.
 if candidate['representation']=='PROFILE_JSON_V1':
  from secret_profile_import import registry_profile
  rows=q(db,"SELECT kcml_secret_v1.read_published_profile_v1("+lit(candidate['type'])+','+lit(candidate['profileId'])+','+b(bytes.fromhex(candidate['schemaDigest'][7:]))+')')
  if len(rows)!=1 or rows[0][0]is None:fail('SECRET_PROFILE_REGISTRY_UNAVAILABLE')
  row=json.loads(rows[0][0]);row['schemaBytes']=bytes.fromhex(row['schemaBytes'])
  # Pins below must be trusted release producer output, not request claims.
  publication=q(db,"SELECT encode(source_ssot_digest,'hex'),encode(review_evidence_digest,'hex') FROM kcml_secret_v1.profile_publication_archive WHERE profile_id="+lit(candidate['profileId'])+' AND schema_digest='+b(bytes.fromhex(candidate['schemaDigest'][7:])))
  if len(publication)!=1:fail('SECRET_PROFILE_REGISTRY_AUTHORITY_UNRESOLVED')
  registry_profile(candidate['profileId'],lambda _:row,'sha256:'+publication[0][0],'sha256:'+publication[0][1])
 key_digest=sha(client_key.encode());op=uid()
 descriptor=canonical({'callerAuthorityKind':'OWNER_FULL','clientKeyDigest':'sha256:'+key_digest.hex(),'operationContractId':'secret.create','operationContractRevision':auth['revision'],'stableBusinessTargetKey':'CREATE_ROOT:secret_record','stableCallerObjectId':auth['owner'],'stableCallerRevisionId':None})
 scope=sha(descriptor)
 # Actual canonical C0 locator arbiter; owner is text, no early owner FK lock.
 locator_insert='INSERT INTO idempotency_locator(locator_id,operation_family,caller_authority_kind,caller_stable_id,business_target_kind,business_target_id,client_key_digest,logical_operation_id,client_request_digest,execution_descriptor_digest,frozen_revision_digest,created_at,terminal_at,retention_until) VALUES('+','.join([lit(uid()),"'SECRET'","'OWNER_FULL'",lit(auth['owner']),"'CREATE_ROOT'","'secret_record'",b(key_digest),lit(op),b(request),b(scope),b(scope),'clock_timestamp()','NULL',lit(retention_until)])+') ON CONFLICT ON CONSTRAINT uq_idempotency_locator_scope DO NOTHING;'
 q(db,locator_insert)
 locator=q(db,"SELECT logical_operation_id,encode(client_request_digest,'hex'),encode(frozen_revision_digest,'hex') FROM idempotency_locator WHERE operation_family='SECRET' AND caller_authority_kind='OWNER_FULL' AND caller_stable_id="+lit(auth['owner'])+" AND business_target_kind='CREATE_ROOT' AND business_target_id='secret_record' AND client_key_digest="+b(key_digest)+' FOR UPDATE')[0]
 claimed=locator[0]
 if claimed!=op:
  if not __import__('hmac').compare_digest(bytes.fromhex(locator[1]),request):fail('IDEMPOTENCY_CONFLICT')
  old=q(db,"SELECT encode(request_digest,'hex'),state FROM domain_idempotency_record WHERE scope_digest="+b(bytes.fromhex(locator[2]))+' AND key_digest='+b(key_digest)+' AND logical_operation_id='+lit(claimed)+' FOR UPDATE')
  if len(old)!=1 or not __import__('hmac').compare_digest(bytes.fromhex(old[0][0]),request):fail('SECRET_RETAINED_COMMAND_UNRESOLVED')
  rows=q(db,"SELECT convert_from(output_receipt_bytes,'UTF8'),secret_id FROM kcml_secret_v1.create_completion WHERE logical_operation_id="+lit(claimed))
  if len(rows)!=1:fail('SECRET_RETAINED_OUTCOME_UNRESOLVED')
  lock_replay_roots_and_validate(db,auth,rows[0][1])
  return {'output':json.loads(rows[0][0]),'logicalOperationId':claimed,'replay':True}
 q(db,'INSERT INTO domain_idempotency_record VALUES('+','.join([b(scope),b(key_digest),b(request),lit(op),"'RESERVED'",'0','NULL'])+') ON CONFLICT(scope_digest,key_digest) DO NOTHING;')
 claimed_idem=q(db,'SELECT logical_operation_id FROM domain_idempotency_record WHERE scope_digest='+b(scope)+' AND key_digest='+b(key_digest)+' FOR UPDATE')
 if len(claimed_idem)!=1 or claimed_idem[0][0]!=op:fail('SECRET_IDEMPOTENCY_SCOPE_CONFLICT')
 if 'locator'in omit:q(db,'DELETE FROM idempotency_locator WHERE logical_operation_id='+lit(op))
 # All C locks are now held. Existing OWNER namespace guard is root10;
 # immutable context/children must wait until new Secret root20 is inserted.
 own=q(db,'SELECT id FROM owner_identity WHERE singleton_key=1 AND id='+lit(auth['owner'])+' FOR UPDATE')
 if len(own)!=1:fail('SECRET_OWNER_IDENTITY_CHANGED')
 ctx=uid();sid=uid();vid=uid();event=uid();snapshot=vid
 now=q(db,"SELECT to_char(clock_timestamp() AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')")[0][0]
 context_sql='INSERT INTO kcml_secret_v1.owner_api_context VALUES('+','.join([lit(ctx),lit(auth['owner']),"'secret.create'","'CREATE_SECRET_CANDIDATE'","'OWNER_API_KEY'",b(request),b(descriptor),b(scope),lit(auth['incarnation']),str(auth['deployment']),lit(auth['revision']),str(auth['credentialVersion']),str(auth['credentialEpoch']),lit(auth['fingerprint']),lit(now)])+')'
 metadata={'ownerId':auth['owner'],'secretId':sid,'secretVersionId':vid,'secretType':candidate['type'],'representation':candidate['representation'],'profileId':candidate.get('profileId'),'schemaId':candidate.get('schemaId'),'schemaDigest':candidate.get('schemaDigest'),'plaintextByteLength':len(candidate['bytes']),'originalImportBytesDigest':'sha256:'+sha(candidate['bytes']).hex(),'canonicalValueDigest':canonical_value_digest(candidate),'trustedContextId':ctx,'logicalOperationId':op}
 envelope=seal(candidate['bytes'],key,key_id,metadata,purpose='SECRET_IMMUTABLE_VERSION')
 output={'secretId':sid,'stableName':body['stableName'],'type':candidate['type'],'versionId':vid,'versionNumber':'1','versionState':'CREATED','recordStatus':'INACTIVE','activeVersionId':None,'stateVersion':'0','createdAt':now};receipt=canonical(output)
 response={'routeId':'route.0386','operationId':'secret.create','logicalOperationId':op,'correlationId':uid(),'status':'SUCCEEDED','terminal':True,'output':output,'error':None,'resultDigest':None,'stateVersion':'0','eventSequence':'1','activationEpoch':None,'idempotencyReplay':False}
 from create_completion_contracts import semantic_result,canonical_digest
 response['resultDigest']=canonical_digest(semantic_result(response));result=bytes.fromhex(response['resultDigest'][7:])
 parts={}
 parts['command']='INSERT INTO domain_command(logical_operation_id,operation_id,owner_id,request_digest,execution_descriptor_bytes,execution_descriptor_digest,state,terminal,state_version,result_digest,platform_incarnation_id,application_deployment_epoch,created_at,updated_at,command_id,operation_contract_revision,caller_channel,execution_context_id,target_aggregate_kind,target_aggregate_id,canonical_arguments_snapshot_id,scope_digest,client_key_digest,correlation_id,accepted_at,terminal_at) VALUES('+','.join([lit(op),"'secret.create'",lit(auth['owner']),b(request),b(descriptor),b(sha(descriptor)),"'SUCCEEDED'",'true','1',b(result),lit(auth['incarnation']),str(auth['deployment']),lit(now),lit(now),lit(uid()),lit(auth['revision']),"'OWNER_API_KEY'",lit(ctx),"'SECRET_RECORD'",lit(sid),lit(snapshot),b(sha(descriptor)),b(key_digest),lit(response['correlationId']),lit(now),lit(now)])+');'
 optional=lambda name:'NULL'if body.get(name)is None else lit(body[name])
 tags='ARRAY['+','.join(lit(x)for x in body.get('tags',[]))+']::text[]'
 parts['root']='INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,description,secret_type,purpose_kind,target_object_id,status,state_version,secret_activation_epoch,tags,group_name,url,username,notes,expires_at,created_at,updated_at) VALUES('+','.join([lit(sid),lit(body['stableName']),lit(body['displayName']),optional('description'),lit(body['type']),optional('purposeKind'),optional('targetObjectId'),lit(root_status),'0','0',tags,optional('group'),optional('url'),optional('username'),optional('notes'),optional('expiration'),lit(now),lit(now)])+');'
 parts['version']='INSERT INTO kcml_secret_v1.secret_version(id,secret_id,version_number,secret_type,value_representation,profile_id,value_schema_id,value_schema_digest,payload_format,plaintext_byte_length,ciphertext,nonce,algorithm,key_id,fingerprint,original_import_bytes_digest,canonical_value_digest,lifecycle,created_at,creator_context_id) VALUES('+','.join([lit(vid),lit(sid),'1',lit(candidate['type']),lit(candidate['representation']),*['NULL' if metadata[k]is None else (b(bytes.fromhex(metadata[k][7:])) if k=='schemaDigest' else lit(metadata[k])) for k in ('profileId','schemaId','schemaDigest')],"'EXACT_SECRET_BYTES_V1'",str(len(candidate['bytes'])),b(envelope['ciphertext']),b(envelope['nonce']),lit(envelope['algorithm']),lit(key_id),lit(fingerprint(candidate['bytes'])),b(sha(candidate['bytes'])),b(bytes.fromhex(metadata['canonicalValueDigest'][7:])),"'CREATED'",lit(now),lit(ctx)])+');'
 parts['event']='INSERT INTO domain_event VALUES('+','.join([lit(event),lit(sid),"'SECRET_RECORD'",lit(op),'1',"'OPERATION_TERMINAL'","'urn:kcml:r9:route:route.0386:event'",b(sha(canonical(__import__('create_completion_contracts')._rows(hashlib.sha256(__import__('ssot_sources').SSOT.read_bytes()).hexdigest())['secret.create']['eventSchema']))),b(receipt),b(sha(receipt)),lit(response['correlationId']),'NULL',lit(now)])+');'
 # E20 root first; all FK parents are held before H15 auth-context,
 # H20 version, H35 command, H36 domain event, H37 completion, H910 outbox.
 for root in sorted({auth['credentialSecretId'],sid}):
  if root==sid:
   if 'root'not in omit:q(db,parts['root'])
  else:
   locked=q(db,'SELECT id FROM kcml_secret_v1.secret_record WHERE id='+lit(root)+' FOR UPDATE')
   if len(locked)!=1:fail('OWNER_API_CREDENTIAL_ROOT_UNAVAILABLE')
 validate_locked_credential_root(db,auth)
 q(db,context_sql)
 for name in ['version','command','event']:
  if name not in omit:q(db,parts[name])
 meta=canonical({k:v for k,v in body.items()if k!='value'})
 if 'completion'not in omit:q(db,'INSERT INTO kcml_secret_v1.create_completion VALUES('+','.join([lit(op),lit(ctx),lit(sid),lit(vid),b(meta),b(sha(meta)),b(receipt),b(sha(receipt)),b(canonical(semantic_result(response))),b(result),lit(event),lit(now)])+');')
 if 'idempotency'not in omit:
  updated=q(db,"UPDATE domain_idempotency_record SET state='SUCCEEDED',state_version=state_version+1,canonical_outcome_digest="+b(result)+' WHERE scope_digest='+b(scope)+' AND key_digest='+b(key_digest)+" AND state='RESERVED' AND state_version=0 RETURNING logical_operation_id")
  if len(updated)!=1:fail('SECRET_IDEMPOTENCY_FINAL_CAS_CONFLICT')
 if 'locator'not in omit:q(db,'UPDATE idempotency_locator SET terminal_at='+lit(now)+' WHERE logical_operation_id='+lit(op))

 if 'outbox'not in omit:q(db,'INSERT INTO transactional_outbox(id,event_id,logical_operation_id,aggregate_id,purpose,consumer_scope,available_at,state,payload_digest) VALUES('+','.join([lit(uid()),lit(event),lit(op),lit(sid),"'DOMAIN_EVENT'","'CANONICAL_SECRET_CONSUMERS'",lit(now),"'READY'",b(sha(receipt))])+');')
 # Class I is LAST. After this point only new audit and audit-archive appends
 # plus audit-head update are legal; no A-H mutation/lock remains.
 if 'audit'not in omit:
  head=q(db,"SELECT last_sequence,encode(last_hash,'hex') FROM audit_head WHERE singleton_key=1 FOR UPDATE")[0]
  sequence=int(head[0])+1;previous=bytes.fromhex(head[1]);audit=uid()
  auditbytes=canonical({'logicalOperationId':op,'eventId':event,'objectId':sid,'actorId':auth['owner'],'beforeDigest':None,'afterDigest':'sha256:'+sha(receipt).hex(),'correlationId':response['correlationId'],'causationId':None,'traceId':response['correlationId'],'occurredAt':now,'chainSequence':str(sequence),'previousHash':'sha256:'+previous.hex()})
  q(db,'INSERT INTO audit_event VALUES('+','.join([lit(audit),str(sequence),b(previous),'kcml_audit_hash_v1(1,'+b(previous)+','+str(sequence)+','+b(auditbytes)+')','1',lit(op),lit(event),b(auditbytes),'false'])+'); UPDATE audit_head SET last_sequence='+str(sequence)+',last_hash=kcml_audit_hash_v1(1,'+b(previous)+','+str(sequence)+','+b(auditbytes)+'),state_version=state_version+1 WHERE singleton_key=1;')
 return {'output':output,'logicalOperationId':op,'response':response,'replay':False,'metadata':metadata,'envelope':envelope}
