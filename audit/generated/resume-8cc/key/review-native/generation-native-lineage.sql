-- §§12.51–55/49.4/49.8/51.20: immutable exact native bytes selected by
-- the server under source-job/phase locks. Client declarations are not producers.
CREATE SCHEMA kcml_native_basis_v1;
CREATE TABLE kcml_native_basis_v1.schema_bundle (
 digest bytea PRIMARY KEY CHECK(octet_length(digest)=32 AND digest=sha256(exact_bytes)),
 schema_id text NOT NULL,exact_bytes bytea NOT NULL,
 CHECK(convert_from(exact_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(exact_bytes,'UTF8')::jsonb->>'$id'=schema_id)
);
CREATE TABLE kcml_native_basis_v1.record (
 record_id text PRIMARY KEY,source_job_id uuid NOT NULL REFERENCES generation_job(id),
 owner_id uuid NOT NULL REFERENCES owner_identity(id),content_digest bytea NOT NULL,
 exact_bytes bytea NOT NULL,schema_bundle_digest bytea,
 schema_id text,definition text,artifact_ref bytea,publication_receipt_id text,artifact_kind text CHECK(artifact_kind IS NULL OR artifact_kind IN('JSON_SCHEMA_BUNDLE','MONITORING_EVIDENCE')),
 CHECK(octet_length(content_digest)=32 AND content_digest=sha256(exact_bytes)),
 FOREIGN KEY(schema_bundle_digest) REFERENCES kcml_native_basis_v1.schema_bundle(digest),
 CHECK((schema_bundle_digest IS NULL AND schema_id IS NULL AND definition IS NULL)
 OR(schema_bundle_digest IS NOT NULL AND schema_id IS NOT NULL AND definition IS NOT NULL))
);
CREATE TABLE kcml_native_basis_v1.child_lineage (
 child_job_id uuid PRIMARY KEY REFERENCES generation_job(id) DEFERRABLE INITIALLY DEFERRED,
 logical_operation_id uuid UNIQUE NOT NULL REFERENCES domain_command(logical_operation_id) DEFERRABLE INITIALLY DEFERRED,
 trusted_context_id uuid NOT NULL REFERENCES generation_create_trusted_context(id),
 source_job_id uuid NOT NULL REFERENCES generation_job(id),phase_run_id uuid NOT NULL,
 body_digest bytea NOT NULL CHECK(octet_length(body_digest)=32),
 lineage_digest bytea NOT NULL CHECK(lineage_digest=sha256(exact_lineage)),
 exact_lineage bytea NOT NULL,
 acceptance_xid xid8 NOT NULL DEFAULT pg_current_xact_id(),
 FOREIGN KEY(child_job_id) REFERENCES kcml_retry_v1.child_scan(child_job_id) DEFERRABLE INITIALLY DEFERRED,
 CHECK(convert_from(exact_lineage,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS)
);
CREATE FUNCTION kcml_native_basis_v1.immutable() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN RAISE EXCEPTION 'GENERATION_NATIVE_BASIS_IMMUTABLE' USING ERRCODE='23514';END$$;
CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON kcml_native_basis_v1.schema_bundle FOR EACH ROW EXECUTE FUNCTION kcml_native_basis_v1.immutable();
CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON kcml_native_basis_v1.record FOR EACH ROW EXECUTE FUNCTION kcml_native_basis_v1.immutable();
CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON kcml_native_basis_v1.child_lineage FOR EACH ROW EXECUTE FUNCTION kcml_native_basis_v1.immutable();
CREATE FUNCTION kcml_native_basis_v1.closure() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE j generation_job;d domain_command;c generation_create_trusted_context;s kcml_retry_v1.child_scan;v jsonb;r jsonb;stored kcml_native_basis_v1.record;inv jsonb;phase_doc jsonb;authority_doc jsonb;required_id text;required_ids text[];
BEGIN
 SELECT * INTO j FROM generation_job WHERE id=NEW.child_job_id;
 SELECT * INTO d FROM domain_command WHERE logical_operation_id=NEW.logical_operation_id;
 SELECT * INTO c FROM generation_create_trusted_context WHERE id=NEW.trusted_context_id;
 SELECT * INTO s FROM kcml_retry_v1.child_scan WHERE child_job_id=NEW.child_job_id;
 IF j.id IS NULL OR d.logical_operation_id IS NULL OR c.id IS NULL OR s.child_job_id IS NULL
 OR j.kind<>'RETRY' OR j.parent_job_id<>NEW.source_job_id OR s.source_job_id<>NEW.source_job_id OR s.phase_run_id<>NEW.phase_run_id
 OR s.transaction_id<>NEW.acceptance_xid OR NEW.acceptance_xid<>pg_current_xact_id()
 OR (j.initiating_execution_context_id,d.execution_context_id,d.target_aggregate_id,j.initial_request_digest)
 IS DISTINCT FROM(c.id,c.id,j.id,NEW.body_digest)
 OR d.operation_id<>'generation.job.create' OR d.owner_id<>j.owner_id OR c.owner_id<>j.owner_id THEN
 RAISE EXCEPTION 'GENERATION_NATIVE_CHILD_ATOMIC_LINEAGE_INVALID' USING ERRCODE='23514';END IF;
 v=convert_from(NEW.exact_lineage,'UTF8')::jsonb;
 IF (SELECT count(*) FROM jsonb_object_keys(v))<>5 OR NOT v ?& ARRAY['basis','inventoryDigest','inventoryBytesHex','sourceSpecificationDigest','childSpecificationDigest']
 OR jsonb_typeof(v->'basis'->'frozenInputs')IS DISTINCT FROM 'array' OR jsonb_typeof(v->'basis'->'frozenSchemaBundleDigests')IS DISTINCT FROM 'array'
 OR sha256(decode(v->>'inventoryBytesHex','hex')) IS DISTINCT FROM decode(substr(v->>'inventoryDigest',8),'hex') THEN
 RAISE EXCEPTION 'GENERATION_NATIVE_LINEAGE_MASK_INVALID' USING ERRCODE='23514';END IF;
 inv=convert_from(decode(v->>'inventoryBytesHex','hex'),'UTF8')::jsonb;
 IF (inv->>'jobId',inv->>'phaseRunId',inv->>'phaseRunDigest') IS DISTINCT FROM(NEW.source_job_id::text,NEW.phase_run_id::text,'sha256:'||encode(s.source_phase_digest,'hex')) THEN
 RAISE EXCEPTION 'GENERATION_NATIVE_LINEAGE_INVENTORY_INVALID' USING ERRCODE='23514';END IF;
 SELECT convert_from(source_bytes,'UTF8')::jsonb INTO phase_doc FROM kcml_retry_v1.phase WHERE phase_run_id=NEW.phase_run_id;
 SELECT convert_from(exact_bytes,'UTF8')::jsonb INTO authority_doc FROM kcml_native_basis_v1.record
 WHERE record_id=phase_doc->>'authorityId' AND content_digest=decode(substr(phase_doc->>'authorityDigest',8),'hex');
 IF authority_doc IS NULL OR authority_doc->>'sourceJobId'<>NEW.source_job_id::text
 OR authority_doc->>'specificationDigest'<>phase_doc->>'specificationDigest' THEN
 RAISE EXCEPTION 'GENERATION_NATIVE_LINEAGE_AUTHORITY_INVALID' USING ERRCODE='23514';END IF;
 required_ids=ARRAY[NEW.phase_run_id::text,phase_doc->>'planId',phase_doc->>'authorityId',
 authority_doc->>'specificationRevisionId',authority_doc->>'ownerApprovalEventId',phase_doc->>'resultDigest'];
 FOREACH required_id IN ARRAY required_ids LOOP
 IF required_id IS NULL OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(v->'basis'->'frozenInputs') entry WHERE entry->>'recordId'=required_id) THEN
 RAISE EXCEPTION 'GENERATION_NATIVE_LINEAGE_SOURCE_COVERAGE_INVALID' USING ERRCODE='23514';END IF;
 END LOOP;
 FOR r IN SELECT value FROM jsonb_array_elements(v->'basis'->'frozenInputs') LOOP
 SELECT * INTO stored FROM kcml_native_basis_v1.record WHERE record_id=r->>'recordId';
 IF stored.record_id IS NULL OR stored.source_job_id<>NEW.source_job_id OR stored.owner_id<>j.owner_id
 OR r->>'contentDigest' IS DISTINCT FROM 'sha256:'||encode(stored.content_digest,'hex')
 OR r->'schema' IS DISTINCT FROM jsonb_build_object('schemaId',stored.schema_id,'bundleDigest','sha256:'||encode(stored.schema_bundle_digest,'hex'),'definition',stored.definition)
 OR NOT(v->'basis'->'frozenSchemaBundleDigests' ? ('sha256:'||encode(stored.schema_bundle_digest,'hex'))) THEN
 RAISE EXCEPTION 'GENERATION_NATIVE_LINEAGE_RECORD_INVALID' USING ERRCODE='23514';END IF;
 END LOOP;
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER child_atomic_lineage AFTER INSERT ON kcml_native_basis_v1.child_lineage DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_native_basis_v1.closure();
REVOKE ALL ON SCHEMA kcml_native_basis_v1 FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA kcml_native_basis_v1 FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_native_basis_v1 FROM PUBLIC;
