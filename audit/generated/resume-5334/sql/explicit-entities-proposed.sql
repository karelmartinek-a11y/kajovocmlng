-- R9 exact physical closure for prose-declared entities.
CREATE TABLE operation_intent_head (
  operation_intent_id uuid PRIMARY KEY,
  current_revision_number bigint NOT NULL CHECK (current_revision_number >= 1),
  state text NOT NULL CHECK (state IN ('COMPILED','VALIDATED','SUPERSEDED','INVALIDATED')),
  state_version bigint NOT NULL DEFAULT 0 CHECK (state_version >= 0),
  validated_at timestamptz NULL,
  updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  CONSTRAINT fk_operation_intent_head_current_revision
    FOREIGN KEY (operation_intent_id,current_revision_number)
    REFERENCES operation_intent (id,revision_number) ON DELETE RESTRICT,
  CONSTRAINT ck_operation_intent_head_validated
    CHECK (state <> 'VALIDATED' OR validated_at IS NOT NULL)
);

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
