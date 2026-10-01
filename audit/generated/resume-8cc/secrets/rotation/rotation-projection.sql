-- Bounded mutation/atomic-outcome fixture proposal, NOT a complete rotation
-- policy: effective dependent invalidation inventory and real key source OPEN.
CREATE TABLE kcml_secret_v1.rotation_projection_completion(
 logical_operation_id uuid PRIMARY KEY REFERENCES domain_command(logical_operation_id),
 context_id uuid NOT NULL REFERENCES kcml_secret_v1.owner_api_context(id),
 secret_id uuid NOT NULL,version_id uuid NOT NULL,event_id uuid NOT NULL UNIQUE,
 output_receipt_bytes bytea NOT NULL,semantic_result_bytes bytea NOT NULL,
 result_digest bytea NOT NULL CHECK(result_digest=sha256(semantic_result_bytes)),
 previous_credential_state bigint NOT NULL,previous_secret_state bigint NOT NULL,
 previous_credential_version bigint NOT NULL,previous_credential_epoch bigint NOT NULL,
 previous_secret_epoch bigint NOT NULL,
 FOREIGN KEY(secret_id,version_id)REFERENCES kcml_secret_v1.secret_version(secret_id,id),
 FOREIGN KEY(event_id,logical_operation_id,secret_id)REFERENCES domain_event(id,logical_operation_id,aggregate_id)DEFERRABLE INITIALLY DEFERRED
);
CREATE TRIGGER owner_rotation_completion_immutable BEFORE UPDATE OR DELETE ON kcml_secret_v1.rotation_projection_completion
 FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.secret_profile_immutable();
CREATE FUNCTION kcml_secret_v1.rotation_projection_closure_v1()RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE x kcml_secret_v1.rotation_projection_completion;c owner_api_credential;r kcml_secret_v1.secret_record;
 d domain_command;ctx kcml_secret_v1.owner_api_context;e domain_event;a audit_event;v kcml_secret_v1.secret_version;
 output jsonb;expected jsonb;
