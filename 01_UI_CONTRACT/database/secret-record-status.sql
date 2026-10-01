-- OWNER-approved derived Secret root presentation status (§8.3/25.6).
-- No new lifecycle/admission permission; existing versions retain own lifecycle.
CREATE FUNCTION kcml_secret_v1.record_status_for_v1(p_secret_id uuid,p_secret_type text,p_active_version_id uuid,p_deleted_at timestamptz)
 RETURNS text LANGUAGE plpgsql STABLE SET search_path=pg_catalog AS $$
DECLARE active_count integer; v kcml_secret_v1.secret_version;
BEGIN
 SELECT count(*) INTO active_count FROM kcml_secret_v1.secret_version WHERE secret_id=p_secret_id AND lifecycle='ACTIVE';
 IF active_count>1 THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_STATUS_MULTIPLE_ACTIVE';END IF;
 IF p_active_version_id IS NULL THEN
  IF active_count<>0 THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_STATUS_ACTIVE_WITHOUT_POINTER';END IF;
 ELSE
  SELECT * INTO v FROM kcml_secret_v1.secret_version WHERE id=p_active_version_id;
  IF v.id IS NULL THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_STATUS_POINTER_UNAVAILABLE';END IF;
  IF v.secret_id IS DISTINCT FROM p_secret_id OR v.secret_type IS DISTINCT FROM p_secret_type THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_STATUS_POINTER_IDENTITY_MISMATCH';END IF;
  IF v.lifecycle IS DISTINCT FROM 'ACTIVE' OR active_count<>1 THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_STATUS_POINTER_NOT_ACTIVE';END IF;
 END IF;
 -- Deletion precedence cannot conceal invalid pointer/version relationships.
 IF p_deleted_at IS NOT NULL THEN RETURN 'DELETED';END IF;
 IF p_active_version_id IS NULL THEN RETURN 'INACTIVE';END IF;
 RETURN 'ACTIVE';
END$$;
CREATE FUNCTION kcml_secret_v1.record_status_v1(p_secret_id uuid) RETURNS text
 LANGUAGE plpgsql STABLE SET search_path=pg_catalog AS $$
DECLARE r kcml_secret_v1.secret_record; computed text;
BEGIN
 SELECT * INTO r FROM kcml_secret_v1.secret_record WHERE id=p_secret_id;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0002',MESSAGE='SECRET_STATUS_RECORD_UNAVAILABLE';END IF;
 computed=kcml_secret_v1.record_status_for_v1(r.id,r.secret_type,r.active_version_id,r.deleted_at);
 IF r.status IS DISTINCT FROM computed THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_STATUS_PROJECTION_MISMATCH';END IF;
 RETURN computed;
END$$;
-- Controlled schema-migration materialization. Only existing internally valid
-- rows are converted; invalid imported/restored lineage blocks installation.
-- No Secret/version IDs, bytes, lifecycle or active pointer are rewritten.
DO $$DECLARE r record; computed text;BEGIN
 FOR r IN SELECT id,secret_type,active_version_id,deleted_at FROM kcml_secret_v1.secret_record ORDER BY id FOR UPDATE LOOP
  computed=kcml_secret_v1.record_status_for_v1(r.id,r.secret_type,r.active_version_id,r.deleted_at);
  UPDATE kcml_secret_v1.secret_record SET status=computed WHERE id=r.id AND status IS DISTINCT FROM computed;
 END LOOP;
END$$;
-- Flush prior immutable-version/root consistency events before DDL.
SET CONSTRAINTS ALL IMMEDIATE;
ALTER TABLE kcml_secret_v1.secret_record ALTER COLUMN status SET DEFAULT 'INACTIVE';
ALTER TABLE kcml_secret_v1.secret_record ADD CONSTRAINT secret_root_status_projection_values CHECK(status IN('INACTIVE','ACTIVE','DELETED'));
SET CONSTRAINTS ALL DEFERRED;
CREATE FUNCTION kcml_secret_v1.record_status_project_before_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF TG_OP='INSERT' THEN
  IF NEW.status IS DISTINCT FROM 'INACTIVE' OR NEW.active_version_id IS NOT NULL OR NEW.deleted_at IS NOT NULL THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_CREATE_RECORD_MUST_BE_INACTIVE';END IF;
 ELSE
  IF NEW.status IS DISTINCT FROM OLD.status THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_STATUS_NOT_EDITABLE';END IF;
 END IF;
 NEW.status=kcml_secret_v1.record_status_for_v1(NEW.id,NEW.secret_type,NEW.active_version_id,NEW.deleted_at);
 RETURN NEW;
END$$;
CREATE TRIGGER secret_status_projection_before BEFORE INSERT OR UPDATE ON kcml_secret_v1.secret_record
 FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.record_status_project_before_v1();
CREATE FUNCTION kcml_secret_v1.record_status_validate_final_v1() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE sid uuid; r kcml_secret_v1.secret_record; computed text;
BEGIN
 IF TG_TABLE_NAME='secret_record' THEN sid=NEW.id;ELSE sid=NEW.secret_id;END IF;
 SELECT * INTO r FROM kcml_secret_v1.secret_record WHERE id=sid;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0002',MESSAGE='SECRET_STATUS_RECORD_UNAVAILABLE';END IF;
 computed=kcml_secret_v1.record_status_for_v1(r.id,r.secret_type,r.active_version_id,r.deleted_at);
 IF r.status IS DISTINCT FROM computed THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SECRET_STATUS_PROJECTION_MISMATCH';END IF;
 -- Validation only: no late E mutation or lock after class I audit_head.
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER secret_status_root_final AFTER INSERT OR UPDATE ON kcml_secret_v1.secret_record
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.record_status_validate_final_v1();
CREATE CONSTRAINT TRIGGER secret_status_version_final AFTER INSERT OR UPDATE ON kcml_secret_v1.secret_version
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_secret_v1.record_status_validate_final_v1();
REVOKE ALL ON FUNCTION kcml_secret_v1.record_status_for_v1(uuid,text,uuid,timestamptz),kcml_secret_v1.record_status_v1(uuid) FROM PUBLIC;
-- Existing domain/auth writers need the exact projection inside trusted paths;
-- no direct editable status field or caller-visible SQL capability is added.
GRANT EXECUTE ON FUNCTION kcml_secret_v1.record_status_for_v1(uuid,text,uuid,timestamptz),kcml_secret_v1.record_status_v1(uuid)
 TO kcml_secret_domain_writer,kcml_secret_authentication_writer;
