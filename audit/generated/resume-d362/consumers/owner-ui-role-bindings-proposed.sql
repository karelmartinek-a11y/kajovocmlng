DO $$BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_owner_ui_builder') THEN CREATE ROLE kcml_owner_ui_builder NOLOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS;END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_owner_ui_input_validator') THEN CREATE ROLE kcml_owner_ui_input_validator NOLOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS;END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_owner_ui_dispatcher') THEN CREATE ROLE kcml_owner_ui_dispatcher NOLOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS;END IF;
END$$;
-- Existing reserved groups are validated, never silently altered. Any unsafe
-- attribute aborts before schema grants/ownership can create an authority path.
DO $$DECLARE name text; profile pg_catalog.pg_roles;BEGIN
 FOREACH name IN ARRAY ARRAY['kcml_owner_ui_builder','kcml_owner_ui_input_validator','kcml_owner_ui_dispatcher','kcml_authentication_writer','kcml_domain_writer'] LOOP
  SELECT * INTO profile FROM pg_catalog.pg_roles WHERE rolname=name;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='OWNER_UI_INFRASTRUCTURE_ROLE_MISSING';END IF;
  IF profile.rolcanlogin OR profile.rolsuper OR profile.rolcreaterole OR profile.rolcreatedb OR profile.rolreplication OR profile.rolbypassrls THEN
   RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='OWNER_UI_RESERVED_ROLE_PROFILE_UNSAFE';
  END IF;
 END LOOP;
END$$;
DO $$DECLARE s text=current_schema();BEGIN
 EXECUTE format('REVOKE CREATE ON SCHEMA %I FROM PUBLIC,kcml_owner_ui_builder,kcml_owner_ui_input_validator,kcml_owner_ui_dispatcher',s);
 EXECUTE format('GRANT USAGE ON SCHEMA %I TO kcml_owner_ui_builder,kcml_owner_ui_input_validator,kcml_owner_ui_dispatcher,kcml_authentication_writer,kcml_domain_writer',s);
 EXECUTE format('GRANT SELECT,INSERT ON %I.owner_ui_authentication_acceptance TO kcml_authentication_writer',s);
 EXECUTE format('GRANT SELECT,INSERT ON %I.owner_ui_validated_input TO kcml_owner_ui_input_validator',s);
 EXECUTE format('GRANT SELECT ON %I.owner_ui_dispatch_registry TO kcml_owner_ui_input_validator',s);
 EXECUTE format('GRANT SELECT ON %I.owner_ui_authentication_acceptance,%I.owner_ui_validated_input,%I.owner_ui_dispatch_registry,%I.owner_identity,%I.owner_session,%I.owner_api_credential,%I.platform_incarnation,%I.application_deployment_head,%I.domain_command TO kcml_owner_ui_builder',s,s,s,s,s,s,s,s,s);
 EXECUTE format('GRANT UPDATE(singleton_key) ON %I.owner_identity,%I.owner_api_credential,%I.platform_incarnation,%I.application_deployment_head TO kcml_owner_ui_builder',s,s,s,s);
 EXECUTE format('GRANT UPDATE(id) ON %I.owner_session TO kcml_owner_ui_builder',s);
 EXECUTE format('GRANT UPDATE(operation_id) ON %I.owner_ui_dispatch_registry TO kcml_owner_ui_builder',s);
 EXECUTE format('GRANT UPDATE(logical_operation_id) ON %I.domain_command TO kcml_owner_ui_builder',s);
 EXECUTE format('GRANT SELECT,INSERT ON %I.owner_ui_accepted_intent,%I.owner_ui_worker_context TO kcml_owner_ui_builder',s,s);
 EXECUTE format('ALTER FUNCTION %I.kcml_owner_ui_descriptor_bytes_v1(uuid,uuid,uuid,uuid) OWNER TO kcml_owner_ui_builder',s);
 EXECUTE format('REVOKE ALL ON FUNCTION %I.kcml_owner_ui_descriptor_bytes_v1(uuid,uuid,uuid,uuid) FROM PUBLIC',s);
 EXECUTE format('GRANT EXECUTE ON FUNCTION %I.kcml_owner_ui_descriptor_bytes_v1(uuid,uuid,uuid,uuid) TO kcml_domain_writer',s);
 EXECUTE format('ALTER FUNCTION %I.kcml_owner_ui_accept_v1(uuid,uuid,uuid) OWNER TO kcml_owner_ui_builder',s);
 EXECUTE format('ALTER FUNCTION %I.kcml_owner_ui_worker_context_v1(uuid) OWNER TO kcml_owner_ui_builder',s);
 EXECUTE format('REVOKE ALL ON FUNCTION %I.kcml_owner_ui_accept_v1(uuid,uuid,uuid) FROM PUBLIC',s);
 EXECUTE format('REVOKE ALL ON FUNCTION %I.kcml_owner_ui_worker_context_v1(uuid) FROM PUBLIC',s);
 EXECUTE format('GRANT EXECUTE ON FUNCTION %I.kcml_owner_ui_accept_v1(uuid,uuid,uuid) TO kcml_domain_writer',s);
 EXECUTE format('GRANT EXECUTE ON FUNCTION %I.kcml_owner_ui_worker_context_v1(uuid) TO kcml_owner_ui_dispatcher',s);
END$$;
-- Groups are infrastructure-only. They are never granted to model/generated
-- code or OWNER clients; credential-verifier and schema-validator service code
-- is the sole receipt producer. No wrapper accepts a caller authority boolean.
DO $$DECLARE s text=current_schema();BEGIN
 EXECUTE format('ALTER FUNCTION %I.kcml_owner_ui_validate_worker_context_v1(uuid,text,text) OWNER TO kcml_owner_ui_builder',s);
 EXECUTE format('REVOKE ALL ON FUNCTION %I.kcml_owner_ui_validate_worker_context_v1(uuid,text,text) FROM PUBLIC',s);
 EXECUTE format('GRANT EXECUTE ON FUNCTION %I.kcml_owner_ui_validate_worker_context_v1(uuid,text,text) TO kcml_owner_ui_dispatcher',s);
END$$;
