-- §§12.54(read 7),49.4,51.10: exact frozen bytes; no current/schema URI fallback.
-- Install after generation-create-foundations.sql. Service role grants are external
-- to this bounded resource; PUBLIC cannot invoke or mutate the archive.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE generation_frozen_bundle_v1 (
 bundle_kind text NOT NULL CHECK(bundle_kind IN ('SCHEMA','DOMAIN_POLICY','AUTHORITY','POLICY_IMPLEMENTATION')),
 bundle_id text NOT NULL CHECK(length(bundle_id)>0),
 bundle_digest bytea NOT NULL CHECK(octet_length(bundle_digest)=32),
 exact_bytes bytea NOT NULL CHECK(octet_length(exact_bytes)>0),
 source_identity text NOT NULL CHECK(length(source_identity)>0),
 source_digest bytea NOT NULL CHECK(octet_length(source_digest)=32),
 created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 PRIMARY KEY(bundle_kind,bundle_id,bundle_digest),
 CHECK(digest(exact_bytes,'sha256')=bundle_digest)
);
CREATE TABLE generation_frozen_policy_binding_v1 (
 snapshot_id uuid PRIMARY KEY REFERENCES generation_job_initial_request_snapshot(snapshot_id)
 DEFERRABLE INITIALLY DEFERRED,
 logical_operation_id uuid NOT NULL UNIQUE REFERENCES domain_command(logical_operation_id)
 DEFERRABLE INITIALLY DEFERRED,
 schema_kind text NOT NULL DEFAULT 'SCHEMA' CHECK(schema_kind='SCHEMA'),
 schema_id text NOT NULL,
 schema_digest bytea NOT NULL CHECK(octet_length(schema_digest)=32),
 policy_kind text NOT NULL DEFAULT 'DOMAIN_POLICY' CHECK(policy_kind='DOMAIN_POLICY'),
 policy_id text NOT NULL,
 policy_digest bytea NOT NULL CHECK(octet_length(policy_digest)=32),
 dependency_closure jsonb NOT NULL CHECK(jsonb_typeof(dependency_closure)='array'),
 FOREIGN KEY(schema_kind,schema_id,schema_digest)
 REFERENCES generation_frozen_bundle_v1(bundle_kind,bundle_id,bundle_digest),
 FOREIGN KEY(policy_kind,policy_id,policy_digest)
 REFERENCES generation_frozen_bundle_v1(bundle_kind,bundle_id,bundle_digest)
);
CREATE FUNCTION kcml_archive_immutable_v1() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='FROZEN_ARCHIVE_IMMUTABLE';END$$;
CREATE TRIGGER frozen_bundle_immutable BEFORE UPDATE OR DELETE ON generation_frozen_bundle_v1
 FOR EACH ROW EXECUTE FUNCTION kcml_archive_immutable_v1();
CREATE TRIGGER frozen_binding_immutable BEFORE UPDATE OR DELETE ON generation_frozen_policy_binding_v1
 FOR EACH ROW EXECUTE FUNCTION kcml_archive_immutable_v1();
CREATE FUNCTION kcml_archive_snapshot_binding_v1() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE s generation_job_initial_request_snapshot%ROWTYPE; d jsonb; p jsonb; seen text[]:=ARRAY[]::text[];
BEGIN
 SELECT * INTO s FROM generation_job_initial_request_snapshot WHERE snapshot_id=NEW.snapshot_id FOR SHARE;
 IF NOT FOUND OR s.logical_operation_id IS DISTINCT FROM NEW.logical_operation_id
 OR s.request_schema_id IS DISTINCT FROM NEW.schema_id
 OR s.request_schema_digest IS DISTINCT FROM NEW.schema_digest THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='FROZEN_ARCHIVE_SNAPSHOT_BINDING_MISMATCH';END IF;
 SELECT convert_from(exact_bytes,'UTF8')::jsonb INTO p FROM generation_frozen_bundle_v1
 WHERE bundle_kind='DOMAIN_POLICY' AND bundle_id=NEW.policy_id AND bundle_digest=NEW.policy_digest;
 IF p->>'policyId' IS DISTINCT FROM NEW.policy_id OR p->>'operationId' IS DISTINCT FROM 'generation.job.create'
 OR (p->>'authorityDigest') IS NULL OR (p->>'authorityDigest') !~ '^sha256:[0-9a-f]{64}$'
 OR (p->>'implementationDigest') IS NULL OR (p->>'implementationDigest') !~ '^sha256:[0-9a-f]{64}$' THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='FROZEN_ARCHIVE_POLICY_DESCRIPTOR_INVALID';END IF;
 IF NOT EXISTS(SELECT 1 FROM generation_frozen_bundle_v1 WHERE bundle_kind='AUTHORITY' AND bundle_digest=decode(substr(p->>'authorityDigest',8),'hex'))
 OR NOT EXISTS(SELECT 1 FROM generation_frozen_bundle_v1 WHERE bundle_kind='POLICY_IMPLEMENTATION' AND bundle_digest=decode(substr(p->>'implementationDigest',8),'hex')) THEN
 RAISE EXCEPTION USING ERRCODE='23503',MESSAGE='FROZEN_ARCHIVE_POLICY_CONTENT_UNAVAILABLE';END IF;
 FOR d IN SELECT value FROM jsonb_array_elements(NEW.dependency_closure) LOOP
 IF jsonb_typeof(d) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(d))<>2
 OR NOT(d ? 'schemaId' AND d ? 'bundleDigest') OR jsonb_typeof(d->'schemaId') IS DISTINCT FROM 'string'
 OR jsonb_typeof(d->'bundleDigest') IS DISTINCT FROM 'string' OR (d->>'bundleDigest') !~ '^sha256:[0-9a-f]{64}$'
 OR (d->>'schemaId')=NEW.schema_id OR (d->>'schemaId')=ANY(seen) THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='FROZEN_ARCHIVE_DEPENDENCY_ADDRESS_INVALID';END IF;
 IF NOT EXISTS(SELECT 1 FROM generation_frozen_bundle_v1 WHERE bundle_kind='SCHEMA'
 AND bundle_id=d->>'schemaId' AND bundle_digest=decode(substr(d->>'bundleDigest',8),'hex')) THEN
 RAISE EXCEPTION USING ERRCODE='23503',MESSAGE='FROZEN_ARCHIVE_DEPENDENCY_UNAVAILABLE';END IF;
 seen:=array_append(seen,d->>'schemaId');
 END LOOP;
 RETURN NEW;
