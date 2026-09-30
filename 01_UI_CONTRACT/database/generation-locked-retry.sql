-- Bounded §12.51.1/§25.11/§25.16/§49.8 source ledger projection.
-- SQL extension candidate; not effective until coordinator materializes it.
-- Actual payload bytes remain authoritative; typed columns select producer scope.
CREATE SCHEMA kcml_retry_v1;
CREATE TABLE kcml_retry_v1.phase (
 phase_run_id uuid PRIMARY KEY, job_id uuid NOT NULL REFERENCES public.generation_job(id),
 source_bytes bytea NOT NULL, source_digest bytea NOT NULL CHECK(octet_length(source_digest)=32),
 UNIQUE(phase_run_id,job_id), CHECK(sha256(source_bytes)=source_digest),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'phaseRunId')::uuid=phase_run_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'jobId')::uuid=job_id)
);
CREATE TABLE kcml_retry_v1.operation (
 operation_id uuid PRIMARY KEY, phase_run_id uuid NOT NULL, job_id uuid NOT NULL,
 source_bytes bytea NOT NULL, source_digest bytea NOT NULL CHECK(sha256(source_bytes)=source_digest),
 FOREIGN KEY(phase_run_id,job_id) REFERENCES kcml_retry_v1.phase(phase_run_id,job_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'operationId')::uuid=operation_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'phaseRunId')::uuid=phase_run_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'jobId')::uuid=job_id),
 UNIQUE(operation_id,phase_run_id,job_id)
);
CREATE TABLE kcml_retry_v1.attempt (
 attempt_id uuid PRIMARY KEY, operation_id uuid NOT NULL, phase_run_id uuid NOT NULL,job_id uuid NOT NULL,
 attempt_sequence bigint NOT NULL CHECK(attempt_sequence>0), source_bytes bytea NOT NULL,
 source_digest bytea NOT NULL CHECK(sha256(source_bytes)=source_digest),
 FOREIGN KEY(operation_id,phase_run_id,job_id) REFERENCES kcml_retry_v1.operation(operation_id,phase_run_id,job_id),
 UNIQUE(operation_id,attempt_sequence),UNIQUE(attempt_id,operation_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'attemptId')::uuid=attempt_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'operationId')::uuid=operation_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'attemptSequence')::bigint=attempt_sequence),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'jobId')::uuid=job_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'phaseRunId')::uuid=phase_run_id)
);
CREATE TABLE kcml_retry_v1.current_state (
 attempt_id uuid PRIMARY KEY, operation_id uuid NOT NULL, state_id uuid NOT NULL UNIQUE,
 state_version bigint NOT NULL CHECK(state_version>0), source_bytes bytea NOT NULL,
 source_digest bytea NOT NULL CHECK(sha256(source_bytes)=source_digest),
 FOREIGN KEY(attempt_id,operation_id) REFERENCES kcml_retry_v1.attempt(attempt_id,operation_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'attemptStateId')::uuid=state_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'attemptId')::uuid=attempt_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'operationId')::uuid=operation_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'stateVersion')::bigint=state_version)
);
CREATE TABLE kcml_retry_v1.evidence (
 evidence_id uuid PRIMARY KEY,operation_id uuid NOT NULL,attempt_id uuid NOT NULL,
 source_bytes bytea NOT NULL,source_digest bytea NOT NULL CHECK(sha256(source_bytes)=source_digest),
 FOREIGN KEY(attempt_id,operation_id) REFERENCES kcml_retry_v1.attempt(attempt_id,operation_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'evidenceId')::uuid=evidence_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'operationId')::uuid=operation_id),
 CHECK((convert_from(source_bytes,'UTF8')::jsonb->>'attemptId')::uuid=attempt_id)
);
CREATE FUNCTION kcml_retry_v1.phase_write_gate() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE p uuid; o uuid;
BEGIN
 IF TG_TABLE_NAME IN ('operation','attempt') THEN p=CASE WHEN TG_OP='DELETE' THEN OLD.phase_run_id ELSE NEW.phase_run_id END;
 ELSE o=CASE WHEN TG_OP='DELETE' THEN OLD.operation_id ELSE NEW.operation_id END;
 SELECT phase_run_id INTO p FROM kcml_retry_v1.operation WHERE operation_id=o;
 END IF;
 PERFORM 1 FROM kcml_retry_v1.phase WHERE phase_run_id=p FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'RETRY_PRODUCER_PHASE_UNAVAILABLE' USING ERRCODE='23503';END IF;
 IF TG_OP='UPDATE' AND TG_TABLE_NAME IN ('attempt','evidence') OR TG_OP='DELETE' THEN
 RAISE EXCEPTION 'RETRY_APPEND_ONLY_SOURCE' USING ERRCODE='23514'; END IF;
 IF TG_OP='UPDATE' AND TG_TABLE_NAME='operation' THEN
 IF (NEW.operation_id,NEW.phase_run_id,NEW.job_id)IS DISTINCT FROM(OLD.operation_id,OLD.phase_run_id,OLD.job_id) THEN
 RAISE EXCEPTION 'RETRY_IMMUTABLE_PRODUCER_SCOPE' USING ERRCODE='23514';END IF;
 IF (convert_from(NEW.source_bytes,'UTF8')::jsonb - ARRAY['currentAttemptId','currentAttemptSequence','currentAttemptStateId','currentAttemptStateVersion','state']) IS DISTINCT FROM (convert_from(OLD.source_bytes,'UTF8')::jsonb - ARRAY['currentAttemptId','currentAttemptSequence','currentAttemptStateId','currentAttemptStateVersion','state']) THEN
 RAISE EXCEPTION 'RETRY_IMMUTABLE_OPERATION_REQUEST' USING ERRCODE='23514';END IF;END IF;
 IF TG_OP='UPDATE' AND TG_TABLE_NAME='current_state' THEN
 IF(NEW.attempt_id,NEW.operation_id,NEW.state_id)IS DISTINCT FROM(OLD.attempt_id,OLD.operation_id,OLD.state_id) OR NEW.state_version<>OLD.state_version+1 THEN
 RAISE EXCEPTION 'RETRY_CURRENT_STATE_VERSION' USING ERRCODE='23514';END IF;END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER gate BEFORE INSERT OR UPDATE OR DELETE ON kcml_retry_v1.operation FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.phase_write_gate();
