-- §8.4/12.54/50.30/50.33 exact source/invocation receipt candidate.
-- SQL stores actual restricted observer receipts; rows do NOT themselves attest
-- systemd. Real installer/bus producer and service-role grants require fixtures.
ALTER TABLE canonical_master_key_generation ADD UNIQUE(key_id,key_generation,exact_service_unit);
CREATE TABLE canonical_encrypted_key_source_version (
 key_id text PRIMARY KEY REFERENCES canonical_master_key_generation(key_id) ON DELETE RESTRICT,
 encrypted_source_digest bytea NOT NULL CHECK(octet_length(encrypted_source_digest)=32),
 source_device bigint NOT NULL CHECK(source_device>=0),
 source_inode bigint NOT NULL CHECK(source_inode>0),
 source_uid integer NOT NULL CHECK(source_uid=0),
 source_mode integer NOT NULL CHECK(source_mode=384), -- octal0600
 installed_at timestamptz NOT NULL,
 UNIQUE(key_id,encrypted_source_digest)
);
CREATE TABLE canonical_key_invocation_receipt (
 key_id text NOT NULL,
 key_generation bigint NOT NULL CHECK(key_generation>=1),
 exact_service_unit text NOT NULL,
 invocation_id bytea NOT NULL CHECK(octet_length(invocation_id)=16 AND invocation_id<>decode(repeat('00',16),'hex')),
 main_pid bigint NOT NULL CHECK(main_pid>0),
 start_monotonic_usec bigint NOT NULL CHECK(start_monotonic_usec>0),
 manager_unique_owner text NOT NULL CHECK(manager_unique_owner ~ '^:[0-9]+\.[0-9]+$'),
 encrypted_source_digest bytea NOT NULL,
 observed_key_fingerprint bytea NOT NULL CHECK(octet_length(observed_key_fingerprint)=32),
 authorized_purposes text[] NOT NULL,
 confirmed_at timestamptz NOT NULL,
 PRIMARY KEY(key_id,invocation_id),
 CONSTRAINT key_receipt_key_generation_fkey FOREIGN KEY(key_id,key_generation,exact_service_unit) REFERENCES canonical_master_key_generation(key_id,key_generation,exact_service_unit) ON DELETE RESTRICT,
 CONSTRAINT key_receipt_encrypted_source_fkey FOREIGN KEY(key_id,encrypted_source_digest) REFERENCES canonical_encrypted_key_source_version(key_id,encrypted_source_digest) ON DELETE RESTRICT,
 CONSTRAINT key_receipt_purpose_mask CHECK(array_ndims(authorized_purposes)=1 AND array_lower(authorized_purposes,1)=1 AND cardinality(authorized_purposes) BETWEEN 1 AND 2 AND array_position(authorized_purposes,NULL) IS NULL AND authorized_purposes <@ ARRAY['GENERATION_INITIAL_REQUEST','SECRET_IMMUTABLE_VERSION']::text[]),
 CONSTRAINT key_receipt_purpose_unique CHECK(cardinality(authorized_purposes)=1 OR authorized_purposes[1]<>authorized_purposes[2])
);
CREATE FUNCTION kcml_key_invocation_fingerprint_v1() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM public.canonical_master_key_generation k WHERE k.key_id=NEW.key_id AND k.key_fingerprint=NEW.observed_key_fingerprint)
 THEN RAISE EXCEPTION 'CRYPTO_KEY_FINGERPRINT_MISMATCH' USING ERRCODE='23514';END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER key_invocation_fingerprint BEFORE INSERT ON canonical_key_invocation_receipt FOR EACH ROW EXECUTE FUNCTION kcml_key_invocation_fingerprint_v1();
CREATE TRIGGER encrypted_key_source_immutable BEFORE UPDATE OR DELETE ON canonical_encrypted_key_source_version FOR EACH ROW EXECUTE FUNCTION kcml_canonical_crypto_registry_immutable_v1();
CREATE TRIGGER key_invocation_receipt_immutable BEFORE UPDATE OR DELETE ON canonical_key_invocation_receipt FOR EACH ROW EXECUTE FUNCTION kcml_canonical_crypto_registry_immutable_v1();
REVOKE ALL ON canonical_encrypted_key_source_version,canonical_key_invocation_receipt FROM PUBLIC;
REVOKE ALL ON FUNCTION kcml_key_invocation_fingerprint_v1() FROM PUBLIC;
-- Deliberately no universal LOGIN grant or PUBLIC publisher function. Exact
-- installation role ACL plus actual observer→DB call path remains required.

DO $$DECLARE r record; name text; BEGIN
 FOREACH name IN ARRAY ARRAY['kcml_key_source_installer','kcml_key_invocation_publisher'] LOOP
  SELECT * INTO r FROM pg_roles WHERE rolname=name;
  IF FOUND THEN
   IF r.rolcanlogin OR r.rolsuper OR r.rolcreatedb OR r.rolcreaterole OR r.rolreplication OR r.rolbypassrls OR r.rolinherit
   THEN RAISE EXCEPTION 'CRYPTO_KEY_INSTALLATION_ROLE_UNSAFE' USING ERRCODE='42501';END IF;
  ELSE EXECUTE format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT',name);END IF;
 END LOOP;
END $$;
GRANT USAGE ON SCHEMA public TO kcml_key_source_installer,kcml_key_invocation_publisher;
GRANT SELECT,INSERT ON canonical_master_key_generation,canonical_encrypted_key_source_version TO kcml_key_source_installer;
GRANT SELECT ON canonical_authenticated_crypto_profile TO kcml_key_source_installer;
GRANT SELECT ON canonical_master_key_generation,canonical_encrypted_key_source_version TO kcml_key_invocation_publisher;
GRANT SELECT,INSERT ON canonical_key_invocation_receipt TO kcml_key_invocation_publisher;
GRANT EXECUTE ON FUNCTION kcml_key_invocation_fingerprint_v1() TO kcml_key_invocation_publisher;
-- No LOGIN membership/authentication is manufactured by this resource. Trusted
-- platform service-role membership and root installer transport remain exact
-- installation obligations. Generated/public/model roles get no grant.
