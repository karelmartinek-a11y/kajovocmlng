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
