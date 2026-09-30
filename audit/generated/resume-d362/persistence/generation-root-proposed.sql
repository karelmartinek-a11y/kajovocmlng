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
