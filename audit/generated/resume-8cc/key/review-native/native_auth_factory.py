"""Actual native HTTP/auth/AES foundation factory; no executed historical SQL.
Fixture credentials/key are isolated random data. Header ceiling is fixture config,
not an assertion that GENERATION.AUTH.TRANSPORT's trusted producer is complete.
"""
from pathlib import Path
import sys,json,hashlib,secrets,copy,struct
ROOT=Path('/workspace/kajovocmlng')
for p in [ROOT/'scripts',ROOT/'audit/generated/resume-34d/auth-crypto',ROOT/'audit/generated/resume-d362/persistence']:sys.path.insert(0,str(p))
from ssot_sources import resource_index,SSOT
from generation_auth_crypto import *
from generation_auth_acceptance import authenticate_owner_api
from generation_descriptor_registry import pin,descriptor as descriptor_bytes
from context_fixture_exports import common,call
from libpq_fixture import DB,lit
from create_operation_contracts import decode_http,validate_body,strict_json
from verify_create_completion import witnesses,canonical_bytes
from create_completion_contracts import semantic_result,canonical_digest
OWNER='00000000-0000-4000-8000-000000009005'
def uid(n):return '00000000-0000-4000-8000-'+str(n).zfill(12)
def b(v):return "decode('"+v.hex()+"','hex')"
class Factory:
 def __init__(self,database):
  self.database=database;self.source=SSOT.read_bytes();self.resources=resource_index();self.pinned=pin();self.owner=OWNER;self.token=secrets.token_urlsafe(32).encode('ascii');self.key=secrets.token_bytes(32);self.keyid='isolated-fixture-not-systemd';self.ceiling=4096
  admin=DB('postgres')
  if not admin.query('SELECT 1 FROM pg_database WHERE datname='+lit(database)):admin.query('CREATE DATABASE '+database)
  admin.close();self.db=DB(database);self.db.query('DROP SCHEMA public CASCADE;CREATE SCHEMA public;DROP SCHEMA IF EXISTS kcml_retry_v1 CASCADE;')
  for name in ['database/generation-create-foundations.sql','database/generation-create-authentication.sql','database/generation-create-preroot.sql','database/canonical-crypto-registry.sql','database/generation-protected-registry-link.sql','database/generation-create-read.sql','database/generation-locator-lock.sql']:self.db.query(self.resources[name]['raw'].decode())
  self.db.query(common(OWNER,OWNER,1)+f"INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,state_version,credential_activation_epoch,created_at)VALUES(1,'{uid(9901)}','{uid(9902)}',{lit(verifier_hash(self.token))},{lit(fingerprint(self.token))},1,0,1,clock_timestamp());")
  self.db.query("INSERT INTO canonical_authenticated_crypto_profile VALUES('KCML_PROTECTED_INPUT_AES256_GCM_V1',"+b(profile_bytes())+','+b(profile_digest())+",'AES_256_GCM');")
  self.db.query('INSERT INTO canonical_master_key_generation VALUES('+lit(self.keyid)+','+b(sha(self.key))+",1,'kcml-master-key','isolated-fixture.service',"+b(profile_digest())+',clock_timestamp());')
 def native(self,body,key):
  row=next(r for r in json.loads(self.resources['contracts/payload-contracts.json']['raw'])['records']if r['operationId']=='generation.job.create')
  raw=canonical_bytes(body);headers=[('Content-Type',b'application/json'),('Idempotency-Key',key.encode()),('Authorization',b'Bearer '+self.token)]
  token=extract_owner_api_token(headers,self.ceiling)
  # The public-gateway responsibility: credential header is never internal native input.
  forwarded=[(k,v.decode('ascii'))for k,v in headers if k.lower()!='authorization']
  native=decode_http('generation.job.create','POST',row['path'],[],forwarded,raw)
  return row,native,raw,token
 def build(self,body,job,op,snapshot,sequence=1,previous_hash=bytes(32),key='joined-native-key'):
  row,native,plain,token=self.native(body,key);keydigest=sha(key.encode());requestdigest=bytes.fromhex(native['requestDigest'][7:]);descriptor=descriptor_bytes(OWNER,'sha256:'+keydigest.hex(),self.pinned)
  accepted=authenticate_owner_api(self.db,token,requestdigest,self.ceiling,descriptor)
  self.db.query(call(OWNER,accepted['authenticationAcceptanceId'],requestdigest.hex(),'sha256:'+keydigest.hex()))
  context=self.db.query('SELECT id FROM generation_create_trusted_context WHERE authentication_acceptance_id='+lit(accepted['authenticationAcceptanceId']))[0][0]
  hook=getattr(self,'acceptance_hook',None)
  if hook:hook(context,op)
  self.db.query('SELECT kcml_generation_lock_retained_locator_v1('+lit(context)+')')
  response,event=witnesses('generation.job.create',row);response['logicalOperationId']=op;response['correlationId']=op;response['output'].update(jobId=job,kind=body['kind'],initialRequestDigest='sha256:'+sha(plain).hex());response['resultDigest']=canonical_digest(semantic_result(response));event['payload']=copy.deepcopy(response['output']);event['payloadDigest']=canonical_digest(event['payload'])
  eventid=uid(int(op[-12:])+10000);outid=uid(int(op[-12:])+20000);auditid=uid(int(op[-12:])+30000);locatorid=uid(int(op[-12:])+40000)
  event.update(logicalOperationId=op,correlationId=op,aggregateId=job,immutableEventId=eventid)
  from jsonschema import Draft202012Validator,FormatChecker
  Draft202012Validator(row['responseSchema'],format_checker=FormatChecker()).validate(response)
  Draft202012Validator(row['eventSchema'],format_checker=FormatChecker()).validate(event)
  meta={'ownerId':OWNER,'jobId':job,'snapshotId':snapshot,'logicalOperationId':op,'requestSchemaId':'urn:kcml:r9:semantic:route.0215:body','requestSchemaDigest':'sha256:'+self.pinned['domainSchemaDigest'].hex(),'contentDigest':'sha256:'+sha(plain).hex(),'trustedContextId':context,'platformIncarnationId':OWNER,'applicationDeploymentEpoch':1,'executionDescriptorDigest':'sha256:'+sha(descriptor).hex(),'initiatingAccessChannel':'OWNER_API_KEY'}
  enc=seal(plain,self.key,self.keyid,meta);receipt=canonical_bytes(response['output']);sem=canonical_bytes(semantic_result(response));pd=sha(receipt);rd=sha(sem);dd=sha(descriptor);scope=dd
  auditbody={'chainSequence':str(sequence),'previousHash':'sha256:'+previous_hash.hex(),'eventId':eventid,'logicalOperationId':op,'actorId':OWNER,'objectId':job,'beforeDigest':None,'afterDigest':'sha256:'+pd.hex(),'correlationId':op,'causationId':None,'traceId':'isolated-native-retry','occurredAt':event['occurredAt']};abytes=canonical_bytes(auditbody);ah=sha(b'KCML-AUDIT-CHAIN'+struct.pack('>I',1)+previous_hash+struct.pack('>q',sequence)+struct.pack('>q',len(abytes))+abytes)
  parts={
   'command':f"INSERT INTO domain_command VALUES('{op}','generation.job.create','{OWNER}',{b(requestdigest)},{b(descriptor)},{b(dd)},'SUCCEEDED',true,1,{b(rd)},'{OWNER}',1,clock_timestamp(),clock_timestamp(),'{op}',{lit(self.pinned['operationRevision'])},'OWNER_API_KEY','{context}','GENERATION_JOB','{job}','{snapshot}',{b(scope)},{b(keydigest)},NULL,NULL,NULL,NULL,NULL,NULL,'{op}',NULL,clock_timestamp(),clock_timestamp(),NULL);",
   'locator':f"INSERT INTO idempotency_locator VALUES('{locatorid}','GENERATION','OWNER_FULL','{OWNER}','CREATE_ROOT','generation_job',{b(keydigest)},'{op}',{b(requestdigest)},{b(dd)},{b(scope)},clock_timestamp(),clock_timestamp(),clock_timestamp()+interval '1 day');",
   'idempotency':f"INSERT INTO domain_idempotency_record VALUES({b(scope)},{b(keydigest)},{b(requestdigest)},'{op}','RESERVED',0,NULL);",
   'event':f"INSERT INTO domain_event VALUES('{eventid}','{job}','GENERATION_JOB','{op}',1,'generation.job.created',{lit(row['eventSchema']['$id'])},{b(sha(canonical_bytes(row['eventSchema'])))},{b(receipt)},{b(pd)},'{op}',NULL,clock_timestamp());",
   'outbox':f"INSERT INTO transactional_outbox(id,event_id,logical_operation_id,aggregate_id,purpose,consumer_scope,available_at,state,state_version,attempt_count,payload_digest,delivery_fence,lease_owner_id,lease_expires_at)VALUES('{outid}','{eventid}','{op}','{job}','DOMAIN_EVENT','owner-generation-sse',clock_timestamp(),'READY',0,0,{b(pd)},0,NULL,NULL);",
   'completion':f"INSERT INTO generation_job_create_completion VALUES('{op}','{job}',{b(sem)},{b(rd)},{b(receipt)},{b(pd)},'{eventid}',1,1,clock_timestamp());",
   'finalize-idempotency':f"UPDATE domain_idempotency_record SET state='EXECUTING',state_version=1 WHERE logical_operation_id='{op}' AND state='RESERVED';UPDATE domain_idempotency_record SET state='SUCCEEDED',state_version=2,canonical_outcome_digest={b(rd)} WHERE logical_operation_id='{op}' AND state='EXECUTING';"
  }
  parts['typed-binding']=f"INSERT INTO generation_create_command_binding VALUES('{op}','{context}','{snapshot}');"
  parent=body.get('parentJobId');parentcol=',parent_job_id' if parent else '';parentval=','+lit(parent)if parent else ''
  parts['root']=f"INSERT INTO generation_job(id,owner_id,initiating_access_channel,initiating_execution_context_id,kind,target_kind,state,state_version,aggregate_event_sequence,initial_request_snapshot_id,initial_request_digest,platform_incarnation_id,application_deployment_epoch,created_at,client_request_id,latest_command_logical_operation_id{parentcol})VALUES('{job}','{OWNER}','OWNER_API_KEY','{context}',{lit(body['kind'])},{lit(body.get('targetKind','PLATFORM_COMPONENT'))},'DISCUSSING',1,1,'{snapshot}',{b(sha(plain))},'{OWNER}',1,{lit(response['output']['createdAt'])},{lit(key)},'{op}'{parentval});"
  parts['snapshot']=f"INSERT INTO generation_job_initial_request_snapshot VALUES('{job}','{snapshot}','{op}',{lit(meta['requestSchemaId'])},{b(self.pinned['domainSchemaDigest'])},{b(sha(plain))},{b(enc['ciphertext'])},{b(enc['nonce'])},{lit(enc['algorithm'])},{lit(self.keyid)},{b(enc['cryptoProfileDigest'])},clock_timestamp());"
  parts['audit']=f"SELECT * FROM audit_head WHERE singleton_key=1 FOR UPDATE;INSERT INTO audit_event VALUES('{auditid}',{sequence},{b(previous_hash)},{b(ah)},1,'{op}','{eventid}',{b(abytes)},false);UPDATE audit_head SET last_sequence={sequence},last_hash={b(ah)},state_version={sequence} WHERE singleton_key=1;"
  metadata=aad(meta,key_id=self.keyid)
  parts['nonce']= 'INSERT INTO canonical_protected_nonce_reservation VALUES('+','.join([lit(self.keyid),b(enc['nonce']),"'GENERATION_INITIAL_REQUEST'",lit(snapshot),lit(op),b(metadata),b(sha(metadata)),b(sha(enc['ciphertext']))])+');'
  parts={k:parts[k]for k in ['locator','idempotency','command','typed-binding','root','snapshot','nonce','event','outbox','completion','finalize-idempotency','audit']}
  return {'parts':parts,'meta':meta,'plain':plain,'envelope':enc,'native':native,'auditHash':ah,'response':response,'context':context,'descriptor':descriptor}
 def insert(self,built):self.db.query(''.join(built['parts'].values()))
