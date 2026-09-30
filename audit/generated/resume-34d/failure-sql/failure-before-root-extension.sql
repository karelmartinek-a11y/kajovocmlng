-- Bounded technical extension of §§12.48,49.3–5,49.25,51.12,51.25.
-- Apply AFTER exact canonical generation-create-foundations.sql.
-- Pre-admission parse/auth/admission errors NEVER enter these tables.
CREATE TABLE generation_create_preroot_snapshot (
 snapshot_id uuid PRIMARY KEY,
 logical_operation_id uuid NOT NULL UNIQUE REFERENCES domain_command(logical_operation_id) DEFERRABLE INITIALLY DEFERRED,
 prospective_job_id uuid NOT NULL,
 trusted_context_id uuid NOT NULL REFERENCES generation_create_trusted_context(id),
 request_schema_id text NOT NULL CHECK(request_schema_id='urn:kcml:r9:semantic:route.0215:body'),
 request_schema_digest bytea NOT NULL CHECK(octet_length(request_schema_digest)=32),
 content_digest bytea NOT NULL CHECK(octet_length(content_digest)=32),
 ciphertext bytea NOT NULL CHECK(octet_length(ciphertext)>0),nonce bytea NOT NULL CHECK(octet_length(nonce)>0),
 algorithm text NOT NULL,key_id text NOT NULL,crypto_profile_digest bytea NOT NULL CHECK(octet_length(crypto_profile_digest)=32),
 created_at timestamptz NOT NULL
);
CREATE TRIGGER generation_preroot_snapshot_immutable BEFORE UPDATE OR DELETE ON generation_create_preroot_snapshot
 FOR EACH ROW EXECUTE FUNCTION kcml_create_record_immutable_v1();
