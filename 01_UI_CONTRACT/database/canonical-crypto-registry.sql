-- Canonical §8.4/50.30 AES256GCM technical registry. This is NOT a systemd
-- producer proof. Installer/actual service invocation identity must be verified
-- before registration/use; a row or bool is not that proof.
CREATE TABLE canonical_authenticated_crypto_profile (
 profile_id text PRIMARY KEY,
 profile_bytes bytea NOT NULL CHECK(octet_length(profile_bytes)>0),
 profile_digest bytea NOT NULL UNIQUE CONSTRAINT canonical_crypto_profile_bytes_digest CHECK(octet_length(profile_digest)=32 AND profile_digest=sha256(profile_bytes)),
 algorithm text NOT NULL CHECK(algorithm='AES_256_GCM'),
 CHECK(convert_from(profile_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS)
);
CREATE TABLE canonical_master_key_generation (
 key_id text PRIMARY KEY CHECK(length(key_id)>0),
 key_fingerprint bytea NOT NULL UNIQUE CHECK(octet_length(key_fingerprint)=32),
 key_generation bigint NOT NULL CHECK(key_generation>=1),
 systemd_credential_name text NOT NULL CHECK(systemd_credential_name<>'' AND position('/'in systemd_credential_name)=0),
 exact_service_unit text NOT NULL CHECK(length(exact_service_unit)>0),
 crypto_profile_digest bytea NOT NULL REFERENCES canonical_authenticated_crypto_profile(profile_digest) ON DELETE RESTRICT,
 created_at timestamptz NOT NULL
);
CREATE TABLE canonical_protected_nonce_reservation (
 key_id text NOT NULL REFERENCES canonical_master_key_generation(key_id) ON DELETE RESTRICT,
 nonce bytea NOT NULL CHECK(octet_length(nonce)=12),
 purpose text NOT NULL CHECK(purpose IN('GENERATION_INITIAL_REQUEST','SECRET_IMMUTABLE_VERSION')),
 protected_object_id uuid NOT NULL,
 logical_operation_id uuid NOT NULL,
 authenticated_metadata_bytes bytea NOT NULL CHECK(octet_length(authenticated_metadata_bytes)>0),
 authenticated_metadata_digest bytea NOT NULL CHECK(octet_length(authenticated_metadata_digest)=32 AND authenticated_metadata_digest=sha256(authenticated_metadata_bytes)),
 ciphertext_digest bytea NOT NULL CHECK(octet_length(ciphertext_digest)=32),
 PRIMARY KEY(key_id,nonce),
 CONSTRAINT canonical_crypto_nonce_one_object UNIQUE(purpose,protected_object_id),
 CHECK(convert_from(authenticated_metadata_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CONSTRAINT canonical_crypto_nonce_purpose_binding CHECK(convert_from(authenticated_metadata_bytes,'UTF8')::jsonb->>'purpose' IS NOT DISTINCT FROM purpose),
 CONSTRAINT canonical_crypto_nonce_key_binding CHECK(convert_from(authenticated_metadata_bytes,'UTF8')::jsonb->>'keyId' IS NOT DISTINCT FROM key_id)
);
CREATE FUNCTION kcml_canonical_crypto_registry_immutable_v1()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='CANONICAL_CRYPTO_REGISTRY_IMMUTABLE';
END;
$$;
CREATE TRIGGER canonical_crypto_profile_immutable BEFORE UPDATE OR DELETE ON canonical_authenticated_crypto_profile FOR EACH ROW EXECUTE FUNCTION kcml_canonical_crypto_registry_immutable_v1();
CREATE TRIGGER canonical_master_key_immutable BEFORE UPDATE OR DELETE ON canonical_master_key_generation FOR EACH ROW EXECUTE FUNCTION kcml_canonical_crypto_registry_immutable_v1();
CREATE TRIGGER canonical_crypto_nonce_immutable BEFORE UPDATE OR DELETE ON canonical_protected_nonce_reservation FOR EACH ROW EXECUTE FUNCTION kcml_canonical_crypto_registry_immutable_v1();
REVOKE ALL ON canonical_authenticated_crypto_profile,canonical_master_key_generation,canonical_protected_nonce_reservation FROM PUBLIC;
REVOKE ALL ON FUNCTION kcml_canonical_crypto_registry_immutable_v1() FROM PUBLIC;
-- Producers reserve SAME transaction as immutable ciphertext persistence;
-- reads require exact reservation (purpose/objectID/keyID/nonce/ciphertext and
-- actual derived metadata bytes). No partial or alternative-purpose fallback.
-- Whole producer physical FKs and installer/service invocation ACL are mandatory
-- additional integration joins, not implied by these global uniqueness tables.
