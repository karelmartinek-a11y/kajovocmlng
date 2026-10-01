-- §§12.51–55,49.4,51.2/51.10/51.20: deployment-owned packages and admitted publisher.
-- Additive; no change to successful/pre-root archive FKs or public OWNER authority.
DO $$BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_generation_archive_builder') THEN
 CREATE ROLE kcml_generation_archive_builder NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='kcml_generation_policy_installer') THEN
 CREATE ROLE kcml_generation_policy_installer NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;END IF;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname IN('kcml_generation_archive_builder','kcml_generation_policy_installer') AND
 (rolinherit OR rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_ROLE_PROFILE_INVALID' USING ERRCODE='55000';END IF;
 IF EXISTS(SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid WHERE r.rolname='kcml_generation_archive_builder') THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_BUILDER_MEMBERSHIP_FORBIDDEN' USING ERRCODE='55000';END IF;
END$$;
CREATE FUNCTION kcml_generation_policy_package_shape_v1(p jsonb) RETURNS boolean
 LANGUAGE plpgsql IMMUTABLE SET search_path=pg_catalog,public AS $$
DECLARE m jsonb;e jsonb;
BEGIN
 IF jsonb_typeof(p)<>'object' OR (SELECT array_agg(k ORDER BY k) FROM jsonb_object_keys(p)k) IS DISTINCT FROM ARRAY['entrypoints','members','packageId','requestPolicy','requestSchema','version'] OR p->>'packageId'<>'urn:kcml:generation:kind-policy-package:1' OR p->'version'<>'1'::jsonb THEN RETURN false;END IF;
 IF jsonb_typeof(p->'members') IS DISTINCT FROM 'array' OR jsonb_array_length(p->'members')=0 OR jsonb_typeof(p->'entrypoints') IS DISTINCT FROM 'array' OR jsonb_array_length(p->'entrypoints')<>1 THEN RETURN false;END IF;
 FOR m IN SELECT value FROM jsonb_array_elements(p->'members') LOOP
 IF jsonb_typeof(m)<>'object' OR (SELECT array_agg(k ORDER BY k) FROM jsonb_object_keys(m)k) IS DISTINCT FROM ARRAY['digest','id','kind'] OR jsonb_typeof(m->'kind') IS DISTINCT FROM 'string' OR jsonb_typeof(m->'digest') IS DISTINCT FROM 'string' OR m->>'kind' NOT IN('SCHEMA','DOMAIN_POLICY','AUTHORITY','POLICY_IMPLEMENTATION') OR jsonb_typeof(m->'id') IS DISTINCT FROM 'string' OR length(m->>'id')=0 OR m->>'digest' !~ '^sha256:[0-9a-f]{64}$' THEN RETURN false;END IF;
 END LOOP;
 IF (SELECT count(*) FROM jsonb_array_elements(p->'members'))<>(SELECT count(DISTINCT(value->>'kind',value->>'id'))FROM jsonb_array_elements(p->'members')) THEN RETURN false;END IF;
 IF jsonb_typeof(p->'requestSchema'->'schemaId') IS DISTINCT FROM 'string' OR jsonb_typeof(p->'requestSchema'->'bundleDigest') IS DISTINCT FROM 'string' OR (SELECT array_agg(k ORDER BY k)FROM jsonb_object_keys(p->'requestSchema')k) IS DISTINCT FROM ARRAY['bundleDigest','definition','schemaId'] OR p->'requestSchema'->'definition'<>'null'::jsonb OR p->'requestSchema'->>'bundleDigest' !~ '^sha256:[0-9a-f]{64}$' THEN RETURN false;END IF;
 IF jsonb_typeof(p->'requestPolicy'->'policyId') IS DISTINCT FROM 'string' OR jsonb_typeof(p->'requestPolicy'->'policyDigest') IS DISTINCT FROM 'string' OR (SELECT array_agg(k ORDER BY k)FROM jsonb_object_keys(p->'requestPolicy')k) IS DISTINCT FROM ARRAY['policyDigest','policyId'] OR p->'requestPolicy'->>'policyDigest' !~ '^sha256:[0-9a-f]{64}$' THEN RETURN false;END IF;
 e:=p->'entrypoints'->0;
 IF jsonb_typeof(e->'handlerId') IS DISTINCT FROM 'string' OR jsonb_typeof(e->'implementationId') IS DISTINCT FROM 'string' OR jsonb_typeof(e->'implementationDigest') IS DISTINCT FROM 'string' OR (SELECT array_agg(k ORDER BY k)FROM jsonb_object_keys(e)k) IS DISTINCT FROM ARRAY['dependencyDigests','handlerId','implementationDigest','implementationId','supportedKinds'] OR e->>'handlerId'<>'GENERATION_OWN_KIND_DISCUSSION_V1' OR e->>'implementationDigest' !~ '^sha256:[0-9a-f]{64}$' OR e->'supportedKinds'<>'["UPDATE","RETRY","REPAIR"]'::jsonb OR jsonb_typeof(e->'dependencyDigests') IS DISTINCT FROM 'array' THEN RETURN false;END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements_text(e->'dependencyDigests')v WHERE v IS NULL OR v !~ '^sha256:[0-9a-f]{64}$') THEN RETURN false;END IF;
 RETURN true;
