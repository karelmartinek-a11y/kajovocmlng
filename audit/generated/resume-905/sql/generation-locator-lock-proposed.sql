-- Bounded §49.4/§51.12 stable locator -> retained idempotency row handoff.
-- Invoke by trusted server adapter after authentication and class B heads, before
-- class E source/root locking. No API-key advisory lock after class B (§51.12).
-- INVOKER has existing server SELECT/FOR UPDATE rights; PUBLIC cannot execute.
-- Empty set is no retained locator, not success/new admission authority.
-- Fresh claim/command/root completion stays with the atomic create producer.
CREATE FUNCTION kcml_generation_lock_retained_locator_v1(p_context_id uuid)
RETURNS SETOF domain_idempotency_record
LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE c generation_create_trusted_context%ROWTYPE;
        l idempotency_locator%ROWTYPE;
        i domain_idempotency_record%ROWTYPE;
        key_digest bytea;
BEGIN
 SELECT * INTO c FROM generation_create_trusted_context WHERE id=p_context_id;
 IF NOT FOUND THEN
  RAISE EXCEPTION USING ERRCODE='P0002',MESSAGE='GENERATION_LOCK_CONTEXT_UNRESOLVED';
 END IF;
 -- Immutable context was produced through canonical auth+pin constructor. Read
 -- native descriptor client-key only after that authoritative binding, not input.
 key_digest=decode(substring(convert_from(c.execution_descriptor_bytes,'UTF8')::jsonb->>'clientKeyDigest' FROM 8),'hex');
 IF octet_length(key_digest) IS DISTINCT FROM 32 THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_LOCK_CONTEXT_KEY_INVALID';
 END IF;
 SELECT * INTO l FROM idempotency_locator
 WHERE operation_family='GENERATION' AND caller_authority_kind='OWNER_FULL'
 AND caller_stable_id=c.owner_id::text AND business_target_kind='CREATE_ROOT'
 AND business_target_id='generation_job' AND client_key_digest=key_digest FOR UPDATE;
 IF NOT FOUND THEN RETURN;END IF;
 IF l.client_request_digest IS DISTINCT FROM c.client_request_digest THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='IDEMPOTENCY_CONFLICT';
 END IF;
 -- Retained old descriptor scope wins over current deployment pin on replay.
 -- Class C1 always follows stable locator C0, before source/root class E.
 SELECT d.* INTO i FROM domain_idempotency_record d
 WHERE d.scope_digest=l.frozen_revision_digest AND d.key_digest=l.client_key_digest
 AND d.logical_operation_id=l.logical_operation_id FOR UPDATE;
 IF NOT FOUND OR i.request_digest IS DISTINCT FROM l.client_request_digest THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='GENERATION_RETAINED_IDEMPOTENCY_INCOMPLETE';
 END IF;
 RETURN NEXT i;
END;
$$;
REVOKE ALL ON FUNCTION kcml_generation_lock_retained_locator_v1(uuid) FROM PUBLIC;
