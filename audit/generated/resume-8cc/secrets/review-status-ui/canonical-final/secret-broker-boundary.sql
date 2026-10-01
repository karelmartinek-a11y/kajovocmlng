-- REVIEW CANDIDATE ONLY: §51.6 actual source/target parent root plan remains
-- OPEN. Do not activate/embed as effective SQL before those roots/FKs/locks
-- are integrated. Bounded consumer tests below are not full lock-order proof.
-- Exact consuming boundaries §§8.7–8.8,49.22.1,50.23.
-- Scope/head/binding producers must originate from trusted runtime gateway and
-- canonical source/target activation repositories. Fixture DML is not proof of
-- those producers. No generation.create or secret.create context substitution.
CREATE TABLE kcml_secret_v1.broker_subject_head (
 object_id uuid PRIMARY KEY, revision_id uuid NOT NULL, activation_set_revision uuid NOT NULL,
 invalidation_epoch bigint NOT NULL CHECK(invalidation_epoch>=0),
 completed_invalidation_epoch bigint NOT NULL CHECK(completed_invalidation_epoch>=0 AND completed_invalidation_epoch<=invalidation_epoch)
);
CREATE TABLE kcml_secret_v1.broker_binding (
 id uuid PRIMARY KEY, revision bigint NOT NULL CHECK(revision>0),
 secret_id uuid NOT NULL REFERENCES kcml_secret_v1.secret_record(id),
 source_object_id uuid NOT NULL REFERENCES kcml_secret_v1.broker_subject_head(object_id), source_revision_id uuid NOT NULL,
 target_object_id uuid NOT NULL REFERENCES kcml_secret_v1.broker_subject_head(object_id), target_revision_id uuid NOT NULL,
 activation_set_revision uuid NOT NULL, purpose text NOT NULL CHECK(purpose<>''),
 consumer_step text NOT NULL CHECK(consumer_step<>''), placement_path text NOT NULL CHECK(placement_path<>''),
 binding_bytes bytea NOT NULL, binding_digest bytea NOT NULL CHECK(binding_digest=sha256(binding_bytes)),
 activated_at timestamptz NOT NULL, expires_at timestamptz, revoked_at timestamptz,
 CHECK(expires_at IS NULL OR expires_at>activated_at), CHECK(revoked_at IS NULL OR revoked_at>=activated_at),
 CHECK(convert_from(binding_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(binding_bytes,'UTF8')::jsonb=jsonb_build_object('bindingId',id::text,'bindingRevision',revision::text,'secretId',secret_id::text,'sourceObjectId',source_object_id::text,'sourceRevisionId',source_revision_id::text,'targetObjectId',target_object_id::text,'targetRevisionId',target_revision_id::text,'activationSetRevision',activation_set_revision::text,'purpose',purpose,'consumerStep',consumer_step,'placementPath',placement_path))
);
CREATE TABLE kcml_secret_v1.broker_use_scope (
 id uuid PRIMARY KEY, logical_operation_id uuid NOT NULL REFERENCES public.domain_command(logical_operation_id),
 execution_context_id uuid NOT NULL, execution_descriptor_digest bytea NOT NULL CHECK(octet_length(execution_descriptor_digest)=32),
 binding_id uuid NOT NULL REFERENCES kcml_secret_v1.broker_binding(id), binding_revision bigint NOT NULL,
 binding_digest bytea NOT NULL CHECK(octet_length(binding_digest)=32), stable_name text NOT NULL,
 source_object_id uuid NOT NULL, source_revision_id uuid NOT NULL, target_object_id uuid NOT NULL,target_revision_id uuid NOT NULL,
 activation_set_revision uuid NOT NULL,purpose text NOT NULL CHECK(purpose<>''), consumer_step text NOT NULL CHECK(consumer_step<>''),placement_path text NOT NULL CHECK(placement_path<>''),
 consumer_declaration_bytes bytea NOT NULL,consumer_declaration_digest bytea NOT NULL CHECK(consumer_declaration_digest=sha256(consumer_declaration_bytes)),
 pending_capability_request_id uuid NOT NULL, correlation_id uuid NOT NULL, expires_at timestamptz NOT NULL, revoked_at timestamptz,
 UNIQUE(logical_operation_id,pending_capability_request_id)
);
CREATE TABLE kcml_secret_v1.broker_resolution (
 id uuid PRIMARY KEY,scope_id uuid NOT NULL REFERENCES kcml_secret_v1.broker_use_scope(id),
 logical_operation_id uuid NOT NULL REFERENCES public.domain_command(logical_operation_id), pending_capability_request_id uuid NOT NULL,
 binding_id uuid NOT NULL,binding_revision bigint NOT NULL,binding_digest bytea NOT NULL,
 source_object_id uuid NOT NULL,source_revision_id uuid NOT NULL,target_object_id uuid NOT NULL,target_revision_id uuid NOT NULL,
 activation_set_revision uuid NOT NULL,purpose text NOT NULL,consumer_step text NOT NULL,placement_path text NOT NULL,correlation_id uuid NOT NULL,
 secret_id uuid NOT NULL REFERENCES kcml_secret_v1.secret_record(id),secret_version_id uuid NOT NULL,secret_activation_epoch bigint NOT NULL,
 expires_at timestamptz NOT NULL,created_at timestamptz NOT NULL,
 FOREIGN KEY(secret_id,secret_version_id) REFERENCES kcml_secret_v1.secret_version(secret_id,id),
 UNIQUE(logical_operation_id,pending_capability_request_id)
);
CREATE TABLE kcml_secret_v1.broker_resolution_audit (
 id uuid PRIMARY KEY,scope_id uuid,correlation_id uuid NOT NULL,resolution_id uuid REFERENCES kcml_secret_v1.broker_resolution(id),
 diagnostic text NOT NULL,occurred_at timestamptz NOT NULL
);
CREATE FUNCTION kcml_secret_v1.broker_append_only_v1() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$BEGIN
 RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_BROKER_EVIDENCE_IMMUTABLE';END$$;
CREATE TRIGGER broker_resolution_immutable BEFORE UPDATE OR DELETE ON kcml_secret_v1.broker_resolution FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.broker_append_only_v1();
CREATE TRIGGER broker_resolution_audit_immutable BEFORE UPDATE OR DELETE ON kcml_secret_v1.broker_resolution_audit FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.broker_append_only_v1();
CREATE FUNCTION kcml_secret_v1.broker_resolve_v1(p_scope uuid,p_pending uuid,p_correlation uuid)
 RETURNS TABLE(diagnostic text,resolution_id uuid,protected_row jsonb)
 LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE s kcml_secret_v1.broker_use_scope; b kcml_secret_v1.broker_binding;
 sr kcml_secret_v1.secret_record; v kcml_secret_v1.secret_version;
 sh kcml_secret_v1.broker_subject_head; th kcml_secret_v1.broker_subject_head;
 c public.domain_command; n public.canonical_protected_nonce_reservation; k public.canonical_master_key_generation; old kcml_secret_v1.broker_resolution; at timestamptz=clock_timestamp(); d text;
BEGIN
 -- Missing current heads and invalidation producers are blocked, never caller
 -- booleans. Parent root locks precede dependent binding/scope rows.
 SELECT * INTO s FROM kcml_secret_v1.broker_use_scope WHERE id=p_scope;
 IF NOT FOUND THEN d='SECRET_USE_CONTEXT_UNAVAILABLE';
 ELSE
  SELECT * INTO b FROM kcml_secret_v1.broker_binding WHERE id=s.binding_id;
  SELECT * INTO sr FROM kcml_secret_v1.secret_record WHERE id=b.secret_id FOR UPDATE;
  PERFORM 1 FROM kcml_secret_v1.broker_subject_head WHERE object_id IN(s.source_object_id,s.target_object_id) ORDER BY object_id FOR UPDATE;
  SELECT * INTO sh FROM kcml_secret_v1.broker_subject_head WHERE object_id=s.source_object_id;
  SELECT * INTO th FROM kcml_secret_v1.broker_subject_head WHERE object_id=s.target_object_id;
  SELECT * INTO b FROM kcml_secret_v1.broker_binding WHERE id=s.binding_id FOR UPDATE;
  SELECT * INTO s FROM kcml_secret_v1.broker_use_scope WHERE id=p_scope FOR UPDATE;
  SELECT * INTO c FROM public.domain_command WHERE logical_operation_id=s.logical_operation_id FOR UPDATE;
  at=clock_timestamp(); -- after all blocking guards, never pre-wait expiry
  IF s.pending_capability_request_id IS DISTINCT FROM p_pending OR s.correlation_id IS DISTINCT FROM p_correlation THEN d='SECRET_PENDING_CAPABILITY_MISMATCH';
  ELSIF s.revoked_at IS NOT NULL OR s.expires_at<=at THEN d='SECRET_USE_CONTEXT_EXPIRED';
  ELSIF c.logical_operation_id IS NULL OR c.execution_context_id IS DISTINCT FROM s.execution_context_id OR c.execution_descriptor_digest IS DISTINCT FROM s.execution_descriptor_digest OR c.terminal OR c.state IN('CANCELLED','FAILED') THEN d='SECRET_USE_COMMAND_SCOPE_MISMATCH';
  ELSIF c.operation_id IN('generation.job.create','secret.create') THEN d='SECRET_CREATE_CONTEXT_NOT_RUNTIME_USE';
  ELSIF sh.object_id IS NULL OR th.object_id IS NULL THEN d='SECRET_SUBJECT_HEAD_UNAVAILABLE';
  ELSIF sh.revision_id IS DISTINCT FROM s.source_revision_id OR th.revision_id IS DISTINCT FROM s.target_revision_id OR sh.activation_set_revision IS DISTINCT FROM s.activation_set_revision OR th.activation_set_revision IS DISTINCT FROM s.activation_set_revision THEN d='SECRET_SOURCE_TARGET_REVISION_STALE';
  ELSIF sh.invalidation_epoch<>sh.completed_invalidation_epoch OR th.invalidation_epoch<>th.completed_invalidation_epoch THEN d='SECRET_INVALIDATION_BARRIER_PENDING';
  ELSIF b.id IS NULL OR b.revoked_at IS NOT NULL OR (b.expires_at IS NOT NULL AND b.expires_at<=at) OR b.revision IS DISTINCT FROM s.binding_revision OR b.binding_digest IS DISTINCT FROM s.binding_digest THEN d='SECRET_BINDING_STALE';
  ELSIF (b.source_object_id,b.source_revision_id,b.target_object_id,b.target_revision_id,b.activation_set_revision,b.purpose,b.consumer_step,b.placement_path) IS DISTINCT FROM (s.source_object_id,s.source_revision_id,s.target_object_id,s.target_revision_id,s.activation_set_revision,s.purpose,s.consumer_step,s.placement_path) THEN d='SECRET_BINDING_SCOPE_MISMATCH';
  ELSIF sr.id IS NULL OR sr.deleted_at IS NOT NULL OR sr.stable_name IS DISTINCT FROM s.stable_name THEN d='SECRET_REFERENCE_UNAVAILABLE';
  ELSIF sr.expires_at IS NOT NULL AND sr.expires_at<=at THEN d='SECRET_EXPIRED';
  ELSE
   SELECT * INTO v FROM kcml_secret_v1.secret_version WHERE secret_id=sr.id AND id=sr.active_version_id;
   IF v.id IS NULL OR v.lifecycle<>'ACTIVE' THEN d='SECRET_ACTIVE_VERSION_UNAVAILABLE';
   ELSE
    SELECT * INTO n FROM public.canonical_protected_nonce_reservation WHERE key_id=v.key_id AND nonce=v.nonce AND purpose='SECRET_IMMUTABLE_VERSION' AND protected_object_id=v.id;
    SELECT * INTO k FROM public.canonical_master_key_generation WHERE key_id=v.key_id;
    IF n.key_id IS NULL OR k.key_id IS NULL OR n.ciphertext_digest IS DISTINCT FROM sha256(v.ciphertext) OR (convert_from(n.authenticated_metadata_bytes,'UTF8')::jsonb->'identity'->>'trustedContextId') IS DISTINCT FROM v.creator_context_id::text THEN d='SECRET_PROTECTED_ROW_AUTHORITY_UNAVAILABLE'; END IF;
   END IF;
  END IF;
 END IF;
 IF d IS NOT NULL THEN
  INSERT INTO kcml_secret_v1.broker_resolution_audit VALUES(gen_random_uuid(),p_scope,p_correlation,NULL,d,at);
  RETURN QUERY SELECT d,NULL::uuid,NULL::jsonb;RETURN;
 END IF;
 IF EXISTS(SELECT 1 FROM kcml_secret_v1.broker_resolution prior WHERE prior.logical_operation_id=s.logical_operation_id AND prior.secret_id=sr.id AND (prior.secret_version_id<>v.id OR prior.secret_activation_epoch<>sr.secret_activation_epoch)) THEN
  d='SECRET_OPERATION_VERSION_PIN_CONFLICT';
  INSERT INTO kcml_secret_v1.broker_resolution_audit VALUES(gen_random_uuid(),p_scope,p_correlation,NULL,d,at);
  RETURN QUERY SELECT d,NULL::uuid,NULL::jsonb;RETURN;
 END IF;
 SELECT * INTO old FROM kcml_secret_v1.broker_resolution WHERE logical_operation_id=s.logical_operation_id AND pending_capability_request_id=p_pending;
 IF FOUND THEN
  IF old.scope_id<>s.id OR old.binding_digest<>s.binding_digest OR old.secret_version_id<>v.id OR old.secret_activation_epoch<>sr.secret_activation_epoch THEN
   d='SECRET_OPERATION_VERSION_PIN_CONFLICT';
   INSERT INTO kcml_secret_v1.broker_resolution_audit VALUES(gen_random_uuid(),p_scope,p_correlation,NULL,d,at);
   RETURN QUERY SELECT d,NULL::uuid,NULL::jsonb;RETURN;
  END IF;
 ELSE
  INSERT INTO kcml_secret_v1.broker_resolution VALUES(gen_random_uuid(),s.id,s.logical_operation_id,p_pending,b.id,b.revision,b.binding_digest,s.source_object_id,s.source_revision_id,s.target_object_id,s.target_revision_id,s.activation_set_revision,s.purpose,s.consumer_step,s.placement_path,p_correlation,sr.id,v.id,sr.secret_activation_epoch,least(s.expires_at,b.expires_at,sr.expires_at),at) RETURNING * INTO old;
 END IF;
 INSERT INTO kcml_secret_v1.broker_resolution_audit VALUES(gen_random_uuid(),p_scope,p_correlation,old.id,'AUTHORIZED_PROTECTED_CANDIDATE',at);
 -- Internal service only. Ciphertext remains inaccessible to handlers; creator
 -- context metadata comes from its own immutable producer, not this use scope.
 RETURN QUERY SELECT 'RESOLVED'::text,old.id,jsonb_build_object('version',to_jsonb(v),'consumerDeclarationHex',encode(s.consumer_declaration_bytes,'hex'),'scopeId',s.id,'consumerPurpose',s.purpose,'resolutionId',old.id,'protectedAuthority',jsonb_build_object('metadataHex',encode(n.authenticated_metadata_bytes,'hex'),'keyFingerprintHex',encode(k.key_fingerprint,'hex'),'keyProfileDigestHex',encode(k.crypto_profile_digest,'hex'),'keyProfileBytesHex',(SELECT encode(cp.profile_bytes,'hex') FROM public.canonical_authenticated_crypto_profile cp WHERE cp.profile_digest=k.crypto_profile_digest),'keyGeneration',k.key_generation,'creationLogicalOperationId',n.logical_operation_id,'ciphertextDigestHex',encode(n.ciphertext_digest,'hex')));
END$$;
REVOKE ALL ON ALL TABLES IN SCHEMA kcml_secret_v1 FROM PUBLIC;
REVOKE ALL ON FUNCTION kcml_secret_v1.broker_resolve_v1(uuid,uuid,uuid) FROM PUBLIC;
-- Coordinator must bind execute to existing canonical broker service identity,
-- never runtime handlers; role/context/UDS publisher proof remains mandatory.

-- Actual plaintext-use success is published only AFTER canonical open and
-- native consumer validation in the same held transaction. No caller flag.
CREATE TABLE kcml_secret_v1.broker_issuance (
 resolution_id uuid PRIMARY KEY REFERENCES kcml_secret_v1.broker_resolution(id),
 scope_id uuid NOT NULL REFERENCES kcml_secret_v1.broker_use_scope(id),
 pending_capability_request_id uuid NOT NULL, correlation_id uuid NOT NULL,
 issued_at timestamptz NOT NULL
);
CREATE TRIGGER broker_issuance_immutable BEFORE UPDATE OR DELETE ON kcml_secret_v1.broker_issuance FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.broker_append_only_v1();
CREATE FUNCTION kcml_secret_v1.broker_record_issuance_v1(p_resolution uuid,p_scope uuid,p_pending uuid,p_correlation uuid)
 RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE r kcml_secret_v1.broker_resolution; sr kcml_secret_v1.secret_record; old kcml_secret_v1.broker_issuance;
BEGIN
 SELECT * INTO STRICT r FROM kcml_secret_v1.broker_resolution WHERE id=p_resolution;
 SELECT * INTO STRICT sr FROM kcml_secret_v1.secret_record WHERE id=r.secret_id FOR UPDATE;
 IF (r.scope_id,r.pending_capability_request_id,r.correlation_id) IS DISTINCT FROM (p_scope,p_pending,p_correlation) OR r.expires_at<=clock_timestamp() THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_ISSUANCE_SCOPE_OR_EXPIRY_MISMATCH';
 END IF;
 IF sr.active_version_id IS DISTINCT FROM r.secret_version_id OR sr.secret_activation_epoch<>r.secret_activation_epoch THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_ISSUANCE_ACTIVE_EPOCH_STALE';
 END IF;
 -- Same pending capability request replays one immutable issuance; never a
 -- fresh version or another side-effect operation. Transport reconciliation
 -- remains current gateway's responsibility, not inferred from this row.
 INSERT INTO kcml_secret_v1.broker_issuance VALUES(r.id,p_scope,p_pending,p_correlation,clock_timestamp()) ON CONFLICT(resolution_id) DO NOTHING;
 SELECT * INTO STRICT old FROM kcml_secret_v1.broker_issuance WHERE resolution_id=r.id;
 IF (old.scope_id,old.pending_capability_request_id,old.correlation_id) IS DISTINCT FROM (p_scope,p_pending,p_correlation) THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_ISSUANCE_REPLAY_CONFLICT';
 END IF;
 RETURN old.resolution_id;
END$$;
REVOKE ALL ON kcml_secret_v1.broker_issuance FROM PUBLIC;
REVOKE ALL ON FUNCTION kcml_secret_v1.broker_record_issuance_v1(uuid,uuid,uuid,uuid) FROM PUBLIC;
