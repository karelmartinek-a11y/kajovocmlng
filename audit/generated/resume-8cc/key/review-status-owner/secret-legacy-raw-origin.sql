-- §8.12 immutable historical RAW preservation, not fresh-import permission.
-- Candidate migration: trusted original admission/archive publisher is an A
-- prerequisite. Exact encrypted original row/schema/receipt bytes remain available.
CREATE TABLE kcml_secret_v1.legacy_raw_origin (
 version_id uuid PRIMARY KEY, secret_id uuid NOT NULL,
 original_schema_id text NOT NULL, original_schema_bytes bytea NOT NULL,
 original_schema_digest bytea NOT NULL CHECK(original_schema_digest=sha256(original_schema_bytes)),
 original_source_identity text NOT NULL CHECK(original_source_identity<>''),
 original_source_digest bytea NOT NULL CHECK(octet_length(original_source_digest)=32),
 original_admission_receipt_bytes bytea NOT NULL CHECK(convert_from(original_admission_receipt_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 original_admission_receipt_digest bytea NOT NULL CHECK(original_admission_receipt_digest=sha256(original_admission_receipt_bytes)),
 original_immutable_row_bytes bytea NOT NULL CHECK(convert_from(original_immutable_row_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 original_immutable_row_digest bytea NOT NULL CHECK(original_immutable_row_digest=sha256(original_immutable_row_bytes)),
 published_at timestamptz NOT NULL, publisher_principal name NOT NULL,
 FOREIGN KEY(secret_id,version_id) REFERENCES kcml_secret_v1.secret_version(secret_id,id) DEFERRABLE INITIALLY DEFERRED,
 CHECK(octet_length(original_schema_bytes)>0),
 CHECK((convert_from(original_schema_bytes,'UTF8')::jsonb->>'$id') IS NOT DISTINCT FROM original_schema_id)
);
CREATE TRIGGER legacy_origin_immutable BEFORE UPDATE OR DELETE ON kcml_secret_v1.legacy_raw_origin FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.secret_profile_immutable();
CREATE FUNCTION kcml_secret_v1.legacy_raw_origin_consistency_v1() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE v kcml_secret_v1.secret_version;a kcml_secret_v1.legacy_raw_origin;m jsonb;r jsonb;
 n public.canonical_protected_nonce_reservation;
BEGIN
 IF TG_TABLE_NAME='secret_version' THEN v=NEW;ELSE SELECT * INTO STRICT v FROM kcml_secret_v1.secret_version WHERE id=NEW.version_id;END IF;
 IF v.value_representation='PROFILE_JSON_V1' OR (v.value_representation='RAW_BINARY' AND v.secret_type='GENERIC_BINARY') OR (v.value_representation='RAW_UTF8' AND v.secret_type IN('PASSWORD','API_KEY','BEARER_TOKEN','WEBHOOK_SECRET','GENERIC_TEXT')) THEN RETURN NULL;END IF;
 SELECT * INTO a FROM kcml_secret_v1.legacy_raw_origin WHERE version_id=v.id AND secret_id=v.secret_id;
 IF a.version_id IS NULL THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_LEGACY_RAW_ORIGIN_REQUIRED';END IF;
 m=convert_from(a.original_immutable_row_bytes,'UTF8')::jsonb;r=convert_from(a.original_admission_receipt_bytes,'UTF8')::jsonb;
 -- Exact immutable field projection; lifecycle/active pointer can change only
 -- under their existing guarded activation contract, never crypto/type/bytes.
 IF m IS DISTINCT FROM jsonb_build_object('versionId',v.id::text,'secretId',v.secret_id::text,'versionNumber',v.version_number::text,'secretType',v.secret_type,'representation',v.value_representation,'profileId',v.profile_id,'schemaId',v.value_schema_id,'schemaDigest',CASE WHEN v.value_schema_digest IS NULL THEN NULL ELSE encode(v.value_schema_digest,'hex') END,'payloadFormat',v.payload_format,'plaintextByteLength',v.plaintext_byte_length,'ciphertextHex',encode(v.ciphertext,'hex'),'nonceHex',encode(v.nonce,'hex'),'algorithm',v.algorithm,'keyId',v.key_id,'fingerprint',v.fingerprint,'originalImportBytesDigest',encode(v.original_import_bytes_digest,'hex'),'canonicalValueDigest',encode(v.canonical_value_digest,'hex'),'creatorContextId',v.creator_context_id::text) THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_LEGACY_IMMUTABLE_ROW_MISMATCH';END IF;
 SELECT * INTO n FROM public.canonical_protected_nonce_reservation WHERE key_id=v.key_id AND nonce=v.nonce AND purpose='SECRET_IMMUTABLE_VERSION' AND protected_object_id=v.id;
 IF n.key_id IS NULL OR n.ciphertext_digest IS DISTINCT FROM sha256(v.ciphertext) OR r IS DISTINCT FROM jsonb_build_object('receiptKind','ORIGINAL_RETAINED_SECRET_ADMISSION','secretId',v.secret_id::text,'versionId',v.id::text,'representation',v.value_representation,'secretType',v.secret_type,'originalSchemaId',a.original_schema_id,'originalSchemaDigest',encode(a.original_schema_digest,'hex'),'originalSourceDigest',encode(a.original_source_digest,'hex'),'originalCreatorContextId',v.creator_context_id::text,'originalLogicalOperationId',n.logical_operation_id::text,'originalImmutableRowDigest',encode(a.original_immutable_row_digest,'hex')) THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_LEGACY_RETAINED_ADMISSION_BINDING_MISMATCH';END IF;
 RETURN NULL;
END$$;
-- Replace only the two incompatible representation/type CHECKs by a deferred
-- exact original-origin invariant. All fresh native request/profile admission,
-- type/FK/immutability/lifecycle/active-pointer checks remain intact.
DO $$DECLARE x record;matched integer=0;BEGIN
 FOR x IN SELECT conname,pg_get_constraintdef(oid) AS expression FROM pg_constraint WHERE conrelid='kcml_secret_v1.secret_version'::regclass AND contype='c' LOOP
  IF x.expression LIKE 'CHECK (((value_representation <> ''RAW_BINARY''%' OR x.expression LIKE 'CHECK (((value_representation <> ''RAW_UTF8''%' THEN
   EXECUTE format('ALTER TABLE kcml_secret_v1.secret_version DROP CONSTRAINT %I',x.conname);matched=matched+1;
  END IF;
 END LOOP;
 IF matched<>2 THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_LEGACY_MIGRATION_BASELINE_UNEXPECTED';END IF;
END$$;
CREATE CONSTRAINT TRIGGER secret_version_raw_original_origin AFTER INSERT OR UPDATE ON kcml_secret_v1.secret_version DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.legacy_raw_origin_consistency_v1();
CREATE CONSTRAINT TRIGGER legacy_origin_exact_version AFTER INSERT ON kcml_secret_v1.legacy_raw_origin DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.legacy_raw_origin_consistency_v1();
REVOKE ALL ON kcml_secret_v1.legacy_raw_origin FROM PUBLIC;
REVOKE ALL ON FUNCTION kcml_secret_v1.legacy_raw_origin_consistency_v1() FROM PUBLIC;
-- No caller bool/legacy flag/import route can publish this table. Original
-- authentic source receipt/schema/archive producer and its restricted release/
-- restore principal must be verified before production migration activation.
DO $$BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_secret_legacy_restore_publisher') THEN
  CREATE ROLE kcml_secret_legacy_restore_publisher NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
 END IF;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_secret_legacy_restore_publisher' AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolinherit OR rolreplication OR rolbypassrls)) THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_LEGACY_RESTORE_ROLE_UNSAFE';END IF;
END$$;
GRANT USAGE ON SCHEMA kcml_secret_v1 TO kcml_secret_legacy_restore_publisher;
GRANT INSERT ON kcml_secret_v1.legacy_raw_origin TO kcml_secret_legacy_restore_publisher;
-- Original source/schema/receipt semantic authentication remains the restore
-- producer duty; INSERT capability is not that proof and cannot mark VERIFIED.
