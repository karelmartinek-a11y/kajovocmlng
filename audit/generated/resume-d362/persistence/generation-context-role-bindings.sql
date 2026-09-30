-- Infrastructure PostgreSQL groups (§51.2), never business roles or OWNER scopes.
-- Deployment migrator alone installs groups/functions in a controlled schema.
DO $$BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_generation_context_builder') THEN CREATE ROLE kcml_generation_context_builder NOLOGIN;END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_authentication_writer') THEN CREATE ROLE kcml_authentication_writer NOLOGIN;END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_domain_writer') THEN CREATE ROLE kcml_domain_writer NOLOGIN;END IF;
END$$;
DO $$BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname IN('kcml_generation_context_builder','kcml_authentication_writer','kcml_domain_writer') AND (rolcanlogin OR rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls)) THEN
 RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='GENERATION_INFRA_ROLE_PROFILE_INVALID';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid WHERE r.rolname='kcml_generation_context_builder') THEN
 RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='GENERATION_BUILDER_ROLE_MEMBERSHIP_FORBIDDEN';
 END IF;
END$$;
DO $$DECLARE s text=current_schema();BEGIN
 EXECUTE format('REVOKE CREATE ON SCHEMA %I FROM PUBLIC,kcml_domain_writer,kcml_authentication_writer,kcml_generation_context_builder',s);
 EXECUTE format('GRANT USAGE ON SCHEMA %I TO kcml_generation_context_builder,kcml_authentication_writer,kcml_domain_writer',s);
 EXECUTE format('GRANT SELECT,INSERT ON %I.generation_create_authentication_acceptance TO kcml_authentication_writer',s);
 -- Canonical authentication producer only: completed password/MFA session issuance
 -- and actual session/API token verification are service logic, never client flags.
 EXECUTE format('GRANT SELECT ON %I.owner_identity,%I.owner_session,%I.owner_api_credential TO kcml_authentication_writer',s,s,s);
 EXECUTE format('GRANT INSERT ON %I.owner_session TO kcml_authentication_writer',s);
 EXECUTE format('GRANT UPDATE(last_seen_at,revoked_at,reauthenticated_at) ON %I.owner_session TO kcml_authentication_writer',s);

 EXECUTE format('GRANT SELECT ON %I.generation_create_authentication_acceptance,%I.generation_create_contract_pin TO kcml_generation_context_builder',s,s);
 EXECUTE format('GRANT SELECT(id,singleton_key,session_epoch) ON %I.owner_identity TO kcml_generation_context_builder',s);
 EXECUTE format('GRANT SELECT(id,owner_identity_id,lookup_digest,session_epoch,revoked_at,expires_at) ON %I.owner_session TO kcml_generation_context_builder',s);
 EXECUTE format('GRANT SELECT(singleton_key,credential_version,fingerprint) ON %I.owner_api_credential TO kcml_generation_context_builder',s);
 EXECUTE format('GRANT SELECT(singleton_key,platform_incarnation_id) ON %I.platform_incarnation TO kcml_generation_context_builder',s);
 EXECUTE format('GRANT SELECT(singleton_key,platform_incarnation_id,application_deployment_epoch) ON %I.application_deployment_head TO kcml_generation_context_builder',s);
 -- PostgreSQL row-lock SELECT needs UPDATE privilege. These groups cannot LOGIN;
 -- domain/auth writers have no membership in builder, so only reviewed function
 -- executes with these privileges. The function does not update these tables.
 EXECUTE format('GRANT UPDATE(id) ON %I.owner_identity,%I.owner_session TO kcml_generation_context_builder',s,s);
 EXECUTE format('GRANT UPDATE(singleton_key) ON %I.owner_api_credential,%I.platform_incarnation,%I.application_deployment_head TO kcml_generation_context_builder',s,s,s);
 EXECUTE format('GRANT SELECT,INSERT ON %I.generation_create_trusted_context TO kcml_generation_context_builder',s);
 EXECUTE format('ALTER FUNCTION %I.kcml_generation_create_context_v1(uuid,bytea,bytea,bytea) OWNER TO kcml_generation_context_builder',s);
 EXECUTE format('REVOKE ALL ON FUNCTION %I.kcml_generation_create_context_v1(uuid,bytea,bytea,bytea) FROM PUBLIC',s);
 EXECUTE format('GRANT EXECUTE ON FUNCTION %I.kcml_generation_create_context_v1(uuid,bytea,bytea,bytea) TO kcml_domain_writer',s);
END$$;
-- No membership grants in the builder role; no generated-handler DB credentials.
-- Login-service membership is deployment-managed and never an OWNER permission.
-- Auth writer acceptance still requires the actual canonical token verifier;
-- INSERT privilege is not a semantic proof of completed session/MFA authentication.
