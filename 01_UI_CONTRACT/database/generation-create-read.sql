-- Server-repository-only query, not an OWNER API or authorization constructor.
-- p_owner MUST come from authenticated service context, never request JSON.
-- Statement snapshot joins frozen CREATE identity and current root metadata.
-- No ciphertext, nonce, credential, plaintext, context descriptor or lease data
-- is exposed by any public wire projection. The root member is INTERNAL ONLY.
CREATE FUNCTION kcml_generation_create_read_storage_v1(p_owner uuid,p_job uuid)
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog,public AS $$
SELECT jsonb_build_object('root',jsonb_build_object(
'jobId',g.id,
'ownerId',g.owner_id,
'initiatingAccessChannel',g.initiating_access_channel,
'initiatingExecutionContextId',g.initiating_execution_context_id,
'kind',g.kind,
'targetKind',g.target_kind,
'targetObjectId',g.target_object_id,
'state',g.state,
'currentPhase',g.current_phase,
'stateVersion',g.state_version::text,
'eventSequence',g.aggregate_event_sequence::text,
'initialRequestSnapshotId',g.initial_request_snapshot_id,
'initialRequestDigest','sha256:'||encode(g.initial_request_digest,'hex'),
'parentJobId',g.parent_job_id,
'currentSpecRevisionId',g.current_spec_revision_id,
'approvedSpecRevisionId',g.approved_spec_revision_id,
'approvedSpecificationDigest','sha256:'||encode(g.approved_specification_digest,'hex'),
'executionAuthorityId',g.execution_authority_id,
'currentCapabilitySnapshotId',g.current_capability_snapshot_id,
'currentPlanId',g.current_plan_id,
'activePhaseRunId',g.active_phase_run_id,
'latestCheckpointId',g.latest_checkpoint_id,
'previousReleaseId',g.previous_release_id,
'candidateReleaseId',g.candidate_release_id,
'activationSetId',g.activation_set_id,
'cancellationVersion',g.cancellation_version::text,
'blockerId',g.blocker_id,
'errorCode',g.error_code,
'coordinatorLeaseOwnerId',g.coordinator_lease_owner_id,
'coordinatorFencingToken',g.coordinator_fencing_token::text,
'coordinatorLeaseExpiresAt',g.coordinator_lease_expires_at,
'coordinatorHeartbeatAt',g.coordinator_heartbeat_at,
'platformIncarnationId',g.platform_incarnation_id,
'applicationDeploymentEpoch',g.application_deployment_epoch::text,
'createdAt',g.created_at,
'startedAt',g.started_at,
'completedAt',g.completed_at,
'clientRequestId',g.client_request_id,
'latestCommandLogicalOperationId',g.latest_command_logical_operation_id),
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
