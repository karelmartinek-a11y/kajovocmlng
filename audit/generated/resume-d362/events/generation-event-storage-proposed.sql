-- Proposed technical materialization of §§12.48,49.4–5,51.5,51.12–14,51.25.
-- Parent applies only after semantic review. Ordinary app roles receive no DML.
-- CREATE-dependent FK constraints below are applied after generation_job exists.
CREATE TABLE domain_command (
 logical_operation_id uuid PRIMARY KEY,
 operation_id text NOT NULL,
 owner_id uuid NOT NULL,
 request_digest bytea NOT NULL CHECK(octet_length(request_digest)=32),
 execution_descriptor_bytes bytea NOT NULL,
 execution_descriptor_digest bytea NOT NULL CHECK(execution_descriptor_digest=sha256(execution_descriptor_bytes)),
 state text NOT NULL CHECK(operation_id<>'generation.job.create' OR state IN('ACCEPTED','SUCCEEDED','FAILED','CANCELLED')),
 terminal boolean NOT NULL,
 state_version bigint NOT NULL DEFAULT 0 CHECK(state_version>=0),
 result_digest bytea NULL CHECK(result_digest IS NULL OR octet_length(result_digest)=32),
 platform_incarnation_id uuid NOT NULL,
 application_deployment_epoch bigint NOT NULL CHECK(application_deployment_epoch>=0),
 created_at timestamptz NOT NULL,
 updated_at timestamptz NOT NULL,
 command_id uuid NOT NULL UNIQUE,
 operation_contract_revision text NOT NULL CHECK(length(operation_contract_revision)>0),
 caller_channel text NOT NULL CHECK(length(caller_channel)>0),
 execution_context_id uuid NOT NULL,
 target_aggregate_kind text NOT NULL,
 target_aggregate_id uuid NOT NULL,
 canonical_arguments_snapshot_id uuid NOT NULL,
 scope_digest bytea NOT NULL CHECK(octet_length(scope_digest)=32),
 client_key_digest bytea NOT NULL CHECK(octet_length(client_key_digest)=32),
 expected_state_version bigint NULL CHECK(expected_state_version IS NULL OR expected_state_version>=0),
 expected_revision_id uuid NULL,
 expected_revision_digest bytea NULL CHECK(expected_revision_digest IS NULL OR octet_length(expected_revision_digest)=32),
 expected_binding_set_revision_id uuid NULL,
 expected_activation_epoch bigint NULL CHECK(expected_activation_epoch IS NULL OR expected_activation_epoch>=0),
 deadline_at timestamptz NULL,
 correlation_id uuid NOT NULL,
 causation_id uuid NULL,
 accepted_at timestamptz NOT NULL,
 terminal_at timestamptz NULL,
 error_digest bytea NULL CHECK(error_digest IS NULL OR octet_length(error_digest)=32),
 CHECK(NOT terminal OR result_digest IS NOT NULL),
 CHECK(terminal=(terminal_at IS NOT NULL)),
 CHECK(operation_id<>'generation.job.create' OR state<>'SUCCEEDED' OR terminal),
 CHECK(operation_id<>'generation.job.create' OR state<>'ACCEPTED' OR NOT terminal)
);
CREATE TABLE domain_idempotency_record (
 scope_digest bytea NOT NULL CHECK(octet_length(scope_digest)=32),
 key_digest bytea NOT NULL CHECK(octet_length(key_digest)=32),
 request_digest bytea NOT NULL CHECK(octet_length(request_digest)=32),
 logical_operation_id uuid NOT NULL UNIQUE REFERENCES domain_command(logical_operation_id) DEFERRABLE INITIALLY DEFERRED,
 state text NOT NULL CHECK(state IN('RESERVED','EXECUTING','WAITING_FOR_INPUT','WAITING_FOR_RECONCILIATION','SUCCEEDED','FAILED_FINAL','CANCELLED_FINAL','MANUAL_REVIEW')),
 state_version bigint NOT NULL DEFAULT 0 CHECK(state_version>=0),
 canonical_outcome_digest bytea NULL CHECK(canonical_outcome_digest IS NULL OR octet_length(canonical_outcome_digest)=32),
 PRIMARY KEY(scope_digest,key_digest)
);
-- Existing database/explicit-entities.sql creates the stable idempotency_locator;
-- do not create a second locator or change its physical scope column names.
CREATE TABLE domain_event (
 id uuid PRIMARY KEY,
 aggregate_id uuid NOT NULL,
 aggregate_kind text NOT NULL,
 logical_operation_id uuid NOT NULL REFERENCES domain_command(logical_operation_id),
 aggregate_sequence bigint NOT NULL CHECK(aggregate_sequence>=1),
 event_type text NOT NULL,
 event_schema_id text NOT NULL,
 event_schema_digest bytea NOT NULL CHECK(octet_length(event_schema_digest)=32),
 payload_bytes bytea NOT NULL CHECK(octet_length(payload_bytes)>0),
 payload_digest bytea NOT NULL CHECK(payload_digest=sha256(payload_bytes)),
 correlation_id uuid NOT NULL,
 causation_id uuid NULL,
 occurred_at timestamptz NOT NULL,
 UNIQUE(aggregate_kind,aggregate_id,aggregate_sequence),
 UNIQUE(id,logical_operation_id,aggregate_id),
 CHECK(event_type<>'generation.job.created' OR (aggregate_kind='GENERATION_JOB' AND aggregate_sequence=1 AND event_schema_id='urn:kcml:r9:route:route.0215:event'))
);
CREATE UNIQUE INDEX uq_generation_created_event ON domain_event(logical_operation_id)
 WHERE event_type='generation.job.created';
