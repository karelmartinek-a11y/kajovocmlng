-- Scoped technical links: §§49.3–49.5. No generation-only FK on a shared
-- domain_command column. Non-generation operations retain their own context
-- and argument-snapshot obligations; this table does not authorize their use.
ALTER TABLE domain_command ADD CONSTRAINT fk_command_owner
 FOREIGN KEY(owner_id) REFERENCES owner_identity(id) ON DELETE RESTRICT;
CREATE TABLE generation_create_command_binding (
 logical_operation_id uuid PRIMARY KEY REFERENCES domain_command(logical_operation_id)
   ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
 trusted_context_id uuid NOT NULL REFERENCES generation_create_trusted_context(id)
   ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
 argument_snapshot_id uuid NOT NULL REFERENCES generation_job_initial_request_snapshot(snapshot_id)
   ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
);
CREATE FUNCTION kcml_generation_command_context_consistency_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE d public.domain_command; c public.generation_create_trusted_context;
 s public.generation_job_initial_request_snapshot; b public.generation_create_command_binding;
BEGIN
 SELECT * INTO d FROM public.domain_command WHERE logical_operation_id=NEW.logical_operation_id;
 SELECT * INTO b FROM public.generation_create_command_binding WHERE logical_operation_id=NEW.logical_operation_id;
 IF d.operation_id<>'generation.job.create' THEN
  IF b.logical_operation_id IS NOT NULL THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_BINDING_OPERATION_KIND_INVALID';
  END IF;
  RETURN NULL;
 END IF;
 IF b.logical_operation_id IS NULL THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_COMMAND_TYPED_BINDING_REQUIRED';
 END IF;
 SELECT * INTO c FROM public.generation_create_trusted_context WHERE id=b.trusted_context_id;
 SELECT * INTO s FROM public.generation_job_initial_request_snapshot WHERE snapshot_id=b.argument_snapshot_id;
 IF c.id IS NULL OR s.snapshot_id IS NULL
 OR d.execution_context_id IS DISTINCT FROM b.trusted_context_id
 OR d.canonical_arguments_snapshot_id IS DISTINCT FROM b.argument_snapshot_id
 OR c.owner_id<>d.owner_id
 OR c.platform_incarnation_id<>d.platform_incarnation_id
 OR c.application_deployment_epoch<>d.application_deployment_epoch
 OR c.client_request_digest IS DISTINCT FROM d.request_digest
 OR c.execution_descriptor_bytes IS DISTINCT FROM d.execution_descriptor_bytes
 OR c.execution_descriptor_digest IS DISTINCT FROM d.execution_descriptor_digest
 OR d.operation_contract_revision IS DISTINCT FROM
   (convert_from(c.execution_descriptor_bytes,'UTF8')::jsonb->>'operationContractRevision')
 OR ('sha256:'||encode(d.client_key_digest,'hex')) IS DISTINCT FROM
   (convert_from(c.execution_descriptor_bytes,'UTF8')::jsonb->>'clientKeyDigest')
 OR d.scope_digest IS DISTINCT FROM sha256(c.execution_descriptor_bytes)
 OR s.logical_operation_id<>d.logical_operation_id OR s.job_id<>d.target_aggregate_id
 OR d.target_aggregate_kind<>'GENERATION_JOB' THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID';
 END IF;
 RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER generation_command_trusted_linkage
 AFTER INSERT OR UPDATE ON domain_command DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION kcml_generation_command_context_consistency_v1();
CREATE CONSTRAINT TRIGGER generation_binding_trusted_linkage
 AFTER INSERT ON generation_create_command_binding DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION kcml_generation_command_context_consistency_v1();
CREATE TRIGGER generation_binding_immutable BEFORE UPDATE OR DELETE ON generation_create_command_binding
 FOR EACH ROW EXECUTE FUNCTION kcml_create_record_immutable_v1();
-- Pending/failure-before-root command persistence is still a separate design
-- obligation. This bounded correction preserves the reviewed successful-create
-- path while removing unrelated operations' generation-specific requirements.
