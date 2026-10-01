-- Candidate technical enforcement of §12.54 global nonce registry and typed AAD.
-- Install after canonical foundations, authentication, preroot and crypto registry.
-- Does not attest a systemd source or authorize service invocation/key provisioning.
-- Exact §12.54 sorted compact UTF8 JSON for the closed typed AAD envelope.
-- All numeric members of this envelope are integers; no floating-point codec
-- or Unicode normalization is introduced. Scalar string escaping is PostgreSQL
-- JSON escaping, verified against the canonical Python profile below.
CREATE FUNCTION kcml_crypto_compact_sorted_json_v1(v jsonb) RETURNS text
LANGUAGE plpgsql IMMUTABLE STRICT SET search_path=pg_catalog AS $$
DECLARE result text;
BEGIN
 CASE jsonb_typeof(v)
 WHEN 'object' THEN
  SELECT '{'||coalesce(string_agg(to_jsonb(e.key)::text||':'||public.kcml_crypto_compact_sorted_json_v1(e.value),',' ORDER BY e.key COLLATE "C"),'')||'}'
  INTO result FROM jsonb_each(v) e;
 WHEN 'array' THEN
  SELECT '['||coalesce(string_agg(public.kcml_crypto_compact_sorted_json_v1(e.value),',' ORDER BY e.ordinality),'')||']'
  INTO result FROM jsonb_array_elements(v) WITH ORDINALITY e(value,ordinality);
 ELSE result:=v::text;
 END CASE;
 RETURN result;
END $$;
REVOKE ALL ON FUNCTION kcml_crypto_compact_sorted_json_v1(jsonb) FROM PUBLIC;
CREATE FUNCTION kcml_generation_protected_registry_link_v1() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE sid uuid; s record; r public.canonical_protected_nonce_reservation;
 c public.generation_create_trusted_context; d public.domain_command;
 k public.canonical_master_key_generation; p public.canonical_authenticated_crypto_profile;
 expected jsonb; found_snapshot boolean:=false;
BEGIN
 IF TG_TABLE_NAME='canonical_protected_nonce_reservation' THEN
  IF NEW.purpose<>'GENERATION_INITIAL_REQUEST' THEN RETURN NULL; END IF;
  sid:=NEW.protected_object_id;
 ELSE sid:=NEW.snapshot_id; END IF;
 SELECT * INTO r FROM public.canonical_protected_nonce_reservation
 WHERE purpose='GENERATION_INITIAL_REQUEST' AND protected_object_id=sid;
 IF r.protected_object_id IS NULL THEN RAISE EXCEPTION 'GENERATION_PROTECTED_RESERVATION_REQUIRED' USING ERRCODE='23514'; END IF;
 FOR s IN
  SELECT snapshot_id,logical_operation_id,job_id,request_schema_id,request_schema_digest,content_digest,ciphertext,nonce,algorithm,key_id,crypto_profile_digest
  FROM public.generation_job_initial_request_snapshot WHERE snapshot_id=sid
  UNION ALL
  SELECT snapshot_id,logical_operation_id,prospective_job_id,request_schema_id,request_schema_digest,content_digest,ciphertext,nonce,algorithm,key_id,crypto_profile_digest
  FROM public.generation_create_preroot_snapshot WHERE snapshot_id=sid
 LOOP
  found_snapshot:=true;
  SELECT * INTO d FROM public.domain_command WHERE logical_operation_id=s.logical_operation_id;
  SELECT * INTO c FROM public.generation_create_trusted_context WHERE id=d.execution_context_id;
  SELECT * INTO k FROM public.canonical_master_key_generation WHERE key_id=s.key_id;
  SELECT * INTO p FROM public.canonical_authenticated_crypto_profile WHERE profile_digest=s.crypto_profile_digest;
  IF d.logical_operation_id IS NULL OR c.id IS NULL OR k.key_id IS NULL OR p.profile_id IS NULL
   OR d.operation_id<>'generation.job.create' OR d.owner_id<>c.owner_id
   OR d.target_aggregate_id<>s.job_id OR d.canonical_arguments_snapshot_id<>s.snapshot_id
   OR k.crypto_profile_digest<>s.crypto_profile_digest
   OR s.algorithm<>p.algorithm OR octet_length(s.nonce)<>12 OR octet_length(s.ciphertext)<16
   OR (r.logical_operation_id,r.key_id,r.nonce,r.ciphertext_digest)
    IS DISTINCT FROM(s.logical_operation_id,s.key_id,s.nonce,sha256(s.ciphertext))
  THEN RAISE EXCEPTION 'GENERATION_PROTECTED_RESERVATION_BINDING_INVALID' USING ERRCODE='23514'; END IF;
  expected:=jsonb_build_object('purpose','GENERATION_INITIAL_REQUEST','keyId',s.key_id,
   'profile',convert_from(p.profile_bytes,'UTF8')::jsonb,'identity',jsonb_build_object(
    'ownerId',c.owner_id::text,'jobId',s.job_id::text,'snapshotId',s.snapshot_id::text,
    'logicalOperationId',s.logical_operation_id::text,'requestSchemaId',s.request_schema_id,
    'requestSchemaDigest','sha256:'||encode(s.request_schema_digest,'hex'),
    'contentDigest','sha256:'||encode(s.content_digest,'hex'),'trustedContextId',c.id::text,
    'platformIncarnationId',c.platform_incarnation_id::text,'applicationDeploymentEpoch',c.application_deployment_epoch,
    'executionDescriptorDigest','sha256:'||encode(c.execution_descriptor_digest,'hex'),
    'initiatingAccessChannel',c.initiating_access_channel));
  IF r.authenticated_metadata_bytes IS DISTINCT FROM convert_to(public.kcml_crypto_compact_sorted_json_v1(expected),'UTF8')
   THEN RAISE EXCEPTION 'GENERATION_PROTECTED_TYPED_AAD_INVALID' USING ERRCODE='23514'; END IF;
 END LOOP;
 IF NOT found_snapshot THEN RAISE EXCEPTION 'GENERATION_PROTECTED_ROW_REQUIRED' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER generation_snapshot_crypto_registry_link
 AFTER INSERT ON generation_job_initial_request_snapshot DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION kcml_generation_protected_registry_link_v1();
CREATE CONSTRAINT TRIGGER generation_preroot_crypto_registry_link
 AFTER INSERT ON generation_create_preroot_snapshot DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION kcml_generation_protected_registry_link_v1();
CREATE CONSTRAINT TRIGGER generation_reservation_crypto_row_link
 AFTER INSERT ON canonical_protected_nonce_reservation DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION kcml_generation_protected_registry_link_v1();
REVOKE ALL ON FUNCTION kcml_generation_protected_registry_link_v1() FROM PUBLIC;