CREATE TABLE transactional_outbox (
 id uuid PRIMARY KEY,
 event_id uuid NOT NULL REFERENCES domain_event(id),
 logical_operation_id uuid NOT NULL,
 aggregate_id uuid NOT NULL,
 purpose text NOT NULL,
 consumer_scope text NOT NULL,
 available_at timestamptz NOT NULL,
 state text NOT NULL CHECK(state IN('READY','RETRY_WAIT','CLAIMED','DELIVERED','FAILED_FINAL','DISPATCH_AUTHORIZED','RECONCILING','CLOSED')),
 state_version bigint NOT NULL DEFAULT 0 CHECK(state_version>=0),
 attempt_count bigint NOT NULL DEFAULT 0 CHECK(attempt_count>=0),
 payload_digest bytea NOT NULL CHECK(octet_length(payload_digest)=32),
 delivery_fence bigint NOT NULL DEFAULT 0 CHECK(delivery_fence>=0),
 lease_owner_id uuid NULL,
 lease_expires_at timestamptz NULL,
 CHECK(purpose<>'DOMAIN_EVENT' OR state IN('READY','RETRY_WAIT','CLAIMED','DELIVERED','FAILED_FINAL')),
 CHECK(state<>'CLAIMED' OR (lease_owner_id IS NOT NULL AND lease_expires_at IS NOT NULL AND delivery_fence>0)),
 UNIQUE(event_id,consumer_scope),
 FOREIGN KEY(event_id,logical_operation_id,aggregate_id) REFERENCES domain_event(id,logical_operation_id,aggregate_id),
 CHECK(length(consumer_scope)>0)
);
-- This is the domain-event delivery slice. SIDE_EFFECT_DISPATCH authority and
-- its composite attempt FKs require the existing full §51.31 outbox extension;
-- this file does not claim that unrelated outbox purposes are closed.
CREATE TABLE audit_head (
 singleton_key smallint PRIMARY KEY DEFAULT 1 CHECK(singleton_key=1),
 last_sequence bigint NOT NULL CHECK(last_sequence>=0),
 last_hash bytea NOT NULL CHECK(octet_length(last_hash)=32),
 chain_format_version integer NOT NULL CHECK(chain_format_version=1),
 state_version bigint NOT NULL DEFAULT 0 CHECK(state_version>=0)
);
INSERT INTO audit_head(singleton_key,last_sequence,last_hash,chain_format_version,state_version)
 VALUES(1,0,decode(repeat('00',32),'hex'),1,0);
