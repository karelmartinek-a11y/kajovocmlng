-- Technical materialization of effective §8.12 immutable ACTIVE publication.
-- Requires exact canonical database/secret-profile-roots.sql first.
-- Publisher is a server/release principal, never a caller/model handler role.
DO $$BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='kcml_secret_profile_publisher') THEN
  CREATE ROLE kcml_secret_profile_publisher NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
 END IF;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_secret_profile_publisher' AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls OR rolinherit)) THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_PROFILE_PUBLISHER_ROLE_UNSAFE';
 END IF;
END$$;
CREATE TABLE kcml_secret_v1.profile_publication_archive (
 secret_type text NOT NULL,
 profile_id text NOT NULL,
 schema_id text NOT NULL,
 schema_digest bytea NOT NULL CHECK(octet_length(schema_digest)=32),
 schema_document_bytes bytea NOT NULL,
 source_ssot_digest bytea NOT NULL CHECK(octet_length(source_ssot_digest)=32),
 review_evidence_digest bytea NOT NULL CHECK(octet_length(review_evidence_digest)=32),
 review_evidence_bytes bytea NOT NULL,
 source_sections text[] NOT NULL CHECK(cardinality(source_sections)>0),
 publisher_principal name NOT NULL,
 published_at timestamptz NOT NULL,
 PRIMARY KEY(secret_type,profile_id,schema_digest),
 CHECK(schema_digest=sha256(schema_document_bytes)),
 CHECK(review_evidence_digest=sha256(review_evidence_bytes)),
 FOREIGN KEY(secret_type,profile_id,schema_digest) REFERENCES kcml_secret_v1.secret_value_profile_registry(secret_type,profile_id,schema_digest) DEFERRABLE INITIALLY DEFERRED
);
CREATE FUNCTION kcml_secret_v1.profile_publication_archive_immutable() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog AS $$BEGIN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_PROFILE_PUBLICATION_IMMUTABLE';
END$$;
CREATE TRIGGER immutable_publication BEFORE UPDATE OR DELETE ON kcml_secret_v1.profile_publication_archive
 FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.profile_publication_archive_immutable();
CREATE FUNCTION kcml_secret_v1.publish_profile_v1(
 p_type text,p_profile text,p_schema_id text,p_schema_bytes bytea,
 p_source_digest bytea,p_review_bytes bytea,p_sections text[])
 RETURNS bytea LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE sd bytea=sha256(p_schema_bytes); rd bytea=sha256(p_review_bytes);
 old kcml_secret_v1.profile_publication_archive%ROWTYPE;
BEGIN
 -- EXECUTE ACL is the authoritative capability. Source/review bytes are the
 -- trusted release producer's outputs, not caller validity flags.
 IF p_schema_bytes IS NULL OR p_review_bytes IS NULL OR octet_length(p_schema_bytes)=0
 OR octet_length(p_review_bytes)=0 OR p_source_digest IS NULL OR octet_length(p_source_digest)<>32
 OR p_sections IS NULL OR cardinality(p_sections)=0 OR array_position(p_sections,NULL) IS NOT NULL THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_PROFILE_PUBLICATION_INPUT_INVALID';
 END IF;
 -- This namespace lock only serializes this immutable first publication.
 PERFORM pg_advisory_xact_lock(hashtextextended('SECRET_PROFILE_PUBLICATION/'||p_type||'/'||p_profile||'/'||encode(sd,'hex'),0));
 SELECT * INTO old FROM kcml_secret_v1.profile_publication_archive
 WHERE secret_type=p_type AND profile_id=p_profile AND schema_digest=sd;
 IF FOUND THEN
  IF old.schema_id IS DISTINCT FROM p_schema_id OR old.schema_document_bytes IS DISTINCT FROM p_schema_bytes
  OR old.source_ssot_digest IS DISTINCT FROM p_source_digest OR old.review_evidence_bytes IS DISTINCT FROM p_review_bytes
  OR old.source_sections IS DISTINCT FROM p_sections THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_PROFILE_PUBLICATION_REPLAY_CONFLICT';
  END IF;
  RETURN sd;
 END IF;
 INSERT INTO kcml_secret_v1.secret_value_profile_registry VALUES
 (p_type,p_profile,p_schema_id,sd,p_schema_bytes,'ACTIVE',p_source_digest,rd,clock_timestamp());
 INSERT INTO kcml_secret_v1.profile_publication_archive VALUES
 (p_type,p_profile,p_schema_id,sd,p_schema_bytes,p_source_digest,rd,p_review_bytes,p_sections,session_user,clock_timestamp());
 RETURN sd;
END$$;
REVOKE ALL ON FUNCTION kcml_secret_v1.publish_profile_v1(text,text,text,bytea,bytea,bytea,text[]) FROM PUBLIC;
REVOKE ALL ON kcml_secret_v1.secret_value_profile_registry,kcml_secret_v1.profile_publication_archive FROM PUBLIC;
GRANT USAGE ON SCHEMA kcml_secret_v1 TO kcml_secret_profile_publisher;
GRANT EXECUTE ON FUNCTION kcml_secret_v1.publish_profile_v1(text,text,text,bytea,bytea,bytea,text[]) TO kcml_secret_profile_publisher;
-- No INSERT grant to publisher: only atomic checked immutable publication.
-- Owner/bootstrap superuser remains administrative authority, not application
-- caller. External actual evidence signer/release producer remains separately
-- required; SQL verifies bytes, identity and ACL, not semantic review by itself.
