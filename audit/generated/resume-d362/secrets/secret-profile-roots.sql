-- Exact physical Secret roots; normative §§8.3/8.4/25.6/49.22.1/51.20.
-- Run in a dedicated database/schema. No OWNER credential/context/outbox stubs.
CREATE SCHEMA kcml_secret_v1;
CREATE TABLE kcml_secret_v1.secret_value_profile_registry (
 secret_type text NOT NULL,
 profile_id text NOT NULL,
 schema_id text NOT NULL,
 schema_digest bytea NOT NULL CHECK (octet_length(schema_digest)=32),
 schema_document_bytes bytea NOT NULL,
 activation_status text NOT NULL CHECK (activation_status='ACTIVE'),
 source_ssot_digest bytea NOT NULL CHECK (octet_length(source_ssot_digest)=32),
 review_evidence_digest bytea NOT NULL CHECK (octet_length(review_evidence_digest)=32),
 created_at timestamptz NOT NULL,
 PRIMARY KEY(secret_type,profile_id,schema_digest),
 CHECK (schema_digest=sha256(schema_document_bytes)),
 CHECK (profile_id IN ('OAUTH_CLIENT_SECRET_V1','OAUTH_BEARER_TOKEN_SET_V1','TOTP_BASE32_V1','X509_PEM_CHAIN_V1','PKCS8_PEM_PRIVATE_KEY_V1','DATABASE_USER_PASSWORD_V1','HTTP_COOKIE_JAR_V1','BROWSER_COOKIE_LOCAL_STORAGE_V1','SSH_PASSWORD_V1','SSH_OPENSSH_PRIVATE_KEY_V1')),
 CHECK ((secret_type='OAUTH_CLIENT' AND profile_id='OAUTH_CLIENT_SECRET_V1') OR
 (secret_type='OAUTH_TOKEN_SET' AND profile_id='OAUTH_BEARER_TOKEN_SET_V1') OR
 (secret_type='TOTP_SEED' AND profile_id='TOTP_BASE32_V1') OR
 (secret_type='CERTIFICATE' AND profile_id='X509_PEM_CHAIN_V1') OR
 (secret_type='PRIVATE_KEY' AND profile_id='PKCS8_PEM_PRIVATE_KEY_V1') OR
 (secret_type='DATABASE_CREDENTIAL' AND profile_id='DATABASE_USER_PASSWORD_V1') OR
 (secret_type='COOKIE_JAR' AND profile_id='HTTP_COOKIE_JAR_V1') OR
 (secret_type='SESSION_STATE' AND profile_id='BROWSER_COOKIE_LOCAL_STORAGE_V1') OR
 (secret_type='SSH_CREDENTIAL' AND profile_id IN ('SSH_PASSWORD_V1','SSH_OPENSSH_PRIVATE_KEY_V1'))),
 CHECK (schema_id='urn:kcml:secret-profile-handoffs:1#/$defs/'||profile_id)
);
CREATE TABLE kcml_secret_v1.secret_record (
 id uuid PRIMARY KEY,
 stable_name text NOT NULL UNIQUE CHECK (stable_name<>''),
 display_name text NOT NULL CHECK (display_name<>''),
 description text,
 secret_type text NOT NULL CHECK (secret_type IN ('PASSWORD','API_KEY','BEARER_TOKEN','OAUTH_CLIENT','OAUTH_TOKEN_SET','TOTP_SEED','CERTIFICATE','PRIVATE_KEY','WEBHOOK_SECRET','DATABASE_CREDENTIAL','SESSION_STATE','COOKIE_JAR','SSH_CREDENTIAL','GENERIC_TEXT','GENERIC_BINARY')),
 purpose_kind text,
 target_object_id uuid,
 status text NOT NULL CHECK(status<>''), -- exact record-status lifecycle remains separately OPEN; no invented enum
 active_version_id uuid,
 state_version bigint NOT NULL CHECK(state_version>=0),
 secret_activation_epoch bigint NOT NULL CHECK(secret_activation_epoch>=0),
 tags text[] NOT NULL DEFAULT ARRAY[]::text[],
 group_name text,
 url text,
 username text,
 notes text,
 expires_at timestamptz,
 created_at timestamptz NOT NULL,
 updated_at timestamptz NOT NULL,
 deleted_at timestamptz,
 CHECK(updated_at>=created_at),
 CHECK(deleted_at IS NULL OR deleted_at>=created_at)
);
CREATE TABLE kcml_secret_v1.secret_version (
 id uuid PRIMARY KEY,
 secret_id uuid NOT NULL REFERENCES kcml_secret_v1.secret_record(id) ON DELETE RESTRICT,
 version_number bigint NOT NULL CHECK(version_number>0),
 secret_type text NOT NULL,
 value_representation text NOT NULL CHECK(value_representation IN ('RAW_UTF8','RAW_BINARY','PROFILE_JSON_V1')),
 profile_id text,
 value_schema_id text,
 value_schema_digest bytea,
 payload_format text NOT NULL CHECK(payload_format='EXACT_SECRET_BYTES_V1'),
 plaintext_byte_length bigint NOT NULL CHECK(plaintext_byte_length>0),
 ciphertext bytea NOT NULL CHECK(octet_length(ciphertext)>0),
 nonce bytea NOT NULL CHECK(octet_length(nonce)>0),
 algorithm text NOT NULL CHECK(algorithm<>''),
 key_id text NOT NULL CHECK(key_id<>''),
 fingerprint text NOT NULL CHECK(fingerprint<>''),
 original_import_bytes_digest bytea NOT NULL CHECK(octet_length(original_import_bytes_digest)=32),
 canonical_value_digest bytea NOT NULL CHECK(octet_length(canonical_value_digest)=32),
 lifecycle text NOT NULL CHECK(lifecycle IN ('CREATED','ACTIVE','RETIRED')),
 created_at timestamptz NOT NULL,
 activated_at timestamptz,
 retired_at timestamptz,
 creator_context_id uuid NOT NULL, -- external exact trusted-context FK added by coordinator, not a local substitute
 activation_logical_operation_id uuid, -- external domain_command FK added by coordinator
 UNIQUE(secret_id,version_number),
 UNIQUE(secret_id,id),
 UNIQUE(secret_id,secret_type,id),
 FOREIGN KEY(secret_type,profile_id,value_schema_digest) REFERENCES kcml_secret_v1.secret_value_profile_registry(secret_type,profile_id,schema_digest) ON DELETE RESTRICT,
 CHECK((value_representation='PROFILE_JSON_V1' AND profile_id IS NOT NULL AND value_schema_id IS NOT NULL AND value_schema_digest IS NOT NULL) OR (value_representation IN ('RAW_UTF8','RAW_BINARY') AND profile_id IS NULL AND value_schema_id IS NULL AND value_schema_digest IS NULL)),
 CHECK(value_schema_digest IS NULL OR octet_length(value_schema_digest)=32),
 CHECK(value_schema_id IS NULL OR value_schema_id='urn:kcml:secret-profile-handoffs:1#/$defs/'||profile_id),
 CHECK(value_representation<>'RAW_BINARY' OR secret_type='GENERIC_BINARY'),
 CHECK(value_representation<>'RAW_UTF8' OR secret_type IN ('PASSWORD','API_KEY','BEARER_TOKEN','WEBHOOK_SECRET','GENERIC_TEXT')),
 CHECK((lifecycle='CREATED' AND activated_at IS NULL AND retired_at IS NULL AND activation_logical_operation_id IS NULL) OR (lifecycle='ACTIVE' AND activated_at IS NOT NULL AND retired_at IS NULL AND activation_logical_operation_id IS NOT NULL) OR (lifecycle='RETIRED' AND activated_at IS NOT NULL AND retired_at IS NOT NULL AND activation_logical_operation_id IS NOT NULL)),
 CHECK(activated_at IS NULL OR activated_at>=created_at),
 CHECK(retired_at IS NULL OR retired_at>=activated_at)
);
ALTER TABLE kcml_secret_v1.secret_record ADD CONSTRAINT secret_active_version_owns_parent FOREIGN KEY(id,secret_type,active_version_id) REFERENCES kcml_secret_v1.secret_version(secret_id,secret_type,id) DEFERRABLE INITIALLY DEFERRED;
CREATE UNIQUE INDEX secret_one_active_version ON kcml_secret_v1.secret_version(secret_id) WHERE lifecycle='ACTIVE';
CREATE FUNCTION kcml_secret_v1.secret_crypto_immutable() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION USING ERRCODE='23514',CONSTRAINT='secret_version_immutable',MESSAGE='SECRET_VERSION_IMMUTABLE'; END IF;
 IF ROW(NEW.id,NEW.secret_id,NEW.version_number,NEW.secret_type,NEW.value_representation,NEW.profile_id,NEW.value_schema_id,NEW.value_schema_digest,NEW.payload_format,NEW.plaintext_byte_length,NEW.ciphertext,NEW.nonce,NEW.algorithm,NEW.key_id,NEW.fingerprint,NEW.original_import_bytes_digest,NEW.canonical_value_digest,NEW.created_at,NEW.creator_context_id)
 IS DISTINCT FROM ROW(OLD.id,OLD.secret_id,OLD.version_number,OLD.secret_type,OLD.value_representation,OLD.profile_id,OLD.value_schema_id,OLD.value_schema_digest,OLD.payload_format,OLD.plaintext_byte_length,OLD.ciphertext,OLD.nonce,OLD.algorithm,OLD.key_id,OLD.fingerprint,OLD.original_import_bytes_digest,OLD.canonical_value_digest,OLD.created_at,OLD.creator_context_id)
 THEN RAISE EXCEPTION USING ERRCODE='23514',CONSTRAINT='secret_version_crypto_immutable',MESSAGE='SECRET_VERSION_CRYPTO_IMMUTABLE'; END IF;
 IF NEW.lifecycle<>OLD.lifecycle AND NOT ((OLD.lifecycle IN ('CREATED','RETIRED') AND NEW.lifecycle='ACTIVE') OR (OLD.lifecycle='ACTIVE' AND NEW.lifecycle='RETIRED')) THEN RAISE EXCEPTION USING ERRCODE='23514',CONSTRAINT='secret_version_lifecycle_transition',MESSAGE='SECRET_VERSION_TRANSITION_INVALID'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER secret_version_immutable BEFORE UPDATE OR DELETE ON kcml_secret_v1.secret_version FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.secret_crypto_immutable();