-- Exact proposed version-1 encoding: SHA256(domain ASCII + uint32BE version +
-- previousHash32 + int64BE positive sequence + int64BE byte length + bytes).
-- PostgreSQL int8send/int4send are network big endian. All inputs are mandatory.
CREATE FUNCTION kcml_audit_hash_v1(format integer, previous bytea, sequence bigint, canonical bytea)
 RETURNS bytea LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE SET search_path=pg_catalog AS $$
BEGIN
 IF format IS DISTINCT FROM 1 OR previous IS NULL OR octet_length(previous)<>32
 OR sequence IS NULL OR sequence<1 OR canonical IS NULL THEN
 RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='AUDIT_HASH_INPUT_INVALID';
 END IF;
 RETURN sha256(convert_to('KCML-AUDIT-CHAIN','UTF8')||int4send(format)||previous||int8send(sequence)||int8send(octet_length(canonical)::bigint)||canonical);
END; $$;
CREATE TABLE audit_event (
 id uuid PRIMARY KEY,
 chain_sequence bigint NOT NULL UNIQUE CHECK(chain_sequence>=1),
 previous_hash bytea NOT NULL CHECK(octet_length(previous_hash)=32),
 event_hash bytea NOT NULL CHECK(octet_length(event_hash)=32),
 chain_format_version integer NOT NULL CHECK(chain_format_version=1),
 logical_operation_id uuid NOT NULL REFERENCES domain_command(logical_operation_id),
 domain_event_id uuid NOT NULL UNIQUE REFERENCES domain_event(id),
 canonical_bytes bytea NOT NULL,
 archive_required boolean NOT NULL,
 CHECK(event_hash=kcml_audit_hash_v1(chain_format_version,previous_hash,chain_sequence,canonical_bytes))
);
CREATE TABLE audit_archive_outbox (
 id uuid PRIMARY KEY,
 audit_event_id uuid NOT NULL UNIQUE REFERENCES audit_event(id),
 available_at timestamptz NOT NULL,
 state text NOT NULL CHECK(state IN('READY','CLAIMED','DELIVERED','DEAD_LETTER')),
 state_version bigint NOT NULL DEFAULT 0 CHECK(state_version>=0)
);
-- Run after parent generation_job_create_completion declaration.
ALTER TABLE generation_job_create_completion
 ADD FOREIGN KEY(immutable_event_id,logical_operation_id,job_id)
 REFERENCES domain_event(id,logical_operation_id,aggregate_id) DEFERRABLE INITIALLY DEFERRED;
CREATE FUNCTION kcml_generation_create_atomic_closure_v1()
 RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE c public.generation_job_create_completion; e public.domain_event; d public.domain_command; a public.audit_event; g public.generation_job;
