-- §25.3/§51.20 exact reserved credential storage joins.
ALTER TABLE public.owner_api_credential ADD CONSTRAINT owner_api_version_same_secret
 FOREIGN KEY(secret_id,secret_version_id)
 REFERENCES kcml_secret_v1.secret_version(secret_id,id)
 ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
CREATE FUNCTION public.kcml_owner_api_active_secret_guard_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE a public.owner_api_credential;
        r kcml_secret_v1.secret_record;
        v kcml_secret_v1.secret_version;
BEGIN
 SELECT * INTO STRICT a FROM public.owner_api_credential WHERE singleton_key=1;
 SELECT * INTO STRICT r FROM kcml_secret_v1.secret_record WHERE id=a.secret_id;
 SELECT * INTO STRICT v FROM kcml_secret_v1.secret_version WHERE id=a.secret_version_id AND secret_id=a.secret_id;
 IF r.stable_name<>'KCML_OWNER_API_KEY' OR r.active_version_id IS DISTINCT FROM a.secret_version_id
 OR v.lifecycle<>'ACTIVE' OR v.fingerprint IS DISTINCT FROM a.fingerprint THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_API_SECRET_POINTER_MISMATCH';END IF;
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER owner_api_active_secret_guard
 AFTER INSERT OR UPDATE ON public.owner_api_credential
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
 EXECUTE FUNCTION public.kcml_owner_api_active_secret_guard_v1();
-- Reserved Secret writers must invoke the same final checker at transaction end
-- whenever reserved root/version is changed, not only when credential is updated.
CREATE FUNCTION kcml_secret_v1.kcml_reserved_owner_api_secret_guard_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE sid uuid; reserved_name text; a public.owner_api_credential;
BEGIN
 IF TG_TABLE_NAME='secret_record' THEN sid=NEW.id; ELSE sid=NEW.secret_id;END IF;
 SELECT stable_name INTO STRICT reserved_name FROM kcml_secret_v1.secret_record WHERE id=sid;
 IF reserved_name<>'KCML_OWNER_API_KEY' THEN RETURN NULL;END IF;
 SELECT * INTO STRICT a FROM public.owner_api_credential WHERE singleton_key=1;
 IF a.secret_id IS DISTINCT FROM sid THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_API_RESERVED_SECRET_MISMATCH';END IF;
 IF NOT EXISTS(SELECT 1 FROM kcml_secret_v1.secret_version v JOIN kcml_secret_v1.secret_record r ON r.id=v.secret_id
 WHERE v.secret_id=sid AND v.id=a.secret_version_id AND r.active_version_id=v.id AND v.lifecycle='ACTIVE' AND v.fingerprint=a.fingerprint) THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_API_SECRET_POINTER_MISMATCH';END IF;
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER reserved_owner_api_root_guard AFTER INSERT OR UPDATE
 ON kcml_secret_v1.secret_record DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
 EXECUTE FUNCTION kcml_secret_v1.kcml_reserved_owner_api_secret_guard_v1();
CREATE CONSTRAINT TRIGGER reserved_owner_api_version_guard AFTER INSERT OR UPDATE
 ON kcml_secret_v1.secret_version DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
 EXECUTE FUNCTION kcml_secret_v1.kcml_reserved_owner_api_secret_guard_v1();
-- Credential version and credential activation epoch belong to their own
-- monotonic rotate/CAS guard, not equality with Secret version_number/epoch.
-- Fingerprint cannot replace constant-time actual-token verifier under lock.
