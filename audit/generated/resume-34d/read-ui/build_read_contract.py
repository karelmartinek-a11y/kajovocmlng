import sys,json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
from create_completion_contracts import UID,DIGEST,COUNTER,TIME,obj,nullable
from follow_up_contracts import STATES
OUT=Path(__file__).parent
rs=resource_index();sql=rs['database/generation-create-foundations.sql']['raw'].decode()
block=sql.split('CREATE TABLE generation_job (',1)[1].split('\n);',1)[0]
def camel(s):
 a=s.split('_');return a[0]+''.join(x.title() for x in a[1:])
props={};maps=[];select=[]
for line in block.splitlines():
 m=re.match(r'  ([a-z_]+) (uuid|text|bigint|bytea|timestamptz) (.*)',line)
 if not m:continue
 col,typ,rest=m.groups();name={'id':'jobId','aggregate_event_sequence':'eventSequence'}.get(col,camel(col))
 shape={'uuid':UID,'text':{'type':'string'},'bigint':COUNTER,'bytea':DIGEST,'timestamptz':TIME}[typ]
 if col=='kind':shape={'enum':['CREATE','UPDATE','FOLLOW_UP','RETRY','REPAIR']}
 if col=='state':shape={'enum':STATES}
 if col=='target_kind':
  from create_operation_contracts import TARGETS
  shape={'enum':TARGETS}
 null='NOT NULL'not in rest and'PRIMARY KEY'not in rest
 props[name]=nullable(shape)if null else shape
 expr="'sha256:'||encode(g."+col+",'hex')"if typ=='bytea'else 'g.'+col+'::text'if typ=='bigint'else 'g.'+col
 select.append("'"+name+"',"+expr)
 maps.append({'wireField':name,'physicalColumn':'generation_job.'+col,'authority':'SSOT §25.11; database/generation-create-foundations.sql generation_job.'+col,'nullable':null,'visibility':'SERVER_REPOSITORY_ONLY'if any(x in col for x in ['execution_context','lease','fencing','incarnation','epoch','heartbeat'])else'CANONICAL_ROOT_METADATA'})
contract={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:internal:generation-root-read:1',**obj(props)}
(OUT/'generation-root-storage-read.schema.json').write_text(json.dumps(contract,indent=2)+'\n')
(OUT/'generation-read-field-mapping.json').write_text(json.dumps({'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'canonicalFoundationSha256':rs['database/generation-create-foundations.sql']['sha256'],'fields':maps,'unresolvedOwnDictionaries':['currentPhase','errorCode'],'notPublicReplacement':True},indent=2)+'\n')
query='''-- Server-repository-only query, not an OWNER API or authorization constructor.
-- p_owner MUST come from authenticated service context, never request JSON.
-- Statement snapshot joins frozen CREATE identity and current root metadata.
-- No ciphertext, nonce, credential, plaintext, context descriptor or lease data
-- is exposed by any public wire projection. The root member is INTERNAL ONLY.
CREATE FUNCTION kcml_generation_create_read_storage_v1(p_owner uuid,p_job uuid)
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog,public AS $$
SELECT jsonb_build_object('root',jsonb_build_object(
'''+',\n'.join(select)+'''),
'creation',jsonb_build_object('logicalOperationId',c.logical_operation_id,
 'resultDigest','sha256:'||encode(c.result_digest,'hex'),
 'semanticResponseHex',encode(c.semantic_response_bytes,'hex'),
 'receiptHex',encode(c.output_receipt_bytes,'hex'),
 'receiptDigest','sha256:'||encode(c.output_receipt_digest,'hex'),
 'eventId',c.immutable_event_id,'stateVersion',c.committed_state_version::text,
 'eventSequence',c.aggregate_event_sequence::text),
'initialRequestRef',jsonb_build_object('snapshotId',s.snapshot_id,
 'jobId',s.job_id,'logicalOperationId',s.logical_operation_id,
 'schemaId',s.request_schema_id,'schemaDigest','sha256:'||encode(s.request_schema_digest,'hex'),
 'contentDigest','sha256:'||encode(s.content_digest,'hex')),
'event',jsonb_build_object('id',e.id,'logicalOperationId',e.logical_operation_id,
 'aggregateId',e.aggregate_id,'sequence',e.aggregate_sequence::text,
 'schemaId',e.event_schema_id,'schemaDigest','sha256:'||encode(e.event_schema_digest,'hex'),
 'payloadHex',encode(e.payload_bytes,'hex'),'payloadDigest','sha256:'||encode(e.payload_digest,'hex')),
'links',jsonb_build_object('outboxId',o.id,'auditId',a.id,'auditSequence',a.chain_sequence::text,
 'locatorId',l.locator_id,'logicalOperationId',d.logical_operation_id,
 'idempotencyState',i.state,'canonicalOutcomeDigest','sha256:'||encode(i.canonical_outcome_digest,'hex')))
FROM public.generation_job g
JOIN public.generation_job_initial_request_snapshot s
 ON(s.job_id,s.snapshot_id,s.content_digest)=(g.id,g.initial_request_snapshot_id,g.initial_request_digest)
JOIN public.generation_job_create_completion c ON c.job_id=g.id AND c.logical_operation_id=s.logical_operation_id
JOIN public.domain_command d ON d.logical_operation_id=c.logical_operation_id
 AND d.operation_id='generation.job.create' AND d.owner_id=g.owner_id
JOIN public.generation_create_command_binding b ON b.logical_operation_id=d.logical_operation_id
 AND b.argument_snapshot_id=s.snapshot_id AND b.trusted_context_id=g.initiating_execution_context_id
JOIN public.domain_event e ON(e.id,e.logical_operation_id,e.aggregate_id)=(c.immutable_event_id,c.logical_operation_id,g.id)
 AND e.event_type='generation.job.created' AND e.aggregate_sequence=c.aggregate_event_sequence
 AND e.payload_bytes=c.output_receipt_bytes AND e.payload_digest=c.output_receipt_digest
JOIN public.transactional_outbox o ON(o.event_id,o.logical_operation_id,o.aggregate_id)=(e.id,d.logical_operation_id,g.id)
 AND o.purpose='DOMAIN_EVENT' AND o.consumer_scope='owner-generation-sse' AND o.payload_digest=e.payload_digest
JOIN public.audit_event a ON a.domain_event_id=e.id AND a.logical_operation_id=d.logical_operation_id
JOIN public.idempotency_locator l ON l.logical_operation_id=d.logical_operation_id AND l.caller_stable_id=g.owner_id::text
 AND l.operation_family='GENERATION' AND l.caller_authority_kind='OWNER_FULL'
 AND l.client_request_digest=d.request_digest AND l.client_key_digest=d.client_key_digest
 AND l.execution_descriptor_digest=d.execution_descriptor_digest AND l.frozen_revision_digest=d.scope_digest
JOIN public.domain_idempotency_record i ON i.logical_operation_id=d.logical_operation_id
 AND i.scope_digest=d.scope_digest AND i.key_digest=d.client_key_digest AND i.request_digest=d.request_digest
 AND i.canonical_outcome_digest=c.result_digest
WHERE g.id=p_job AND g.owner_id=p_owner;
$$;
REVOKE ALL ON FUNCTION kcml_generation_create_read_storage_v1(uuid,uuid) FROM PUBLIC;
-- No broad role or generated-handler grant. Installation must explicitly bind
-- this query to the existing canonical service repository and authenticated
-- read context. Supplying p_owner is NOT by itself authentication evidence.
'''
(OUT/'generation-create-read-storage.sql').write_text(query)
print(len(props),'physical canonical root columns mapped')
