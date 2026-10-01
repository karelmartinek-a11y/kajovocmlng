-- §§51.6/12.51.2: admit all known source/new child E90 roots before phase H50.
-- No visible child may commit without the same transaction's exact frozen scan.
ALTER TABLE generation_job ALTER CONSTRAINT generation_job_parent_job_id_fkey DEFERRABLE INITIALLY DEFERRED;
CREATE OR REPLACE FUNCTION kcml_retry_v1.child_insert_guard() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$BEGIN
 IF NEW.kind='RETRY' AND NEW.parent_job_id IS NULL THEN RAISE EXCEPTION 'RETRY_CHILD_PARENT_REQUIRED' USING ERRCODE='23514';END IF;
 RETURN NEW;
END$$;
CREATE FUNCTION kcml_retry_v1.ordered_child_commit_guard() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE g public.generation_job;s kcml_retry_v1.child_scan;
BEGIN
 SELECT * INTO STRICT g FROM public.generation_job WHERE id=NEW.id;
 IF g.kind<>'RETRY' THEN RETURN NULL;END IF;
 SELECT * INTO s FROM kcml_retry_v1.child_scan WHERE child_job_id=g.id;
 IF s.child_job_id IS NULL OR s.transaction_id IS DISTINCT FROM pg_current_xact_id()
 OR s.source_job_id IS DISTINCT FROM g.parent_job_id
 OR NOT EXISTS(SELECT 1 FROM public.generation_job p WHERE p.id=s.source_job_id AND p.owner_id=g.owner_id)
 OR NOT EXISTS(SELECT 1 FROM public.generation_job_create_completion c JOIN public.domain_command d ON d.logical_operation_id=c.logical_operation_id WHERE c.job_id=g.id AND d.state='SUCCEEDED') THEN
 RAISE EXCEPTION 'RETRY_CHILD_SCAN_TRANSACTION_REQUIRED' USING ERRCODE='23514';END IF;
 RETURN NULL;
END$$;
CREATE CONSTRAINT TRIGGER ordered_child_commit_guard AFTER INSERT ON public.generation_job DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_retry_v1.ordered_child_commit_guard();
REVOKE ALL ON FUNCTION kcml_retry_v1.ordered_child_commit_guard() FROM PUBLIC;

-- The narrow compound adapter has already locked both known E90 roots and phaseH50.
-- Never expose this stage as a standalone public/client function or a preheld flag.
CREATE FUNCTION kcml_retry_v1.reserve_child_ordered(p_child uuid,p_phase uuid,p_source uuid,p_digest bytea,p_fence bigint) RETURNS jsonb LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE g public.generation_job; saved kcml_retry_v1.child_scan; scanned jsonb; raw bytea;
BEGIN
 SELECT * INTO g FROM public.generation_job WHERE id=p_source;
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

REVOKE ALL ON FUNCTION kcml_retry_v1.reserve_child_ordered(uuid,uuid,uuid,bytea,bigint) FROM PUBLIC;
