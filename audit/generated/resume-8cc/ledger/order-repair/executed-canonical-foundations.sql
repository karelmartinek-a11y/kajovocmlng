-- Required source-owned authentication fields (§25.3); physical keys §51.11.
-- This creates no business role/status/scope/account lifecycle.
CREATE EXTENSION IF NOT EXISTS citext;
CREATE TABLE owner_identity (
 id uuid PRIMARY KEY,
 singleton_key smallint NOT NULL DEFAULT 1 UNIQUE CHECK(singleton_key=1),
 username citext NOT NULL UNIQUE CHECK(username::text COLLATE "C"='KRMAR78'),
 password_hash text NOT NULL CHECK(length(password_hash)>0),
 password_changed_at timestamptz NOT NULL,
 mfa_enabled boolean NOT NULL,
 mfa_secret_ciphertext bytea NULL,
 deployment_managed boolean NOT NULL,
 session_epoch bigint NOT NULL DEFAULT 0 CHECK(session_epoch>=0),
 state_version bigint NOT NULL DEFAULT 0 CHECK(state_version>=0),
 aggregate_event_sequence bigint NOT NULL DEFAULT 0 CHECK(aggregate_event_sequence>=0),
 created_at timestamptz NOT NULL,
 updated_at timestamptz NOT NULL,
 password_source text NOT NULL CHECK(password_source='GITHUB_ACTIONS_PASS')
);
CREATE TABLE owner_session (
 id uuid PRIMARY KEY,
 owner_identity_id uuid NOT NULL REFERENCES owner_identity(id) ON DELETE RESTRICT,
 lookup_digest bytea NOT NULL UNIQUE CHECK(octet_length(lookup_digest)=32),
 session_hash text NOT NULL CHECK(length(session_hash)>0),
 created_at timestamptz NOT NULL,
 last_seen_at timestamptz NOT NULL,
 expires_at timestamptz NOT NULL,
 revoked_at timestamptz NULL,
 reauthenticated_at timestamptz NULL,
 session_epoch bigint NOT NULL CHECK(session_epoch>=0),
 device_metadata text NULL,
 ip_address inet NULL,
 user_agent text NULL,
 CHECK(expires_at>created_at),
 CHECK(last_seen_at>=created_at),
 CHECK(reauthenticated_at IS NULL OR reauthenticated_at>=created_at)
);
CREATE TABLE owner_api_credential (
 singleton_key smallint PRIMARY KEY DEFAULT 1 CHECK(singleton_key=1),
 secret_id uuid NOT NULL,
 secret_version_id uuid NOT NULL,
 verifier_hash text NOT NULL CHECK(length(verifier_hash)>0),
 fingerprint text NOT NULL CHECK(length(fingerprint)>0),
 credential_version bigint NOT NULL CHECK(credential_version>=1),
 state_version bigint NOT NULL DEFAULT 0 CHECK(state_version>=0),
 credential_activation_epoch bigint NOT NULL CHECK(credential_activation_epoch>=0),
 last_rotate_logical_operation_id uuid NULL,
 last_rotate_outcome_digest bytea NULL CHECK(octet_length(last_rotate_outcome_digest)=32),
 created_at timestamptz NOT NULL,
 rotated_at timestamptz NULL,
 last_used_at timestamptz NULL,
 last_usage_metadata text NULL,
 audit_correlation_id uuid NULL
);
-- Secret root/version composite FKs are added after their exact physical resource;
-- the constructor checks credential version/fingerprint but is not the API verifier.
CREATE TABLE platform_incarnation (
 singleton_key smallint PRIMARY KEY DEFAULT 1 CHECK(singleton_key=1),
 platform_incarnation_id uuid NOT NULL UNIQUE,
 incarnation_sequence bigint NOT NULL CHECK(incarnation_sequence>=1),
 created_at timestamptz NOT NULL,
 reason text NOT NULL,
 source_restore_evidence_id uuid NULL,
 source_deployment_evidence_id uuid NULL
);
CREATE TABLE application_deployment_head (
 singleton_key smallint PRIMARY KEY DEFAULT 1 CHECK(singleton_key=1),
 application_deployment_epoch bigint NOT NULL CHECK(application_deployment_epoch>=0),
 current_application_release_id uuid NOT NULL,
 current_manifest_digest bytea NOT NULL CHECK(octet_length(current_manifest_digest)=32),
 platform_incarnation_id uuid NOT NULL,
 state_version bigint NOT NULL DEFAULT 0 CHECK(state_version>=0),
 updated_at timestamptz NOT NULL
);
-- Historical incarnations remain legitimate immutable context provenance, so no
-- FK incorrectly couples a retained old context ID to the single mutable head.
CREATE FUNCTION kcml_authentication_singleton_guard_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog AS $$BEGIN
 IF TG_OP='DELETE' OR NEW.singleton_key IS DISTINCT FROM OLD.singleton_key THEN
 RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='FIXED_SINGLETON_IDENTITY_IMMUTABLE';END IF;
 RETURN NEW;END$$;
CREATE TRIGGER owner_fixed_singleton BEFORE UPDATE OF singleton_key OR DELETE ON owner_identity
 FOR EACH ROW EXECUTE FUNCTION kcml_authentication_singleton_guard_v1();
CREATE TRIGGER api_fixed_singleton BEFORE UPDATE OF singleton_key OR DELETE ON owner_api_credential
 FOR EACH ROW EXECUTE FUNCTION kcml_authentication_singleton_guard_v1();
CREATE TRIGGER incarnation_fixed_singleton BEFORE UPDATE OF singleton_key OR DELETE ON platform_incarnation
 FOR EACH ROW EXECUTE FUNCTION kcml_authentication_singleton_guard_v1();
