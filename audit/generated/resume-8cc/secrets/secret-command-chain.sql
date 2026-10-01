-- Scoped technical Secret API acceptance/CREATE commit §§7.2,8.12,12.48,
-- 49.4,49.22.1,51.12–14,51.20. Requires canonical foundation+Secret roots.
CREATE TABLE kcml_secret_v1.operation_contract_publication (
 operation_id text NOT NULL CHECK(operation_id IN ('secret.create','ownerApiKey.rotate')),
 application_deployment_epoch bigint NOT NULL CHECK(application_deployment_epoch>=0),
 operation_revision text NOT NULL CHECK(operation_revision<>''),
 request_schema_bytes bytea NOT NULL,
 request_schema_digest bytea NOT NULL CHECK(request_schema_digest=sha256(request_schema_bytes)),
 source_ssot_digest bytea NOT NULL CHECK(octet_length(source_ssot_digest)=32),
 PRIMARY KEY(operation_id,application_deployment_epoch)
);
CREATE TRIGGER secret_contract_publication_immutable BEFORE UPDATE OR DELETE ON kcml_secret_v1.operation_contract_publication
 FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.secret_profile_immutable();
CREATE TABLE kcml_secret_v1.owner_api_context (
 id uuid PRIMARY KEY,
 owner_id uuid NOT NULL REFERENCES owner_identity(id),
 operation_id text NOT NULL CHECK(operation_id IN ('secret.create','ownerApiKey.rotate')),
 purpose text NOT NULL CHECK((operation_id='secret.create' AND purpose='CREATE_SECRET_CANDIDATE') OR (operation_id='ownerApiKey.rotate' AND purpose='ROTATE_OWNER_API_CREDENTIAL')),
 initiating_access_channel text NOT NULL CHECK(initiating_access_channel='OWNER_API_KEY'),
 request_digest bytea NOT NULL CHECK(octet_length(request_digest)=32),
 execution_descriptor_bytes bytea NOT NULL,
 execution_descriptor_digest bytea NOT NULL CHECK(execution_descriptor_digest=sha256(execution_descriptor_bytes)),
 platform_incarnation_id uuid NOT NULL,
 application_deployment_epoch bigint NOT NULL CHECK(application_deployment_epoch>=0),
 operation_revision text NOT NULL,
 api_credential_version bigint NOT NULL CHECK(api_credential_version>=1),
 api_credential_activation_epoch bigint NOT NULL CHECK(api_credential_activation_epoch>=0),
 api_fingerprint text NOT NULL CHECK(api_fingerprint<>''),
 accepted_at timestamptz NOT NULL,
 UNIQUE(id,owner_id,operation_id)
 ,FOREIGN KEY(operation_id,application_deployment_epoch) REFERENCES kcml_secret_v1.operation_contract_publication(operation_id,application_deployment_epoch)
);
CREATE FUNCTION kcml_secret_v1.context_head_binding_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE credential public.owner_api_credential; pi uuid; epoch bigint; owner uuid;
 pin kcml_secret_v1.operation_contract_publication; descriptor jsonb; expected jsonb;
 expected_bytes bytea;
