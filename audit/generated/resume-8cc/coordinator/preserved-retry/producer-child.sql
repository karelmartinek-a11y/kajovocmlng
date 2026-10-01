-- Candidate specialization §§12.51.1,25.11,25.16,49.8–49.9.
-- Server-side membership capture; no caller member-count/validity flag.
CREATE TABLE kcml_retry_v1.phase_membership (
 phase_run_id uuid NOT NULL REFERENCES kcml_retry_v1.phase(phase_run_id),
 sequence bigint NOT NULL CHECK(sequence>0), operation_id uuid NOT NULL UNIQUE REFERENCES kcml_retry_v1.operation(operation_id),
 PRIMARY KEY(phase_run_id,sequence)
);
CREATE FUNCTION kcml_retry_v1.capture_member() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 PERFORM 1 FROM kcml_retry_v1.phase WHERE phase_run_id=NEW.phase_run_id FOR UPDATE;
 INSERT INTO kcml_retry_v1.phase_membership SELECT NEW.phase_run_id,coalesce(max(sequence),0)+1,NEW.operation_id FROM kcml_retry_v1.phase_membership WHERE phase_run_id=NEW.phase_run_id;
 RETURN NULL;
END $$;
CREATE TRIGGER capture_member AFTER INSERT ON kcml_retry_v1.operation FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.capture_member();
-- Existing rows require server-only transactional backfill before activation.
INSERT INTO kcml_retry_v1.phase_membership SELECT phase_run_id,row_number() OVER(PARTITION BY phase_run_id ORDER BY operation_id),operation_id FROM kcml_retry_v1.operation;
CREATE TRIGGER membership_immutable BEFORE UPDATE OR DELETE ON kcml_retry_v1.phase_membership FOR EACH ROW EXECUTE FUNCTION public.kcml_create_record_immutable_v1();
CREATE TABLE kcml_retry_v1.child_scan (
 child_job_id uuid PRIMARY KEY REFERENCES public.generation_job(id) DEFERRABLE INITIALLY DEFERRED,
 phase_run_id uuid NOT NULL REFERENCES kcml_retry_v1.phase(phase_run_id),
 source_job_id uuid NOT NULL REFERENCES public.generation_job(id),
 source_phase_digest bytea NOT NULL CHECK(octet_length(source_phase_digest)=32),
 source_parent_fence bigint NOT NULL, source_incarnation uuid NOT NULL,source_epoch bigint NOT NULL,
 scan_bytes bytea NOT NULL,scan_digest bytea NOT NULL CHECK(sha256(scan_bytes)=scan_digest),
 transaction_id xid8 NOT NULL, UNIQUE(child_job_id,phase_run_id)
);
CREATE TRIGGER frozen_child_scan BEFORE UPDATE OR DELETE ON kcml_retry_v1.child_scan FOR EACH ROW EXECUTE FUNCTION public.kcml_create_record_immutable_v1();
CREATE FUNCTION kcml_retry_v1.reserve_child(p_child uuid,p_phase uuid,p_source uuid,p_digest bytea,p_fence bigint) RETURNS jsonb LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE g public.generation_job; saved kcml_retry_v1.child_scan; scanned jsonb; raw bytea;
BEGIN
 SELECT * INTO g FROM public.generation_job WHERE id=p_source FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'RETRY_SOURCE_JOB_UNAVAILABLE' USING ERRCODE='23514'; END IF;
 SELECT * INTO saved FROM kcml_retry_v1.child_scan WHERE child_job_id=p_child;
 IF FOUND THEN
  IF (saved.phase_run_id,saved.source_job_id,saved.source_phase_digest) IS DISTINCT FROM(p_phase,p_source,p_digest) THEN RAISE EXCEPTION 'RETRY_CHILD_REPLAY_CONFLICT' USING ERRCODE='23514';END IF;
  RETURN convert_from(saved.scan_bytes,'UTF8')::jsonb;
 END IF;
 IF g.coordinator_fencing_token IS DISTINCT FROM p_fence OR g.coordinator_lease_owner_id IS NULL OR g.coordinator_lease_expires_at<=clock_timestamp()
 OR NOT EXISTS(SELECT 1 FROM public.platform_incarnation p WHERE p.platform_incarnation_id=g.platform_incarnation_id)
 OR NOT EXISTS(SELECT 1 FROM public.application_deployment_head p WHERE p.platform_incarnation_id=g.platform_incarnation_id AND p.application_deployment_epoch=g.application_deployment_epoch)
 THEN RAISE EXCEPTION 'RETRY_SOURCE_FENCE_STALE' USING ERRCODE='23514';END IF;
 scanned=kcml_retry_v1.scan(p_phase,p_source,p_digest);
 IF EXISTS(SELECT operation_id FROM kcml_retry_v1.operation WHERE phase_run_id=p_phase EXCEPT SELECT operation_id FROM kcml_retry_v1.phase_membership WHERE phase_run_id=p_phase)
 OR EXISTS(SELECT operation_id FROM kcml_retry_v1.phase_membership WHERE phase_run_id=p_phase EXCEPT SELECT operation_id FROM kcml_retry_v1.operation WHERE phase_run_id=p_phase)
 OR (SELECT coalesce(max(sequence),0)<>count(*) FROM kcml_retry_v1.phase_membership WHERE phase_run_id=p_phase)
 THEN RAISE EXCEPTION 'RETRY_PHASE_MEMBERSHIP_INCOMPLETE' USING ERRCODE='23514';END IF;
 -- Open attempts/outcomes cannot be laundered through schema-only scan.
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(scanned->'rows') r WHERE r->>'evidenceId' IS NULL OR convert_from(decode(r->>'stateBytes','hex'),'UTF8')::jsonb->>'state' IN ('INTENT_RECORDED','DISPATCHING','OUTCOME_RECORDED','RECONCILING','UNKNOWN')) THEN
 RAISE EXCEPTION 'RETRY_SOURCE_PRODUCER_INCOMPLETE' USING ERRCODE='23514';END IF;
 raw=convert_to(scanned::text,'UTF8');
 INSERT INTO kcml_retry_v1.child_scan VALUES(p_child,p_phase,p_source,p_digest,p_fence,g.platform_incarnation_id,g.application_deployment_epoch,raw,sha256(raw),pg_current_xact_id());
 RETURN scanned;
