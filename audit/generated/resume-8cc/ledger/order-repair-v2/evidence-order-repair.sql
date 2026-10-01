-- Exact dedicated G sequence authority. State H150 remains its guarded
-- projection; absent first allocator is created under canonical E root+F fence.
CREATE TABLE kcml_effect_v1.evidence_head(
 operation_id uuid NOT NULL,sequence bigint NOT NULL,
 primary_parent_uuid uuid NOT NULL REFERENCES public.generation_job(id),
 last_sequence bigint NOT NULL CHECK(last_sequence>=0),
 PRIMARY KEY(operation_id,sequence),
 FOREIGN KEY(operation_id,sequence)REFERENCES kcml_effect_v1.attempt(operation_id,sequence) DEFERRABLE INITIALLY DEFERRED
);
CREATE FUNCTION kcml_effect_v1.evidence_head_scope() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN
 IF (NEW.operation_id,NEW.sequence,NEW.primary_parent_uuid) IS DISTINCT FROM(OLD.operation_id,OLD.sequence,OLD.primary_parent_uuid) OR NEW.last_sequence IS DISTINCT FROM OLD.last_sequence+1 THEN RAISE EXCEPTION 'EFFECT_EVIDENCE_ALLOCATOR_SCOPE' USING ERRCODE='23514';END IF;RETURN NEW;END $$;
CREATE TRIGGER evidence_head_scope BEFORE UPDATE ON kcml_effect_v1.evidence_head FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.evidence_head_scope();
DO $$DECLARE c text;BEGIN
 SELECT conname INTO STRICT c FROM pg_constraint WHERE conrelid='kcml_effect_v1.evidence'::regclass AND confrelid='kcml_effect_v1.attempt'::regclass AND contype='f';
 EXECUTE format('ALTER TABLE kcml_effect_v1.evidence ALTER CONSTRAINT %I DEFERRABLE INITIALLY DEFERRED',c);
