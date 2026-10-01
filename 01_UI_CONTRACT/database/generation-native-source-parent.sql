-- §§49.4/49.8/51.6/51.20: this source-native schema copy belongs to the
-- exact source job archive. It does not replace global schema package authority.
-- Empty fresh installation only: no guessed parent/backfill of historical rows.
DO $$BEGIN
 IF EXISTS(SELECT 1 FROM kcml_native_basis_v1.schema_bundle) OR EXISTS(SELECT 1 FROM kcml_native_basis_v1.record) OR EXISTS(SELECT 1 FROM kcml_native_basis_v1.child_lineage) THEN
 RAISE EXCEPTION 'NATIVE_PARENT_MIGRATION_REQUIRES_EXPLICIT_EXISTING_ROW_PROVENANCE' USING ERRCODE='23514'; END IF;
END$$;
ALTER TABLE kcml_native_basis_v1.record DROP CONSTRAINT record_schema_bundle_digest_fkey;
ALTER TABLE kcml_native_basis_v1.schema_bundle DROP CONSTRAINT schema_bundle_pkey;
ALTER TABLE kcml_native_basis_v1.schema_bundle
 ADD COLUMN source_job_id uuid NOT NULL REFERENCES public.generation_job(id),
 ADD COLUMN primary_parent_uuid uuid GENERATED ALWAYS AS(source_job_id) STORED NOT NULL,
 ADD COLUMN lock_kind_ordinal integer GENERATED ALWAYS AS(154) STORED NOT NULL,
 ADD COLUMN lock_stable_id bytea GENERATED ALWAYS AS(digest) STORED NOT NULL,
 ADD PRIMARY KEY(source_job_id,digest);
ALTER TABLE kcml_native_basis_v1.record
 ADD CONSTRAINT record_scoped_schema_fk FOREIGN KEY(source_job_id,schema_bundle_digest) REFERENCES kcml_native_basis_v1.schema_bundle(source_job_id,digest),
 ADD COLUMN primary_parent_uuid uuid GENERATED ALWAYS AS(source_job_id) STORED NOT NULL,
 ADD COLUMN lock_kind_ordinal integer GENERATED ALWAYS AS(155) STORED NOT NULL,
 ADD COLUMN lock_stable_id text COLLATE "C" GENERATED ALWAYS AS(record_id) STORED NOT NULL;
ALTER TABLE kcml_native_basis_v1.child_lineage
 ADD COLUMN primary_parent_uuid uuid GENERATED ALWAYS AS(child_job_id) STORED NOT NULL,
 ADD COLUMN lock_kind_ordinal integer GENERATED ALWAYS AS(153) STORED NOT NULL,
 ADD COLUMN lock_stable_id bytea GENERATED ALWAYS AS(uuid_send(child_job_id)) STORED NOT NULL;
-- Ordinals are a root-reviewed proposed allocation; no runtime name inference.
