-- §51.20 exact OWNER credential -> selected Secret/version physical binding.
-- Requires canonical owner_api_credential and secret-profile-roots first.
ALTER TABLE owner_api_credential ADD CONSTRAINT owner_credential_secret_version_fk
 FOREIGN KEY(secret_id,secret_version_id) REFERENCES kcml_secret_v1.secret_version(secret_id,id)
 DEFERRABLE INITIALLY DEFERRED;
CREATE FUNCTION kcml_secret_v1.owner_credential_secret_consistency_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE c owner_api_credential%ROWTYPE; r kcml_secret_v1.secret_record%ROWTYPE;
        v kcml_secret_v1.secret_version%ROWTYPE;
BEGIN
 SELECT * INTO c FROM owner_api_credential WHERE singleton_key=1;
 IF NOT FOUND THEN RETURN NULL; END IF;
 SELECT * INTO STRICT r FROM kcml_secret_v1.secret_record WHERE id=c.secret_id;
 SELECT * INTO STRICT v FROM kcml_secret_v1.secret_version WHERE secret_id=c.secret_id AND id=c.secret_version_id;
 IF r.stable_name IS DISTINCT FROM 'KCML_OWNER_API_KEY' OR r.secret_type IS DISTINCT FROM 'API_KEY'
 OR v.secret_type IS DISTINCT FROM 'API_KEY' OR r.active_version_id IS DISTINCT FROM v.id
 OR v.lifecycle IS DISTINCT FROM 'ACTIVE' OR c.fingerprint IS DISTINCT FROM v.fingerprint THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_CREDENTIAL_SECRET_BINDING_MISMATCH';
 END IF;
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER owner_credential_secret_binding AFTER INSERT OR UPDATE ON owner_api_credential
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.owner_credential_secret_consistency_v1();
CREATE CONSTRAINT TRIGGER secret_owner_root_binding AFTER INSERT OR UPDATE ON kcml_secret_v1.secret_record
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.owner_credential_secret_consistency_v1();
CREATE CONSTRAINT TRIGGER secret_owner_version_binding AFTER INSERT OR UPDATE ON kcml_secret_v1.secret_version
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.owner_credential_secret_consistency_v1();
-- This only enforces selected identity/stable name/current active fingerprint.
-- Actual verifier hash derivation and monotonic credential epoch/version update
-- must come from authenticated atomic rotation producer, not this trigger.
