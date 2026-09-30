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
