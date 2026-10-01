-- Required concrete OWNER_FULL read path §§7.2,8.5,25.6,51.6–7.
-- Authentication is actual canonical constant-time verifier executed by the
-- trusted server while this transaction holds B3 SHARE. SQL never treats an
-- owner UUID/create context/caller authorized flag as authentication.
-- Canonical owner/platform/deployment/API tables, Secret roots and nonce/key
-- registry are prerequisites. No grant to callers/generated handlers.
CREATE TABLE kcml_secret_v1.owner_value_read_audit (
 id uuid PRIMARY KEY, owner_id uuid NOT NULL REFERENCES public.owner_identity(id),
 api_credential_version bigint NOT NULL,api_credential_epoch bigint NOT NULL,
 secret_id uuid NOT NULL REFERENCES kcml_secret_v1.secret_record(id),
 secret_version_id uuid NOT NULL, correlation_id uuid NOT NULL,
 occurred_at timestamptz NOT NULL,
 FOREIGN KEY(secret_id,secret_version_id) REFERENCES kcml_secret_v1.secret_version(secret_id,id)
);
CREATE TRIGGER owner_value_read_audit_immutable BEFORE UPDATE OR DELETE ON kcml_secret_v1.owner_value_read_audit FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.secret_profile_immutable();
CREATE FUNCTION kcml_secret_v1.owner_api_value_read_begin_v1(p_secret uuid,p_version uuid)
 RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE pi public.platform_incarnation;dh public.application_deployment_head;
 c public.owner_api_credential;o public.owner_identity; sr kcml_secret_v1.secret_record;
 credential_root kcml_secret_v1.secret_record;credential_version kcml_secret_v1.secret_version;
 v kcml_secret_v1.secret_version;n public.canonical_protected_nonce_reservation;k public.canonical_master_key_generation;
 diagnostic text='VALUE_READ_READY';at timestamptz;record_status text;status_message text;