CREATE TABLE generation_create_preroot_outcome (
 logical_operation_id uuid NOT NULL REFERENCES domain_command(logical_operation_id),
 state_version bigint NOT NULL CHECK(state_version>=0),
 canonical_bytes bytea NOT NULL CHECK(convert_from(canonical_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 canonical_digest bytea NOT NULL CHECK(canonical_digest=sha256(canonical_bytes)),
 audit_id uuid NOT NULL UNIQUE REFERENCES audit_event(id) DEFERRABLE INITIALLY DEFERRED,
 PRIMARY KEY(logical_operation_id,state_version)
);
CREATE TRIGGER generation_preroot_outcome_immutable BEFORE UPDATE OR DELETE ON generation_create_preroot_outcome
 FOR EACH ROW EXECUTE FUNCTION kcml_create_record_immutable_v1();
-- Audit of an accepted command rejection is not a fabricated created-domain-event.
ALTER TABLE audit_event ALTER COLUMN domain_event_id DROP NOT NULL;
CREATE OR REPLACE FUNCTION kcml_generation_command_context_consistency_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE d public.domain_command;c public.generation_create_trusted_context;s public.generation_job_initial_request_snapshot;
 b public.generation_create_command_binding;p public.generation_create_preroot_snapshot;
BEGIN
 SELECT * INTO d FROM public.domain_command WHERE logical_operation_id=NEW.logical_operation_id;
 SELECT * INTO b FROM public.generation_create_command_binding WHERE logical_operation_id=d.logical_operation_id;
 SELECT * INTO p FROM public.generation_create_preroot_snapshot WHERE logical_operation_id=d.logical_operation_id;
 IF d.operation_id<>'generation.job.create' THEN
  IF b.logical_operation_id IS NOT NULL OR p.snapshot_id IS NOT NULL THEN RAISE EXCEPTION 'GENERATION_BINDING_OPERATION_KIND_INVALID' USING ERRCODE='23514';END IF;RETURN NULL;
 END IF;
 IF b.logical_operation_id IS NULL AND p.snapshot_id IS NULL THEN RAISE EXCEPTION 'GENERATION_COMMAND_TYPED_BINDING_REQUIRED' USING ERRCODE='23514';END IF;
 IF b.logical_operation_id IS NOT NULL THEN
  SELECT * INTO s FROM public.generation_job_initial_request_snapshot WHERE snapshot_id=b.argument_snapshot_id;
  IF s.snapshot_id IS NULL OR s.logical_operation_id<>d.logical_operation_id OR s.job_id<>d.target_aggregate_id OR b.argument_snapshot_id<>d.canonical_arguments_snapshot_id OR b.trusted_context_id<>d.execution_context_id THEN RAISE EXCEPTION 'GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID' USING ERRCODE='23514';END IF;
 ELSE
  IF p.snapshot_id<>d.canonical_arguments_snapshot_id OR p.prospective_job_id<>d.target_aggregate_id OR p.trusted_context_id<>d.execution_context_id THEN RAISE EXCEPTION 'GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID' USING ERRCODE='23514';END IF;
 END IF;
 SELECT * INTO c FROM public.generation_create_trusted_context WHERE id=d.execution_context_id;
 IF c.id IS NULL OR c.owner_id<>d.owner_id OR c.platform_incarnation_id<>d.platform_incarnation_id OR c.application_deployment_epoch<>d.application_deployment_epoch OR c.client_request_digest<>d.request_digest OR c.execution_descriptor_bytes<>d.execution_descriptor_bytes OR c.execution_descriptor_digest<>d.execution_descriptor_digest OR d.operation_contract_revision IS DISTINCT FROM(convert_from(c.execution_descriptor_bytes,'UTF8')::jsonb->>'operationContractRevision') OR ('sha256:'||encode(d.client_key_digest,'hex')) IS DISTINCT FROM(convert_from(c.execution_descriptor_bytes,'UTF8')::jsonb->>'clientKeyDigest') OR d.scope_digest<>sha256(c.execution_descriptor_bytes) OR d.target_aggregate_kind<>'GENERATION_JOB' THEN RAISE EXCEPTION 'GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID' USING ERRCODE='23514';END IF;
 IF p.snapshot_id IS NOT NULL AND s.snapshot_id IS NOT NULL AND (p.snapshot_id,p.request_schema_id,p.request_schema_digest,p.content_digest,p.ciphertext,p.nonce,p.algorithm,p.key_id,p.crypto_profile_digest) IS DISTINCT FROM(s.snapshot_id,s.request_schema_id,s.request_schema_digest,s.content_digest,s.ciphertext,s.nonce,s.algorithm,s.key_id,s.crypto_profile_digest) THEN RAISE EXCEPTION 'GENERATION_PREROOT_SNAPSHOT_TRANSFER_MISMATCH' USING ERRCODE='23514';END IF;
 RETURN NULL;
END;$$;
CREATE CONSTRAINT TRIGGER generation_preroot_snapshot_link AFTER INSERT ON generation_create_preroot_snapshot DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_generation_command_context_consistency_v1();
CREATE FUNCTION kcml_generation_preroot_closure_v1() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE d public.domain_command;o public.generation_create_preroot_outcome;a public.audit_event;j jsonb;expected_state text;
BEGIN
 SELECT * INTO d FROM public.domain_command WHERE logical_operation_id=NEW.logical_operation_id;
 IF d.operation_id<>'generation.job.create' OR d.state='SUCCEEDED' THEN RETURN NULL;END IF;
 SELECT * INTO o FROM public.generation_create_preroot_outcome WHERE logical_operation_id=d.logical_operation_id AND state_version=d.state_version;
 SELECT * INTO a FROM public.audit_event WHERE id=o.audit_id;
 IF o.logical_operation_id IS NULL OR a.id IS NULL THEN RAISE EXCEPTION 'GENERATION_PREROOT_RETAINED_OUTCOME_REQUIRED' USING ERRCODE='23514';END IF;
 j=convert_from(o.canonical_bytes,'UTF8')::jsonb;
 expected_state=CASE WHEN d.state='FAILED' AND d.terminal THEN 'FAILED_FINAL' WHEN d.state='CANCELLED' AND d.terminal THEN 'CANCELLED_FINAL' WHEN d.state='ACCEPTED' OR j#>>'{error,retryDirective}'='RETRY_SAME_OPERATION' THEN 'EXECUTING' ELSE 'WAITING_FOR_RECONCILIATION' END;
 IF jsonb_typeof(j->'terminal') IS DISTINCT FROM 'boolean' OR jsonb_typeof(j->'status') IS DISTINCT FROM 'string' OR jsonb_typeof(j->'logicalOperationId') IS DISTINCT FROM 'string' OR (d.state<>'ACCEPTED' AND (jsonb_typeof(j#>'{error,message}') IS DISTINCT FROM 'string' OR (j#>'{error,detailsDigest}' IS DISTINCT FROM 'null'::jsonb AND (jsonb_typeof(j#>'{error,detailsDigest}') IS DISTINCT FROM 'string' OR j#>>'{error,detailsDigest}' !~ '^sha256:[0-9a-f]{64}$')))) OR j->>'routeId' IS DISTINCT FROM 'route.0215' OR j->>'operationId' IS DISTINCT FROM 'generation.job.create' OR j->>'correlationId' IS DISTINCT FROM d.correlation_id::text OR j->'stateVersion' IS DISTINCT FROM 'null'::jsonb OR j->'eventSequence' IS DISTINCT FROM 'null'::jsonb OR j->'activationEpoch' IS DISTINCT FROM 'null'::jsonb OR (SELECT count(*) FROM jsonb_object_keys(j))<>11 OR (d.state='ACCEPTED' AND j->'error' IS DISTINCT FROM 'null'::jsonb) OR (d.state<>'ACCEPTED' AND (jsonb_typeof(j->'error') IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(j->'error'))<>5 OR NOT EXISTS(SELECT 1 FROM public.generation_create_retained_error_tuple t WHERE t.stable_code=j#>>'{error,stableCode}' AND t.classification=j#>>'{error,classification}' AND t.retry_directive=j#>>'{error,retryDirective}') OR (d.state='CANCELLED') IS DISTINCT FROM(j#>>'{error,stableCode}'='CREATE_CANCELLED') OR d.terminal IS DISTINCT FROM(j#>>'{error,classification}'<>'UNKNOWN' AND j#>>'{error,retryDirective}'<>'RETRY_SAME_OPERATION'))) THEN RAISE EXCEPTION 'GENERATION_PREROOT_NATIVE_OUTCOME_INVALID' USING ERRCODE='23514';END IF;
 IF j->>'status' IS DISTINCT FROM d.state OR j->>'logicalOperationId' IS DISTINCT FROM d.logical_operation_id::text OR (j->>'terminal')::boolean IS DISTINCT FROM d.terminal OR j->'output' IS DISTINCT FROM 'null'::jsonb OR d.result_digest IS DISTINCT FROM o.canonical_digest OR (d.state IN('FAILED','CANCELLED') AND (j->'error' IS NULL OR j->'error'='null'::jsonb)) OR (d.state='FAILED' AND NOT d.terminal AND j#>>'{error,retryDirective}' NOT IN('RECONCILE_THEN_RETRY','RETRY_SAME_OPERATION')) OR EXISTS(SELECT 1 FROM public.generation_job WHERE id=d.target_aggregate_id) OR EXISTS(SELECT 1 FROM public.domain_event WHERE logical_operation_id=d.logical_operation_id) OR (a.chain_sequence=1 AND a.previous_hash<>decode(repeat('00',32),'hex')) OR (a.chain_sequence>1 AND NOT EXISTS(SELECT 1 FROM public.audit_event prev WHERE prev.chain_sequence=a.chain_sequence-1 AND prev.event_hash=a.previous_hash)) OR a.domain_event_id IS NOT NULL OR a.logical_operation_id<>d.logical_operation_id OR convert_from(a.canonical_bytes,'UTF8')::jsonb->>'objectId' IS DISTINCT FROM d.logical_operation_id::text OR convert_from(a.canonical_bytes,'UTF8')::jsonb->>'actorId' IS DISTINCT FROM d.owner_id::text OR convert_from(a.canonical_bytes,'UTF8')::jsonb->>'afterDigest' IS DISTINCT FROM 'sha256:'||encode(o.canonical_digest,'hex') OR NOT EXISTS(SELECT 1 FROM public.domain_idempotency_record i WHERE i.logical_operation_id=d.logical_operation_id AND i.state=expected_state AND i.scope_digest=d.scope_digest AND i.key_digest=d.client_key_digest AND i.request_digest=d.request_digest AND i.canonical_outcome_digest=o.canonical_digest) OR NOT EXISTS(SELECT 1 FROM public.idempotency_locator l WHERE l.logical_operation_id=d.logical_operation_id AND l.operation_family='GENERATION' AND l.caller_stable_id=d.owner_id::text AND l.caller_authority_kind='OWNER_FULL' AND l.business_target_kind='CREATE_ROOT' AND l.business_target_id='generation_job' AND l.client_request_digest=d.request_digest AND l.client_key_digest=d.client_key_digest AND l.execution_descriptor_digest=d.execution_descriptor_digest AND l.frozen_revision_digest=d.scope_digest) OR NOT EXISTS(SELECT 1 FROM public.audit_head h WHERE h.singleton_key=1 AND h.last_sequence>=a.chain_sequence AND EXISTS(SELECT 1 FROM public.audit_event tail WHERE tail.chain_sequence=h.last_sequence AND tail.event_hash=h.last_hash)) OR(a.archive_required AND NOT EXISTS(SELECT 1 FROM public.audit_archive_outbox x WHERE x.audit_event_id=a.id)) THEN RAISE EXCEPTION 'GENERATION_PREROOT_ATOMIC_CLOSURE_INCOMPLETE' USING ERRCODE='23514';END IF;
 RETURN NULL;
END;$$;
CREATE CONSTRAINT TRIGGER generation_preroot_command_closure AFTER INSERT OR UPDATE ON domain_command DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_generation_preroot_closure_v1();
CREATE CONSTRAINT TRIGGER generation_preroot_outcome_closure AFTER INSERT ON generation_create_preroot_outcome DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_generation_preroot_closure_v1();
-- Shared audit may omit domain_event_id only for the exact retained command audit.
CREATE FUNCTION kcml_generation_preroot_audit_link_v1() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE a public.audit_event;
BEGIN
 SELECT * INTO a FROM public.audit_event WHERE id=NEW.id;
 IF a.domain_event_id IS NULL AND NOT EXISTS(SELECT 1 FROM public.generation_create_preroot_outcome o JOIN public.domain_command d USING(logical_operation_id) WHERE o.audit_id=a.id AND o.logical_operation_id=a.logical_operation_id AND d.operation_id='generation.job.create') THEN RAISE EXCEPTION 'GENERATION_PREROOT_AUDIT_TYPED_LINK_REQUIRED' USING ERRCODE='23514';END IF;
 RETURN NULL;
END;$$;
CREATE CONSTRAINT TRIGGER generation_preroot_audit_link AFTER INSERT ON audit_event DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_generation_preroot_audit_link_v1();
CREATE TABLE generation_create_retained_error_tuple (
 stable_code text PRIMARY KEY,classification text NOT NULL,retry_directive text NOT NULL
);
CREATE TRIGGER generation_error_tuple_immutable BEFORE UPDATE OR DELETE ON generation_create_retained_error_tuple FOR EACH ROW EXECUTE FUNCTION kcml_create_record_immutable_v1();
INSERT INTO generation_create_retained_error_tuple VALUES
('CREATE_CANCELLED','CANCELLED','DO_NOT_RETRY'),
('CREATE_INPUT_INVALID','VALIDATION','DO_NOT_RETRY'),
('CREATE_AUTHENTICATION_REQUIRED','AUTHENTICATION','DO_NOT_RETRY'),
('CREATE_REFERENCE_INVALID','VALIDATION','DO_NOT_RETRY'),
('CREATE_POLICY_UNRESOLVED','DEPENDENCY','DO_NOT_RETRY'),
('CREATE_RECOVERY_BARRIER','CONFLICT','DO_NOT_RETRY'),
('IDEMPOTENCY_CONFLICT','CONFLICT','DO_NOT_RETRY'),
('CREATE_PERSISTENCE_FAILED','INTERNAL','RETRY_SAME_OPERATION'),
('SIDE_EFFECT_OUTCOME_UNKNOWN','UNKNOWN','RECONCILE_THEN_RETRY'),
('FOLLOW_UP_ATOMIC_ADMISSION_UNVERIFIED','DEPENDENCY','DO_NOT_RETRY'),
('FOLLOW_UP_BASIS_BYTES_DIGEST_MISMATCH','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_BASIS_BYTES_UNAVAILABLE','DEPENDENCY','DO_NOT_RETRY'),
('FOLLOW_UP_BASIS_DIGEST_CONFLICT','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_BASIS_IDENTITY_MISMATCH','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_BASIS_INCONSISTENT','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_BASIS_INSUFFICIENT','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_BASIS_INVALID','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_BASIS_NOT_IMMUTABLE','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_BASIS_UNAVAILABLE','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_FINAL_OUTPUT_UNPUBLISHED','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_FROZEN_DESCRIPTOR_INVALID','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_FROZEN_IDENTITY_MISMATCH','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_FROZEN_LINEAGE_DIGEST_MISMATCH','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_FROZEN_SNAPSHOT_UNAVAILABLE','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_KIND_REQUIRED','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_PARENT_REQUIRED','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_PUBLICATION_RECEIPT_MISMATCH','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED','DEPENDENCY','DO_NOT_RETRY'),
('FOLLOW_UP_SNAPSHOT_IDENTITY_INVALID','VALIDATION','DO_NOT_RETRY'),
('FOLLOW_UP_SOURCE_OWNER_MISMATCH','AUTHORIZATION','DO_NOT_RETRY'),
('FOLLOW_UP_SOURCE_STATE_INVALID','VALIDATION','DO_NOT_RETRY');
CREATE FUNCTION kcml_generation_command_version_step_v1() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF OLD.operation_id='generation.job.create' AND NEW.state_version<>OLD.state_version+1 THEN RAISE EXCEPTION 'GENERATION_COMMAND_STATE_VERSION_STEP' USING ERRCODE='40001';END IF;
 RETURN NEW;
END;$$;
CREATE TRIGGER generation_command_version_step BEFORE UPDATE ON domain_command FOR EACH ROW EXECUTE FUNCTION kcml_generation_command_version_step_v1();