CREATE TRIGGER gate BEFORE INSERT OR UPDATE OR DELETE ON kcml_retry_v1.attempt FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.phase_write_gate();
CREATE TRIGGER gate BEFORE INSERT OR UPDATE OR DELETE ON kcml_retry_v1.current_state FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.phase_write_gate();
CREATE TRIGGER gate BEFORE INSERT OR UPDATE OR DELETE ON kcml_retry_v1.evidence FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.phase_write_gate();
CREATE FUNCTION kcml_retry_v1.scan(p_phase uuid,p_job uuid,p_digest bytea) RETURNS jsonb LANGUAGE plpgsql VOLATILE SET search_path=pg_catalog AS $$
DECLARE ph kcml_retry_v1.phase%ROWTYPE; result jsonb;
BEGIN
 -- Lock before reading members. All writers use the same parent gate, so neither
 -- an insert phantom nor current-attempt update can occur before tx completion.
 SELECT * INTO ph FROM kcml_retry_v1.phase WHERE phase_run_id=p_phase FOR UPDATE;
 IF NOT FOUND OR ph.job_id<>p_job THEN RAISE EXCEPTION 'RETRY_SOURCE_PHASE_IDENTITY' USING ERRCODE='23514'; END IF;
 IF ph.source_digest<>p_digest THEN RAISE EXCEPTION 'RETRY_SOURCE_PHASE_DIGEST' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM kcml_retry_v1.operation o LEFT JOIN kcml_retry_v1.attempt a ON a.attempt_id=(convert_from(o.source_bytes,'UTF8')::jsonb->>'currentAttemptId')::uuid LEFT JOIN kcml_retry_v1.current_state s ON s.attempt_id=a.attempt_id
 WHERE o.phase_run_id=p_phase AND(a.attempt_id IS NULL OR s.attempt_id IS NULL OR a.operation_id<>o.operation_id OR s.operation_id<>o.operation_id
 OR (convert_from(o.source_bytes,'UTF8')::jsonb->>'currentAttemptSequence')::bigint<>a.attempt_sequence
 OR (convert_from(o.source_bytes,'UTF8')::jsonb->>'currentAttemptStateId')::uuid<>s.state_id
 OR (convert_from(o.source_bytes,'UTF8')::jsonb->>'currentAttemptStateVersion')::bigint<>s.state_version
 OR convert_from(o.source_bytes,'UTF8')::jsonb->>'state'<>convert_from(s.source_bytes,'UTF8')::jsonb->>'state')) THEN
 RAISE EXCEPTION 'RETRY_CURRENT_LEDGER_JOIN_DRIFT' USING ERRCODE='23514';END IF;
 SELECT jsonb_build_object('phaseBytes',encode(ph.source_bytes,'hex'),'phaseDigest',encode(ph.source_digest,'hex'),'rows',coalesce(jsonb_agg(jsonb_build_object(
 'operationId',o.operation_id,'operationBytes',encode(o.source_bytes,'hex'),'operationDigest',encode(o.source_digest,'hex'),
 'attemptId',a.attempt_id,'attemptBytes',encode(a.source_bytes,'hex'),'attemptDigest',encode(a.source_digest,'hex'),
 'stateId',s.state_id,'stateBytes',encode(s.source_bytes,'hex'),'stateDigest',encode(s.source_digest,'hex'),
 'evidenceId',e.evidence_id,'evidenceBytes',encode(e.source_bytes,'hex'),'evidenceDigest',encode(e.source_digest,'hex')) ORDER BY o.operation_id)FILTER(WHERE o.operation_id IS NOT NULL),'[]'::jsonb))
 INTO result FROM kcml_retry_v1.operation o
 LEFT JOIN kcml_retry_v1.attempt a ON a.attempt_id=(convert_from(o.source_bytes,'UTF8')::jsonb->>'currentAttemptId')::uuid
 LEFT JOIN kcml_retry_v1.current_state s ON s.attempt_id=a.attempt_id
 LEFT JOIN kcml_retry_v1.evidence e ON e.evidence_id=(convert_from(s.source_bytes,'UTF8')::jsonb->>'evidenceId')::uuid
 WHERE o.phase_run_id=p_phase;
 RETURN result;
