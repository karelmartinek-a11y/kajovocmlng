-- Exact source-bound descriptor/payload linkage in the same create transaction.
-- Requires domain_command exact context FK and actual generation root/snapshot.
CREATE FUNCTION kcml_generation_snapshot_schema_pin_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE c public.generation_create_trusted_context;
        p public.generation_create_contract_pin;
        d public.domain_command;
BEGIN
 SELECT * INTO STRICT d FROM public.domain_command WHERE logical_operation_id=NEW.logical_operation_id;
 IF d.operation_id<>'generation.job.create' THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_SNAPSHOT_WRONG_OPERATION';END IF;
 SELECT * INTO STRICT c FROM public.generation_create_trusted_context WHERE id=d.execution_context_id;
 SELECT * INTO STRICT p FROM public.generation_create_contract_pin
 WHERE application_deployment_epoch=c.application_deployment_epoch AND contract_digest=c.operation_contract_digest;
 IF NEW.request_schema_digest IS DISTINCT FROM p.domain_schema_digest
 OR NEW.request_schema_id IS DISTINCT FROM convert_from(p.domain_schema_bytes,'UTF8')::jsonb->>'$id' THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_SNAPSHOT_SCHEMA_PIN_MISMATCH';END IF;
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER generation_snapshot_schema_pin
 AFTER INSERT OR UPDATE ON generation_job_initial_request_snapshot
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
 EXECUTE FUNCTION kcml_generation_snapshot_schema_pin_v1();
