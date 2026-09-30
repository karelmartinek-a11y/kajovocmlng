-- Exact scoped materialization: §25.3, §26.1, §49.4, §51.2, §51.5-6/51.11.
-- Symbolic OWNER/OWNER_API identifies the logical singleton; §51.11 mandates
-- SMALLINT singleton_key=1 as its physical key. No text-key lookup is permitted.
-- Authentication acceptance is a server-owned immutable receipt written only by
-- the canonical authentication service after verifying actual session/API material.
-- It is not a client input, model proposal or reusable authorization boolean.
CREATE TABLE generation_create_authentication_acceptance (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES owner_identity(id) ON DELETE RESTRICT,
  access_channel text NOT NULL CHECK(access_channel IN ('OWNER_SESSION','OWNER_API_KEY')),
  session_id uuid NULL REFERENCES owner_session(id) ON DELETE RESTRICT,
  session_epoch bigint NULL CHECK(session_epoch>=0),
  session_lookup_digest bytea NULL CHECK(octet_length(session_lookup_digest)=32),
  api_credential_version bigint NULL CHECK(api_credential_version>=1),
  api_credential_fingerprint text NULL,
  accepted_at timestamptz NOT NULL,
  UNIQUE(id,owner_id,access_channel),
  CHECK((access_channel='OWNER_SESSION' AND session_id IS NOT NULL AND session_epoch IS NOT NULL AND session_lookup_digest IS NOT NULL AND api_credential_version IS NULL AND api_credential_fingerprint IS NULL)
     OR (access_channel='OWNER_API_KEY' AND session_id IS NULL AND session_epoch IS NULL AND session_lookup_digest IS NULL AND api_credential_version IS NOT NULL AND api_credential_fingerprint IS NOT NULL))
);
CREATE TABLE generation_create_trusted_context (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES owner_identity(id) ON DELETE RESTRICT,
  authentication_acceptance_id uuid NOT NULL REFERENCES generation_create_authentication_acceptance(id) ON DELETE RESTRICT,
  initiating_access_channel text NOT NULL CHECK(initiating_access_channel IN ('OWNER_SESSION','OWNER_API_KEY')),
  platform_incarnation_id uuid NOT NULL,
  application_deployment_epoch bigint NOT NULL CHECK(application_deployment_epoch>=0),
  operation_contract_digest bytea NOT NULL CHECK(octet_length(operation_contract_digest)=32),
  client_request_digest bytea NOT NULL CHECK(octet_length(client_request_digest)=32),
  execution_descriptor_bytes bytea NOT NULL CHECK(octet_length(execution_descriptor_bytes)>0),
  execution_descriptor_digest bytea NOT NULL CHECK(octet_length(execution_descriptor_digest)=32),
  accepted_at timestamptz NOT NULL,
  UNIQUE(id,owner_id,initiating_access_channel),
  FOREIGN KEY(application_deployment_epoch,operation_contract_digest) REFERENCES generation_create_contract_pin(application_deployment_epoch,contract_digest) ON DELETE RESTRICT,
  FOREIGN KEY(authentication_acceptance_id,owner_id,initiating_access_channel)
    REFERENCES generation_create_authentication_acceptance(id,owner_id,access_channel) ON DELETE RESTRICT,
  CHECK(execution_descriptor_digest=sha256(execution_descriptor_bytes))
);
CREATE TRIGGER generation_create_authentication_immutable BEFORE UPDATE
ON generation_create_authentication_acceptance FOR EACH ROW
EXECUTE FUNCTION kcml_reject_generation_create_snapshot_update_v1();
CREATE TRIGGER generation_create_context_immutable BEFORE UPDATE
ON generation_create_trusted_context FOR EACH ROW
EXECUTE FUNCTION kcml_reject_generation_create_snapshot_update_v1();
-- Canonical service role grants are an installation prerequisite:
-- authentication writer alone INSERTs authentication acceptance;
-- domain writer has SELECT receipt + EXECUTE constructor, no INSERT receipt;
-- generated handlers have no DB credential/network path (§51.2).
-- Controlled-schema SECURITY DEFINER is owned by restricted NOLOGIN builder.
-- Exact infrastructure grants are in generation-context-role-bindings.sql.
-- Installer pins its controlled schema and puts pg_temp explicitly LAST.
-- Without this, temp relation shadowing could bypass SECURITY DEFINER reads.
SELECT set_config('search_path',format('%I,pg_catalog,pg_temp',current_schema()),false);
CREATE OR REPLACE FUNCTION kcml_generation_create_context_v1(
 p_authentication_acceptance_id uuid,
 p_client_request_digest bytea,
 p_operation_contract_digest bytea,
 p_execution_descriptor_bytes bytea)