CREATE TRIGGER deployment_fixed_singleton BEFORE UPDATE OF singleton_key OR DELETE ON application_deployment_head
 FOR EACH ROW EXECUTE FUNCTION kcml_authentication_singleton_guard_v1();
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
-- Candidate physical projection of SSOT §25.11 and §51.9; coordinator review required.
-- Referenced external roots must be installed from their own authoritative DDL.
-- This file never supplies placeholder external roots or grants client authority.
CREATE TABLE generation_job (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES owner_identity(id) ON DELETE RESTRICT,
  initiating_access_channel text NOT NULL,
  initiating_execution_context_id uuid NOT NULL,
  kind text NOT NULL CHECK (kind IN ('CREATE','UPDATE','FOLLOW_UP','RETRY','REPAIR')),
  target_kind text NULL CHECK (target_kind IN ('MCP_SERVER','MCP_TOOL','MCP_RESOURCE','MCP_PROMPT','AI_AGENT','AGENT_TOOL_ADAPTER','AGENT_AS_TOOL','AGENT_HANDOFF','PLATFORM_COMPONENT','MANAGED_RUNTIME','EXTERNAL_API_CONNECTOR','WEBHOOK_HANDLER','PULSE_INTEGRATION','BROWSER_AUTOMATION','OWNER_UI')),
  target_object_id uuid NULL,
  state text NOT NULL CHECK (state IN ('ACTIVATING','ANALYZING','BLOCKED','CANCELLED','CML_CONFORMANCE','COMPLETED','DISCUSSING','FAILED','IMPLEMENTING','INTEGRATING','VALIDATING')),
  current_phase text NULL,
  state_version bigint NOT NULL DEFAULT 0 CHECK (state_version>=0),
  aggregate_event_sequence bigint NOT NULL DEFAULT 0 CHECK (aggregate_event_sequence>=0),
  initial_request_snapshot_id uuid NOT NULL UNIQUE,
  initial_request_digest bytea NOT NULL CHECK (octet_length(initial_request_digest)=32),
  parent_job_id uuid NULL REFERENCES generation_job(id) ON DELETE RESTRICT,
  current_spec_revision_id uuid NULL,
  approved_spec_revision_id uuid NULL,
  approved_specification_digest bytea NULL CHECK (octet_length(approved_specification_digest)=32),
  execution_authority_id uuid NULL,
  current_capability_snapshot_id uuid NULL,
  current_plan_id uuid NULL,
  active_phase_run_id uuid NULL,
  latest_checkpoint_id uuid NULL,
  previous_release_id uuid NULL,
  candidate_release_id uuid NULL,
  activation_set_id uuid NULL,
  cancellation_version bigint NOT NULL DEFAULT 0 CHECK (cancellation_version>=0),
  blocker_id uuid NULL,
  error_code text NULL,
  coordinator_lease_owner_id uuid NULL,
  coordinator_fencing_token bigint NOT NULL DEFAULT 0 CHECK (coordinator_fencing_token>=0),
  coordinator_lease_expires_at timestamptz NULL,
  coordinator_heartbeat_at timestamptz NULL,
  platform_incarnation_id uuid NOT NULL,
  application_deployment_epoch bigint NOT NULL CHECK (application_deployment_epoch>=0),
  created_at timestamptz NOT NULL,
  started_at timestamptz NULL,
  completed_at timestamptz NULL,
  client_request_id text NOT NULL,
  latest_command_logical_operation_id uuid NOT NULL REFERENCES domain_command(logical_operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
  UNIQUE(owner_id,client_request_id),
  CHECK (parent_job_id IS DISTINCT FROM id),
  CHECK (target_object_id IS NULL OR target_kind IS NOT NULL),
  CHECK (kind<>'UPDATE' OR (target_object_id IS NOT NULL AND target_kind IS NOT NULL)),
  CHECK (kind<>'FOLLOW_UP' OR parent_job_id IS NOT NULL),
  CHECK ((approved_spec_revision_id IS NULL)=(approved_specification_digest IS NULL)),
  CHECK ((coordinator_lease_owner_id IS NULL)=(coordinator_lease_expires_at IS NULL)),
  CHECK (coordinator_heartbeat_at IS NULL OR coordinator_lease_owner_id IS NOT NULL),
  CHECK (started_at IS NULL OR started_at>=created_at),
  CHECK (completed_at IS NULL OR completed_at>=created_at)
);

-- SSOT25.11/12.47–12.49: exact CREATE persistence subordinate tables.
-- Prerequisites still BLOCKED: complete generation_job/domain_command schemas,
-- trustedcontext construction, actual crypto-profile binding, event/outbox/audit
-- physical joins, and operation-specific admission/locks. No executable-helper
-- or production-acceptance claim is made by parsing these declarations.
CREATE TABLE generation_job_initial_request_snapshot (
  job_id uuid PRIMARY KEY REFERENCES generation_job(id) ON DELETE RESTRICT,
  snapshot_id uuid NOT NULL UNIQUE,
  logical_operation_id uuid NOT NULL UNIQUE
    REFERENCES domain_command(logical_operation_id) ON DELETE RESTRICT
    DEFERRABLE INITIALLY DEFERRED,
  request_schema_id text NOT NULL
    CHECK (request_schema_id = 'urn:kcml:r9:semantic:route.0215:body'),
  request_schema_digest bytea NOT NULL CHECK (octet_length(request_schema_digest)=32),
  content_digest bytea NOT NULL CHECK (octet_length(content_digest)=32),
  ciphertext bytea NOT NULL CHECK (octet_length(ciphertext)>0),
  nonce bytea NOT NULL CHECK (octet_length(nonce)>0),
  algorithm text NOT NULL CHECK (length(algorithm)>0),
  key_id text NOT NULL CHECK (length(key_id)>0),
  crypto_profile_digest bytea NOT NULL CHECK (octet_length(crypto_profile_digest)=32),
  created_at timestamptz NOT NULL
);
-- Ciphertext decrypts to canonical bytes of the exact typed request body.
-- content_digest covers those plaintext canonical bytes, never ciphertext.
-- The protectedbody remains OWNER-accessible through existing Secret/context
-- rules; this table never automatically creates a secret_record or binding.
-- algorithm/key_id/nonce are verified against the existing authenticated crypto
-- profile; nonempty SQL fields alone do not authorize a crypto algorithm.

CREATE TABLE generation_job_follow_up_basis (
  job_id uuid PRIMARY KEY REFERENCES generation_job(id) ON DELETE RESTRICT,
  source_job_id uuid NOT NULL REFERENCES generation_job(id) ON DELETE RESTRICT,
  source_snapshot_id uuid NOT NULL,
  basis_kind text NOT NULL CHECK (basis_kind IN ('INITIAL_REQUEST','SPECIFICATION_REVISION','PUBLISHED_FINAL_OUTPUT')),
  revision_id uuid NULL,
  artifact_id uuid NULL,
  publication_receipt_id uuid NULL,
  content_digest bytea NOT NULL CHECK (octet_length(content_digest)=32),
  lineage_digest bytea NOT NULL CHECK (octet_length(lineage_digest)=32),
  CHECK (job_id <> source_job_id),
  CHECK (
    (basis_kind='INITIAL_REQUEST' AND revision_id IS NULL AND artifact_id IS NULL AND publication_receipt_id IS NULL)
    OR (basis_kind='SPECIFICATION_REVISION' AND revision_id IS NOT NULL AND artifact_id IS NULL AND publication_receipt_id IS NULL)
    OR (basis_kind='PUBLISHED_FINAL_OUTPUT' AND revision_id IS NULL AND artifact_id IS NOT NULL AND publication_receipt_id IS NOT NULL)
  )
);
-- The same frozen snapshot selects retained actual bytes; source current state
-- and pointers never rewrite lineage. Source snapshot/revision/artifact/receipt
-- physical FK bindings and sufficient-basis policy remain explicit prerequisites.

CREATE TABLE generation_job_create_completion (
  logical_operation_id uuid PRIMARY KEY
    REFERENCES domain_command(logical_operation_id) ON DELETE RESTRICT
    DEFERRABLE INITIALLY DEFERRED,
  job_id uuid NOT NULL UNIQUE REFERENCES generation_job(id) ON DELETE RESTRICT,
  semantic_response_bytes bytea NOT NULL CHECK (octet_length(semantic_response_bytes)>0),
  result_digest bytea NOT NULL CHECK (octet_length(result_digest)=32),
  output_receipt_bytes bytea NOT NULL CHECK (octet_length(output_receipt_bytes)>0),
  output_receipt_digest bytea NOT NULL CHECK (octet_length(output_receipt_digest)=32),
  immutable_event_id uuid NOT NULL UNIQUE,
  aggregate_event_sequence bigint NOT NULL CHECK (aggregate_event_sequence>=1),
  committed_state_version bigint NOT NULL CHECK (committed_state_version>=0),
  created_at timestamptz NOT NULL,
  CHECK (result_digest = sha256(semantic_response_bytes)),
  CHECK (output_receipt_digest = sha256(output_receipt_bytes))
);
-- semantic_response_bytes are exact canonical semantic_result(response) bytes:
-- exclude resultDigest and idempotencyReplay per create_completion_contracts.py.
-- output_receipt_bytes are exact canonical GenerationCreated bytes; no intent,
-- sourcebody, plaintext credential, provider data or execution authority appears.
-- Actual event/outbox/audit FK columns and atomic closure constraints must bind
-- this row before whole-operation readiness; unique UUID fields are insufficient.

CREATE OR REPLACE FUNCTION kcml_reject_generation_create_snapshot_update_v1()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='GENERATION_CREATE_IMMUTABLE_SNAPSHOT';
END;
$$;
CREATE TRIGGER generation_initial_request_immutable
BEFORE UPDATE ON generation_job_initial_request_snapshot
FOR EACH ROW EXECUTE FUNCTION kcml_reject_generation_create_snapshot_update_v1();
CREATE TRIGGER generation_follow_up_basis_immutable
BEFORE UPDATE ON generation_job_follow_up_basis
FOR EACH ROW EXECUTE FUNCTION kcml_reject_generation_create_snapshot_update_v1();
CREATE TRIGGER generation_create_completion_immutable
BEFORE UPDATE ON generation_job_create_completion
FOR EACH ROW EXECUTE FUNCTION kcml_reject_generation_create_snapshot_update_v1();
-- Deletion is not authorized by these triggers. Retention/tombstone and canonical
-- cleanup authority require separate exact bindings per49.4; no cascade is used.
-- Immutable initial request is retained independently of mutable source job pointers.
-- These circular FKs are deliberately DEFERRABLE so root + snapshot are one atomic set.
ALTER TABLE generation_job_initial_request_snapshot ADD UNIQUE(job_id,snapshot_id,content_digest);
ALTER TABLE generation_job ADD CONSTRAINT generation_job_initial_snapshot
  FOREIGN KEY(id,initial_request_snapshot_id,initial_request_digest)
  REFERENCES generation_job_initial_request_snapshot(job_id,snapshot_id,content_digest)
  ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
-- The composite FK also verifies the root's digest, not merely snapshot identity.

CREATE OR REPLACE FUNCTION kcml_generation_job_write_guard_v1()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  IF OLD.state IN ('COMPLETED','FAILED','CANCELLED') THEN
    RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='GENERATION_TERMINAL_IMMUTABLE';
  END IF;
  IF NEW.id<>OLD.id OR NEW.owner_id<>OLD.owner_id
     OR NEW.kind<>OLD.kind OR NEW.created_at<>OLD.created_at
     OR NEW.initiating_access_channel<>OLD.initiating_access_channel
     OR NEW.initiating_execution_context_id<>OLD.initiating_execution_context_id
     OR NEW.target_kind IS DISTINCT FROM OLD.target_kind
     OR NEW.target_object_id IS DISTINCT FROM OLD.target_object_id
     OR NEW.initial_request_snapshot_id<>OLD.initial_request_snapshot_id
     OR NEW.initial_request_digest<>OLD.initial_request_digest
     OR NEW.client_request_id<>OLD.client_request_id
     OR NEW.parent_job_id IS DISTINCT FROM OLD.parent_job_id THEN
    RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='GENERATION_FROZEN_INPUT_IMMUTABLE';
  END IF;
  IF NEW.state_version<>OLD.state_version+1 THEN
    RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='GENERATION_STATE_VERSION_STEP';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER generation_job_write_guard BEFORE UPDATE ON generation_job
FOR EACH ROW EXECUTE FUNCTION kcml_generation_job_write_guard_v1();
-- This trigger supplements, never replaces, the operation's expected state/fence CAS.
-- Current phase mapping, approved-spec same-job composite FK, authority/plan/checkpoint/
-- release/activation references, target-kind root relations and authenticated context
-- FKs are listed as explicit unresolved joins in generation-root-contract.json.
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
CREATE TABLE idempotency_locator (
  locator_id uuid PRIMARY KEY,
  operation_family text NOT NULL,
  caller_authority_kind text NOT NULL,
  caller_stable_id text NOT NULL,
  business_target_kind text NOT NULL,
  business_target_id text NOT NULL,
  client_key_digest bytea NOT NULL CHECK (octet_length(client_key_digest)=32),
  logical_operation_id uuid NOT NULL UNIQUE REFERENCES domain_command(logical_operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
  client_request_digest bytea NOT NULL CHECK (octet_length(client_request_digest)=32),
  execution_descriptor_digest bytea NOT NULL CHECK (octet_length(execution_descriptor_digest)=32),
  frozen_revision_digest bytea NOT NULL CHECK (octet_length(frozen_revision_digest)=32),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  terminal_at timestamptz NULL,
  retention_until timestamptz NOT NULL,
  CONSTRAINT uq_idempotency_locator_scope UNIQUE
    (operation_family,caller_authority_kind,caller_stable_id,business_target_kind,business_target_id,client_key_digest),
  CONSTRAINT ck_idempotency_locator_retention CHECK (retention_until > created_at)
);
CREATE INDEX ix_idempotency_locator_logical_operation ON idempotency_locator(logical_operation_id);
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
-- Deployment-owned immutable pin from actual consumed authoritative resource bytes.
-- Fresh create resolves by locked deployment epoch, never caller-selected schema.
CREATE TABLE generation_create_contract_pin (
 id uuid PRIMARY KEY,
 application_deployment_epoch bigint NOT NULL UNIQUE CHECK(application_deployment_epoch>=0),
 operation_id text NOT NULL CHECK(operation_id='generation.job.create'),
 operation_contract_revision text NOT NULL CHECK(length(operation_contract_revision)>0),
 operation_record_bytes bytea NOT NULL,
 route_record_bytes bytea NOT NULL,
 domain_schema_bytes bytea NOT NULL,
 contract_revision_bytes bytea NOT NULL,
 operation_resource_digest bytea NOT NULL CHECK(octet_length(operation_resource_digest)=32),
 route_resource_digest bytea NOT NULL CHECK(octet_length(route_resource_digest)=32),
 schema_resource_digest bytea NOT NULL CHECK(octet_length(schema_resource_digest)=32),
 contract_digest bytea NOT NULL CHECK(contract_digest=sha256(contract_revision_bytes)),
 UNIQUE(application_deployment_epoch,contract_digest),
 domain_schema_digest bytea NOT NULL CHECK(domain_schema_digest=sha256(domain_schema_bytes)),
 CHECK(convert_from(operation_record_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(route_record_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(domain_schema_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(contract_revision_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(operation_record_bytes,'UTF8')::jsonb->>'operationId' IS NOT DISTINCT FROM operation_id),
 CHECK(convert_from(operation_record_bytes,'UTF8')::jsonb->>'operationRevision' IS NOT DISTINCT FROM operation_contract_revision),
 CHECK(convert_from(route_record_bytes,'UTF8')::jsonb->>'operationId' IS NOT DISTINCT FROM operation_id),
 CHECK(convert_from(route_record_bytes,'UTF8')::jsonb#>'{requestSchema,properties,body}' IS NOT DISTINCT FROM convert_from(domain_schema_bytes,'UTF8')::jsonb),
 CHECK(convert_from(route_record_bytes,'UTF8')::jsonb->>'routeId' IS NOT NULL),
 CHECK(convert_from(contract_revision_bytes,'UTF8')::jsonb->'operationRecord' IS NOT DISTINCT FROM convert_from(operation_record_bytes,'UTF8')::jsonb),
 CHECK(convert_from(contract_revision_bytes,'UTF8')::jsonb->'routeRecord' IS NOT DISTINCT FROM convert_from(route_record_bytes,'UTF8')::jsonb),
 CHECK(convert_from(contract_revision_bytes,'UTF8')::jsonb->'domainSchema' IS NOT DISTINCT FROM convert_from(domain_schema_bytes,'UTF8')::jsonb)
);
CREATE TRIGGER generation_create_contract_pin_immutable BEFORE UPDATE
 ON generation_create_contract_pin FOR EACH ROW
 EXECUTE FUNCTION kcml_reject_generation_create_snapshot_update_v1();
-- INSERT belongs only to deployment migrator, never auth/domain/model clients.
-- Exact scoped materialization: §25.3, §26.1, §49.4, §51.2, §51.5-6/51.11.
-- Symbolic OWNER/OWNER_API identifies the logical singleton; §51.11 mandates
-- SMALLINT singleton_key=1 as its physical key. No text-key lookup is permitted.
-- Authentication acceptance is a server-owned immutable receipt written only by
-- the canonical authentication service after verifying actual session/API material.
-- It is not a client input, model proposal or reusable authorization boolean.
CREATE TABLE generation_create_authentication_acceptance (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES owner_identity(id) ON DELETE RESTRICT,
  access_channel text NOT NULL CHECK(access_channel IN ('OWNER_SESSION','OWNER_API_KEY')),
  session_id uuid NULL REFERENCES owner_session(id) ON DELETE RESTRICT,
  session_epoch bigint NULL CHECK(session_epoch>=0),
  session_lookup_digest bytea NULL CHECK(octet_length(session_lookup_digest)=32),
  api_credential_version bigint NULL CHECK(api_credential_version>=1),
  api_credential_fingerprint text NULL,
  accepted_at timestamptz NOT NULL,
  UNIQUE(id,owner_id,access_channel),
  CHECK((access_channel='OWNER_SESSION' AND session_id IS NOT NULL AND session_epoch IS NOT NULL AND session_lookup_digest IS NOT NULL AND api_credential_version IS NULL AND api_credential_fingerprint IS NULL)
     OR (access_channel='OWNER_API_KEY' AND session_id IS NULL AND session_epoch IS NULL AND session_lookup_digest IS NULL AND api_credential_version IS NOT NULL AND api_credential_fingerprint IS NOT NULL))
);
CREATE TABLE generation_create_trusted_context (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES owner_identity(id) ON DELETE RESTRICT,
  authentication_acceptance_id uuid NOT NULL REFERENCES generation_create_authentication_acceptance(id) ON DELETE RESTRICT,
  initiating_access_channel text NOT NULL CHECK(initiating_access_channel IN ('OWNER_SESSION','OWNER_API_KEY')),
  platform_incarnation_id uuid NOT NULL,
  application_deployment_epoch bigint NOT NULL CHECK(application_deployment_epoch>=0),
  operation_contract_digest bytea NOT NULL CHECK(octet_length(operation_contract_digest)=32),
  client_request_digest bytea NOT NULL CHECK(octet_length(client_request_digest)=32),
  execution_descriptor_bytes bytea NOT NULL CHECK(octet_length(execution_descriptor_bytes)>0),
  execution_descriptor_digest bytea NOT NULL CHECK(octet_length(execution_descriptor_digest)=32),
  accepted_at timestamptz NOT NULL,
  UNIQUE(id,owner_id,initiating_access_channel),
  FOREIGN KEY(application_deployment_epoch,operation_contract_digest) REFERENCES generation_create_contract_pin(application_deployment_epoch,contract_digest) ON DELETE RESTRICT,
  FOREIGN KEY(authentication_acceptance_id,owner_id,initiating_access_channel)
    REFERENCES generation_create_authentication_acceptance(id,owner_id,access_channel) ON DELETE RESTRICT,
  CHECK(execution_descriptor_digest=sha256(execution_descriptor_bytes))
);
CREATE TRIGGER generation_create_authentication_immutable BEFORE UPDATE
ON generation_create_authentication_acceptance FOR EACH ROW
EXECUTE FUNCTION kcml_reject_generation_create_snapshot_update_v1();
CREATE TRIGGER generation_create_context_immutable BEFORE UPDATE
ON generation_create_trusted_context FOR EACH ROW
EXECUTE FUNCTION kcml_reject_generation_create_snapshot_update_v1();
-- Canonical service role grants are an installation prerequisite:
-- authentication writer alone INSERTs authentication acceptance;
-- domain writer has SELECT receipt + EXECUTE constructor, no INSERT receipt;
-- generated handlers have no DB credential/network path (§51.2).
-- Controlled-schema SECURITY DEFINER is owned by restricted NOLOGIN builder.
-- Exact infrastructure grants are in generation-context-role-bindings.sql.
-- Installer pins its controlled schema and puts pg_temp explicitly LAST.
-- Without this, temp relation shadowing could bypass SECURITY DEFINER reads.
SELECT set_config('search_path',format('%I,pg_catalog,pg_temp',current_schema()),false);
CREATE OR REPLACE FUNCTION kcml_generation_create_context_v1(
 p_authentication_acceptance_id uuid,
 p_client_request_digest bytea,
 p_operation_contract_digest bytea,
 p_execution_descriptor_bytes bytea)
RETURNS generation_create_trusted_context LANGUAGE plpgsql SECURITY DEFINER SET search_path FROM CURRENT AS $$
DECLARE a generation_create_authentication_acceptance%ROWTYPE;
        o owner_identity%ROWTYPE;
        s owner_session%ROWTYPE;
        api owner_api_credential%ROWTYPE;
        pi platform_incarnation%ROWTYPE;
        dh application_deployment_head%ROWTYPE;
        c generation_create_trusted_context%ROWTYPE;
        now_at timestamptz;
        pin generation_create_contract_pin%ROWTYPE;
        descriptor jsonb;
        expected_descriptor jsonb;
        expected_descriptor_bytes bytea;
BEGIN
 IF octet_length(p_client_request_digest) IS DISTINCT FROM 32
    OR octet_length(p_operation_contract_digest) IS DISTINCT FROM 32
    OR p_execution_descriptor_bytes IS NULL OR octet_length(p_execution_descriptor_bytes)=0 THEN
  RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='GENERATION_CONTEXT_INPUT_INVALID';
 END IF;
 SELECT * INTO a FROM generation_create_authentication_acceptance
 WHERE id=p_authentication_acceptance_id;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0002',MESSAGE='GENERATION_AUTH_RECEIPT_UNRESOLVED';END IF;
 -- Receipt is immutable. Only persisted identity, never arbitrary actor metadata.
 SELECT platform_incarnation_id INTO STRICT pi.platform_incarnation_id FROM platform_incarnation WHERE singleton_key=1 FOR SHARE;
 SELECT platform_incarnation_id,application_deployment_epoch INTO STRICT dh.platform_incarnation_id,dh.application_deployment_epoch FROM application_deployment_head WHERE singleton_key=1 FOR SHARE;
 SELECT * INTO pin FROM generation_create_contract_pin WHERE application_deployment_epoch=dh.application_deployment_epoch;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0002',MESSAGE='GENERATION_CONTRACT_PIN_UNRESOLVED';END IF;
 IF pin.contract_digest IS DISTINCT FROM p_operation_contract_digest THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_CONTRACT_PIN_MISMATCH';
 END IF;
 BEGIN
  IF NOT(convert_from(p_execution_descriptor_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) THEN
   RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='GENERATION_DESCRIPTOR_ENCODING_INVALID';
  END IF;
  descriptor=convert_from(p_execution_descriptor_bytes,'UTF8')::jsonb;
 EXCEPTION WHEN SQLSTATE '22021' OR SQLSTATE '22P02' THEN
  RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='GENERATION_DESCRIPTOR_ENCODING_INVALID';
 END;
 IF jsonb_typeof(descriptor->'clientKeyDigest')<>'string' OR octet_length(descriptor->>'clientKeyDigest') IS DISTINCT FROM 71 OR descriptor->>'clientKeyDigest' !~ '^sha256:[0-9a-f]{64}$' THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_DESCRIPTOR_KEY_DIGEST_INVALID';
 END IF;
 expected_descriptor=jsonb_build_object('callerAuthorityKind','OWNER_FULL','clientKeyDigest',descriptor->>'clientKeyDigest','operationContractId',pin.operation_id,'operationContractRevision',pin.operation_contract_revision,'stableBusinessTargetKey','CREATE_ROOT:generation_job','stableCallerObjectId',a.owner_id::text,'stableCallerRevisionId',NULL);
 IF descriptor IS DISTINCT FROM expected_descriptor THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_DESCRIPTOR_PIN_BINDING_MISMATCH';
 END IF;
 -- The pinned seven-field mask contains only strings and null. Produce exact
 -- lexicographic-key UTF8 bytes, no jsonb::text ordering/whitespace assumptions.
 expected_descriptor_bytes=convert_to('{"callerAuthorityKind":"OWNER_FULL","clientKeyDigest":'||to_json(descriptor->>'clientKeyDigest')::text||',"operationContractId":'||to_json(pin.operation_id)::text||',"operationContractRevision":'||to_json(pin.operation_contract_revision)::text||',"stableBusinessTargetKey":"CREATE_ROOT:generation_job","stableCallerObjectId":'||to_json(a.owner_id::text)::text||',"stableCallerRevisionId":null}','UTF8');
 IF p_execution_descriptor_bytes IS DISTINCT FROM expected_descriptor_bytes THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_DESCRIPTOR_NONCANONICAL';
 END IF;
 IF dh.platform_incarnation_id<>pi.platform_incarnation_id THEN
  RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='GENERATION_CONTEXT_INCARNATION_MISMATCH';
 END IF;
 IF a.access_channel='OWNER_API_KEY' THEN
  SELECT credential_version,fingerprint INTO STRICT api.credential_version,api.fingerprint FROM owner_api_credential WHERE singleton_key=1 FOR SHARE;
 END IF;
 SELECT id,session_epoch INTO STRICT o.id,o.session_epoch FROM owner_identity WHERE singleton_key=1 AND id=a.owner_id FOR SHARE;
 now_at=clock_timestamp();
 IF a.accepted_at>now_at THEN
  RAISE EXCEPTION USING ERRCODE='28000',MESSAGE='GENERATION_AUTH_RECEIPT_FUTURE';
 END IF;
 IF a.access_channel='OWNER_SESSION' THEN
  SELECT owner_identity_id,lookup_digest,session_epoch,revoked_at,expires_at INTO STRICT s.owner_identity_id,s.lookup_digest,s.session_epoch,s.revoked_at,s.expires_at FROM owner_session WHERE id=a.session_id FOR SHARE;
  IF s.owner_identity_id<>o.id OR s.lookup_digest<>a.session_lookup_digest
     OR s.session_epoch<>a.session_epoch OR s.session_epoch<>o.session_epoch
     OR s.revoked_at IS NOT NULL OR s.expires_at<=now_at THEN
   RAISE EXCEPTION USING ERRCODE='28000',MESSAGE='GENERATION_SESSION_AUTH_STALE';
  END IF;
 ELSE
  IF api.credential_version<>a.api_credential_version
     OR api.fingerprint<>a.api_credential_fingerprint THEN
   RAISE EXCEPTION USING ERRCODE='28000',MESSAGE='GENERATION_API_AUTH_STALE';
  END IF;
 END IF;
 INSERT INTO generation_create_trusted_context
 (id,owner_id,authentication_acceptance_id,initiating_access_channel,
 platform_incarnation_id,application_deployment_epoch,operation_contract_digest,
 client_request_digest,execution_descriptor_bytes,execution_descriptor_digest,accepted_at)
 VALUES(gen_random_uuid(),o.id,a.id,a.access_channel,pi.platform_incarnation_id,
 dh.application_deployment_epoch,p_operation_contract_digest,p_client_request_digest,
 p_execution_descriptor_bytes,sha256(p_execution_descriptor_bytes),now_at)
 RETURNING * INTO c;
 RETURN c;
END;
$$;
-- Persist context before dispatch; main mutation still rechecks current heads,
-- recovery, idempotency and own admission under its canonical transaction locks.
-- No MFA requirement or new scope/role business permission is added to API-key use.
-- The SQL constructor does not implement session/API token hashing; authenticating
-- token material belongs to the canonical authentication service, with acceptance
-- INSERT restricted to that writer. Test receipts prove consuming current records,
-- not deployed service credential verification.

REVOKE ALL ON FUNCTION kcml_generation_create_context_v1(uuid,bytea,bytea,bytea) FROM PUBLIC;
-- Infrastructure PostgreSQL groups (§51.2), never business roles or OWNER scopes.
-- Deployment migrator alone installs groups/functions in a controlled schema.
DO $$BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_generation_context_builder') THEN CREATE ROLE kcml_generation_context_builder NOLOGIN;END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_authentication_writer') THEN CREATE ROLE kcml_authentication_writer NOLOGIN;END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_domain_writer') THEN CREATE ROLE kcml_domain_writer NOLOGIN;END IF;
END$$;
DO $$BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname IN('kcml_generation_context_builder','kcml_authentication_writer','kcml_domain_writer') AND (rolcanlogin OR rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls)) THEN
 RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='GENERATION_INFRA_ROLE_PROFILE_INVALID';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid WHERE r.rolname='kcml_generation_context_builder') THEN
 RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='GENERATION_BUILDER_ROLE_MEMBERSHIP_FORBIDDEN';
 END IF;
END$$;
DO $$DECLARE s text=current_schema();BEGIN
 EXECUTE format('REVOKE CREATE ON SCHEMA %I FROM PUBLIC,kcml_domain_writer,kcml_authentication_writer,kcml_generation_context_builder',s);
 EXECUTE format('GRANT USAGE ON SCHEMA %I TO kcml_generation_context_builder,kcml_authentication_writer,kcml_domain_writer',s);
 EXECUTE format('GRANT SELECT,INSERT ON %I.generation_create_authentication_acceptance TO kcml_authentication_writer',s);
 -- Canonical authentication producer only: completed password/MFA session issuance
 -- and actual session/API token verification are service logic, never client flags.
 EXECUTE format('GRANT SELECT ON %I.owner_identity,%I.owner_session,%I.owner_api_credential TO kcml_authentication_writer',s,s,s);
 EXECUTE format('GRANT INSERT ON %I.owner_session TO kcml_authentication_writer',s);
 EXECUTE format('GRANT UPDATE(last_seen_at,revoked_at,reauthenticated_at) ON %I.owner_session TO kcml_authentication_writer',s);

 EXECUTE format('GRANT SELECT ON %I.generation_create_authentication_acceptance,%I.generation_create_contract_pin TO kcml_generation_context_builder',s,s);
 EXECUTE format('GRANT SELECT(id,singleton_key,session_epoch) ON %I.owner_identity TO kcml_generation_context_builder',s);
 EXECUTE format('GRANT SELECT(id,owner_identity_id,lookup_digest,session_epoch,revoked_at,expires_at) ON %I.owner_session TO kcml_generation_context_builder',s);
 EXECUTE format('GRANT SELECT(singleton_key,credential_version,fingerprint) ON %I.owner_api_credential TO kcml_generation_context_builder',s);
 EXECUTE format('GRANT SELECT(singleton_key,platform_incarnation_id) ON %I.platform_incarnation TO kcml_generation_context_builder',s);
 EXECUTE format('GRANT SELECT(singleton_key,platform_incarnation_id,application_deployment_epoch) ON %I.application_deployment_head TO kcml_generation_context_builder',s);
 -- PostgreSQL row-lock SELECT needs UPDATE privilege. These groups cannot LOGIN;
 -- domain/auth writers have no membership in builder, so only reviewed function
 -- executes with these privileges. The function does not update these tables.
 EXECUTE format('GRANT UPDATE(id) ON %I.owner_identity,%I.owner_session TO kcml_generation_context_builder',s,s);
 EXECUTE format('GRANT UPDATE(singleton_key) ON %I.owner_api_credential,%I.platform_incarnation,%I.application_deployment_head TO kcml_generation_context_builder',s,s,s);
 EXECUTE format('GRANT SELECT,INSERT ON %I.generation_create_trusted_context TO kcml_generation_context_builder',s);
 EXECUTE format('ALTER FUNCTION %I.kcml_generation_create_context_v1(uuid,bytea,bytea,bytea) OWNER TO kcml_generation_context_builder',s);
 EXECUTE format('REVOKE ALL ON FUNCTION %I.kcml_generation_create_context_v1(uuid,bytea,bytea,bytea) FROM PUBLIC',s);
 EXECUTE format('GRANT EXECUTE ON FUNCTION %I.kcml_generation_create_context_v1(uuid,bytea,bytea,bytea) TO kcml_domain_writer',s);
END$$;
-- No membership grants in the builder role; no generated-handler DB credentials.
-- Login-service membership is deployment-managed and never an OWNER permission.
-- Auth writer acceptance still requires the actual canonical token verifier;
-- INSERT privilege is not a semantic proof of completed session/MFA authentication.
-- Apply after exact root and trusted context resources exist; no external stubs.
ALTER TABLE generation_job ADD CONSTRAINT generation_job_context_owner_channel
 FOREIGN KEY(initiating_execution_context_id,owner_id,initiating_access_channel)
 REFERENCES generation_create_trusted_context(id,owner_id,initiating_access_channel)
 ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
-- Scoped technical links: §§49.3–49.5. No generation-only FK on a shared
-- domain_command column. Non-generation operations retain their own context
-- and argument-snapshot obligations; this table does not authorize their use.
ALTER TABLE domain_command ADD CONSTRAINT fk_command_owner
 FOREIGN KEY(owner_id) REFERENCES owner_identity(id) ON DELETE RESTRICT;
CREATE TABLE generation_create_command_binding (
 logical_operation_id uuid PRIMARY KEY REFERENCES domain_command(logical_operation_id)
   ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
 trusted_context_id uuid NOT NULL REFERENCES generation_create_trusted_context(id)
   ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
 argument_snapshot_id uuid NOT NULL REFERENCES generation_job_initial_request_snapshot(snapshot_id)
   ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
);
CREATE FUNCTION kcml_generation_command_context_consistency_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE d public.domain_command; c public.generation_create_trusted_context;
 s public.generation_job_initial_request_snapshot; b public.generation_create_command_binding;
BEGIN
 SELECT * INTO d FROM public.domain_command WHERE logical_operation_id=NEW.logical_operation_id;
 SELECT * INTO b FROM public.generation_create_command_binding WHERE logical_operation_id=NEW.logical_operation_id;
 IF d.operation_id<>'generation.job.create' THEN
  IF b.logical_operation_id IS NOT NULL THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_BINDING_OPERATION_KIND_INVALID';
  END IF;
  RETURN NULL;
 END IF;
 IF b.logical_operation_id IS NULL THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_COMMAND_TYPED_BINDING_REQUIRED';
 END IF;
 SELECT * INTO c FROM public.generation_create_trusted_context WHERE id=b.trusted_context_id;
 SELECT * INTO s FROM public.generation_job_initial_request_snapshot WHERE snapshot_id=b.argument_snapshot_id;
 IF c.id IS NULL OR s.snapshot_id IS NULL
 OR d.execution_context_id IS DISTINCT FROM b.trusted_context_id
 OR d.canonical_arguments_snapshot_id IS DISTINCT FROM b.argument_snapshot_id
 OR c.owner_id<>d.owner_id
 OR c.platform_incarnation_id<>d.platform_incarnation_id
 OR c.application_deployment_epoch<>d.application_deployment_epoch
 OR c.client_request_digest IS DISTINCT FROM d.request_digest
 OR c.execution_descriptor_bytes IS DISTINCT FROM d.execution_descriptor_bytes
 OR c.execution_descriptor_digest IS DISTINCT FROM d.execution_descriptor_digest
 OR d.operation_contract_revision IS DISTINCT FROM
   (convert_from(c.execution_descriptor_bytes,'UTF8')::jsonb->>'operationContractRevision')
 OR ('sha256:'||encode(d.client_key_digest,'hex')) IS DISTINCT FROM
   (convert_from(c.execution_descriptor_bytes,'UTF8')::jsonb->>'clientKeyDigest')
 OR d.scope_digest IS DISTINCT FROM sha256(c.execution_descriptor_bytes)
 OR s.logical_operation_id<>d.logical_operation_id OR s.job_id<>d.target_aggregate_id
 OR d.target_aggregate_kind<>'GENERATION_JOB' THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID';
 END IF;
 RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER generation_command_trusted_linkage
 AFTER INSERT OR UPDATE ON domain_command DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION kcml_generation_command_context_consistency_v1();
CREATE CONSTRAINT TRIGGER generation_binding_trusted_linkage
 AFTER INSERT ON generation_create_command_binding DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION kcml_generation_command_context_consistency_v1();
CREATE TRIGGER generation_binding_immutable BEFORE UPDATE OR DELETE ON generation_create_command_binding
 FOR EACH ROW EXECUTE FUNCTION kcml_create_record_immutable_v1();
-- Pending/failure-before-root command persistence is still a separate design
-- obligation. This bounded correction preserves the reviewed successful-create
-- path while removing unrelated operations' generation-specific requirements.
-- Exact source-bound descriptor/payload linkage in the same create transaction.
-- Requires domain_command exact context FK and actual generation root/snapshot.
CREATE FUNCTION kcml_generation_snapshot_schema_pin_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE c public.generation_create_trusted_context;
        p public.generation_create_contract_pin;
        d public.domain_command;
BEGIN
 SELECT * INTO STRICT d FROM public.domain_command WHERE logical_operation_id=NEW.logical_operation_id;
 IF d.operation_id<>'generation.job.create' THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_SNAPSHOT_WRONG_OPERATION';END IF;
 SELECT * INTO STRICT c FROM public.generation_create_trusted_context WHERE id=d.execution_context_id;
 SELECT * INTO STRICT p FROM public.generation_create_contract_pin
 WHERE application_deployment_epoch=c.application_deployment_epoch AND contract_digest=c.operation_contract_digest;
 IF NEW.request_schema_digest IS DISTINCT FROM p.domain_schema_digest
 OR NEW.request_schema_id IS DISTINCT FROM convert_from(p.domain_schema_bytes,'UTF8')::jsonb->>'$id' THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_SNAPSHOT_SCHEMA_PIN_MISMATCH';END IF;
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER generation_snapshot_schema_pin
 AFTER INSERT OR UPDATE ON generation_job_initial_request_snapshot
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
 EXECUTE FUNCTION kcml_generation_snapshot_schema_pin_v1();
