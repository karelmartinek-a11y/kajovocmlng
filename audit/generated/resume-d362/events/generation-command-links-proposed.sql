-- Apply AFTER coordinator integrates the exact trusted context and encrypted
-- snapshot resources from persistence agent. Dependencies are real roots,
-- never minimal test fixture stand-ins in canonical package.
ALTER TABLE domain_command ADD CONSTRAINT fk_command_owner
 FOREIGN KEY(owner_id) REFERENCES owner_identity(id) ON DELETE RESTRICT;
ALTER TABLE domain_command ADD CONSTRAINT fk_command_trusted_context
 FOREIGN KEY(execution_context_id) REFERENCES generation_create_trusted_context(id)
 ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE domain_command ADD CONSTRAINT fk_command_frozen_argument_snapshot
 FOREIGN KEY(canonical_arguments_snapshot_id) REFERENCES generation_job_initial_request_snapshot(snapshot_id)
 ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
CREATE FUNCTION kcml_generation_command_context_consistency_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE d public.domain_command; c public.generation_create_trusted_context; s public.generation_job_initial_request_snapshot;
BEGIN
 SELECT * INTO d FROM public.domain_command WHERE logical_operation_id=NEW.logical_operation_id;
 IF d.operation_id<>'generation.job.create' THEN RETURN NULL; END IF;
 SELECT * INTO c FROM public.generation_create_trusted_context WHERE id=d.execution_context_id;
 SELECT * INTO s FROM public.generation_job_initial_request_snapshot WHERE snapshot_id=d.canonical_arguments_snapshot_id;
 IF c.id IS NULL OR s.snapshot_id IS NULL OR c.owner_id<>d.owner_id
 OR c.platform_incarnation_id<>d.platform_incarnation_id OR c.application_deployment_epoch<>d.application_deployment_epoch
 OR c.client_request_digest IS DISTINCT FROM d.request_digest
 OR c.execution_descriptor_bytes IS DISTINCT FROM d.execution_descriptor_bytes
 OR c.execution_descriptor_digest IS DISTINCT FROM d.execution_descriptor_digest
 OR s.logical_operation_id<>d.logical_operation_id OR s.job_id<>d.target_aggregate_id
 OR d.target_aggregate_kind<>'GENERATION_JOB' THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID';
 END IF;
 RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER generation_command_trusted_linkage
 AFTER INSERT OR UPDATE ON domain_command DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION kcml_generation_command_context_consistency_v1();