BEGIN
 -- A deferred trigger reads FINAL rows; never OLD/NEW stale snapshots.
 SELECT * INTO c FROM public.generation_job_create_completion WHERE logical_operation_id=NEW.logical_operation_id;
 IF NOT FOUND THEN
  IF TG_TABLE_NAME='domain_command' AND NEW.operation_id='generation.job.create' AND NEW.state='SUCCEEDED' THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_CREATE_COMPLETION_REQUIRED';
  END IF;
  RETURN NULL;
 END IF;
 SELECT * INTO e FROM public.domain_event WHERE id=c.immutable_event_id;
 SELECT * INTO d FROM public.domain_command WHERE logical_operation_id=c.logical_operation_id;
 SELECT * INTO g FROM public.generation_job WHERE id=c.job_id;
 SELECT * INTO a FROM public.audit_event WHERE domain_event_id=e.id;
 IF e.id IS NULL OR d.logical_operation_id IS NULL OR g.id IS NULL OR a.id IS NULL
 OR d.state<>'SUCCEEDED' OR d.result_digest IS DISTINCT FROM c.result_digest
 OR e.event_type<>'generation.job.created' OR e.aggregate_kind<>'GENERATION_JOB' OR e.aggregate_sequence<>c.aggregate_event_sequence
 OR e.payload_digest IS DISTINCT FROM c.output_receipt_digest OR e.payload_bytes IS DISTINCT FROM c.output_receipt_bytes
 OR g.aggregate_event_sequence<e.aggregate_sequence
 OR (convert_from(e.payload_bytes,'UTF8')::jsonb->>'jobId') IS DISTINCT FROM g.id::text
 OR (convert_from(e.payload_bytes,'UTF8')::jsonb->>'kind') IS DISTINCT FROM g.kind
 OR (convert_from(e.payload_bytes,'UTF8')::jsonb->>'initialRequestDigest') IS DISTINCT FROM ('sha256:'||encode(g.initial_request_digest,'hex'))
 OR (convert_from(e.payload_bytes,'UTF8')::jsonb->>'stateVersion') IS DISTINCT FROM c.committed_state_version::text
 OR c.committed_state_version>g.state_version
 OR (convert_from(e.payload_bytes,'UTF8')::jsonb->>'createdAt')::timestamptz IS DISTINCT FROM g.created_at
 OR a.logical_operation_id<>d.logical_operation_id
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'logicalOperationId') IS DISTINCT FROM d.logical_operation_id::text
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'eventId') IS DISTINCT FROM e.id::text
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'objectId') IS DISTINCT FROM g.id::text
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'actorId') IS DISTINCT FROM d.owner_id::text
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'afterDigest') IS DISTINCT FROM ('sha256:'||encode(e.payload_digest,'hex'))
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'chainSequence') IS DISTINCT FROM a.chain_sequence::text
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'previousHash') IS DISTINCT FROM ('sha256:'||encode(a.previous_hash,'hex'))
 OR (a.chain_sequence=1 AND a.previous_hash<>decode(repeat('00',32),'hex'))
 OR (a.chain_sequence>1 AND NOT EXISTS(SELECT 1 FROM public.audit_event p WHERE p.chain_sequence=a.chain_sequence-1 AND p.event_hash=a.previous_hash))
 OR NOT EXISTS(SELECT 1 FROM public.audit_head h JOIN public.audit_event tail ON tail.chain_sequence=h.last_sequence AND tail.event_hash=h.last_hash WHERE h.singleton_key=1 AND h.last_sequence>=a.chain_sequence)
 OR NOT EXISTS(SELECT 1 FROM public.transactional_outbox o WHERE o.event_id=e.id AND o.purpose='DOMAIN_EVENT' AND o.payload_digest=e.payload_digest)
 OR NOT EXISTS(SELECT 1 FROM public.domain_idempotency_record i WHERE i.logical_operation_id=d.logical_operation_id AND i.state='SUCCEEDED' AND i.request_digest=d.request_digest AND i.scope_digest=d.scope_digest AND i.key_digest=d.client_key_digest AND i.canonical_outcome_digest=c.result_digest)
 OR NOT EXISTS(SELECT 1 FROM public.idempotency_locator l WHERE l.logical_operation_id=d.logical_operation_id AND l.client_request_digest=d.request_digest AND l.client_key_digest=d.client_key_digest AND l.execution_descriptor_digest=d.execution_descriptor_digest
 AND l.frozen_revision_digest=d.scope_digest
 AND l.operation_family='GENERATION'
 AND l.caller_authority_kind=(convert_from(d.execution_descriptor_bytes,'UTF8')::jsonb->>'callerAuthorityKind')
 AND l.caller_stable_id::text=(convert_from(d.execution_descriptor_bytes,'UTF8')::jsonb->>'stableCallerObjectId')
 AND l.business_target_kind='CREATE_ROOT'
 AND l.business_target_id='generation_job'
 AND (convert_from(d.execution_descriptor_bytes,'UTF8')::jsonb->>'stableBusinessTargetKey')='CREATE_ROOT:generation_job')
 OR (a.archive_required AND NOT EXISTS(SELECT 1 FROM public.audit_archive_outbox o WHERE o.audit_event_id=a.id)) THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_CREATE_ATOMIC_CLOSURE_INCOMPLETE';
 END IF;
 RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER generation_create_completion_closure AFTER INSERT ON generation_job_create_completion
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_generation_create_atomic_closure_v1();
CREATE CONSTRAINT TRIGGER generation_create_command_closure AFTER INSERT OR UPDATE ON domain_command
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_generation_create_atomic_closure_v1();

