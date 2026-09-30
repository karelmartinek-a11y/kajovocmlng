-- INTEGRATION PROPOSAL, deliberately not executed without coordinator roots.
-- Confirmed by generation_events: public.domain_command.logical_operation_id PK.
-- Native operation IDs verified against pinned operation-contracts.json.
ALTER TABLE kcml_secret_v1.secret_version
 ADD CONSTRAINT secret_activation_command_exact_fk
 FOREIGN KEY(activation_logical_operation_id)
 REFERENCES public.domain_command(logical_operation_id)
 ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
CREATE FUNCTION kcml_secret_v1.secret_activation_command_kind() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE stable_operation text; stable_name text;
BEGIN
 IF NEW.activation_logical_operation_id IS NULL THEN RETURN NULL; END IF;
 SELECT c.operation_id INTO STRICT stable_operation FROM public.domain_command c
 WHERE c.logical_operation_id=NEW.activation_logical_operation_id;
 SELECT r.stable_name INTO STRICT stable_name FROM kcml_secret_v1.secret_record r WHERE r.id=NEW.secret_id;
 IF stable_operation NOT IN ('secret.version.activate','secret.rotate','ownerApiKey.rotate') OR
 (stable_operation='ownerApiKey.rotate' AND stable_name<>'KCML_OWNER_API_KEY') OR
 (stable_name='KCML_OWNER_API_KEY' AND stable_operation<>'ownerApiKey.rotate') THEN
 RAISE EXCEPTION USING ERRCODE='23514',CONSTRAINT='secret_activation_command_kind',MESSAGE='SECRET_ACTIVATION_COMMAND_KIND_MISMATCH';
 END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER secret_activation_command_kind
 AFTER INSERT OR UPDATE ON kcml_secret_v1.secret_version
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
 EXECUTE FUNCTION kcml_secret_v1.secret_activation_command_kind();
-- creator_context_id MUST use the actual operation-scoped Secret trusted context.
-- public.generation_create_trusted_context is generation-only, not generic.
-- No guessed FK/stub is provided. Required exact key and server provenance remain OPEN.
-- Reserved OWNER key additionally requires owner_api_credential composite FK and
-- verifier/credential-version/epoch consistency under own §51.20 authority.