END $$;
CREATE OR REPLACE FUNCTION kcml_effect_v1.append_evidence(p_op uuid,p_sequence bigint,p_id uuid,p_kind text,p_raw bytea) RETURNS bigint LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE s kcml_effect_v1.state;a kcml_effect_v1.attempt;o kcml_effect_v1.operation;n bigint;prior kcml_effect_v1.evidence;item record;allocated bigint;
BEGIN
 -- fence_guard holds actual generation root E90 and concurrency claim F.
 PERFORM kcml_effect_v1.fence_guard(p_op,p_sequence);
 SELECT * INTO STRICT o FROM kcml_effect_v1.operation WHERE id=p_op;
 SELECT * INTO STRICT s FROM kcml_effect_v1.state WHERE operation_id=p_op AND sequence=p_sequence;
 SELECT * INTO STRICT a FROM kcml_effect_v1.attempt WHERE operation_id=p_op AND sequence=p_sequence;
 SELECT * INTO prior FROM kcml_effect_v1.evidence WHERE id=p_id;
 IF FOUND THEN
  IF (prior.operation_id,prior.sequence,prior.kind,prior.exact_bytes,prior.content_digest,prior.source_fence,prior.incarnation)IS DISTINCT FROM(p_op,p_sequence,p_kind,p_raw,sha256(p_raw),a.parent_fence,a.incarnation)THEN RAISE EXCEPTION 'EFFECT_EVIDENCE_REPLAY_CONFLICT' USING ERRCODE='23514';END IF;
  RETURN prior.evidence_sequence;
 END IF;
 IF s.state IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL')THEN RAISE EXCEPTION 'EFFECT_TERMINAL_EVIDENCE_DENIED' USING ERRCODE='23514';END IF;
 IF (SELECT count(*)FROM kcml_effect_v1.evidence WHERE operation_id=p_op AND sequence=p_sequence)<>s.last_evidence_sequence OR EXISTS(SELECT 1 FROM kcml_effect_v1.evidence WHERE operation_id=p_op AND sequence=p_sequence AND evidence_sequence>s.last_evidence_sequence)THEN RAISE EXCEPTION 'EFFECT_EVIDENCE_ALLOCATOR_SOURCE_DRIFT' USING ERRCODE='23514';END IF;
 INSERT INTO kcml_effect_v1.evidence_head VALUES(p_op,p_sequence,o.parent_id,s.last_evidence_sequence)ON CONFLICT DO NOTHING;
 SELECT last_sequence INTO STRICT allocated FROM kcml_effect_v1.evidence_head WHERE operation_id=p_op AND sequence=p_sequence FOR UPDATE;
 IF allocated IS DISTINCT FROM s.last_evidence_sequence THEN RAISE EXCEPTION 'EFFECT_EVIDENCE_ALLOCATOR_SOURCE_DRIFT' USING ERRCODE='23514';END IF;
 n=allocated+1;
 UPDATE kcml_effect_v1.evidence_head SET last_sequence=n WHERE operation_id=p_op AND sequence=p_sequence;
 -- All three physical H150 row identities are known before acquiring any H.
 -- Deferred evidence FK permits insertion before an immutable attempt key lock
 -- when its UUID sorts first. This is not an unlocked FK bypass at COMMIT.
 FOR item IN SELECT * FROM(VALUES(a.id,'ATTEMPT'),(s.state_id,'STATE'),(p_id,'EVIDENCE'))v(id,kind)ORDER BY id LOOP
  CASE item.kind
  WHEN 'ATTEMPT' THEN PERFORM 1 FROM kcml_effect_v1.attempt WHERE operation_id=p_op AND sequence=p_sequence FOR KEY SHARE;
  WHEN 'STATE' THEN PERFORM 1 FROM kcml_effect_v1.state WHERE operation_id=p_op AND sequence=p_sequence FOR UPDATE;
  WHEN 'EVIDENCE' THEN INSERT INTO kcml_effect_v1.evidence(operation_id,sequence,evidence_sequence,id,kind,exact_bytes,content_digest,source_fence,incarnation,observed_at)VALUES(p_op,p_sequence,n,p_id,p_kind,p_raw,sha256(p_raw),a.parent_fence,a.incarnation,clock_timestamp());
  END CASE;
 END LOOP;
 -- This is an update of the already-held STATE row, not a new lower lock.
 UPDATE kcml_effect_v1.state SET last_evidence_sequence=n,state_version=state_version+1 WHERE operation_id=p_op AND sequence=p_sequence;
 RETURN n;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
REVOKE ALL ON kcml_effect_v1.evidence_head FROM PUBLIC;
CREATE FUNCTION kcml_effect_v1.evidence_head_projection() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$DECLARE h kcml_effect_v1.evidence_head;s kcml_effect_v1.state;o kcml_effect_v1.operation;BEGIN
 SELECT * INTO h FROM kcml_effect_v1.evidence_head WHERE operation_id=NEW.operation_id AND sequence=NEW.sequence;
 IF NOT FOUND THEN IF NEW.last_evidence_sequence<>0 THEN RAISE EXCEPTION 'EFFECT_EVIDENCE_ALLOCATOR_REQUIRED' USING ERRCODE='23514';END IF;RETURN NULL;END IF;
 SELECT * INTO STRICT s FROM kcml_effect_v1.state WHERE operation_id=NEW.operation_id AND sequence=NEW.sequence;
 SELECT * INTO STRICT o FROM kcml_effect_v1.operation WHERE id=NEW.operation_id;
 IF h.last_sequence IS DISTINCT FROM s.last_evidence_sequence OR h.primary_parent_uuid IS DISTINCT FROM o.parent_id THEN RAISE EXCEPTION 'EFFECT_EVIDENCE_ALLOCATOR_PROJECTION_DRIFT' USING ERRCODE='23514';END IF;RETURN NULL;END $$;
CREATE CONSTRAINT TRIGGER evidence_head_projection AFTER INSERT OR UPDATE ON kcml_effect_v1.evidence_head DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.evidence_head_projection();
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;

CREATE CONSTRAINT TRIGGER evidence_head_state_projection AFTER INSERT OR UPDATE ON kcml_effect_v1.state DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.evidence_head_projection();
CREATE TRIGGER evidence_head_no_delete BEFORE DELETE ON kcml_effect_v1.evidence_head FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.immutable();
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