END $$;
CREATE FUNCTION kcml_retry_v1.child_insert_guard() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE s kcml_retry_v1.child_scan;
BEGIN
 IF NEW.kind<>'RETRY' THEN RETURN NEW;END IF;
 SELECT * INTO s FROM kcml_retry_v1.child_scan WHERE child_job_id=NEW.id;
 IF NOT FOUND OR s.transaction_id IS DISTINCT FROM pg_current_xact_id() OR NEW.parent_job_id IS DISTINCT FROM s.source_job_id OR NOT EXISTS(SELECT 1 FROM public.generation_job p WHERE p.id=s.source_job_id AND p.owner_id=NEW.owner_id) THEN RAISE EXCEPTION 'RETRY_CHILD_SCAN_TRANSACTION_REQUIRED' USING ERRCODE='23514';END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER child_insert_guard BEFORE INSERT ON public.generation_job FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.child_insert_guard();
CREATE FUNCTION kcml_retry_v1.child_commit_guard() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM public.generation_job g JOIN public.generation_job_create_completion c ON c.job_id=g.id JOIN public.domain_command d ON d.logical_operation_id=c.logical_operation_id WHERE g.id=NEW.child_job_id AND g.kind='RETRY' AND g.parent_job_id=NEW.source_job_id AND d.state='SUCCEEDED') THEN
 RAISE EXCEPTION 'RETRY_CHILD_COMMIT_INCOMPLETE' USING ERRCODE='23514';END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER child_commit_guard AFTER INSERT ON kcml_retry_v1.child_scan DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.child_commit_guard();
REVOKE ALL ON ALL TABLES IN SCHEMA kcml_retry_v1 FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_retry_v1 FROM PUBLIC;