EXCEPTION WHEN OTHERS THEN RETURN false;
END$$;
CREATE TABLE generation_policy_release_v1 (
 application_deployment_epoch bigint PRIMARY KEY,
 operation_contract_digest bytea NOT NULL,
 package_id text NOT NULL CHECK(package_id='urn:kcml:generation:kind-policy-package:1'),
 package_digest bytea NOT NULL CHECK(octet_length(package_digest)=32),
 package_bytes bytea NOT NULL CHECK(package_digest=sha256(package_bytes)),
 request_schema_id text NOT NULL,
 request_schema_digest bytea NOT NULL CHECK(octet_length(request_schema_digest)=32),
 request_policy_id text NOT NULL,
 request_policy_digest bytea NOT NULL CHECK(octet_length(request_policy_digest)=32),
 installed_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 UNIQUE(application_deployment_epoch,package_digest),
 FOREIGN KEY(application_deployment_epoch,operation_contract_digest)
 REFERENCES generation_create_contract_pin(application_deployment_epoch,contract_digest),
 CHECK(convert_from(package_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CONSTRAINT generation_policy_package_mask CHECK(kcml_generation_policy_package_shape_v1(convert_from(package_bytes,'UTF8')::jsonb)),
 CHECK(convert_from(package_bytes,'UTF8')::jsonb->>'packageId' IS NOT DISTINCT FROM package_id)
);
CREATE TABLE generation_policy_release_blob_v1 (
 application_deployment_epoch bigint NOT NULL REFERENCES generation_policy_release_v1(application_deployment_epoch),
 bundle_kind text NOT NULL CHECK(bundle_kind IN('SCHEMA','DOMAIN_POLICY','AUTHORITY','POLICY_IMPLEMENTATION')),
 bundle_id text NOT NULL,
 bundle_digest bytea NOT NULL CHECK(bundle_digest=sha256(exact_bytes)),
 exact_bytes bytea NOT NULL,
 source_identity text NOT NULL,
 source_digest bytea NOT NULL CHECK(octet_length(source_digest)=32),
 PRIMARY KEY(application_deployment_epoch,bundle_kind,bundle_id,bundle_digest)
);
CREATE TABLE generation_accepted_policy_package_v1 (
 snapshot_id uuid PRIMARY KEY,
 logical_operation_id uuid NOT NULL UNIQUE REFERENCES domain_command(logical_operation_id) DEFERRABLE INITIALLY DEFERRED,
 trusted_context_id uuid NOT NULL REFERENCES generation_create_trusted_context(id),
 application_deployment_epoch bigint NOT NULL,
 package_digest bytea NOT NULL,
 FOREIGN KEY(application_deployment_epoch,package_digest)
 REFERENCES generation_policy_release_v1(application_deployment_epoch,package_digest)
);
CREATE TRIGGER policy_release_immutable BEFORE UPDATE OR DELETE ON generation_policy_release_v1 FOR EACH ROW EXECUTE FUNCTION kcml_archive_immutable_v1();
CREATE TRIGGER policy_release_blob_immutable BEFORE UPDATE OR DELETE ON generation_policy_release_blob_v1 FOR EACH ROW EXECUTE FUNCTION kcml_archive_immutable_v1();
CREATE TRIGGER accepted_policy_package_immutable BEFORE UPDATE OR DELETE ON generation_accepted_policy_package_v1 FOR EACH ROW EXECUTE FUNCTION kcml_archive_immutable_v1();
CREATE TABLE generation_policy_acceptance_ticket_v1(
 trusted_context_id uuid PRIMARY KEY REFERENCES generation_create_trusted_context(id),
 logical_operation_id uuid NOT NULL UNIQUE,
 acceptance_txid xid8 NOT NULL
);
CREATE TRIGGER policy_acceptance_ticket_immutable BEFORE UPDATE OR DELETE ON generation_policy_acceptance_ticket_v1 FOR EACH ROW EXECUTE FUNCTION kcml_archive_immutable_v1();
CREATE FUNCTION kcml_pin_policy_acceptance_v1(p_context uuid,p_command uuid) RETURNS void
 LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE c public.generation_create_trusted_context;a public.generation_create_authentication_acceptance;
 credential public.owner_api_credential;session public.owner_session;owner public.owner_identity;
BEGIN
 IF EXISTS(SELECT 1 FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode IN('RowExclusiveLock','ShareRowExclusiveLock','ExclusiveLock','AccessExclusiveLock') AND relation IN('public.domain_command'::regclass,'public.generation_job'::regclass,'public.domain_event'::regclass,'public.transactional_outbox'::regclass,'public.audit_event'::regclass)) THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_ACCEPTANCE_LOCK_ORDER' USING ERRCODE='23514';END IF;
 SELECT * INTO c FROM public.generation_create_trusted_context WHERE id=p_context;
 SELECT * INTO a FROM public.generation_create_authentication_acceptance WHERE id=c.authentication_acceptance_id;
 IF c.id IS NULL OR a.id IS NULL OR a.owner_id<>c.owner_id OR a.access_channel<>c.initiating_access_channel THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_ACCEPTED_CONTEXT_MISMATCH' USING ERRCODE='23514';END IF;
 -- Current auth-class B checks use actual locked immutable receipt/current rows,
 -- never caller authorized=true. Public gateway's actual verifier remains required.
 IF a.access_channel='OWNER_API_KEY' THEN
 SELECT * INTO credential FROM public.owner_api_credential WHERE singleton_key=1 FOR SHARE;
 IF credential.singleton_key IS NULL OR (a.api_credential_version,a.api_credential_fingerprint,a.api_credential_activation_epoch)
 IS DISTINCT FROM(credential.credential_version,credential.fingerprint,credential.credential_activation_epoch) THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_AUTHORITY_STALE' USING ERRCODE='23514';END IF;
 ELSE
 SELECT * INTO owner FROM public.owner_identity WHERE id=c.owner_id FOR SHARE;
 SELECT * INTO session FROM public.owner_session WHERE id=a.session_id FOR SHARE;
 IF session.id IS NULL OR session.owner_identity_id<>owner.id OR session.revoked_at IS NOT NULL
 OR session.expires_at<=clock_timestamp() OR session.session_epoch<>owner.session_epoch OR session.session_epoch<>a.session_epoch
 OR session.lookup_digest IS DISTINCT FROM a.session_lookup_digest THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_AUTHORITY_STALE' USING ERRCODE='23514';END IF;
 END IF;
 INSERT INTO public.generation_policy_acceptance_ticket_v1 VALUES(p_context,p_command,pg_current_xact_id());
END$$;
CREATE FUNCTION kcml_publish_accepted_policy_package_v1(p_context uuid,p_command uuid,p_snapshot uuid)
 RETURNS bytea LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE c public.generation_create_trusted_context;d public.domain_command;a public.generation_create_authentication_acceptance;
 credential public.owner_api_credential;session public.owner_session;owner public.owner_identity;
 release public.generation_policy_release_v1;blob public.generation_policy_release_blob_v1;s record;prior public.generation_accepted_policy_package_v1;
 protected_kind text; schema_id text;schema_digest bytea;present integer;
BEGIN
 SELECT * INTO c FROM public.generation_create_trusted_context WHERE id=p_context;
 SELECT * INTO d FROM public.domain_command WHERE logical_operation_id=p_command;
 SELECT * INTO a FROM public.generation_create_authentication_acceptance WHERE id=c.authentication_acceptance_id;
 IF c.id IS NULL OR d.logical_operation_id IS NULL OR a.id IS NULL OR d.operation_id<>'generation.job.create'
 OR (d.execution_context_id,d.owner_id,d.canonical_arguments_snapshot_id,d.request_digest,d.execution_descriptor_digest)
 IS DISTINCT FROM(c.id,c.owner_id,p_snapshot,c.client_request_digest,c.execution_descriptor_digest)
 OR a.owner_id<>c.owner_id OR a.access_channel<>c.initiating_access_channel THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_ACCEPTED_CONTEXT_MISMATCH' USING ERRCODE='23514';END IF;
 IF NOT EXISTS(SELECT 1 FROM public.generation_policy_acceptance_ticket_v1 t WHERE t.trusted_context_id=p_context AND t.logical_operation_id=p_command AND t.acceptance_txid=pg_current_xact_id()) THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_ACCEPTANCE_PHASE_REQUIRED' USING ERRCODE='23514';END IF;
 SELECT * INTO release FROM public.generation_policy_release_v1 WHERE application_deployment_epoch=c.application_deployment_epoch;
 IF release.application_deployment_epoch IS NULL OR release.operation_contract_digest<>c.operation_contract_digest THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_DEPLOYED_PACKAGE_UNAVAILABLE' USING ERRCODE='23514';END IF;
 SELECT * INTO s FROM public.generation_job_initial_request_snapshot WHERE snapshot_id=p_snapshot;
 IF FOUND THEN protected_kind:='SUCCESS';schema_id:=s.request_schema_id;schema_digest:=s.request_schema_digest;
 IF s.logical_operation_id<>p_command OR s.job_id<>d.target_aggregate_id THEN RAISE EXCEPTION 'GENERATION_ARCHIVE_ACCEPTED_CONTEXT_MISMATCH' USING ERRCODE='23514';END IF;
 ELSE
 SELECT * INTO s FROM public.generation_create_preroot_snapshot WHERE snapshot_id=p_snapshot;
 IF NOT FOUND OR s.logical_operation_id<>p_command OR s.prospective_job_id<>d.target_aggregate_id OR s.trusted_context_id<>p_context THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_PROTECTED_SNAPSHOT_UNAVAILABLE' USING ERRCODE='23514';END IF;
 protected_kind:='PREROOT';schema_id:=s.request_schema_id;schema_digest:=s.request_schema_digest;
 END IF;
 IF (schema_id,schema_digest) IS DISTINCT FROM(release.request_schema_id,release.request_schema_digest) THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_RELEASE_SCHEMA_MISMATCH' USING ERRCODE='23514';END IF;
 SELECT * INTO prior FROM public.generation_accepted_policy_package_v1 WHERE snapshot_id=p_snapshot;
 IF FOUND THEN
 IF (prior.logical_operation_id,prior.trusted_context_id,prior.application_deployment_epoch,prior.package_digest)
 IS DISTINCT FROM(p_command,p_context,release.application_deployment_epoch,release.package_digest) THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_PACKAGE_REPLAY_CONFLICT' USING ERRCODE='23514';END IF;
 RETURN prior.package_digest;
 END IF;
 IF NOT public.kcml_generation_policy_package_shape_v1(convert_from(release.package_bytes,'UTF8')::jsonb) THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_PACKAGE_MASK_INVALID' USING ERRCODE='23514';END IF;
 IF (convert_from(release.package_bytes,'UTF8')::jsonb->'requestSchema'->>'schemaId',convert_from(release.package_bytes,'UTF8')::jsonb->'requestSchema'->>'bundleDigest',convert_from(release.package_bytes,'UTF8')::jsonb->'requestPolicy'->>'policyId',convert_from(release.package_bytes,'UTF8')::jsonb->'requestPolicy'->>'policyDigest') IS DISTINCT FROM(release.request_schema_id,'sha256:'||encode(release.request_schema_digest,'hex'),release.request_policy_id,'sha256:'||encode(release.request_policy_digest,'hex')) THEN RAISE EXCEPTION 'GENERATION_ARCHIVE_PACKAGE_REQUEST_IDENTITY_MISMATCH' USING ERRCODE='23514';END IF;
 IF (SELECT count(*)FROM public.generation_policy_release_blob_v1 WHERE application_deployment_epoch=release.application_deployment_epoch)<>jsonb_array_length(convert_from(release.package_bytes,'UTF8')::jsonb->'members') THEN RAISE EXCEPTION 'GENERATION_ARCHIVE_PACKAGE_MEMBER_UNAVAILABLE' USING ERRCODE='23514';END IF;
 -- Only exact installer-owned release rows may be archived; no bytes/code input.
 FOR blob IN SELECT * FROM public.generation_policy_release_blob_v1 WHERE application_deployment_epoch=release.application_deployment_epoch ORDER BY bundle_kind,bundle_id,bundle_digest LOOP
 PERFORM public.kcml_archive_publish_v1(blob.bundle_kind,blob.bundle_id,blob.bundle_digest,blob.exact_bytes,blob.source_identity,blob.source_digest);
 END LOOP;
 -- All declared package members must have authentic available immutable bytes.
 FOR s IN SELECT value FROM jsonb_array_elements(convert_from(release.package_bytes,'UTF8')::jsonb->'members') LOOP
 IF NOT EXISTS(SELECT 1 FROM public.generation_frozen_bundle_v1 b WHERE b.bundle_kind=s.value->>'kind' AND b.bundle_id=s.value->>'id'
 AND 'sha256:'||encode(b.bundle_digest,'hex')=s.value->>'digest') THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_PACKAGE_MEMBER_UNAVAILABLE' USING ERRCODE='23514';END IF;
 END LOOP;
 IF protected_kind='SUCCESS' THEN
 INSERT INTO public.generation_frozen_policy_binding_v1(snapshot_id,logical_operation_id,schema_id,schema_digest,policy_id,policy_digest,dependency_closure)
 VALUES(p_snapshot,p_command,release.request_schema_id,release.request_schema_digest,release.request_policy_id,release.request_policy_digest,'[]') ON CONFLICT DO NOTHING;
 ELSE
 INSERT INTO public.generation_preroot_frozen_policy_binding_v1(snapshot_id,logical_operation_id,schema_id,schema_digest,policy_id,policy_digest,dependency_closure)
 VALUES(p_snapshot,p_command,release.request_schema_id,release.request_schema_digest,release.request_policy_id,release.request_policy_digest,'[]') ON CONFLICT DO NOTHING;
 END IF;
 IF protected_kind='SUCCESS' THEN
 IF NOT EXISTS(SELECT 1 FROM public.generation_frozen_policy_binding_v1 q WHERE q.snapshot_id=p_snapshot AND q.logical_operation_id=p_command AND (q.schema_id,q.schema_digest,q.policy_id,q.policy_digest,q.dependency_closure) IS NOT DISTINCT FROM(release.request_schema_id,release.request_schema_digest,release.request_policy_id,release.request_policy_digest,'[]'::jsonb)) THEN RAISE EXCEPTION 'GENERATION_ARCHIVE_REQUEST_BINDING_CONFLICT' USING ERRCODE='23514';END IF;
 ELSE
 IF NOT EXISTS(SELECT 1 FROM public.generation_preroot_frozen_policy_binding_v1 q WHERE q.snapshot_id=p_snapshot AND q.logical_operation_id=p_command AND (q.schema_id,q.schema_digest,q.policy_id,q.policy_digest,q.dependency_closure) IS NOT DISTINCT FROM(release.request_schema_id,release.request_schema_digest,release.request_policy_id,release.request_policy_digest,'[]'::jsonb)) THEN RAISE EXCEPTION 'GENERATION_ARCHIVE_REQUEST_BINDING_CONFLICT' USING ERRCODE='23514';END IF;
 END IF;
 INSERT INTO public.generation_accepted_policy_package_v1 VALUES(p_snapshot,p_command,p_context,release.application_deployment_epoch,release.package_digest);
 RETURN release.package_digest;
END$$;
REVOKE ALL ON generation_policy_release_v1,generation_policy_release_blob_v1,generation_accepted_policy_package_v1 FROM PUBLIC;
REVOKE ALL ON FUNCTION kcml_publish_accepted_policy_package_v1(uuid,uuid,uuid) FROM PUBLIC;
ALTER FUNCTION kcml_publish_accepted_policy_package_v1(uuid,uuid,uuid) OWNER TO kcml_generation_archive_builder;
GRANT USAGE ON SCHEMA public TO kcml_generation_archive_builder,kcml_generation_policy_installer;
GRANT SELECT,INSERT ON generation_policy_release_v1,generation_policy_release_blob_v1 TO kcml_generation_policy_installer;
GRANT SELECT ON generation_create_contract_pin TO kcml_generation_policy_installer;
GRANT SELECT ON generation_policy_release_v1,generation_policy_release_blob_v1,generation_create_trusted_context,domain_command,
 generation_create_authentication_acceptance,generation_job_initial_request_snapshot,generation_create_preroot_snapshot,
 owner_api_credential,owner_session,owner_identity,generation_frozen_bundle_v1 TO kcml_generation_archive_builder;
GRANT UPDATE(application_deployment_epoch) ON generation_policy_release_v1 TO kcml_generation_archive_builder;
GRANT UPDATE(singleton_key) ON owner_api_credential TO kcml_generation_archive_builder;
GRANT UPDATE(id) ON owner_session,owner_identity TO kcml_generation_archive_builder;
GRANT SELECT,INSERT ON generation_accepted_policy_package_v1,generation_frozen_bundle_v1,generation_frozen_policy_binding_v1,generation_preroot_frozen_policy_binding_v1 TO kcml_generation_archive_builder;
GRANT UPDATE(snapshot_id) ON generation_accepted_policy_package_v1 TO kcml_generation_archive_builder;
GRANT UPDATE(bundle_id) ON generation_frozen_bundle_v1 TO kcml_generation_archive_builder;
GRANT EXECUTE ON FUNCTION kcml_archive_publish_v1(text,text,bytea,bytea,text,bytea) TO kcml_generation_archive_builder;
GRANT EXECUTE ON FUNCTION kcml_publish_accepted_policy_package_v1(uuid,uuid,uuid) TO kcml_domain_writer;

REVOKE ALL ON generation_policy_acceptance_ticket_v1 FROM PUBLIC;
REVOKE ALL ON FUNCTION kcml_pin_policy_acceptance_v1(uuid,uuid) FROM PUBLIC;
ALTER FUNCTION kcml_pin_policy_acceptance_v1(uuid,uuid) OWNER TO kcml_generation_archive_builder;
GRANT SELECT,INSERT ON generation_policy_acceptance_ticket_v1 TO kcml_generation_archive_builder;
GRANT EXECUTE ON FUNCTION kcml_pin_policy_acceptance_v1(uuid,uuid) TO kcml_domain_writer;

GRANT UPDATE(snapshot_id) ON generation_job_initial_request_snapshot,generation_create_preroot_snapshot TO kcml_generation_archive_builder;
CREATE FUNCTION kcml_accepted_package_guard_v1() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE c public.generation_create_trusted_context;r public.generation_policy_release_v1;d public.domain_command;p public.generation_accepted_policy_package_v1;
BEGIN
 IF TG_TABLE_NAME='generation_accepted_policy_package_v1' THEN
 SELECT * INTO p FROM public.generation_accepted_policy_package_v1 WHERE snapshot_id=NEW.snapshot_id;
 SELECT * INTO d FROM public.domain_command WHERE logical_operation_id=p.logical_operation_id;
 ELSE
 SELECT * INTO d FROM public.domain_command WHERE logical_operation_id=NEW.logical_operation_id;
 SELECT * INTO p FROM public.generation_accepted_policy_package_v1 WHERE snapshot_id=NEW.snapshot_id;
 END IF;
 SELECT * INTO c FROM public.generation_create_trusted_context WHERE id=d.execution_context_id;
 SELECT * INTO r FROM public.generation_policy_release_v1 WHERE application_deployment_epoch=c.application_deployment_epoch;
 IF r.application_deployment_epoch IS NULL THEN RETURN NULL;END IF;
 IF p.snapshot_id IS NULL OR (p.logical_operation_id,p.trusted_context_id,p.application_deployment_epoch,p.package_digest)
 IS DISTINCT FROM(d.logical_operation_id,c.id,c.application_deployment_epoch,r.package_digest) OR p.snapshot_id<>d.canonical_arguments_snapshot_id
 OR NOT(EXISTS(SELECT 1 FROM public.generation_job_initial_request_snapshot WHERE snapshot_id=p.snapshot_id AND logical_operation_id=p.logical_operation_id) OR EXISTS(SELECT 1 FROM public.generation_create_preroot_snapshot WHERE snapshot_id=p.snapshot_id AND logical_operation_id=p.logical_operation_id AND trusted_context_id=p.trusted_context_id)) THEN
 RAISE EXCEPTION 'GENERATION_ARCHIVE_ACCEPTED_PACKAGE_REQUIRED' USING ERRCODE='23514';END IF;
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER accepted_package_guard AFTER INSERT ON generation_accepted_policy_package_v1 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_accepted_package_guard_v1();
CREATE CONSTRAINT TRIGGER initial_package_guard AFTER INSERT ON generation_job_initial_request_snapshot DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_accepted_package_guard_v1();
CREATE CONSTRAINT TRIGGER preroot_package_guard AFTER INSERT ON generation_create_preroot_snapshot DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_accepted_package_guard_v1();
