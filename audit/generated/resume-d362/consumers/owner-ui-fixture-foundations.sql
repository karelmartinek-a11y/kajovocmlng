-- ISOLATED REVIEW FIXTURE ONLY: source-owned auth consuming columns, not complete authentication migrations.
CREATE TABLE owner_identity(id uuid PRIMARY KEY,singleton_key smallint UNIQUE CHECK(singleton_key=1),session_epoch bigint NOT NULL);
CREATE TABLE owner_session(id uuid PRIMARY KEY,owner_identity_id uuid NOT NULL,lookup_digest bytea NOT NULL,session_epoch bigint NOT NULL,revoked_at timestamptz,expires_at timestamptz NOT NULL);
CREATE TABLE owner_api_credential(singleton_key smallint PRIMARY KEY CHECK(singleton_key=1),credential_version bigint NOT NULL,fingerprint text NOT NULL);
CREATE TABLE platform_incarnation(singleton_key smallint PRIMARY KEY CHECK(singleton_key=1),platform_incarnation_id uuid NOT NULL);
CREATE TABLE application_deployment_head(singleton_key smallint PRIMARY KEY CHECK(singleton_key=1),platform_incarnation_id uuid NOT NULL,application_deployment_epoch bigint NOT NULL);
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