END$$;
CREATE CONSTRAINT TRIGGER frozen_snapshot_binding AFTER INSERT ON generation_frozen_policy_binding_v1
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_archive_snapshot_binding_v1();
CREATE FUNCTION kcml_archive_snapshot_required_v1() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM generation_frozen_policy_binding_v1 WHERE snapshot_id=NEW.snapshot_id) THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='FROZEN_ARCHIVE_REQUIRED';END IF;
 RETURN NEW;
END$$;
CREATE CONSTRAINT TRIGGER frozen_snapshot_archive_required AFTER INSERT ON generation_job_initial_request_snapshot
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_archive_snapshot_required_v1();
CREATE FUNCTION kcml_archive_publish_v1(p_kind text,p_id text,p_digest bytea,p_bytes bytea,p_source text,p_source_digest bytea)
 RETURNS void LANGUAGE plpgsql SECURITY INVOKER SET search_path=public,pg_catalog AS $$
DECLARE prior generation_frozen_bundle_v1%ROWTYPE;
BEGIN
 IF p_kind IS NULL OR p_id IS NULL OR p_digest IS NULL OR p_bytes IS NULL OR p_source IS NULL OR p_source_digest IS NULL
 OR digest(p_bytes,'sha256') IS DISTINCT FROM p_digest THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='FROZEN_ARCHIVE_PUBLISH_INVALID';END IF;
 INSERT INTO generation_frozen_bundle_v1 VALUES(p_kind,p_id,p_digest,p_bytes,p_source,p_source_digest,transaction_timestamp())
 ON CONFLICT DO NOTHING;
 SELECT * INTO STRICT prior FROM generation_frozen_bundle_v1 WHERE bundle_kind=p_kind AND bundle_id=p_id AND bundle_digest=p_digest FOR SHARE;
 IF prior.exact_bytes IS DISTINCT FROM p_bytes OR prior.source_identity IS DISTINCT FROM p_source OR prior.source_digest IS DISTINCT FROM p_source_digest THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='FROZEN_ARCHIVE_REPLAY_CONFLICT';END IF;
END$$;
REVOKE ALL ON generation_frozen_bundle_v1,generation_frozen_policy_binding_v1 FROM PUBLIC;
REVOKE ALL ON FUNCTION kcml_archive_publish_v1(text,text,bytea,bytea,text,bytea) FROM PUBLIC;

CREATE FUNCTION kcml_archive_read_v1(p_snapshot uuid,p_command uuid) RETURNS jsonb
 LANGUAGE sql SECURITY INVOKER SET search_path=public,pg_catalog AS $$
 SELECT jsonb_build_object('binding',jsonb_build_object('schemaId',b.schema_id,
 'schemaDigest','sha256:'||encode(b.schema_digest,'hex'),'policyId',b.policy_id,
 'policyDigest','sha256:'||encode(b.policy_digest,'hex'),'dependencies',b.dependency_closure),
 'bundles',(SELECT jsonb_object_agg('sha256:'||encode(a.bundle_digest,'hex'),encode(a.exact_bytes,'hex'))
 FROM generation_frozen_bundle_v1 a WHERE
 (a.bundle_kind='SCHEMA' AND ((a.bundle_id=b.schema_id AND a.bundle_digest=b.schema_digest)
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(b.dependency_closure)d WHERE d->>'schemaId'=a.bundle_id AND d->>'bundleDigest'='sha256:'||encode(a.bundle_digest,'hex'))))
 OR (a.bundle_kind='DOMAIN_POLICY' AND a.bundle_id=b.policy_id AND a.bundle_digest=b.policy_digest)
 OR (a.bundle_kind IN('AUTHORITY','POLICY_IMPLEMENTATION') AND 'sha256:'||encode(a.bundle_digest,'hex') IN
 ((convert_from(p.exact_bytes,'UTF8')::jsonb)->>'authorityDigest',(convert_from(p.exact_bytes,'UTF8')::jsonb)->>'implementationDigest'))
 )) FROM generation_frozen_policy_binding_v1 b JOIN generation_frozen_bundle_v1 p
 ON p.bundle_kind='DOMAIN_POLICY' AND p.bundle_id=b.policy_id AND p.bundle_digest=b.policy_digest
 WHERE b.snapshot_id=p_snapshot AND b.logical_operation_id=p_command;
$$;
REVOKE ALL ON FUNCTION kcml_archive_read_v1(uuid,uuid) FROM PUBLIC;