CREATE FUNCTION kcml_create_record_immutable_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='CREATE_IMMUTABLE_RECORD';
END; $$;
CREATE TRIGGER create_domain_event_immutable BEFORE UPDATE OR DELETE ON domain_event
 FOR EACH ROW EXECUTE FUNCTION kcml_create_record_immutable_v1();
CREATE TRIGGER create_audit_event_immutable BEFORE UPDATE OR DELETE ON audit_event
 FOR EACH ROW EXECUTE FUNCTION kcml_create_record_immutable_v1();
CREATE FUNCTION kcml_create_command_frozen_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF NEW.logical_operation_id IS DISTINCT FROM OLD.logical_operation_id
 OR NEW.request_digest IS DISTINCT FROM OLD.request_digest
 OR NEW.execution_descriptor_bytes IS DISTINCT FROM OLD.execution_descriptor_bytes
 OR NEW.execution_descriptor_digest IS DISTINCT FROM OLD.execution_descriptor_digest
 OR NEW.owner_id IS DISTINCT FROM OLD.owner_id
 OR NEW.operation_id IS DISTINCT FROM OLD.operation_id
 OR (NEW.command_id,NEW.operation_contract_revision,NEW.caller_channel,NEW.execution_context_id,NEW.target_aggregate_kind,NEW.target_aggregate_id,NEW.canonical_arguments_snapshot_id,NEW.scope_digest,NEW.client_key_digest,NEW.expected_state_version,NEW.expected_revision_id,NEW.expected_revision_digest,NEW.expected_binding_set_revision_id,NEW.expected_activation_epoch,NEW.deadline_at,NEW.correlation_id,NEW.causation_id,NEW.created_at,NEW.accepted_at)
 IS DISTINCT FROM
 (OLD.command_id,OLD.operation_contract_revision,OLD.caller_channel,OLD.execution_context_id,OLD.target_aggregate_kind,OLD.target_aggregate_id,OLD.canonical_arguments_snapshot_id,OLD.scope_digest,OLD.client_key_digest,OLD.expected_state_version,OLD.expected_revision_id,OLD.expected_revision_digest,OLD.expected_binding_set_revision_id,OLD.expected_activation_epoch,OLD.deadline_at,OLD.correlation_id,OLD.causation_id,OLD.created_at,OLD.accepted_at)
 OR (OLD.terminal AND NEW IS DISTINCT FROM OLD) THEN
 RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='CREATE_COMMAND_FROZEN_SCOPE';
 END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER create_command_frozen BEFORE UPDATE ON domain_command
 FOR EACH ROW EXECUTE FUNCTION kcml_create_command_frozen_v1();
CREATE FUNCTION kcml_audit_hash(format integer, previous bytea, sequence bigint, canonical bytea)
 RETURNS bytea LANGUAGE sql IMMUTABLE PARALLEL SAFE SET search_path=pg_catalog,public AS $$
 SELECT public.kcml_audit_hash_v1(format,previous,sequence,canonical);
