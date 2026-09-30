-- Scoped OWNER facade materialization, §§43.3,49.3–5,50.10–11,50.25,50.31.
-- Prerequisites: actual source owner/session/API/platform/deployment roots and
-- generic domain_command. Auth fixture roots are NEVER declared in this file.
CREATE TABLE owner_ui_authentication_acceptance (
 id uuid PRIMARY KEY, owner_id uuid NOT NULL REFERENCES owner_identity(id),
 access_channel text NOT NULL CHECK(access_channel IN('OWNER_SESSION','OWNER_API_KEY')),
 session_id uuid NULL REFERENCES owner_session(id), session_epoch bigint NULL,
 session_lookup_digest bytea NULL CHECK(session_lookup_digest IS NULL OR octet_length(session_lookup_digest)=32),
 api_credential_version bigint NULL, api_credential_fingerprint text NULL,
 accepted_at timestamptz NOT NULL,
 CHECK((access_channel='OWNER_SESSION' AND session_id IS NOT NULL AND session_epoch IS NOT NULL AND session_lookup_digest IS NOT NULL AND api_credential_version IS NULL AND api_credential_fingerprint IS NULL)
 OR(access_channel='OWNER_API_KEY' AND session_id IS NULL AND session_epoch IS NULL AND session_lookup_digest IS NULL AND api_credential_version IS NOT NULL AND api_credential_fingerprint IS NOT NULL))
);
CREATE TABLE owner_ui_dispatch_registry (
 operation_id text PRIMARY KEY CHECK(operation_id IN('runtime.owner.start.request','runtime.owner.stop.request','generation.spec.owner_input.append')),
 action_id text NOT NULL UNIQUE CHECK(action_id IN('dashboard.start','dashboard.stop','gen.editSpec')),
 worker_operation_id text NOT NULL,
 worker_execution_class text NOT NULL CHECK(worker_execution_class IN('AUTOMATED_MAINTENANCE','INTERNAL_PROTOCOL')),
 input_schema_digest bytea NOT NULL CHECK(octet_length(input_schema_digest)=32),
 worker_schema_digest bytea NOT NULL CHECK(octet_length(worker_schema_digest)=32),
 contract_digest bytea NOT NULL CHECK(octet_length(contract_digest)=32),
 CHECK((action_id='dashboard.start' AND operation_id='runtime.owner.start.request' AND worker_operation_id='runtime.instance.start' AND worker_execution_class='AUTOMATED_MAINTENANCE')
 OR(action_id='dashboard.stop' AND operation_id='runtime.owner.stop.request' AND worker_operation_id='runtime.stop' AND worker_execution_class='AUTOMATED_MAINTENANCE')
 OR(action_id='gen.editSpec' AND operation_id='generation.spec.owner_input.append' AND worker_operation_id='generation.spec.propose' AND worker_execution_class='INTERNAL_PROTOCOL'))
);
-- Canonical input validator alone publishes this receipt after strict UTF8/JSON/
-- exact native mask + own byte/digest/identity validation. It cannot authorize effects.
CREATE TABLE owner_ui_validated_input (
 id uuid PRIMARY KEY,
 operation_id text NOT NULL REFERENCES owner_ui_dispatch_registry(operation_id),
 input_schema_digest bytea NOT NULL CHECK(octet_length(input_schema_digest)=32),
 request_bytes bytea NOT NULL CHECK(octet_length(request_bytes)>0),
 request_content_digest bytea NOT NULL CHECK(request_content_digest=sha256(request_bytes)),
 canonical_request_bytes bytea NOT NULL CHECK(octet_length(canonical_request_bytes)>0),
 request_digest bytea NOT NULL CHECK(request_digest=sha256(canonical_request_bytes)),
 target_id uuid NOT NULL, target_snapshot_bytes bytea NOT NULL,
 target_snapshot_digest bytea NOT NULL CHECK(target_snapshot_digest=sha256(target_snapshot_bytes)),
 validated_at timestamptz NOT NULL,
 CHECK(convert_from(request_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(canonical_request_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(target_snapshot_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS)
);
CREATE TABLE owner_ui_accepted_intent (
 id uuid PRIMARY KEY,
 logical_operation_id uuid NOT NULL UNIQUE REFERENCES domain_command(logical_operation_id) DEFERRABLE INITIALLY DEFERRED,
 authentication_acceptance_id uuid NOT NULL REFERENCES owner_ui_authentication_acceptance(id),
 validated_input_id uuid NOT NULL UNIQUE REFERENCES owner_ui_validated_input(id),
 owner_id uuid NOT NULL REFERENCES owner_identity(id),
 operation_id text NOT NULL REFERENCES owner_ui_dispatch_registry(operation_id),
 request_digest bytea NOT NULL CHECK(octet_length(request_digest)=32),
 frozen_target_digest bytea NOT NULL CHECK(octet_length(frozen_target_digest)=32),
 contract_digest bytea NOT NULL CHECK(octet_length(contract_digest)=32),
 worker_schema_digest bytea NOT NULL CHECK(octet_length(worker_schema_digest)=32),
 platform_incarnation_id uuid NOT NULL,
 application_deployment_epoch bigint NOT NULL CHECK(application_deployment_epoch>=0),
 accepted_at timestamptz NOT NULL
);
-- Cancellation/current operation outcome remains canonical domain_command state.
-- No mutable accepted-intent field can erase frozen inputs or OWNER authority.
CREATE TABLE owner_ui_worker_context (
 id uuid PRIMARY KEY,
 intent_id uuid NOT NULL UNIQUE REFERENCES owner_ui_accepted_intent(id),
 parent_logical_operation_id uuid NOT NULL UNIQUE REFERENCES domain_command(logical_operation_id),
 owner_id uuid NOT NULL REFERENCES owner_identity(id),
 worker_operation_id text NOT NULL,
 worker_execution_class text NOT NULL CHECK(worker_execution_class IN('AUTOMATED_MAINTENANCE','INTERNAL_PROTOCOL')),
 request_digest bytea NOT NULL CHECK(octet_length(request_digest)=32),
 input_snapshot_digest bytea NOT NULL CHECK(octet_length(input_snapshot_digest)=32),
 worker_schema_digest bytea NOT NULL CHECK(octet_length(worker_schema_digest)=32),
 platform_incarnation_id uuid NOT NULL, application_deployment_epoch bigint NOT NULL CHECK(application_deployment_epoch>=0),
 issued_at timestamptz NOT NULL
);
SELECT set_config('search_path',format('%I,pg_catalog,pg_temp',current_schema()),false);
CREATE FUNCTION kcml_owner_ui_frozen_guard_v1() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='OWNER_UI_FROZEN_IMMUTABLE';END;$$;
CREATE TRIGGER owner_ui_auth_frozen BEFORE UPDATE OR DELETE ON owner_ui_authentication_acceptance FOR EACH ROW EXECUTE FUNCTION kcml_owner_ui_frozen_guard_v1();
CREATE TRIGGER owner_ui_input_frozen BEFORE UPDATE OR DELETE ON owner_ui_validated_input FOR EACH ROW EXECUTE FUNCTION kcml_owner_ui_frozen_guard_v1();
CREATE TRIGGER owner_ui_intent_frozen BEFORE UPDATE OR DELETE ON owner_ui_accepted_intent FOR EACH ROW EXECUTE FUNCTION kcml_owner_ui_frozen_guard_v1();
CREATE TRIGGER owner_ui_worker_frozen BEFORE UPDATE OR DELETE ON owner_ui_worker_context FOR EACH ROW EXECUTE FUNCTION kcml_owner_ui_frozen_guard_v1();
CREATE FUNCTION kcml_owner_ui_descriptor_bytes_v1(p_auth uuid,p_input uuid,p_logical uuid,p_context uuid)
RETURNS bytea LANGUAGE sql SECURITY DEFINER SET search_path FROM CURRENT AS $$
 SELECT convert_to(jsonb_build_object(
 'schemaVersion','OWNER_UI_EXECUTION_DESCRIPTOR/1','contextId',p_context,
 'logicalOperationId',p_logical,'ownerId',a.owner_id,'authenticationAcceptanceId',a.id,
 'operationId',v.operation_id,'validatedInputId',v.id,'targetId',v.target_id,
 'requestDigest','sha256:'||encode(v.request_digest,'hex'),
 'targetSnapshotDigest','sha256:'||encode(v.target_snapshot_digest,'hex'),
 'inputSchemaDigest','sha256:'||encode(v.input_schema_digest,'hex'),
 'workerSchemaDigest','sha256:'||encode(r.worker_schema_digest,'hex'),
 'contractDigest','sha256:'||encode(r.contract_digest,'hex'))::text,'UTF8')
 FROM owner_ui_authentication_acceptance a,owner_ui_validated_input v
 JOIN owner_ui_dispatch_registry r ON r.operation_id=v.operation_id
 WHERE a.id=p_auth AND v.id=p_input;
$$;
CREATE FUNCTION kcml_owner_ui_accept_v1(p_auth uuid,p_validated_input uuid,p_logical uuid)
RETURNS owner_ui_accepted_intent LANGUAGE plpgsql SECURITY DEFINER SET search_path FROM CURRENT AS $$
DECLARE a owner_ui_authentication_acceptance; v owner_ui_validated_input; r owner_ui_dispatch_registry;
 o owner_identity; s owner_session; api owner_api_credential; pi platform_incarnation; dh application_deployment_head;
 c domain_command; i owner_ui_accepted_intent; at timestamptz:=clock_timestamp();
BEGIN
 SELECT * INTO STRICT a FROM owner_ui_authentication_acceptance WHERE id=p_auth;
 SELECT * INTO STRICT v FROM owner_ui_validated_input WHERE id=p_validated_input;
 SELECT * INTO STRICT pi FROM platform_incarnation WHERE singleton_key=1 FOR SHARE;
 SELECT * INTO STRICT dh FROM application_deployment_head WHERE singleton_key=1 FOR SHARE;
 SELECT * INTO STRICT r FROM owner_ui_dispatch_registry WHERE operation_id=v.operation_id FOR SHARE;
 SELECT * INTO STRICT o FROM owner_identity WHERE singleton_key=1 AND id=a.owner_id FOR SHARE;
 IF pi.platform_incarnation_id<>dh.platform_incarnation_id THEN RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='OWNER_UI_HEAD_MISMATCH';END IF;
 IF a.accepted_at>at OR v.validated_at>at THEN RAISE EXCEPTION USING ERRCODE='28000',MESSAGE='OWNER_UI_PRODUCER_RECEIPT_FUTURE';END IF;
 IF a.access_channel='OWNER_SESSION' THEN
  SELECT * INTO STRICT s FROM owner_session WHERE id=a.session_id FOR SHARE;
  IF s.owner_identity_id<>o.id OR s.lookup_digest<>a.session_lookup_digest OR s.session_epoch<>a.session_epoch OR s.session_epoch<>o.session_epoch OR s.revoked_at IS NOT NULL OR s.expires_at<=at THEN RAISE EXCEPTION USING ERRCODE='28000',MESSAGE='OWNER_UI_SESSION_STALE';END IF;
 ELSE
  SELECT * INTO STRICT api FROM owner_api_credential WHERE singleton_key=1 FOR SHARE;
  IF api.credential_version<>a.api_credential_version OR api.fingerprint<>a.api_credential_fingerprint THEN RAISE EXCEPTION USING ERRCODE='28000',MESSAGE='OWNER_UI_API_STALE';END IF;
 END IF;
 IF convert_from(v.canonical_request_bytes,'UTF8')::jsonb IS DISTINCT FROM jsonb_build_object('actionId',r.action_id,'body',convert_from(v.request_bytes,'UTF8')::jsonb) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_UI_REQUEST_SEMANTIC_BINDING_MISMATCH';END IF;
 SELECT * INTO STRICT c FROM domain_command WHERE logical_operation_id=p_logical FOR UPDATE;
 IF r.action_id IN('dashboard.start','dashboard.stop') THEN
  IF convert_from(v.request_bytes,'UTF8')::jsonb->>'schemaVersion' IS DISTINCT FROM 'RUNTIME_OWNER_INTENT/1'
     OR convert_from(v.request_bytes,'UTF8')::jsonb->>'action' IS DISTINCT FROM (CASE WHEN r.action_id='dashboard.start' THEN 'START' ELSE 'STOP' END)
     OR c.target_aggregate_kind<>'RUNTIME_INSTANCE'
     OR convert_from(v.request_bytes,'UTF8')::jsonb->>'runtimeInstanceId' IS DISTINCT FROM v.target_id::text
     OR convert_from(v.target_snapshot_bytes,'UTF8')::jsonb->>'runtimeInstanceId' IS DISTINCT FROM v.target_id::text
     OR convert_from(v.request_bytes,'UTF8')::jsonb->>'componentId' IS DISTINCT FROM convert_from(v.target_snapshot_bytes,'UTF8')::jsonb->>'componentId'
     OR convert_from(v.request_bytes,'UTF8')::jsonb->>'expectedRuntimeGeneration' IS DISTINCT FROM convert_from(v.target_snapshot_bytes,'UTF8')::jsonb->>'runtimeGeneration'
     OR convert_from(v.request_bytes,'UTF8')::jsonb->>'expectedActivationEpoch' IS DISTINCT FROM convert_from(v.target_snapshot_bytes,'UTF8')::jsonb->>'activationEpoch'
     OR convert_from(v.target_snapshot_bytes,'UTF8')::jsonb->>'applicationDeploymentEpoch' IS DISTINCT FROM dh.application_deployment_epoch::text
     OR convert_from(v.target_snapshot_bytes,'UTF8')::jsonb->>'platformIncarnationId' IS DISTINCT FROM pi.platform_incarnation_id::text THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_UI_RUNTIME_SNAPSHOT_BINDING_MISMATCH';
  END IF;
 ELSE
  IF c.target_aggregate_kind<>'GENERATION_JOB' OR convert_from(v.request_bytes,'UTF8')::jsonb->>'schemaVersion' IS DISTINCT FROM 'SPECIFICATION_OWNER_INPUT/1' OR convert_from(v.request_bytes,'UTF8')::jsonb->>'variant' NOT IN('OWNER_TEXT','SPECIFICATION_CANDIDATE') OR convert_from(v.request_bytes,'UTF8')::jsonb->>'jobId' IS DISTINCT FROM v.target_id::text THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_UI_SPECIFICATION_TARGET_MISMATCH';END IF;
 END IF;
 IF v.input_schema_digest<>r.input_schema_digest THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_UI_INPUT_SCHEMA_PIN_MISMATCH';END IF;
 SELECT * INTO i FROM owner_ui_accepted_intent WHERE logical_operation_id=p_logical;
 IF i.id IS NOT NULL THEN
  IF i.owner_id<>a.owner_id OR i.operation_id<>v.operation_id OR i.request_digest<>v.request_digest THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_UI_IDEMPOTENCY_CONFLICT';END IF;
  RETURN i;
 END IF;
 IF c.operation_id<>r.operation_id OR c.owner_id<>a.owner_id OR c.request_digest<>v.request_digest OR c.target_aggregate_id<>v.target_id OR c.caller_channel<>a.access_channel OR c.execution_descriptor_bytes IS DISTINCT FROM kcml_owner_ui_descriptor_bytes_v1(a.id,v.id,c.logical_operation_id,c.execution_context_id) OR c.platform_incarnation_id<>pi.platform_incarnation_id OR c.application_deployment_epoch<>dh.application_deployment_epoch OR c.state<>'ACCEPTED' OR c.terminal THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_UI_COMMAND_SCOPE_MISMATCH';END IF;
 INSERT INTO owner_ui_accepted_intent VALUES(c.execution_context_id,c.logical_operation_id,a.id,v.id,a.owner_id,r.operation_id,v.request_digest,v.target_snapshot_digest,r.contract_digest,r.worker_schema_digest,pi.platform_incarnation_id,dh.application_deployment_epoch,at) RETURNING * INTO i;
 RETURN i;
EXCEPTION WHEN NO_DATA_FOUND THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='OWNER_UI_ADMISSION_DEPENDENCY_UNAVAILABLE';
END;$$;
CREATE FUNCTION kcml_owner_ui_worker_context_v1(p_intent uuid)
RETURNS owner_ui_worker_context LANGUAGE plpgsql SECURITY DEFINER SET search_path FROM CURRENT AS $$
DECLARE i owner_ui_accepted_intent; v owner_ui_validated_input; r owner_ui_dispatch_registry; c domain_command;
 pi platform_incarnation; dh application_deployment_head; w owner_ui_worker_context;
BEGIN
 -- Global heads precede root claim, matching §51.6 lock ordering.
 SELECT * INTO STRICT pi FROM platform_incarnation WHERE singleton_key=1 FOR SHARE;
 SELECT * INTO STRICT dh FROM application_deployment_head WHERE singleton_key=1 FOR SHARE;
 SELECT * INTO STRICT i FROM owner_ui_accepted_intent WHERE id=p_intent;
 SELECT * INTO STRICT r FROM owner_ui_dispatch_registry WHERE operation_id=i.operation_id FOR SHARE;
 SELECT * INTO STRICT c FROM domain_command WHERE logical_operation_id=i.logical_operation_id FOR UPDATE;
 SELECT * INTO STRICT v FROM owner_ui_validated_input WHERE id=i.validated_input_id;
 IF pi.platform_incarnation_id<>dh.platform_incarnation_id OR pi.platform_incarnation_id<>i.platform_incarnation_id OR dh.application_deployment_epoch<>i.application_deployment_epoch THEN RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='OWNER_UI_WORKER_HEAD_CHANGED';END IF;
 IF c.execution_context_id<>i.id OR c.canonical_arguments_snapshot_id<>v.id OR c.execution_descriptor_bytes IS DISTINCT FROM kcml_owner_ui_descriptor_bytes_v1(i.authentication_acceptance_id,v.id,c.logical_operation_id,i.id) OR c.operation_id<>i.operation_id OR c.owner_id<>i.owner_id OR c.request_digest<>i.request_digest OR c.target_aggregate_id<>v.target_id OR v.request_digest<>i.request_digest OR v.target_snapshot_digest<>i.frozen_target_digest THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_UI_WORKER_INTENT_LINK_MISMATCH';END IF;
 IF c.error_digest IS NOT NULL THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='OWNER_UI_WORKER_RECONCILIATION_REQUIRED';END IF;
 IF c.terminal OR c.state<>'ACCEPTED' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='OWNER_UI_WORKER_PARENT_NOT_ADMISSIBLE';END IF;
 IF r.contract_digest<>i.contract_digest OR r.worker_schema_digest<>i.worker_schema_digest OR r.input_schema_digest<>v.input_schema_digest THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_UI_WORKER_REGISTRY_CHANGED';END IF;
 SELECT * INTO w FROM owner_ui_worker_context WHERE intent_id=i.id;
 IF w.id IS NOT NULL THEN RETURN w;END IF;
 -- Original OWNER session need not remain open: this is a retained committed
 -- intent, not fresh OWNER authentication. Current cancellation/head/registry
 -- and exact worker eligibility are independently enforced before any effect.
 INSERT INTO owner_ui_worker_context VALUES(gen_random_uuid(),i.id,c.logical_operation_id,i.owner_id,r.worker_operation_id,r.worker_execution_class,i.request_digest,i.frozen_target_digest,r.worker_schema_digest,pi.platform_incarnation_id,dh.application_deployment_epoch,clock_timestamp()) RETURNING * INTO w;
 RETURN w;
EXCEPTION WHEN NO_DATA_FOUND THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='OWNER_UI_WORKER_DEPENDENCY_UNAVAILABLE';
END;$$;
CREATE FUNCTION kcml_owner_ui_validate_worker_context_v1(p_context uuid,p_operation text,p_class text)
RETURNS owner_ui_worker_context LANGUAGE plpgsql SECURITY DEFINER SET search_path FROM CURRENT AS $$
DECLARE w owner_ui_worker_context; current_w owner_ui_worker_context;
BEGIN
 SELECT * INTO STRICT w FROM owner_ui_worker_context WHERE id=p_context;
 IF w.worker_operation_id<>p_operation OR w.worker_execution_class<>p_class THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_UI_WORKER_OPERATION_SCOPE_MISMATCH';
 END IF;
 SELECT * INTO STRICT current_w FROM kcml_owner_ui_worker_context_v1(w.intent_id);
 IF current_w.id<>w.id THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_UI_WORKER_CONTEXT_IDENTITY_MISMATCH';END IF;
 RETURN current_w;
EXCEPTION WHEN NO_DATA_FOUND THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='OWNER_UI_WORKER_CONTEXT_UNAVAILABLE';
END;$$;