BEGIN
 SELECT platform_incarnation_id INTO STRICT pi FROM public.platform_incarnation WHERE singleton_key=1 FOR SHARE;
 SELECT application_deployment_epoch INTO STRICT epoch FROM public.application_deployment_head WHERE singleton_key=1 AND platform_incarnation_id=pi FOR SHARE;
 SELECT * INTO STRICT credential FROM public.owner_api_credential WHERE singleton_key=1 FOR SHARE;
 SELECT id INTO STRICT owner FROM public.owner_identity WHERE singleton_key=1 FOR SHARE;
 SELECT * INTO STRICT pin FROM kcml_secret_v1.operation_contract_publication WHERE operation_id=NEW.operation_id AND application_deployment_epoch=epoch;
 IF NOT(convert_from(NEW.execution_descriptor_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_CONTEXT_DESCRIPTOR_INVALID';END IF;
 descriptor=convert_from(NEW.execution_descriptor_bytes,'UTF8')::jsonb;
 expected=jsonb_build_object('callerAuthorityKind','OWNER_FULL','clientKeyDigest',descriptor->>'clientKeyDigest',
 'operationContractId',NEW.operation_id,'operationContractRevision',pin.operation_revision,
 'stableBusinessTargetKey',CASE WHEN NEW.operation_id='secret.create' THEN 'CREATE_ROOT:secret_record' ELSE 'KCML_OWNER_API_KEY' END,
 'stableCallerObjectId',owner::text,'stableCallerRevisionId',NULL);
 IF descriptor IS DISTINCT FROM expected OR (descriptor->>'clientKeyDigest') IS NULL
 OR (descriptor->>'clientKeyDigest') !~ '^sha256:[0-9a-f]{64}$'
 OR NEW.operation_revision IS DISTINCT FROM pin.operation_revision THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_CONTEXT_DESCRIPTOR_BINDING_MISMATCH';END IF;
 expected_bytes=convert_to('{"callerAuthorityKind":"OWNER_FULL","clientKeyDigest":'||to_json(descriptor->>'clientKeyDigest')::text||',"operationContractId":'||to_json(NEW.operation_id)::text||',"operationContractRevision":'||to_json(pin.operation_revision)::text||',"stableBusinessTargetKey":'||to_json(expected->>'stableBusinessTargetKey')::text||',"stableCallerObjectId":'||to_json(owner::text)::text||',"stableCallerRevisionId":null}','UTF8');
 IF NEW.execution_descriptor_bytes IS DISTINCT FROM expected_bytes THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_CONTEXT_DESCRIPTOR_NONCANONICAL';END IF;
 IF NEW.owner_id IS DISTINCT FROM owner OR NEW.platform_incarnation_id IS DISTINCT FROM pi
 OR NEW.application_deployment_epoch IS DISTINCT FROM epoch
 OR NEW.api_credential_version IS DISTINCT FROM credential.credential_version
 OR NEW.api_credential_activation_epoch IS DISTINCT FROM credential.credential_activation_epoch
 OR NEW.api_fingerprint IS DISTINCT FROM credential.fingerprint
 OR NEW.accepted_at>clock_timestamp() THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_OWNER_CONTEXT_HEAD_MISMATCH';END IF;
 RETURN NEW;
END$$;
CREATE TRIGGER secret_context_current_heads BEFORE INSERT ON kcml_secret_v1.owner_api_context
 FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.context_head_binding_v1();
CREATE TRIGGER secret_context_immutable BEFORE UPDATE OR DELETE ON kcml_secret_v1.owner_api_context
 FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.secret_profile_immutable();
CREATE TABLE kcml_secret_v1.create_completion (
 logical_operation_id uuid PRIMARY KEY REFERENCES domain_command(logical_operation_id),
 trusted_context_id uuid NOT NULL UNIQUE REFERENCES kcml_secret_v1.owner_api_context(id),
 secret_id uuid NOT NULL,
 version_id uuid NOT NULL,
 native_metadata_bytes bytea NOT NULL,
 native_metadata_digest bytea NOT NULL CHECK(native_metadata_digest=sha256(native_metadata_bytes)),
 output_receipt_bytes bytea NOT NULL,
 output_receipt_digest bytea NOT NULL CHECK(output_receipt_digest=sha256(output_receipt_bytes)),
 semantic_result_bytes bytea NOT NULL,
 result_digest bytea NOT NULL CONSTRAINT secret_semantic_result_digest CHECK(result_digest=sha256(semantic_result_bytes)),
 immutable_event_id uuid NOT NULL UNIQUE,
 created_at timestamptz NOT NULL,
 FOREIGN KEY(secret_id,version_id) REFERENCES kcml_secret_v1.secret_version(secret_id,id),
 FOREIGN KEY(immutable_event_id,logical_operation_id,secret_id) REFERENCES domain_event(id,logical_operation_id,aggregate_id) DEFERRABLE INITIALLY DEFERRED
);
CREATE FUNCTION kcml_secret_v1.context_single_command_binding_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE count_commands integer; d public.domain_command;
BEGIN
 SELECT count(*) INTO count_commands FROM public.domain_command WHERE execution_context_id=NEW.id;
 SELECT * INTO d FROM public.domain_command WHERE execution_context_id=NEW.id;
 IF count_commands<>1 OR d.operation_id IS DISTINCT FROM NEW.operation_id OR d.owner_id IS DISTINCT FROM NEW.owner_id
 OR d.request_digest IS DISTINCT FROM NEW.request_digest OR d.execution_descriptor_digest IS DISTINCT FROM NEW.execution_descriptor_digest
 OR d.caller_channel IS DISTINCT FROM NEW.initiating_access_channel THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_CONTEXT_SINGLE_COMMAND_REQUIRED';END IF;
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER secret_context_scoped_one_command AFTER INSERT ON kcml_secret_v1.owner_api_context
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.context_single_command_binding_v1();
-- Existing canonical locator C0 and RESERVED idempotency C1 are claimed
-- before E roots. No extra scope table/FK or new advisory namespace exists.
CREATE TRIGGER secret_completion_immutable BEFORE UPDATE OR DELETE ON kcml_secret_v1.create_completion
 FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.secret_profile_immutable();
CREATE FUNCTION kcml_secret_v1.create_atomic_closure_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE c kcml_secret_v1.create_completion; ctx kcml_secret_v1.owner_api_context;
 d public.domain_command; e public.domain_event; a public.audit_event;
 r kcml_secret_v1.secret_record; v kcml_secret_v1.secret_version; output jsonb; expected_semantic jsonb;
BEGIN
 SELECT * INTO c FROM kcml_secret_v1.create_completion WHERE logical_operation_id=NEW.logical_operation_id;
 SELECT * INTO d FROM public.domain_command WHERE logical_operation_id=NEW.logical_operation_id;
 IF c.logical_operation_id IS NULL THEN
  IF d.operation_id='secret.create' AND d.state='SUCCEEDED' THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_CREATE_COMPLETION_REQUIRED';END IF;
  RETURN NULL;
 END IF;
 SELECT * INTO STRICT ctx FROM kcml_secret_v1.owner_api_context WHERE id=c.trusted_context_id;
 SELECT * INTO STRICT r FROM kcml_secret_v1.secret_record WHERE id=c.secret_id;
 SELECT * INTO STRICT v FROM kcml_secret_v1.secret_version WHERE id=c.version_id;
 SELECT * INTO e FROM public.domain_event WHERE id=c.immutable_event_id;
 SELECT * INTO a FROM public.audit_event WHERE domain_event_id=e.id;
 output=convert_from(c.output_receipt_bytes,'UTF8')::jsonb;
 expected_semantic=jsonb_build_object('routeId','route.0386','operationId','secret.create','logicalOperationId',d.logical_operation_id::text,'correlationId',d.correlation_id::text,'status','SUCCEEDED','terminal',true,'output',output,'error',NULL,'stateVersion','0','eventSequence','1','activationEpoch',NULL);
 IF c.semantic_result_bytes IS DISTINCT FROM convert_to(public.kcml_crypto_compact_sorted_json_v1(expected_semantic),'UTF8') THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_CREATE_SEMANTIC_RESULT_MISMATCH';END IF;
 IF ctx.operation_id IS DISTINCT FROM 'secret.create' OR ctx.purpose IS DISTINCT FROM 'CREATE_SECRET_CANDIDATE'
 OR d.operation_id IS DISTINCT FROM 'secret.create' OR d.execution_context_id IS DISTINCT FROM ctx.id
 OR d.owner_id IS DISTINCT FROM ctx.owner_id OR d.caller_channel IS DISTINCT FROM ctx.initiating_access_channel
 OR d.request_digest IS DISTINCT FROM ctx.request_digest OR d.execution_descriptor_bytes IS DISTINCT FROM ctx.execution_descriptor_bytes
 OR d.operation_contract_revision IS DISTINCT FROM ctx.operation_revision
 OR d.platform_incarnation_id IS DISTINCT FROM ctx.platform_incarnation_id OR d.application_deployment_epoch IS DISTINCT FROM ctx.application_deployment_epoch
 OR d.state IS DISTINCT FROM 'SUCCEEDED' OR NOT d.terminal OR d.result_digest IS DISTINCT FROM c.result_digest
 OR d.target_aggregate_kind IS DISTINCT FROM 'SECRET_RECORD' OR d.target_aggregate_id IS DISTINCT FROM r.id
 OR d.canonical_arguments_snapshot_id IS DISTINCT FROM v.id OR v.creator_context_id IS DISTINCT FROM ctx.id
 OR v.secret_id IS DISTINCT FROM r.id OR v.lifecycle IS DISTINCT FROM 'CREATED' OR r.active_version_id IS NOT NULL
 OR r.secret_activation_epoch<>0 OR r.state_version<>0
 OR v.secret_type IS DISTINCT FROM r.secret_type OR v.created_at IS DISTINCT FROM r.created_at
 OR (convert_from(c.native_metadata_bytes,'UTF8')::jsonb->>'stableName') IS DISTINCT FROM r.stable_name
 OR (convert_from(c.native_metadata_bytes,'UTF8')::jsonb->>'displayName') IS DISTINCT FROM r.display_name
 OR (convert_from(c.native_metadata_bytes,'UTF8')::jsonb->>'description') IS DISTINCT FROM r.description
 OR (convert_from(c.native_metadata_bytes,'UTF8')::jsonb->>'type') IS DISTINCT FROM r.secret_type
 OR (convert_from(c.native_metadata_bytes,'UTF8')::jsonb->>'purposeKind') IS DISTINCT FROM r.purpose_kind
 OR (convert_from(c.native_metadata_bytes,'UTF8')::jsonb->>'targetObjectId') IS DISTINCT FROM r.target_object_id::text
 OR coalesce(convert_from(c.native_metadata_bytes,'UTF8')::jsonb->'tags','[]'::jsonb) IS DISTINCT FROM to_jsonb(r.tags)
 OR (convert_from(c.native_metadata_bytes,'UTF8')::jsonb->>'group') IS DISTINCT FROM r.group_name
 OR (convert_from(c.native_metadata_bytes,'UTF8')::jsonb->>'url') IS DISTINCT FROM r.url
 OR (convert_from(c.native_metadata_bytes,'UTF8')::jsonb->>'username') IS DISTINCT FROM r.username
 OR (convert_from(c.native_metadata_bytes,'UTF8')::jsonb->>'notes') IS DISTINCT FROM r.notes
 OR (convert_from(c.native_metadata_bytes,'UTF8')::jsonb->>'expiration')::timestamptz IS DISTINCT FROM r.expires_at
 OR output IS DISTINCT FROM jsonb_build_object('secretId',r.id::text,'stableName',r.stable_name,'type',v.secret_type,'versionId',v.id::text,
 'versionNumber',v.version_number::text,'versionState','CREATED','activeVersionId',NULL,'stateVersion',r.state_version::text,'createdAt',to_char(r.created_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))
 OR e.id IS NULL OR e.event_type IS DISTINCT FROM 'OPERATION_TERMINAL' OR e.aggregate_kind IS DISTINCT FROM 'SECRET_RECORD'
 OR e.aggregate_sequence<>1 OR e.payload_bytes IS DISTINCT FROM c.output_receipt_bytes OR e.payload_digest IS DISTINCT FROM c.output_receipt_digest
 OR a.id IS NULL OR a.logical_operation_id IS DISTINCT FROM d.logical_operation_id
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'logicalOperationId') IS DISTINCT FROM d.logical_operation_id::text
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'eventId') IS DISTINCT FROM e.id::text
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'objectId') IS DISTINCT FROM r.id::text
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'actorId') IS DISTINCT FROM ctx.owner_id::text
 OR (convert_from(a.canonical_bytes,'UTF8')::jsonb->>'afterDigest') IS DISTINCT FROM ('sha256:'||encode(e.payload_digest,'hex'))
 OR NOT EXISTS(SELECT 1 FROM public.audit_head h JOIN public.audit_event tail ON tail.chain_sequence=h.last_sequence AND tail.event_hash=h.last_hash WHERE h.singleton_key=1 AND h.last_sequence>=a.chain_sequence)
 OR (a.chain_sequence=1 AND a.previous_hash<>decode(repeat('00',32),'hex'))
 OR (a.chain_sequence>1 AND NOT EXISTS(SELECT 1 FROM public.audit_event prev WHERE prev.chain_sequence=a.chain_sequence-1 AND prev.event_hash=a.previous_hash))
 OR NOT EXISTS(SELECT 1 FROM public.transactional_outbox o WHERE o.event_id=e.id AND o.logical_operation_id=d.logical_operation_id AND o.aggregate_id=r.id AND o.purpose='DOMAIN_EVENT' AND o.payload_digest=e.payload_digest)
 OR NOT EXISTS(SELECT 1 FROM public.domain_idempotency_record i WHERE i.logical_operation_id=d.logical_operation_id AND i.state='SUCCEEDED' AND i.request_digest=d.request_digest AND i.key_digest=d.client_key_digest AND i.scope_digest=d.scope_digest AND i.canonical_outcome_digest=c.result_digest)
 OR NOT EXISTS(SELECT 1 FROM public.idempotency_locator l WHERE l.logical_operation_id=d.logical_operation_id AND l.operation_family='SECRET' AND l.caller_authority_kind='OWNER_FULL' AND l.caller_stable_id=ctx.owner_id::text AND l.business_target_kind='CREATE_ROOT' AND l.business_target_id='secret_record' AND l.client_key_digest=d.client_key_digest AND l.client_request_digest=d.request_digest AND l.execution_descriptor_digest=d.execution_descriptor_digest AND l.frozen_revision_digest=d.scope_digest)
 OR (a.archive_required AND NOT EXISTS(SELECT 1 FROM public.audit_archive_outbox o WHERE o.audit_event_id=a.id)) THEN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_CREATE_ATOMIC_CLOSURE_INCOMPLETE';END IF;
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER secret_create_completion_closure AFTER INSERT ON kcml_secret_v1.create_completion
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.create_atomic_closure_v1();
CREATE CONSTRAINT TRIGGER secret_create_command_closure AFTER INSERT OR UPDATE ON domain_command
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.create_atomic_closure_v1();
-- API verification is performed by actual native constant-time token producer
-- before INSERT under the SAME transaction's credential SHARE lock. This SQL
-- neither accepts a caller authorized flag nor exposes context INSERT to PUBLIC.
REVOKE ALL ON kcml_secret_v1.owner_api_context,kcml_secret_v1.create_completion FROM PUBLIC;
DO $$DECLARE role_name text;BEGIN
 FOREACH role_name IN ARRAY ARRAY['kcml_secret_authentication_writer','kcml_secret_domain_writer'] LOOP
  IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=role_name) THEN
   EXECUTE format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',role_name);
  END IF;
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=role_name AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolinherit OR rolreplication OR rolbypassrls)) THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_AUTHENTICATION_ROLE_UNSAFE';END IF;
 END LOOP;
END$$;
GRANT USAGE ON SCHEMA kcml_secret_v1,public TO kcml_secret_authentication_writer,kcml_secret_domain_writer;
GRANT SELECT,INSERT ON kcml_secret_v1.owner_api_context TO kcml_secret_authentication_writer;
GRANT SELECT ON kcml_secret_v1.operation_contract_publication,owner_identity,owner_api_credential,platform_incarnation,application_deployment_head TO kcml_secret_authentication_writer;
GRANT SELECT ON domain_command TO kcml_secret_authentication_writer;
-- SHARE row locks need UPDATE privilege; immutable singleton guard permits no
-- identity rewrite. Verifier/context insertion capability is never granted to
-- client/handler/domain writer roles. No group membership is assigned here.
GRANT UPDATE(singleton_key) ON owner_identity,owner_api_credential,platform_incarnation,application_deployment_head TO kcml_secret_authentication_writer;
GRANT SELECT ON kcml_secret_v1.owner_api_context TO kcml_secret_domain_writer;
REVOKE INSERT,UPDATE,DELETE ON kcml_secret_v1.owner_api_context FROM kcml_secret_domain_writer;