RETURNS generation_create_trusted_context LANGUAGE plpgsql SECURITY DEFINER SET search_path FROM CURRENT AS $$
DECLARE a generation_create_authentication_acceptance%ROWTYPE;
        o owner_identity%ROWTYPE;
        s owner_session%ROWTYPE;
        api owner_api_credential%ROWTYPE;
        pi platform_incarnation%ROWTYPE;
        dh application_deployment_head%ROWTYPE;
        c generation_create_trusted_context%ROWTYPE;
        now_at timestamptz;
        pin generation_create_contract_pin%ROWTYPE;
        descriptor jsonb;
        expected_descriptor jsonb;
        expected_descriptor_bytes bytea;
BEGIN
 IF octet_length(p_client_request_digest) IS DISTINCT FROM 32
    OR octet_length(p_operation_contract_digest) IS DISTINCT FROM 32
    OR p_execution_descriptor_bytes IS NULL OR octet_length(p_execution_descriptor_bytes)=0 THEN
  RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='GENERATION_CONTEXT_INPUT_INVALID';
 END IF;
 SELECT * INTO a FROM generation_create_authentication_acceptance
 WHERE id=p_authentication_acceptance_id;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0002',MESSAGE='GENERATION_AUTH_RECEIPT_UNRESOLVED';END IF;
 -- Receipt is immutable. Only persisted identity, never arbitrary actor metadata.
 SELECT platform_incarnation_id INTO STRICT pi.platform_incarnation_id FROM platform_incarnation WHERE singleton_key=1 FOR SHARE;
 SELECT platform_incarnation_id,application_deployment_epoch INTO STRICT dh.platform_incarnation_id,dh.application_deployment_epoch FROM application_deployment_head WHERE singleton_key=1 FOR SHARE;
 SELECT * INTO pin FROM generation_create_contract_pin WHERE application_deployment_epoch=dh.application_deployment_epoch;
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
  SELECT credential_version,fingerprint INTO STRICT api.credential_version,api.fingerprint FROM owner_api_credential WHERE singleton_key=1 FOR SHARE;
 END IF;
 SELECT id,session_epoch INTO STRICT o.id,o.session_epoch FROM owner_identity WHERE singleton_key=1 AND id=a.owner_id FOR SHARE;
 now_at=clock_timestamp();
 IF a.accepted_at>now_at THEN
  RAISE EXCEPTION USING ERRCODE='28000',MESSAGE='GENERATION_AUTH_RECEIPT_FUTURE';
 END IF;
 IF a.access_channel='OWNER_SESSION' THEN
  SELECT owner_identity_id,lookup_digest,session_epoch,revoked_at,expires_at INTO STRICT s.owner_identity_id,s.lookup_digest,s.session_epoch,s.revoked_at,s.expires_at FROM owner_session WHERE id=a.session_id FOR SHARE;
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
 INSERT INTO generation_create_trusted_context
 (id,owner_id,authentication_acceptance_id,initiating_access_channel,
 platform_incarnation_id,application_deployment_epoch,operation_contract_digest,
 client_request_digest,execution_descriptor_bytes,execution_descriptor_digest,accepted_at)
 VALUES(gen_random_uuid(),o.id,a.id,a.access_channel,pi.platform_incarnation_id,
 dh.application_deployment_epoch,p_operation_contract_digest,p_client_request_digest,
 p_execution_descriptor_bytes,sha256(p_execution_descriptor_bytes),now_at)
 RETURNING * INTO c;
 RETURN c;
END;
$$;
-- Persist context before dispatch; main mutation still rechecks current heads,
-- recovery, idempotency and own admission under its canonical transaction locks.
-- No MFA requirement or new scope/role business permission is added to API-key use.
-- The SQL constructor does not implement session/API token hashing; authenticating
-- token material belongs to the canonical authentication service, with acceptance
-- INSERT restricted to that writer. Test receipts prove consuming current records,
-- not deployed service credential verification.

REVOKE ALL ON FUNCTION kcml_generation_create_context_v1(uuid,bytea,bytea,bytea) FROM PUBLIC;