$$;
CREATE FUNCTION kcml_create_idempotency_frozen_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF NEW.scope_digest IS DISTINCT FROM OLD.scope_digest OR NEW.key_digest IS DISTINCT FROM OLD.key_digest
 OR NEW.request_digest IS DISTINCT FROM OLD.request_digest OR NEW.logical_operation_id IS DISTINCT FROM OLD.logical_operation_id
 OR (OLD.state IN('SUCCEEDED','FAILED_FINAL','CANCELLED_FINAL') AND NEW IS DISTINCT FROM OLD) THEN
 RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='CREATE_IDEMPOTENCY_FROZEN_SCOPE';
 END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER create_idempotency_frozen BEFORE UPDATE ON domain_idempotency_record
 FOR EACH ROW EXECUTE FUNCTION kcml_create_idempotency_frozen_v1();
-- Locator identity and frozen digests remain immutable; retention/detail cleanup
-- is a separate operation and cannot reuse a business key for another command.
CREATE FUNCTION kcml_create_locator_frozen_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF (NEW.operation_family,NEW.caller_authority_kind,NEW.caller_stable_id,NEW.business_target_kind,NEW.business_target_id,NEW.client_key_digest,NEW.logical_operation_id,NEW.client_request_digest,NEW.execution_descriptor_digest,NEW.frozen_revision_digest)
 IS DISTINCT FROM
 (OLD.operation_family,OLD.caller_authority_kind,OLD.caller_stable_id,OLD.business_target_kind,OLD.business_target_id,OLD.client_key_digest,OLD.logical_operation_id,OLD.client_request_digest,OLD.execution_descriptor_digest,OLD.frozen_revision_digest) THEN
 RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='CREATE_LOCATOR_FROZEN_SCOPE';
 END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER create_locator_frozen BEFORE UPDATE ON idempotency_locator
 FOR EACH ROW EXECUTE FUNCTION kcml_create_locator_frozen_v1();

CREATE FUNCTION kcml_create_outbox_frozen_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF TG_OP='DELETE' THEN
  RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='CREATE_OUTBOX_RETENTION_AUTHORITY_REQUIRED';
 END IF;
 IF (NEW.id,NEW.event_id,NEW.logical_operation_id,NEW.aggregate_id,NEW.purpose,NEW.consumer_scope,NEW.payload_digest)
 IS DISTINCT FROM
 (OLD.id,OLD.event_id,OLD.logical_operation_id,OLD.aggregate_id,OLD.purpose,OLD.consumer_scope,OLD.payload_digest) THEN
  RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='CREATE_OUTBOX_FROZEN_DELIVERY';
 END IF;
 IF NEW IS NOT DISTINCT FROM OLD THEN RETURN NEW; END IF;
 IF NEW.state_version<>OLD.state_version+1 THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='CREATE_OUTBOX_STATE_VERSION_INVALID';
 END IF;
 IF OLD.purpose='DOMAIN_EVENT' THEN
  IF OLD.state IN('DELIVERED','FAILED_FINAL') THEN
   RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='CREATE_OUTBOX_TERMINAL_IMMUTABLE';
  END IF;
  IF NOT ((OLD.state IN('READY','RETRY_WAIT') AND NEW.state='CLAIMED')
   OR (OLD.state='CLAIMED' AND NEW.state IN('CLAIMED','DELIVERED','RETRY_WAIT','FAILED_FINAL'))) THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='CREATE_OUTBOX_TRANSITION_INVALID';
  END IF;
  IF NEW.state='CLAIMED' AND (NEW.delivery_fence<>OLD.delivery_fence+1 OR NEW.lease_owner_id IS NULL OR NEW.lease_expires_at IS NULL
   OR (OLD.state='CLAIMED' AND OLD.lease_expires_at>clock_timestamp())) THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='CREATE_OUTBOX_CLAIM_FENCE_INVALID';
  END IF;
  IF OLD.state='CLAIMED' AND NEW.state<>'CLAIMED' AND (NEW.delivery_fence<>OLD.delivery_fence OR OLD.lease_expires_at<=clock_timestamp()) THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='CREATE_OUTBOX_STALE_DELIVERY_LEASE';
  END IF;
 END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER create_outbox_frozen BEFORE UPDATE OR DELETE ON transactional_outbox
 FOR EACH ROW EXECUTE FUNCTION kcml_create_outbox_frozen_v1();