BEGIN
 SELECT * INTO STRICT pi FROM public.platform_incarnation WHERE singleton_key=1 FOR SHARE;
 SELECT * INTO STRICT dh FROM public.application_deployment_head WHERE singleton_key=1 FOR SHARE;
 SELECT * INTO STRICT c FROM public.owner_api_credential WHERE singleton_key=1 FOR SHARE;
 SELECT * INTO STRICT o FROM public.owner_identity WHERE singleton_key=1 FOR UPDATE;
 -- All known class E ordinal20 roots sorted by UUID; no later root discovery.
 PERFORM 1 FROM kcml_secret_v1.secret_record WHERE id IN(c.secret_id,p_secret) ORDER BY id FOR UPDATE;
 SELECT * INTO credential_root FROM kcml_secret_v1.secret_record WHERE id=c.secret_id;
 SELECT * INTO credential_version FROM kcml_secret_v1.secret_version WHERE secret_id=c.secret_id AND id=c.secret_version_id;
 at=clock_timestamp();
 IF pi.platform_incarnation_id IS DISTINCT FROM dh.platform_incarnation_id OR kcml_secret_v1.record_status_v1(c.secret_id) IS DISTINCT FROM 'ACTIVE' OR credential_root.stable_name IS DISTINCT FROM 'KCML_OWNER_API_KEY' OR credential_root.active_version_id IS DISTINCT FROM credential_version.id OR credential_version.secret_type IS DISTINCT FROM 'API_KEY' OR credential_version.lifecycle IS DISTINCT FROM 'ACTIVE' OR credential_version.fingerprint IS DISTINCT FROM c.fingerprint THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_VALUE_READ_AUTHORITY_BINDING_INVALID';
 END IF;
 SELECT * INTO sr FROM kcml_secret_v1.secret_record WHERE id=p_secret;
 IF sr.id IS NULL THEN diagnostic='SECRET_OWNER_VALUE_REFERENCE_UNAVAILABLE';
 ELSE
  BEGIN
   record_status=kcml_secret_v1.record_status_v1(sr.id);
  EXCEPTION WHEN check_violation THEN
   GET STACKED DIAGNOSTICS status_message=MESSAGE_TEXT;
   IF status_message NOT IN('SECRET_STATUS_MULTIPLE_ACTIVE','SECRET_STATUS_ACTIVE_WITHOUT_POINTER','SECRET_STATUS_POINTER_UNAVAILABLE','SECRET_STATUS_POINTER_IDENTITY_MISMATCH','SECRET_STATUS_POINTER_NOT_ACTIVE','SECRET_STATUS_PROJECTION_MISMATCH') THEN RAISE;END IF;
   diagnostic=status_message;
  END;
 END IF;
 IF diagnostic<>'VALUE_READ_READY' THEN NULL;
 ELSIF record_status='DELETED' THEN diagnostic='SECRET_OWNER_VALUE_REFERENCE_UNAVAILABLE';
 ELSIF sr.stable_name='KCML_OWNER_API_KEY' THEN diagnostic='OWNER_CREDENTIAL_REVEAL_REQUIRES_OWNER_SESSION';
 ELSE
  SELECT * INTO v FROM kcml_secret_v1.secret_version WHERE secret_id=sr.id AND id=coalesce(p_version,sr.active_version_id);
  IF v.id IS NULL THEN diagnostic='SECRET_OWNER_VERSION_UNAVAILABLE';
  ELSE
   SELECT * INTO n FROM public.canonical_protected_nonce_reservation WHERE key_id=v.key_id AND nonce=v.nonce AND purpose='SECRET_IMMUTABLE_VERSION' AND protected_object_id=v.id;
   SELECT * INTO k FROM public.canonical_master_key_generation WHERE key_id=v.key_id;
   IF n.key_id IS NULL OR k.key_id IS NULL OR n.ciphertext_digest IS DISTINCT FROM sha256(v.ciphertext) OR (convert_from(n.authenticated_metadata_bytes,'UTF8')::jsonb->'identity'->>'ownerId') IS DISTINCT FROM o.id::text OR (convert_from(n.authenticated_metadata_bytes,'UTF8')::jsonb->'identity'->>'trustedContextId') IS DISTINCT FROM v.creator_context_id::text THEN diagnostic='SECRET_PROTECTED_ROW_AUTHORITY_UNAVAILABLE'; END IF;
  END IF;
 END IF;
 -- Verifier is INTERNAL service data; fresh credential verification must run
 -- before exposing even a resource-existence diagnostic or opening ciphertext.
 RETURN jsonb_build_object('diagnostic',diagnostic,'ownerId',o.id,'apiCredentialVersion',c.credential_version,'apiCredentialEpoch',c.credential_activation_epoch,'verifierHash',c.verifier_hash,'fingerprint',c.fingerprint,
 'recordMetadata',CASE WHEN sr.id IS NOT NULL AND record_status IN('INACTIVE','ACTIVE','DELETED') THEN to_jsonb(sr) ELSE NULL END,'recordStatus',record_status,
 'protectedRow',CASE WHEN diagnostic='VALUE_READ_READY' THEN jsonb_build_object('version',to_jsonb(v),'recordStatus',record_status,'recordStateVersion',sr.state_version::text,'protectedAuthority',jsonb_build_object('metadataHex',encode(n.authenticated_metadata_bytes,'hex'),'keyFingerprintHex',encode(k.key_fingerprint,'hex'),'keyProfileDigestHex',encode(k.crypto_profile_digest,'hex'),'keyProfileBytesHex',(SELECT encode(cp.profile_bytes,'hex') FROM public.canonical_authenticated_crypto_profile cp WHERE cp.profile_digest=k.crypto_profile_digest),'keyGeneration',k.key_generation,'creationLogicalOperationId',n.logical_operation_id,'ciphertextDigestHex',encode(n.ciphertext_digest,'hex'))) ELSE NULL END);
END$$;
CREATE FUNCTION kcml_secret_v1.owner_api_value_read_audit_v1(p_owner uuid,p_credential_version bigint,p_epoch bigint,p_secret uuid,p_version uuid,p_correlation uuid)
 RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE c public.owner_api_credential;o public.owner_identity;result uuid=gen_random_uuid();
BEGIN
 -- Called only by actual verifier/open server under the SAME held B→E TX.
 SELECT * INTO STRICT c FROM public.owner_api_credential WHERE singleton_key=1 FOR SHARE;
 SELECT * INTO STRICT o FROM public.owner_identity WHERE singleton_key=1 FOR UPDATE;
 IF o.id<>p_owner OR c.credential_version<>p_credential_version OR c.credential_activation_epoch<>p_epoch THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_VALUE_READ_CONTEXT_CHANGED'; END IF;
 INSERT INTO kcml_secret_v1.owner_value_read_audit VALUES(result,p_owner,p_credential_version,p_epoch,p_secret,p_version,p_correlation,clock_timestamp());
 RETURN result;
END$$;
REVOKE ALL ON kcml_secret_v1.owner_value_read_audit FROM PUBLIC;
REVOKE ALL ON FUNCTION kcml_secret_v1.owner_api_value_read_begin_v1(uuid,uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION kcml_secret_v1.owner_api_value_read_audit_v1(uuid,bigint,bigint,uuid,uuid,uuid) FROM PUBLIC;
-- CURRENT or IMMUTABLE_VERSION native selector from exact GET transport mask.
-- Read consumes the approved record_status_v1 projector; DELETED cannot be
-- reactivated by selecting an old immutable version. Internal status diagnostics
-- are returned only after actual fresh bearer verification in the server helper.