CREATE FUNCTION kcml_secret_v1.secret_candidate_identity() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE parent_type text; profile_status text;
BEGIN
 SELECT r.secret_type INTO STRICT parent_type FROM kcml_secret_v1.secret_record r WHERE r.id=NEW.secret_id FOR SHARE;
 IF NEW.secret_type<>parent_type THEN RAISE EXCEPTION USING ERRCODE='23514',CONSTRAINT='secret_version_parent_type',MESSAGE='SECRET_PARENT_TYPE_MISMATCH'; END IF;
 IF NEW.lifecycle<>'CREATED' THEN RAISE EXCEPTION USING ERRCODE='23514',CONSTRAINT='secret_new_version_created',MESSAGE='SECRET_NEW_VERSION_NOT_CREATED'; END IF;
 IF NEW.value_representation='PROFILE_JSON_V1' THEN
  SELECT p.activation_status INTO profile_status FROM kcml_secret_v1.secret_value_profile_registry p WHERE p.secret_type=NEW.secret_type AND p.profile_id=NEW.profile_id AND p.schema_digest=NEW.value_schema_digest;
  IF profile_status IS DISTINCT FROM 'ACTIVE' THEN RAISE EXCEPTION USING ERRCODE='23514',CONSTRAINT='secret_profile_active',MESSAGE='SECRET_PROFILE_UNVERIFIED'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER secret_candidate_identity BEFORE INSERT ON kcml_secret_v1.secret_version FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.secret_candidate_identity();
