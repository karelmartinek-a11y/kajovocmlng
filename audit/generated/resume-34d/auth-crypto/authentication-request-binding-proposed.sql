-- Technical §51.20/49.4 receipt-to-exact-command acceptance binding.
-- Existing unbound retained receipts remain readable but cannot authorize NEW
-- context creation. No historical immutable auth receipt is rewritten.
ALTER TABLE generation_create_authentication_acceptance
 ADD COLUMN authenticated_request_digest bytea NULL
  CHECK(authenticated_request_digest IS NULL OR octet_length(authenticated_request_digest)=32),
 ADD COLUMN authenticated_descriptor_digest bytea NULL
  CHECK(authenticated_descriptor_digest IS NULL OR octet_length(authenticated_descriptor_digest)=32),
 ADD COLUMN api_credential_activation_epoch bigint NULL
  CHECK(api_credential_activation_epoch IS NULL OR api_credential_activation_epoch>=1);
CREATE FUNCTION kcml_generation_auth_request_binding_v1()
RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE a generation_create_authentication_acceptance%ROWTYPE;
        api_epoch bigint;
BEGIN
 SELECT * INTO STRICT a FROM generation_create_authentication_acceptance
 WHERE id=NEW.authentication_acceptance_id;
 IF a.authenticated_request_digest IS NULL OR a.authenticated_request_digest IS DISTINCT FROM NEW.client_request_digest THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_AUTH_REQUEST_BINDING_MISMATCH';
 END IF;
 IF a.authenticated_descriptor_digest IS NULL OR a.authenticated_descriptor_digest IS DISTINCT FROM NEW.execution_descriptor_digest THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_AUTH_DESCRIPTOR_BINDING_MISMATCH';
 END IF;
 IF a.access_channel='OWNER_API_KEY' THEN
  SELECT credential_activation_epoch INTO STRICT api_epoch FROM owner_api_credential WHERE singleton_key=1 FOR SHARE;
  IF a.api_credential_activation_epoch IS NULL OR a.api_credential_activation_epoch IS DISTINCT FROM api_epoch THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_AUTH_CREDENTIAL_EPOCH_MISMATCH';
  END IF;
 END IF;
 RETURN NEW;
END;
$$;
CREATE TRIGGER generation_auth_request_binding BEFORE INSERT
ON generation_create_trusted_context FOR EACH ROW
EXECUTE FUNCTION kcml_generation_auth_request_binding_v1();
-- All authentication producers, including OWNER session, MUST bind verified
-- material + current credential/session state to exact request digest in the
-- SAME transaction. Session receipt also retains existing own epoch/expiry guards.

GRANT SELECT(credential_activation_epoch) ON owner_api_credential TO kcml_generation_context_builder;

ALTER TABLE generation_create_trusted_context ADD CONSTRAINT generation_auth_receipt_single_context UNIQUE(authentication_acceptance_id);