END $$;
REVOKE ALL ON SCHEMA kcml_retry_v1 FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA kcml_retry_v1 FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_retry_v1 FROM PUBLIC;

CREATE FUNCTION kcml_retry_v1.check_current_join() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE o kcml_retry_v1.operation%ROWTYPE; a kcml_retry_v1.attempt%ROWTYPE; s kcml_retry_v1.current_state%ROWTYPE; e kcml_retry_v1.evidence%ROWTYPE; v jsonb;
BEGIN
 SELECT * INTO o FROM kcml_retry_v1.operation WHERE operation_id=NEW.operation_id;
 v=convert_from(o.source_bytes,'UTF8')::jsonb;
 SELECT * INTO a FROM kcml_retry_v1.attempt WHERE attempt_id=(v->>'currentAttemptId')::uuid AND operation_id=o.operation_id;
 SELECT * INTO s FROM kcml_retry_v1.current_state WHERE attempt_id=a.attempt_id AND operation_id=o.operation_id;
 IF a.attempt_id IS NULL OR s.attempt_id IS NULL OR a.attempt_sequence<>(v->>'currentAttemptSequence')::bigint OR s.state_id<>(v->>'currentAttemptStateId')::uuid OR s.state_version<>(v->>'currentAttemptStateVersion')::bigint OR convert_from(s.source_bytes,'UTF8')::jsonb->>'state'<>v->>'state' THEN
 RAISE EXCEPTION 'RETRY_DEFERRED_CURRENT_JOIN_DRIFT' USING ERRCODE='23514';END IF;
 v=convert_from(s.source_bytes,'UTF8')::jsonb;
 IF v->>'evidenceId' IS NOT NULL THEN
 SELECT * INTO e FROM kcml_retry_v1.evidence WHERE evidence_id=(v->>'evidenceId')::uuid AND attempt_id=a.attempt_id AND operation_id=o.operation_id;
 IF e.evidence_id IS NULL OR 'sha256:'||encode(e.source_digest,'hex')<>v->>'evidenceDigest' OR (convert_from(e.source_bytes,'UTF8')::jsonb->>'jobId')::uuid<>o.job_id OR (convert_from(e.source_bytes,'UTF8')::jsonb->>'phaseRunId')::uuid<>o.phase_run_id THEN
 RAISE EXCEPTION 'RETRY_DEFERRED_EVIDENCE_JOIN_DRIFT' USING ERRCODE='23514';END IF;END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER exact_join AFTER INSERT OR UPDATE ON kcml_retry_v1.operation DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.check_current_join();
CREATE CONSTRAINT TRIGGER exact_join AFTER INSERT OR UPDATE ON kcml_retry_v1.attempt DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.check_current_join();
CREATE CONSTRAINT TRIGGER exact_join AFTER INSERT OR UPDATE ON kcml_retry_v1.current_state DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.check_current_join();
CREATE CONSTRAINT TRIGGER exact_join AFTER INSERT ON kcml_retry_v1.evidence DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.check_current_join();
REVOKE ALL ON FUNCTION kcml_retry_v1.check_current_join() FROM PUBLIC;