CREATE FUNCTION kcml_secret_v1.secret_active_pointer_consistency() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE sid uuid; pointer uuid; active_count integer; active_id uuid;
BEGIN
 IF TG_TABLE_NAME='secret_record' THEN sid=NEW.id; ELSE sid=NEW.secret_id; END IF;
 SELECT active_version_id INTO pointer FROM kcml_secret_v1.secret_record WHERE id=sid;
 SELECT count(*),min(id::text)::uuid INTO active_count,active_id FROM kcml_secret_v1.secret_version WHERE secret_id=sid AND lifecycle='ACTIVE';
 IF (pointer IS NULL AND active_count<>0) OR (pointer IS NOT NULL AND (active_count<>1 OR pointer IS DISTINCT FROM active_id)) THEN RAISE EXCEPTION USING ERRCODE='23514',CONSTRAINT='secret_active_pointer_consistency',MESSAGE='SECRET_ACTIVE_POINTER_INCONSISTENT'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER secret_record_pointer_check AFTER INSERT OR UPDATE ON kcml_secret_v1.secret_record DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.secret_active_pointer_consistency();
CREATE CONSTRAINT TRIGGER secret_version_pointer_check AFTER INSERT OR UPDATE ON kcml_secret_v1.secret_version DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.secret_active_pointer_consistency();
CREATE FUNCTION kcml_secret_v1.secret_profile_immutable() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN RAISE EXCEPTION USING ERRCODE='23514',CONSTRAINT='secret_profile_definition_immutable',MESSAGE='SECRET_PROFILE_DEFINITION_IMMUTABLE'; END $$;
CREATE TRIGGER secret_profile_definition_immutable BEFORE UPDATE OR DELETE ON kcml_secret_v1.secret_value_profile_registry FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.secret_profile_immutable();