BEGIN
 SELECT * INTO d FROM domain_command WHERE logical_operation_id=NEW.logical_operation_id;
 IF d.operation_id IS DISTINCT FROM 'ownerApiKey.rotate'THEN RETURN NULL;END IF;
 SELECT * INTO x FROM kcml_secret_v1.rotation_projection_completion WHERE logical_operation_id=d.logical_operation_id;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_ROTATION_COMPLETION_REQUIRED';END IF;
 SELECT * INTO STRICT ctx FROM kcml_secret_v1.owner_api_context WHERE id=x.context_id;
 SELECT * INTO STRICT c FROM owner_api_credential WHERE singleton_key=1;
 SELECT * INTO STRICT r FROM kcml_secret_v1.secret_record WHERE id=x.secret_id;
 SELECT * INTO STRICT v FROM kcml_secret_v1.secret_version WHERE id=x.version_id;
 SELECT * INTO e FROM domain_event WHERE id=x.event_id;
 SELECT * INTO a FROM audit_event WHERE domain_event_id=x.event_id;
 output=convert_from(x.output_receipt_bytes,'UTF8')::jsonb;
 expected=jsonb_build_object('routeId','route.0024','operationId','ownerApiKey.rotate','logicalOperationId',d.logical_operation_id::text,'correlationId',d.correlation_id::text,'status','SUCCEEDED','terminal',true,'output',output,'error',NULL,'stateVersion',c.state_version::text,'eventSequence',r.secret_activation_epoch::text,'activationEpoch',r.secret_activation_epoch::text);
 IF x.semantic_result_bytes IS DISTINCT FROM convert_to(kcml_crypto_compact_sorted_json_v1(expected),'UTF8')THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_ROTATION_SEMANTIC_RESULT_MISMATCH';END IF;
 IF c.secret_id IS DISTINCT FROM x.secret_id OR c.secret_version_id IS DISTINCT FROM x.version_id
 OR c.state_version IS DISTINCT FROM x.previous_credential_state+1 OR c.credential_version IS DISTINCT FROM x.previous_credential_version+1
 OR c.credential_activation_epoch IS DISTINCT FROM x.previous_credential_epoch+1
 OR c.last_rotate_logical_operation_id IS DISTINCT FROM d.logical_operation_id OR c.last_rotate_outcome_digest IS DISTINCT FROM x.result_digest
 OR r.state_version IS DISTINCT FROM x.previous_secret_state+1 OR r.secret_activation_epoch IS DISTINCT FROM x.previous_secret_epoch+1
 OR kcml_secret_v1.record_status_v1(r.id)IS DISTINCT FROM'ACTIVE'OR r.active_version_id IS DISTINCT FROM v.id
 OR v.secret_id IS DISTINCT FROM r.id OR v.lifecycle IS DISTINCT FROM'ACTIVE'OR v.secret_type IS DISTINCT FROM'API_KEY'
 OR v.fingerprint IS DISTINCT FROM c.fingerprint OR r.stable_name IS DISTINCT FROM'KCML_OWNER_API_KEY'
 OR ctx.operation_id IS DISTINCT FROM'ownerApiKey.rotate'OR ctx.api_credential_version IS DISTINCT FROM x.previous_credential_version
 OR ctx.api_credential_activation_epoch IS DISTINCT FROM x.previous_credential_epoch
 OR d.execution_context_id IS DISTINCT FROM ctx.id OR d.result_digest IS DISTINCT FROM x.result_digest
 OR d.target_aggregate_id IS DISTINCT FROM r.id OR d.canonical_arguments_snapshot_id IS DISTINCT FROM v.id
 OR d.request_digest IS DISTINCT FROM ctx.request_digest OR d.execution_descriptor_digest IS DISTINCT FROM ctx.execution_descriptor_digest
 OR output IS DISTINCT FROM jsonb_build_object('secretId',r.id::text,'activeVersionId',v.id::text,'versionNumber',v.version_number::text,'recordStatus','ACTIVE','secretStateVersion',r.state_version::text,'secretActivationEpoch',r.secret_activation_epoch::text,'credentialVersion',c.credential_version::text,'credentialStateVersion',c.state_version::text,'credentialActivationEpoch',c.credential_activation_epoch::text,'fingerprint',c.fingerprint,'rotatedAt',to_char(c.rotated_at AT TIME ZONE'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))
 OR e.id IS NULL OR e.logical_operation_id IS DISTINCT FROM d.logical_operation_id OR e.aggregate_id IS DISTINCT FROM r.id
 OR e.aggregate_sequence IS DISTINCT FROM r.secret_activation_epoch OR e.payload_bytes IS DISTINCT FROM x.output_receipt_bytes OR e.payload_digest IS DISTINCT FROM sha256(x.output_receipt_bytes)
 OR a.id IS NULL OR a.logical_operation_id IS DISTINCT FROM d.logical_operation_id
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'eventId')IS DISTINCT FROM e.id::text
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'objectId')IS DISTINCT FROM r.id::text
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'actorId')IS DISTINCT FROM ctx.owner_id::text
 OR NOT EXISTS(SELECT 1 FROM transactional_outbox o WHERE o.event_id=e.id AND o.logical_operation_id=d.logical_operation_id AND o.aggregate_id=r.id AND o.payload_digest=e.payload_digest AND o.purpose='DOMAIN_EVENT')
 OR NOT EXISTS(SELECT 1 FROM domain_idempotency_record i WHERE i.logical_operation_id=d.logical_operation_id AND i.state='SUCCEEDED'AND i.canonical_outcome_digest=x.result_digest AND i.request_digest=d.request_digest AND i.scope_digest=d.scope_digest AND i.key_digest=d.client_key_digest)
 OR NOT EXISTS(SELECT 1 FROM idempotency_locator l WHERE l.logical_operation_id=d.logical_operation_id AND l.client_request_digest=d.request_digest AND l.execution_descriptor_digest=d.execution_descriptor_digest AND l.frozen_revision_digest=d.scope_digest AND l.client_key_digest=d.client_key_digest)
 THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_ROTATION_PROJECTION_ATOMIC_CLOSURE_INVALID';END IF;
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER owner_rotation_completion_closure AFTER INSERT ON kcml_secret_v1.rotation_projection_completion
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.rotation_projection_closure_v1();
CREATE CONSTRAINT TRIGGER owner_rotation_command_closure AFTER INSERT ON domain_command
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.rotation_projection_closure_v1();
REVOKE ALL ON kcml_secret_v1.rotation_projection_completion FROM PUBLIC;
