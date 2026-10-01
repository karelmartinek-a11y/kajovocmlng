-- No late lower-class reacquisition: reads validate current B values already locked by genuine in-memory verifier; E10OWNER already held by adapter.
-- Exact canonical constructor validations preserved; only server-preallocated contextID permits deferred root FK. Called late H after genuine B/C/E.
CREATE OR REPLACE FUNCTION public.kcml_generation_create_context_ordered_v1(
 p_authentication_acceptance_id uuid,
 p_context_id uuid,
 p_client_request_digest bytea,
 p_operation_contract_digest bytea,
 p_execution_descriptor_bytes bytea)
RETURNS public.generation_create_trusted_context LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE a public.generation_create_authentication_acceptance%ROWTYPE;
        o public.owner_identity%ROWTYPE;
        s public.owner_session%ROWTYPE;
        api public.owner_api_credential%ROWTYPE;
        pi public.platform_incarnation%ROWTYPE;
        dh public.application_deployment_head%ROWTYPE;
        c public.generation_create_trusted_context%ROWTYPE;
        now_at timestamptz;
        pin public.generation_create_contract_pin%ROWTYPE;
        descriptor jsonb;
        expected_descriptor jsonb;
        expected_descriptor_bytes bytea;
BEGIN
 IF octet_length(p_client_request_digest) IS DISTINCT FROM 32
    OR octet_length(p_operation_contract_digest) IS DISTINCT FROM 32
    OR p_execution_descriptor_bytes IS NULL OR octet_length(p_execution_descriptor_bytes)=0 THEN
  RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='GENERATION_CONTEXT_INPUT_INVALID';
 END IF;
 SELECT * INTO a FROM public.generation_create_authentication_acceptance
 WHERE id=p_authentication_acceptance_id;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0002',MESSAGE='GENERATION_AUTH_RECEIPT_UNRESOLVED';END IF;
 -- Receipt is immutable. Only persisted identity, never arbitrary actor metadata.
 SELECT platform_incarnation_id INTO STRICT pi.platform_incarnation_id FROM public.platform_incarnation WHERE singleton_key=1;
 SELECT platform_incarnation_id,application_deployment_epoch INTO STRICT dh.platform_incarnation_id,dh.application_deployment_epoch FROM public.application_deployment_head WHERE singleton_key=1;
 SELECT * INTO pin FROM public.generation_create_contract_pin WHERE application_deployment_epoch=dh.application_deployment_epoch;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0002',MESSAGE='GENERATION_CONTRACT_PIN_UNRESOLVED';END IF;
 IF pin.contract_digest IS DISTINCT FROM p_operation_contract_digest THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_CONTRACT_PIN_MISMATCH';
 END IF;
 BEGIN
  IF NOT(convert_from(p_execution_descriptor_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) THEN
   RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='GENERATION_DESCRIPTOR_ENCODING_INVALID';
  END IF;
  descriptor=convert_from(p_execution_descriptor_bytes,'UTF8')::jsonb;
 EXCEPTION WHEN SQLSTATE '22021' OR SQLSTATE '22P02' THEN
  RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='GENERATION_DESCRIPTOR_ENCODING_INVALID';
 END;
 IF jsonb_typeof(descriptor->'clientKeyDigest')<>'string' OR octet_length(descriptor->>'clientKeyDigest') IS DISTINCT FROM 71 OR descriptor->>'clientKeyDigest' !~ '^sha256:[0-9a-f]{64}$' THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_DESCRIPTOR_KEY_DIGEST_INVALID';
 END IF;
 expected_descriptor=jsonb_build_object('callerAuthorityKind','OWNER_FULL','clientKeyDigest',descriptor->>'clientKeyDigest','operationContractId',pin.operation_id,'operationContractRevision',pin.operation_contract_revision,'stableBusinessTargetKey','CREATE_ROOT:generation_job','stableCallerObjectId',a.owner_id::text,'stableCallerRevisionId',NULL);
 IF descriptor IS DISTINCT FROM expected_descriptor THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_DESCRIPTOR_PIN_BINDING_MISMATCH';
 END IF;
 -- The pinned seven-field mask contains only strings and null. Produce exact
 -- lexicographic-key UTF8 bytes, no jsonb::text ordering/whitespace assumptions.
 expected_descriptor_bytes=convert_to('{"callerAuthorityKind":"OWNER_FULL","clientKeyDigest":'||to_json(descriptor->>'clientKeyDigest')::text||',"operationContractId":'||to_json(pin.operation_id)::text||',"operationContractRevision":'||to_json(pin.operation_contract_revision)::text||',"stableBusinessTargetKey":"CREATE_ROOT:generation_job","stableCallerObjectId":'||to_json(a.owner_id::text)::text||',"stableCallerRevisionId":null}','UTF8');
 IF p_execution_descriptor_bytes IS DISTINCT FROM expected_descriptor_bytes THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_DESCRIPTOR_NONCANONICAL';
 END IF;
 IF dh.platform_incarnation_id<>pi.platform_incarnation_id THEN
  RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='GENERATION_CONTEXT_INCARNATION_MISMATCH';
 END IF;
 IF a.access_channel='OWNER_API_KEY' THEN
  SELECT credential_version,fingerprint INTO STRICT api.credential_version,api.fingerprint FROM public.owner_api_credential WHERE singleton_key=1;
 END IF;
 SELECT id,session_epoch INTO STRICT o.id,o.session_epoch FROM public.owner_identity WHERE singleton_key=1 AND id=a.owner_id;
 now_at=clock_timestamp();
 IF a.accepted_at>now_at THEN
  RAISE EXCEPTION USING ERRCODE='28000',MESSAGE='GENERATION_AUTH_RECEIPT_FUTURE';
 END IF;
 IF a.access_channel='OWNER_SESSION' THEN
  SELECT owner_identity_id,lookup_digest,session_epoch,revoked_at,expires_at INTO STRICT s.owner_identity_id,s.lookup_digest,s.session_epoch,s.revoked_at,s.expires_at FROM public.owner_session WHERE id=a.session_id;
  IF s.owner_identity_id<>o.id OR s.lookup_digest<>a.session_lookup_digest
     OR s.session_epoch<>a.session_epoch OR s.session_epoch<>o.session_epoch
     OR s.revoked_at IS NOT NULL OR s.expires_at<=now_at THEN
   RAISE EXCEPTION USING ERRCODE='28000',MESSAGE='GENERATION_SESSION_AUTH_STALE';
  END IF;
 ELSE
  IF api.credential_version<>a.api_credential_version
     OR api.fingerprint<>a.api_credential_fingerprint THEN
   RAISE EXCEPTION USING ERRCODE='28000',MESSAGE='GENERATION_API_AUTH_STALE';
  END IF;
 END IF;
 INSERT INTO public.generation_create_trusted_context
 (id,owner_id,authentication_acceptance_id,initiating_access_channel,
 platform_incarnation_id,application_deployment_epoch,operation_contract_digest,
 client_request_digest,execution_descriptor_bytes,execution_descriptor_digest,accepted_at)
 VALUES(p_context_id,o.id,a.id,a.access_channel,pi.platform_incarnation_id,
 dh.application_deployment_epoch,p_operation_contract_digest,p_client_request_digest,
 p_execution_descriptor_bytes,sha256(p_execution_descriptor_bytes),now_at)
 RETURNING * INTO c;
 RETURN c;
END;
$$;
REVOKE ALL ON FUNCTION public.kcml_generation_create_context_ordered_v1(uuid,uuid,bytea,bytea,bytea) FROM PUBLIC;
ALTER FUNCTION public.kcml_generation_create_context_ordered_v1(uuid,uuid,bytea,bytea,bytea) OWNER TO kcml_generation_context_builder;
GRANT EXECUTE ON FUNCTION public.kcml_generation_create_context_ordered_v1(uuid,uuid,bytea,bytea,bytea) TO kcml_domain_writer;
