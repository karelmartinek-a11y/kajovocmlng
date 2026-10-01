-- Additive candidate §§25.16,49.8,49.9,49.11,51.31; not activated yet.
CREATE SCHEMA kcml_effect_v1;
CREATE TABLE kcml_effect_v1.phase_run (
 id uuid PRIMARY KEY,parent_id uuid NOT NULL REFERENCES public.generation_job(id),state text NOT NULL CHECK(state IN('RUNNING','FAILED')),
 plan_bytes bytea NOT NULL,plan_digest bytea NOT NULL CHECK(sha256(plan_bytes)=plan_digest),specification_digest bytea NOT NULL CHECK(octet_length(specification_digest)=32),
 failed_source_bytes bytea NULL,failed_source_digest bytea NULL CHECK(sha256(failed_source_bytes)=failed_source_digest),start_fence bigint NOT NULL,start_incarnation uuid NOT NULL,start_epoch bigint NOT NULL,
 CHECK((state='FAILED')=(failed_source_bytes IS NOT NULL))
);
CREATE TABLE kcml_effect_v1.operation (
 id uuid PRIMARY KEY,phase_run_id uuid NOT NULL REFERENCES kcml_effect_v1.phase_run(id),
 parent_id uuid NOT NULL REFERENCES generation_job(id),logical_operation_id uuid NOT NULL REFERENCES domain_command(logical_operation_id),step_key text NOT NULL,
 request_bytes bytea NOT NULL,request_digest bytea NOT NULL CHECK(sha256(request_bytes)=request_digest),
 target_binding_id uuid NOT NULL,target_revision_id uuid NOT NULL,target_key text NOT NULL CHECK(length(target_key)>0),
 current_sequence bigint NOT NULL CHECK(current_sequence>0),state text NOT NULL,
 classifier_id text NOT NULL,classifier_digest bytea NOT NULL CHECK(octet_length(classifier_digest)=32),
 UNIQUE(phase_run_id,step_key),UNIQUE(id,parent_id,phase_run_id)
);
CREATE TABLE kcml_effect_v1.attempt (
 operation_id uuid NOT NULL REFERENCES kcml_effect_v1.operation(id),sequence bigint NOT NULL CHECK(sequence>0),id uuid NOT NULL UNIQUE,
 dispatch_outbox_id uuid NOT NULL UNIQUE,parent_fence bigint NOT NULL CHECK(parent_fence>0),incarnation uuid NOT NULL,epoch bigint NOT NULL,
 cancellation_version bigint NOT NULL CHECK(cancellation_version>=0),deadline timestamptz NOT NULL,
 concurrency_key_digest bytea NOT NULL CHECK(octet_length(concurrency_key_digest)=32),concurrency_owner uuid NOT NULL,concurrency_fence bigint NOT NULL CHECK(concurrency_fence>0),
 PRIMARY KEY(operation_id,sequence)
);
CREATE TABLE kcml_effect_v1.state (
 operation_id uuid NOT NULL,sequence bigint NOT NULL,state text NOT NULL CHECK(state IN('INTENT_RECORDED','DISPATCHING','OUTCOME_RECORDED','RECONCILING','CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL','UNKNOWN')),
 state_version bigint NOT NULL CHECK(state_version>0),last_evidence_sequence bigint NOT NULL DEFAULT 0 CHECK(last_evidence_sequence>=0),
 outcome_digest bytea NULL CHECK(octet_length(outcome_digest)=32),reconciliation_relation uuid NULL,
 state_id uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),
 PRIMARY KEY(operation_id,sequence),FOREIGN KEY(operation_id,sequence) REFERENCES kcml_effect_v1.attempt(operation_id,sequence),
 CHECK((state='UNKNOWN')=(reconciliation_relation IS NOT NULL)),CHECK((state IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL'))=(outcome_digest IS NOT NULL))
);
CREATE TABLE kcml_effect_v1.concurrency_claim (
 key_digest bytea PRIMARY KEY CHECK(octet_length(key_digest)=32),owner_id uuid NOT NULL,fence bigint NOT NULL CHECK(fence>0),expires_at timestamptz NOT NULL
);
CREATE TABLE kcml_effect_v1.evidence (
 operation_id uuid NOT NULL,sequence bigint NOT NULL,evidence_sequence bigint NOT NULL CHECK(evidence_sequence>0),id uuid NOT NULL UNIQUE,
 kind text NOT NULL CHECK(kind IN('REQUEST','DISPATCH_PREPARED','RESPONSE','TRANSPORT_ERROR','READ_BACK','RECONCILIATION','CONFIRMATION')),
 exact_bytes bytea NOT NULL,content_digest bytea NOT NULL CHECK(sha256(exact_bytes)=content_digest),source_fence bigint NOT NULL,incarnation uuid NOT NULL,observed_at timestamptz NOT NULL,
 PRIMARY KEY(operation_id,sequence,evidence_sequence),FOREIGN KEY(operation_id,sequence) REFERENCES kcml_effect_v1.attempt(operation_id,sequence)
);
CREATE TABLE kcml_effect_v1.checkpoint (
 id uuid PRIMARY KEY,parent_id uuid NOT NULL REFERENCES generation_job(id),sequence bigint NOT NULL CHECK(sequence>0),
 parent_state_version bigint NOT NULL,parent_fence bigint NOT NULL,incarnation uuid NOT NULL,epoch bigint NOT NULL,
 operation_id uuid NOT NULL,attempt_sequence bigint NOT NULL,phase text NOT NULL CHECK(phase IN('PRE','POST')),exact_bytes bytea NOT NULL,content_digest bytea NOT NULL CHECK(sha256(exact_bytes)=content_digest),
 UNIQUE(parent_id,sequence),UNIQUE(operation_id,attempt_sequence,phase),FOREIGN KEY(operation_id,attempt_sequence) REFERENCES kcml_effect_v1.attempt(operation_id,sequence)
);
CREATE TABLE kcml_effect_v1.checkpoint_head(parent_id uuid PRIMARY KEY REFERENCES generation_job(id),last_sequence bigint NOT NULL CHECK(last_sequence>=0),latest_id uuid NULL REFERENCES kcml_effect_v1.checkpoint(id) DEFERRABLE INITIALLY DEFERRED);
ALTER TABLE public.transactional_outbox ADD COLUMN is_dispatch_authority boolean NOT NULL DEFAULT false,ADD COLUMN side_effect_operation_id uuid NULL,ADD COLUMN side_effect_attempt_sequence bigint NULL,ADD COLUMN target_idempotency_key text NULL,ADD COLUMN immutable_request_digest bytea NULL,ADD COLUMN concurrency_key_digest bytea NULL;
ALTER TABLE public.transactional_outbox ADD CONSTRAINT effect_dispatch_shape CHECK((purpose='SIDE_EFFECT_DISPATCH')=is_dispatch_authority AND (NOT is_dispatch_authority OR (side_effect_operation_id IS NOT NULL AND side_effect_attempt_sequence IS NOT NULL AND target_idempotency_key IS NOT NULL AND immutable_request_digest IS NOT NULL AND concurrency_key_digest IS NOT NULL AND octet_length(immutable_request_digest)=32 AND octet_length(concurrency_key_digest)=32)));
ALTER TABLE public.transactional_outbox ADD CONSTRAINT effect_dispatch_unique UNIQUE(side_effect_operation_id,side_effect_attempt_sequence,id);
ALTER TABLE public.transactional_outbox ADD CONSTRAINT effect_dispatch_attempt FOREIGN KEY(side_effect_operation_id,side_effect_attempt_sequence) REFERENCES kcml_effect_v1.attempt(operation_id,sequence) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE kcml_effect_v1.attempt ADD CONSTRAINT attempt_dispatch_authority FOREIGN KEY(operation_id,sequence,dispatch_outbox_id) REFERENCES public.transactional_outbox(side_effect_operation_id,side_effect_attempt_sequence,id) DEFERRABLE INITIALLY DEFERRED;
CREATE UNIQUE INDEX effect_dispatch_one ON public.transactional_outbox(side_effect_operation_id,side_effect_attempt_sequence) WHERE purpose='SIDE_EFFECT_DISPATCH' AND is_dispatch_authority;
CREATE FUNCTION kcml_effect_v1.fence_guard(p_op uuid,p_sequence bigint) RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE o kcml_effect_v1.operation;a kcml_effect_v1.attempt;g public.generation_job;c kcml_effect_v1.concurrency_claim;
BEGIN
 SELECT * INTO STRICT o FROM kcml_effect_v1.operation WHERE id=p_op;
 SELECT * INTO STRICT a FROM kcml_effect_v1.attempt WHERE operation_id=p_op AND sequence=p_sequence;
 SELECT * INTO STRICT g FROM public.generation_job WHERE id=o.parent_id FOR UPDATE;
 SELECT * INTO c FROM kcml_effect_v1.concurrency_claim WHERE key_digest=a.concurrency_key_digest FOR UPDATE;
 IF g.coordinator_fencing_token IS DISTINCT FROM a.parent_fence OR g.platform_incarnation_id IS DISTINCT FROM a.incarnation OR g.application_deployment_epoch IS DISTINCT FROM a.epoch
 OR g.cancellation_version IS DISTINCT FROM a.cancellation_version OR g.coordinator_lease_owner_id IS NULL OR g.coordinator_lease_expires_at<=clock_timestamp() OR a.deadline<=clock_timestamp()
 OR g.state IN('CANCELLED','COMPLETED','FAILED') OR c.owner_id IS DISTINCT FROM a.concurrency_owner OR c.fence IS DISTINCT FROM a.concurrency_fence OR c.expires_at<=clock_timestamp()
 OR NOT EXISTS(SELECT 1 FROM public.platform_incarnation WHERE platform_incarnation_id=a.incarnation)
 OR NOT EXISTS(SELECT 1 FROM public.application_deployment_head WHERE platform_incarnation_id=a.incarnation AND application_deployment_epoch=a.epoch)
 THEN RAISE EXCEPTION 'EFFECT_FENCE_INVALID' USING ERRCODE='23514';END IF;
END $$;
CREATE FUNCTION kcml_effect_v1.require_atomic_attempt() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE o kcml_effect_v1.operation;a kcml_effect_v1.attempt;s kcml_effect_v1.state;
BEGIN
 SELECT * INTO STRICT o FROM kcml_effect_v1.operation WHERE id=NEW.operation_id;
 SELECT * INTO STRICT a FROM kcml_effect_v1.attempt WHERE operation_id=o.id AND sequence=o.current_sequence;
 SELECT * INTO s FROM kcml_effect_v1.state WHERE operation_id=a.operation_id AND sequence=a.sequence;
 IF s.operation_id IS NULL OR s.state IS DISTINCT FROM o.state OR NOT EXISTS(SELECT 1 FROM public.transactional_outbox b WHERE b.id=a.dispatch_outbox_id AND b.is_dispatch_authority AND b.purpose='SIDE_EFFECT_DISPATCH' AND b.side_effect_operation_id=o.id AND b.side_effect_attempt_sequence=a.sequence AND b.target_idempotency_key=o.target_key AND b.immutable_request_digest=o.request_digest AND b.concurrency_key_digest=a.concurrency_key_digest)
 OR NOT EXISTS(SELECT 1 FROM kcml_effect_v1.checkpoint WHERE operation_id=o.id AND attempt_sequence=a.sequence AND phase='PRE')
 OR (s.state IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL') AND NOT EXISTS(SELECT 1 FROM kcml_effect_v1.checkpoint p JOIN public.domain_event e ON (convert_from(e.payload_bytes,'UTF8')::jsonb->>'checkpointId')=p.id::text AND (convert_from(e.payload_bytes,'UTF8')::jsonb->>'checkpointDigest')='sha256:'||encode(p.content_digest,'hex') JOIN public.transactional_outbox b ON b.event_id=e.id AND b.payload_digest=e.payload_digest WHERE p.operation_id=o.id AND p.attempt_sequence=a.sequence AND p.phase='POST' AND b.purpose='SIDE_EFFECT_CONTINUATION' AND b.logical_operation_id=o.logical_operation_id))
 OR (SELECT count(*) FROM kcml_effect_v1.evidence WHERE operation_id=o.id AND sequence=a.sequence)<>s.last_evidence_sequence
 OR EXISTS(SELECT 1 FROM kcml_effect_v1.evidence e WHERE e.operation_id=o.id AND e.sequence=a.sequence AND (e.evidence_sequence>s.last_evidence_sequence OR e.source_fence IS DISTINCT FROM a.parent_fence OR e.incarnation IS DISTINCT FROM a.incarnation)) THEN
 RAISE EXCEPTION 'EFFECT_ATOMIC_ATTEMPT_INCOMPLETE' USING ERRCODE='23514';END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER effect_attempt_closure AFTER INSERT ON kcml_effect_v1.attempt DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.require_atomic_attempt();
CREATE CONSTRAINT TRIGGER effect_state_closure AFTER INSERT OR UPDATE ON kcml_effect_v1.state DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.require_atomic_attempt();
CREATE FUNCTION kcml_effect_v1.append_evidence(p_op uuid,p_sequence bigint,p_id uuid,p_kind text,p_raw bytea) RETURNS bigint LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE s kcml_effect_v1.state;a kcml_effect_v1.attempt;n bigint;
BEGIN
 PERFORM kcml_effect_v1.fence_guard(p_op,p_sequence);
 SELECT * INTO STRICT s FROM kcml_effect_v1.state WHERE operation_id=p_op AND sequence=p_sequence FOR UPDATE;
 SELECT * INTO STRICT a FROM kcml_effect_v1.attempt WHERE operation_id=p_op AND sequence=p_sequence;
 IF s.state IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL') THEN RAISE EXCEPTION 'EFFECT_TERMINAL_EVIDENCE_DENIED' USING ERRCODE='23514';END IF;
 n=s.last_evidence_sequence+1;
 INSERT INTO kcml_effect_v1.evidence VALUES(p_op,p_sequence,n,p_id,p_kind,p_raw,sha256(p_raw),a.parent_fence,a.incarnation,clock_timestamp());
 UPDATE kcml_effect_v1.state SET last_evidence_sequence=n,state_version=state_version+1 WHERE operation_id=p_op AND sequence=p_sequence;
 RETURN n;
END $$;
CREATE FUNCTION kcml_effect_v1.dispatch_guard(p_op uuid,p_sequence bigint) RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE s kcml_effect_v1.state;a kcml_effect_v1.attempt;
BEGIN
 PERFORM kcml_effect_v1.fence_guard(p_op,p_sequence);
 SELECT * INTO STRICT s FROM kcml_effect_v1.state WHERE operation_id=p_op AND sequence=p_sequence FOR UPDATE;
 IF NOT EXISTS(SELECT 1 FROM kcml_effect_v1.operation o JOIN kcml_effect_v1.phase_run p ON p.id=o.phase_run_id JOIN public.generation_job g ON g.id=o.parent_id WHERE o.id=p_op AND g.active_phase_run_id=p.id AND p.state='RUNNING') THEN RAISE EXCEPTION 'EFFECT_PHASE_NOT_EXECUTING' USING ERRCODE='23514';END IF;
 IF s.state IS DISTINCT FROM 'INTENT_RECORDED' THEN RAISE EXCEPTION 'EFFECT_DISPATCH_STATE_INVALID' USING ERRCODE='23514';END IF;
 SELECT * INTO STRICT a FROM kcml_effect_v1.attempt WHERE operation_id=p_op AND sequence=p_sequence;
 UPDATE kcml_effect_v1.state SET state='DISPATCHING',state_version=state_version+1 WHERE operation_id=p_op AND sequence=p_sequence;
 UPDATE kcml_effect_v1.operation SET state='DISPATCHING' WHERE id=p_op;
 UPDATE public.transactional_outbox SET state='DISPATCH_AUTHORIZED',state_version=state_version+1 WHERE id=a.dispatch_outbox_id;
END $$;
CREATE FUNCTION kcml_effect_v1.write_checkpoint(p_op uuid,p_sequence bigint,p_id uuid,p_phase text,p_raw bytea) RETURNS bigint LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE o kcml_effect_v1.operation;g public.generation_job;a kcml_effect_v1.attempt;n bigint;v jsonb;
BEGIN
 PERFORM kcml_effect_v1.fence_guard(p_op,p_sequence);
 SELECT * INTO STRICT o FROM kcml_effect_v1.operation WHERE id=p_op;
 SELECT * INTO STRICT g FROM public.generation_job WHERE id=o.parent_id;
 SELECT * INTO STRICT a FROM kcml_effect_v1.attempt WHERE operation_id=p_op AND sequence=p_sequence;
 INSERT INTO kcml_effect_v1.checkpoint_head VALUES(g.id,0,NULL)ON CONFLICT DO NOTHING;
 SELECT last_sequence+1 INTO n FROM kcml_effect_v1.checkpoint_head WHERE parent_id=g.id FOR UPDATE;
 IF p_raw IS NULL THEN p_raw=kcml_effect_v1.compile_checkpoint(p_op,p_sequence);
 ELSIF p_raw IS DISTINCT FROM kcml_effect_v1.compile_checkpoint(p_op,p_sequence) THEN RAISE EXCEPTION 'EFFECT_CHECKPOINT_FULL_MASK' USING ERRCODE='23514';END IF;
 v=convert_from(p_raw,'UTF8')::jsonb;
 IF v->>'parentId' IS DISTINCT FROM g.id::text OR v->>'stateVersion' IS DISTINCT FROM g.state_version::text OR v->>'fence' IS DISTINCT FROM a.parent_fence::text OR v->>'incarnation' IS DISTINCT FROM a.incarnation::text OR v->>'sequence' IS DISTINCT FROM n::text OR v->>'operationId' IS DISTINCT FROM o.id::text THEN
 RAISE EXCEPTION 'EFFECT_CHECKPOINT_IDENTITY' USING ERRCODE='23514';END IF;
 INSERT INTO kcml_effect_v1.checkpoint VALUES(p_id,g.id,n,g.state_version,a.parent_fence,a.incarnation,a.epoch,p_op,p_sequence,p_phase,p_raw,sha256(p_raw));
 UPDATE kcml_effect_v1.checkpoint_head SET last_sequence=n,latest_id=p_id WHERE parent_id=g.id;
 RETURN n;
END $$;
CREATE FUNCTION kcml_effect_v1.immutable() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN RAISE EXCEPTION 'EFFECT_IMMUTABLE' USING ERRCODE='55000';END$$;
CREATE TRIGGER attempt_immutable BEFORE UPDATE OR DELETE ON kcml_effect_v1.attempt FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.immutable();
CREATE TRIGGER evidence_immutable BEFORE UPDATE OR DELETE ON kcml_effect_v1.evidence FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.immutable();
CREATE TRIGGER checkpoint_immutable BEFORE UPDATE OR DELETE ON kcml_effect_v1.checkpoint FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.immutable();
REVOKE ALL ON SCHEMA kcml_effect_v1 FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA kcml_effect_v1 FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
CREATE FUNCTION kcml_effect_v1.classify_cas_v1(observation jsonb,request_digest bytea,target_key text,operation_id uuid) RETURNS text LANGUAGE plpgsql IMMUTABLE SET search_path=pg_catalog AS $$
BEGIN
 IF jsonb_typeof(observation) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(observation))<>7 OR NOT observation ?& ARRAY['requestDigest','targetIdempotencyKey','beforeVersion','afterVersion','beforeValueDigest','afterValueDigest','appliedOperationId']
 OR EXISTS(SELECT 1 FROM unnest(ARRAY['requestDigest','targetIdempotencyKey','beforeVersion','afterVersion','beforeValueDigest','afterValueDigest']) field WHERE jsonb_typeof(observation->field) IS DISTINCT FROM 'string')
 OR NOT (jsonb_typeof(observation->'appliedOperationId')='null' OR (jsonb_typeof(observation->'appliedOperationId')='string' AND (observation->>'appliedOperationId')~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'))
 OR observation->>'beforeVersion' IS NULL OR observation->>'afterVersion' IS NULL OR observation->>'beforeVersion'!~'^(0|[1-9][0-9]*)$' OR observation->>'afterVersion'!~'^(0|[1-9][0-9]*)$'
 OR observation->>'beforeValueDigest' IS NULL OR observation->>'afterValueDigest' IS NULL OR observation->>'beforeValueDigest'!~'^sha256:[0-9a-f]{64}$' OR observation->>'afterValueDigest'!~'^sha256:[0-9a-f]{64}$'
 THEN RAISE EXCEPTION 'EFFECT_OBSERVATION_MASK_INVALID' USING ERRCODE='23514';END IF;
 IF observation->>'requestDigest' IS DISTINCT FROM 'sha256:'||encode(request_digest,'hex') OR observation->>'targetIdempotencyKey' IS DISTINCT FROM target_key THEN RETURN 'UNKNOWN';END IF;
 IF observation->>'appliedOperationId' IS NULL AND observation->>'beforeVersion'=observation->>'afterVersion' AND observation->>'beforeValueDigest'=observation->>'afterValueDigest' THEN RETURN 'CONFIRMED_NOT_APPLIED';END IF;
 IF observation->>'appliedOperationId'=operation_id::text AND (observation->>'afterVersion')::numeric>(observation->>'beforeVersion')::numeric THEN RETURN 'CONFIRMED_APPLIED';END IF;
 RETURN 'UNKNOWN';
END $$;
CREATE FUNCTION kcml_effect_v1.confirm_cas_v1(p_op uuid,p_sequence bigint,p_checkpoint uuid,p_checkpoint_bytes bytea,p_event uuid,p_outbox uuid) RETURNS text LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE o kcml_effect_v1.operation;s kcml_effect_v1.state;e kcml_effect_v1.evidence;outcome text;code bytea;payload bytea;
BEGIN
 PERFORM kcml_effect_v1.fence_guard(p_op,p_sequence);
 SELECT * INTO STRICT s FROM kcml_effect_v1.state WHERE operation_id=p_op AND sequence=p_sequence FOR UPDATE;
 SELECT * INTO STRICT o FROM kcml_effect_v1.operation WHERE id=p_op;
 IF s.state IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL') THEN
 IF NOT EXISTS(SELECT 1 FROM kcml_effect_v1.checkpoint WHERE id=p_checkpoint AND operation_id=p_op AND attempt_sequence=p_sequence AND phase='POST' AND (p_checkpoint_bytes IS NULL OR exact_bytes=p_checkpoint_bytes)) THEN RAISE EXCEPTION 'EFFECT_OUTCOME_REPLAY_CONFLICT' USING ERRCODE='23514';END IF;
 RETURN s.state;END IF;
 IF s.state NOT IN('DISPATCHING','OUTCOME_RECORDED','RECONCILING') THEN RAISE EXCEPTION 'EFFECT_OUTCOME_STATE_INVALID' USING ERRCODE='23514';END IF;
 SELECT * INTO STRICT e FROM kcml_effect_v1.evidence WHERE operation_id=p_op AND sequence=p_sequence AND evidence_sequence=s.last_evidence_sequence AND kind IN('READ_BACK','RESPONSE','RECONCILIATION');
 code=convert_to(pg_get_functiondef('kcml_effect_v1.classify_cas_v1(jsonb,bytea,text,uuid)'::regprocedure),'UTF8');
 IF o.classifier_id IS DISTINCT FROM 'CAS_READ_BACK_V1' OR o.classifier_digest IS DISTINCT FROM sha256(code) OR NOT EXISTS(SELECT 1 FROM public.generation_frozen_bundle_v1 WHERE bundle_kind='POLICY_IMPLEMENTATION' AND bundle_id=o.classifier_id AND bundle_digest=o.classifier_digest AND exact_bytes=code) THEN RAISE EXCEPTION 'EFFECT_FROZEN_CLASSIFIER_UNAVAILABLE' USING ERRCODE='23514';END IF;
 outcome=kcml_effect_v1.classify_cas_v1(kcml_effect_v1.strict_observation(e.exact_bytes),o.request_digest,o.target_key,o.id);
 IF outcome='UNKNOWN' THEN RAISE EXCEPTION 'EFFECT_RECONCILIATION_REQUIRED' USING ERRCODE='23514';END IF;
 IF s.state='DISPATCHING' THEN
 UPDATE kcml_effect_v1.state SET state='OUTCOME_RECORDED',state_version=state_version+1 WHERE operation_id=p_op AND sequence=p_sequence;
 UPDATE kcml_effect_v1.operation SET state='OUTCOME_RECORDED' WHERE id=p_op;END IF;
 UPDATE kcml_effect_v1.state SET state=outcome,state_version=state_version+1,outcome_digest=e.content_digest WHERE operation_id=p_op AND sequence=p_sequence;
 UPDATE kcml_effect_v1.operation SET state=outcome WHERE id=p_op;
 PERFORM kcml_effect_v1.write_checkpoint(p_op,p_sequence,p_checkpoint,'POST',p_checkpoint_bytes);
 SELECT exact_bytes INTO p_checkpoint_bytes FROM kcml_effect_v1.checkpoint WHERE id=p_checkpoint;
 payload=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('operationId',o.id,'attemptSequence',p_sequence::text,'outcome',outcome,'evidenceDigest','sha256:'||encode(e.content_digest,'hex'),'checkpointId',p_checkpoint,'checkpointDigest','sha256:'||encode(sha256(p_checkpoint_bytes),'hex'))),'UTF8');
 INSERT INTO public.domain_event VALUES(p_event,o.id,'SIDE_EFFECT',o.logical_operation_id,2,'side.effect.outcome.recorded','urn:kcml:side-effect-outcome:1',sha256(kcml_effect_v1.event_mask('OUTCOME')),payload,sha256(payload),o.logical_operation_id,NULL,clock_timestamp());
 INSERT INTO public.transactional_outbox(id,event_id,logical_operation_id,aggregate_id,purpose,consumer_scope,available_at,state,payload_digest) VALUES(p_outbox,p_event,o.logical_operation_id,o.id,'SIDE_EFFECT_CONTINUATION','generation-effect-continuation',clock_timestamp(),'READY',sha256(payload));
 RETURN outcome;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
CREATE FUNCTION kcml_effect_v1.record_intent(
 p_op uuid,p_phase uuid,p_parent uuid,p_logical uuid,p_step text,p_attempt uuid,p_outbox uuid,p_event uuid,p_checkpoint uuid,
 p_request bytea,p_binding uuid,p_revision uuid,p_target_key text,p_fence bigint,p_cancel bigint,p_deadline timestamptz,
 p_concurrency_key bytea,p_concurrency_owner uuid,p_concurrency_fence bigint,p_classifier_digest bytea,p_checkpoint_bytes bytea)
RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE g public.generation_job;prior kcml_effect_v1.operation;payload bytea;
BEGIN
 SELECT * INTO STRICT g FROM public.generation_job WHERE id=p_parent FOR UPDATE;
 PERFORM 1 FROM kcml_effect_v1.phase_run WHERE id=p_phase AND parent_id=p_parent FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'EFFECT_PHASE_PARENT_IDENTITY' USING ERRCODE='23514';END IF;
 IF NOT EXISTS(SELECT 1 FROM kcml_effect_v1.phase_run WHERE id=p_phase AND state='RUNNING') OR g.active_phase_run_id IS DISTINCT FROM p_phase THEN RAISE EXCEPTION 'EFFECT_PHASE_NOT_EXECUTING' USING ERRCODE='23514';END IF;
 SELECT * INTO prior FROM kcml_effect_v1.operation WHERE id=p_op;
 IF FOUND THEN
  IF (prior.phase_run_id,prior.parent_id,prior.logical_operation_id,prior.step_key,prior.request_bytes,prior.target_binding_id,prior.target_revision_id,prior.target_key,prior.classifier_digest)
  IS DISTINCT FROM(p_phase,p_parent,p_logical,p_step,p_request,p_binding,p_revision,p_target_key,p_classifier_digest) THEN RAISE EXCEPTION 'EFFECT_INTENT_REPLAY_CONFLICT' USING ERRCODE='23514';END IF;
  RETURN;
 END IF;
 IF p_cancel IS DISTINCT FROM g.cancellation_version THEN RAISE EXCEPTION 'EFFECT_FENCE_INVALID' USING ERRCODE='23514';END IF;
 INSERT INTO kcml_effect_v1.operation VALUES(p_op,p_phase,p_parent,p_logical,p_step,p_request,sha256(p_request),p_binding,p_revision,p_target_key,1,'INTENT_RECORDED','CAS_READ_BACK_V1',p_classifier_digest);
 INSERT INTO kcml_effect_v1.attempt VALUES(p_op,1,p_attempt,p_outbox,p_fence,g.platform_incarnation_id,g.application_deployment_epoch,p_cancel,p_deadline,p_concurrency_key,p_concurrency_owner,p_concurrency_fence);
 INSERT INTO kcml_effect_v1.state VALUES(p_op,1,'INTENT_RECORDED',1,0,NULL,NULL);
 PERFORM kcml_effect_v1.fence_guard(p_op,1);
 PERFORM kcml_effect_v1.write_checkpoint(p_op,1,p_checkpoint,'PRE',p_checkpoint_bytes);
 payload=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('operationId',p_op,'attemptId',p_attempt,'requestDigest','sha256:'||encode(sha256(p_request),'hex'),'targetBindingId',p_binding,'targetRevisionId',p_revision)),'UTF8');
 INSERT INTO public.domain_event VALUES(p_event,p_op,'SIDE_EFFECT',p_logical,1,'side.effect.intent.recorded','urn:kcml:side-effect-intent:1',sha256(kcml_effect_v1.event_mask('INTENT')),payload,sha256(payload),p_logical,NULL,clock_timestamp());
 INSERT INTO public.transactional_outbox(id,event_id,logical_operation_id,aggregate_id,purpose,consumer_scope,available_at,state,payload_digest,is_dispatch_authority,side_effect_operation_id,side_effect_attempt_sequence,target_idempotency_key,immutable_request_digest,concurrency_key_digest)
 VALUES(p_outbox,p_event,p_logical,p_op,'SIDE_EFFECT_DISPATCH','generation-effect-dispatch',clock_timestamp(),'READY',sha256(payload),true,p_op,1,p_target_key,sha256(p_request),p_concurrency_key);
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
CREATE FUNCTION kcml_effect_v1.operation_immutable_scope() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN
 IF TG_OP='DELETE' OR (to_jsonb(NEW)-ARRAY['state','current_sequence'])IS DISTINCT FROM(to_jsonb(OLD)-ARRAY['state','current_sequence']) THEN RAISE EXCEPTION 'EFFECT_IMMUTABLE_OPERATION_SCOPE' USING ERRCODE='55000';END IF; RETURN NEW;END$$;
CREATE TRIGGER immutable_operation_scope BEFORE UPDATE OR DELETE ON kcml_effect_v1.operation FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.operation_immutable_scope();
CREATE FUNCTION kcml_effect_v1.operation_closure() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$DECLARE current_row kcml_effect_v1.operation;BEGIN
 SELECT * INTO STRICT current_row FROM kcml_effect_v1.operation WHERE id=NEW.id;
 IF NOT EXISTS(SELECT 1 FROM kcml_effect_v1.state WHERE operation_id=current_row.id AND sequence=current_row.current_sequence AND state=current_row.state)THEN RAISE EXCEPTION 'EFFECT_OPERATION_STATE_DRIFT' USING ERRCODE='23514';END IF;RETURN NULL;END$$;
CREATE CONSTRAINT TRIGGER operation_state_closure AFTER INSERT OR UPDATE ON kcml_effect_v1.operation DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.operation_closure();
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
CREATE FUNCTION kcml_effect_v1.event_mask(p_kind text) RETURNS bytea LANGUAGE plpgsql IMMUTABLE SET search_path=pg_catalog AS $$
DECLARE props jsonb;req jsonb;sid text;
BEGIN
 IF p_kind='INTENT' THEN
 sid='urn:kcml:side-effect-intent:1';props='{"operationId":{"type":"string","format":"uuid"},"attemptId":{"type":"string","format":"uuid"},"requestDigest":{"type":"string","pattern":"^sha256:[0-9a-f]{64}$"},"targetBindingId":{"type":"string","format":"uuid"},"targetRevisionId":{"type":"string","format":"uuid"}}'::jsonb;req='["operationId","attemptId","requestDigest","targetBindingId","targetRevisionId"]';
 ELSIF p_kind='OUTCOME' THEN
 sid='urn:kcml:side-effect-outcome:1';props='{"operationId":{"type":"string","format":"uuid"},"attemptSequence":{"type":"string","pattern":"^[1-9][0-9]*$"},"outcome":{"enum":["CONFIRMED_APPLIED","CONFIRMED_NOT_APPLIED","FAILED_FINAL"]},"evidenceDigest":{"type":"string","pattern":"^sha256:[0-9a-f]{64}$"},"checkpointId":{"type":"string","format":"uuid"},"checkpointDigest":{"type":"string","pattern":"^sha256:[0-9a-f]{64}$"}}'::jsonb;req='["operationId","attemptSequence","outcome","evidenceDigest","checkpointId","checkpointDigest"]';
 ELSE RAISE EXCEPTION 'EFFECT_EVENT_KIND_UNSUPPORTED' USING ERRCODE='23514';END IF;
 RETURN convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('$schema','https://json-schema.org/draft/2020-12/schema','$id',sid,'type','object','additionalProperties',false,'required',req,'properties',props)),'UTF8');
END $$;
CREATE FUNCTION kcml_effect_v1.publish_native_projection(p_op uuid,p_plan bytea,p_observation_schema jsonb) RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE o kcml_effect_v1.operation;a kcml_effect_v1.attempt;s kcml_effect_v1.state;e kcml_effect_v1.evidence;ph kcml_retry_v1.phase;plan jsonb;node jsonb;raw bytea;evraw bytea;ed bytea;
BEGIN
 SELECT * INTO STRICT o FROM kcml_effect_v1.operation WHERE id=p_op;
 PERFORM 1 FROM public.generation_job WHERE id=o.parent_id FOR UPDATE;
 SELECT * INTO STRICT ph FROM kcml_retry_v1.phase WHERE phase_run_id=o.phase_run_id FOR UPDATE;
 SELECT * INTO STRICT a FROM kcml_effect_v1.attempt WHERE operation_id=o.id AND sequence=o.current_sequence;
 SELECT * INTO STRICT s FROM kcml_effect_v1.state WHERE operation_id=o.id AND sequence=o.current_sequence FOR UPDATE;
 SELECT * INTO STRICT e FROM kcml_effect_v1.evidence WHERE operation_id=o.id AND sequence=o.current_sequence AND evidence_sequence=s.last_evidence_sequence;
 IF s.state NOT IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL') THEN RAISE EXCEPTION 'EFFECT_NATIVE_OUTCOME_UNRESOLVED' USING ERRCODE='23514';END IF;
 plan=convert_from(p_plan,'UTF8')::jsonb;
 IF plan->>'jobId' IS DISTINCT FROM o.parent_id::text OR plan->>'planId' IS DISTINCT FROM(convert_from(ph.source_bytes,'UTF8')::jsonb->>'planId') OR 'sha256:'||encode(sha256(p_plan),'hex') IS DISTINCT FROM(convert_from(ph.source_bytes,'UTF8')::jsonb->>'planDigest') THEN RAISE EXCEPTION 'EFFECT_NATIVE_PLAN_LINEAGE' USING ERRCODE='23514';END IF;
 SELECT value INTO STRICT node FROM jsonb_array_elements(plan->'nodes') WHERE value->>'nodeId'=o.step_key;
 evraw=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('evidenceId',e.id,'operationId',o.id,'attemptId',a.id,'jobId',o.parent_id,'phaseRunId',o.phase_run_id,'requestDigest','sha256:'||encode(o.request_digest,'hex'),'targetBindingId',o.target_binding_id,'targetBindingRevisionId',o.target_revision_id,'targetIdempotencyKey',o.target_key,'outcome',s.state,'recordedAt',to_char(e.observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),'classifierId',o.classifier_id,'classifierDigest','sha256:'||encode(o.classifier_digest,'hex'),'observationSchema',p_observation_schema,'observations',convert_from(e.exact_bytes,'UTF8')::jsonb)),'UTF8');ed=sha256(evraw);
 raw=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('operationId',o.id,'jobId',o.parent_id,'phaseRunId',o.phase_run_id,'nodeId',o.step_key,'currentAttemptId',a.id,'currentAttemptSequence',a.sequence::text,'currentAttemptStateId',s.state_id,'currentAttemptStateVersion',s.state_version::text,'state',s.state,'requestDigest','sha256:'||encode(o.request_digest,'hex'),'retryClass',node->>'retryClass','sideEffectClass',node->>'sideEffectClass','targetBindingId',o.target_binding_id,'targetBindingRevisionId',o.target_revision_id,'targetIdempotencyKey',o.target_key)),'UTF8');
 IF EXISTS(SELECT 1 FROM kcml_retry_v1.operation WHERE operation_id=o.id)THEN
 IF NOT EXISTS(SELECT 1 FROM kcml_retry_v1.operation WHERE operation_id=o.id AND phase_run_id=o.phase_run_id AND job_id=o.parent_id AND source_bytes=raw AND source_digest=sha256(raw)) OR NOT EXISTS(SELECT 1 FROM kcml_retry_v1.attempt WHERE attempt_id=a.id AND operation_id=o.id AND attempt_sequence=a.sequence AND phase_run_id=o.phase_run_id AND job_id=o.parent_id AND source_bytes=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('attemptId',a.id,'operationId',o.id,'jobId',o.parent_id,'phaseRunId',o.phase_run_id,'attemptSequence',a.sequence::text,'requestDigest','sha256:'||encode(o.request_digest,'hex'),'targetBindingId',o.target_binding_id,'targetBindingRevisionId',o.target_revision_id,'targetIdempotencyKey',o.target_key)),'UTF8')) OR NOT EXISTS(SELECT 1 FROM kcml_retry_v1.current_state WHERE attempt_id=a.id AND operation_id=o.id AND state_id=s.state_id AND state_version=s.state_version AND source_bytes=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('attemptStateId',s.state_id,'operationId',o.id,'attemptId',a.id,'attemptSequence',a.sequence::text,'state',s.state,'stateVersion',s.state_version::text,'evidenceId',e.id,'evidenceDigest','sha256:'||encode(ed,'hex'))),'UTF8')) OR NOT EXISTS(SELECT 1 FROM kcml_retry_v1.evidence WHERE evidence_id=e.id AND operation_id=o.id AND attempt_id=a.id AND source_bytes=evraw AND source_digest=ed)THEN RAISE EXCEPTION 'EFFECT_NATIVE_PUBLICATION_REPLAY_CONFLICT' USING ERRCODE='23514';END IF;
 RETURN;END IF;
 INSERT INTO kcml_retry_v1.operation VALUES(o.id,o.phase_run_id,o.parent_id,raw,sha256(raw));
 raw=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('attemptId',a.id,'operationId',o.id,'jobId',o.parent_id,'phaseRunId',o.phase_run_id,'attemptSequence',a.sequence::text,'requestDigest','sha256:'||encode(o.request_digest,'hex'),'targetBindingId',o.target_binding_id,'targetBindingRevisionId',o.target_revision_id,'targetIdempotencyKey',o.target_key)),'UTF8');
 INSERT INTO kcml_retry_v1.attempt VALUES(a.id,o.id,o.phase_run_id,o.parent_id,a.sequence,raw,sha256(raw));
 raw=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('attemptStateId',s.state_id,'operationId',o.id,'attemptId',a.id,'attemptSequence',a.sequence::text,'state',s.state,'stateVersion',s.state_version::text,'evidenceId',e.id,'evidenceDigest','sha256:'||encode(ed,'hex'))),'UTF8');
 INSERT INTO kcml_retry_v1.current_state VALUES(a.id,o.id,s.state_id,s.state_version,raw,sha256(raw));
 INSERT INTO kcml_retry_v1.evidence VALUES(e.id,o.id,a.id,evraw,ed);
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
-- Full checkpoint compilation sources beyond generation_job are immutable
-- execution-context snapshots. Missing native producers remain explicit, never
-- an empty-object/default budget or model-proposed approval.
CREATE TABLE kcml_effect_v1.checkpoint_context (
 parent_id uuid PRIMARY KEY REFERENCES public.generation_job(id),
 approved_revision_id uuid NOT NULL,specification_digest bytea NOT NULL CHECK(octet_length(specification_digest)=32),
 plan_id uuid NOT NULL,plan_digest bytea NOT NULL CHECK(octet_length(plan_digest)=32),
 agent_graph_ref jsonb NOT NULL,binding_snapshot_ref jsonb NOT NULL,budget_snapshot_ref jsonb NOT NULL,
 activation_epoch bigint NOT NULL CHECK(activation_epoch>=0),provider_handles jsonb NOT NULL,
 workspace_refs jsonb NOT NULL,browser_refs jsonb NOT NULL,event_cursors jsonb NOT NULL
);
CREATE TRIGGER checkpoint_context_immutable BEFORE UPDATE OR DELETE ON kcml_effect_v1.checkpoint_context FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.immutable();
CREATE FUNCTION kcml_effect_v1.assert_archived_ref(p_ref jsonb) RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF jsonb_typeof(p_ref) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(p_ref))<>4 OR NOT p_ref ?& ARRAY['recordId','contentDigest','schemaId','schemaDigest']
 OR EXISTS(SELECT 1 FROM unnest(ARRAY['recordId','contentDigest','schemaId','schemaDigest'])field WHERE jsonb_typeof(p_ref->field)IS DISTINCT FROM 'string')
 OR p_ref->>'contentDigest'!~'^sha256:[0-9a-f]{64}$' OR p_ref->>'schemaDigest'!~'^sha256:[0-9a-f]{64}$'
 OR NOT EXISTS(SELECT 1 FROM public.generation_frozen_bundle_v1 WHERE bundle_id=p_ref->>'recordId' AND bundle_digest=decode(substr(p_ref->>'contentDigest',8),'hex'))
 OR NOT EXISTS(SELECT 1 FROM public.generation_frozen_bundle_v1 WHERE bundle_kind='SCHEMA' AND bundle_id=p_ref->>'schemaId' AND bundle_digest=decode(substr(p_ref->>'schemaDigest',8),'hex'))
 THEN RAISE EXCEPTION 'EFFECT_CHECKPOINT_SOURCE_UNAVAILABLE' USING ERRCODE='23514';END IF;
END $$;
CREATE FUNCTION kcml_effect_v1.compile_checkpoint(p_op uuid,p_sequence bigint) RETURNS bytea LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE o kcml_effect_v1.operation;g public.generation_job;a kcml_effect_v1.attempt;c kcml_effect_v1.checkpoint_context;n bigint;v jsonb;pending jsonb;completed jsonb;watermark bigint;bytes bytea;
BEGIN
 PERFORM kcml_effect_v1.fence_guard(p_op,p_sequence);
 SELECT * INTO STRICT o FROM kcml_effect_v1.operation WHERE id=p_op;
 SELECT * INTO STRICT g FROM public.generation_job WHERE id=o.parent_id;
 SELECT * INTO STRICT a FROM kcml_effect_v1.attempt WHERE operation_id=p_op AND sequence=p_sequence;
 SELECT * INTO c FROM kcml_effect_v1.checkpoint_context WHERE parent_id=g.id;
 IF NOT FOUND OR c.approved_revision_id IS DISTINCT FROM g.approved_spec_revision_id OR c.specification_digest IS DISTINCT FROM g.approved_specification_digest OR c.plan_id IS DISTINCT FROM g.current_plan_id THEN RAISE EXCEPTION 'EFFECT_CHECKPOINT_APPROVED_SOURCE_UNAVAILABLE' USING ERRCODE='23514';END IF;
 IF NOT EXISTS(SELECT 1 FROM public.generation_frozen_bundle_v1 WHERE bundle_id=c.plan_id::text AND bundle_digest=c.plan_digest)THEN RAISE EXCEPTION 'EFFECT_CHECKPOINT_PLAN_UNAVAILABLE' USING ERRCODE='23514';END IF;
 PERFORM kcml_effect_v1.assert_archived_ref(c.agent_graph_ref);PERFORM kcml_effect_v1.assert_archived_ref(c.binding_snapshot_ref);PERFORM kcml_effect_v1.assert_archived_ref(c.budget_snapshot_ref);
 IF jsonb_typeof(c.workspace_refs)IS DISTINCT FROM 'array' OR jsonb_typeof(c.browser_refs)IS DISTINCT FROM 'array' OR jsonb_typeof(c.provider_handles)IS DISTINCT FROM 'array' OR jsonb_typeof(c.event_cursors)IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'EFFECT_CHECKPOINT_SOURCE_MASK' USING ERRCODE='23514';END IF;
 FOR v IN SELECT value FROM jsonb_array_elements(c.workspace_refs) LOOP PERFORM kcml_effect_v1.assert_archived_ref(v);END LOOP;
 FOR v IN SELECT value FROM jsonb_array_elements(c.browser_refs) LOOP PERFORM kcml_effect_v1.assert_archived_ref(v);END LOOP;
 FOR v IN SELECT value FROM jsonb_array_elements(c.provider_handles) LOOP
 IF jsonb_typeof(v)IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(v))<>3 OR NOT v ?& ARRAY['providerId','requestId','handle'] OR EXISTS(SELECT 1 FROM unnest(ARRAY['providerId','requestId','handle'])field WHERE jsonb_typeof(v->field)IS DISTINCT FROM 'string')THEN RAISE EXCEPTION 'EFFECT_CHECKPOINT_SOURCE_MASK' USING ERRCODE='23514';END IF;END LOOP;
 FOR v IN SELECT value FROM jsonb_array_elements(c.event_cursors) LOOP
 IF jsonb_typeof(v)IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(v))<>2 OR NOT v ?& ARRAY['streamId','sequence'] OR jsonb_typeof(v->'streamId')IS DISTINCT FROM 'string' OR jsonb_typeof(v->'sequence')IS DISTINCT FROM 'string' OR v->>'sequence'!~'^(0|[1-9][0-9]*)$'THEN RAISE EXCEPTION 'EFFECT_CHECKPOINT_SOURCE_MASK' USING ERRCODE='23514';END IF;END LOOP;
 INSERT INTO kcml_effect_v1.checkpoint_head VALUES(g.id,0,NULL)ON CONFLICT DO NOTHING;
 SELECT last_sequence+1 INTO n FROM kcml_effect_v1.checkpoint_head WHERE parent_id=g.id FOR UPDATE;
 SELECT coalesce(jsonb_agg(jsonb_build_object('operationId',x.id,'attemptSequence',x.current_sequence::text,'state',x.state)ORDER BY x.id),'[]') INTO pending FROM kcml_effect_v1.operation x WHERE x.parent_id=g.id AND x.state NOT IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL');
 SELECT coalesce(jsonb_agg(x.step_key ORDER BY x.step_key),'[]') INTO completed FROM kcml_effect_v1.operation x WHERE x.parent_id=g.id AND x.state='CONFIRMED_APPLIED';
 SELECT coalesce(max(aggregate_sequence),0) INTO watermark FROM public.domain_event WHERE aggregate_id=g.id;
 RETURN convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('parentId',g.id,'stateVersion',g.state_version::text,'incarnation',a.incarnation,'fence',a.parent_fence::text,'sequence',n::text,'operationId',o.id,
 'state',g.state,'substate',g.current_phase,'approvedRevisionId',c.approved_revision_id,'specificationDigest','sha256:'||encode(c.specification_digest,'hex'),'planId',c.plan_id,'planDigest','sha256:'||encode(c.plan_digest,'hex'),'agentGraphRef',c.agent_graph_ref,
 'bindingSnapshotRef',c.binding_snapshot_ref,'activationEpoch',c.activation_epoch::text,'completedStepKeys',completed,'eventWatermark',watermark::text,'pendingSideEffects',pending,'providerHandles',c.provider_handles,'eventCursors',c.event_cursors,
 'workspaceRefs',c.workspace_refs,'browserRefs',c.browser_refs,'budgetSnapshotRef',c.budget_snapshot_ref,'cancellationVersion',g.cancellation_version::text,'deadline',to_char(a.deadline AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'))),'UTF8');
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
CREATE TABLE kcml_effect_v1.phase_seal(phase_run_id uuid PRIMARY KEY REFERENCES kcml_retry_v1.phase(phase_run_id),exact_bytes bytea NOT NULL,content_digest bytea NOT NULL CHECK(sha256(exact_bytes)=content_digest));
CREATE TRIGGER phase_seal_immutable BEFORE UPDATE OR DELETE ON kcml_effect_v1.phase_seal FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.immutable();
CREATE FUNCTION kcml_effect_v1.producer_gate() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE p uuid;o uuid;
BEGIN
 IF TG_TABLE_NAME='operation' THEN p=CASE WHEN TG_OP='DELETE' THEN OLD.phase_run_id ELSE NEW.phase_run_id END;
 ELSE o=CASE WHEN TG_OP='DELETE' THEN OLD.operation_id ELSE NEW.operation_id END;SELECT phase_run_id INTO STRICT p FROM kcml_effect_v1.operation WHERE id=o;END IF;
 PERFORM 1 FROM kcml_effect_v1.phase_run WHERE id=p FOR UPDATE;
 IF EXISTS(SELECT 1 FROM kcml_effect_v1.phase_seal WHERE phase_run_id=p)THEN RAISE EXCEPTION 'EFFECT_PHASE_SEALED' USING ERRCODE='23514';END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER producer_gate BEFORE INSERT OR UPDATE OR DELETE ON kcml_effect_v1.operation FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.producer_gate();
CREATE TRIGGER producer_gate BEFORE INSERT OR UPDATE OR DELETE ON kcml_effect_v1.attempt FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.producer_gate();
CREATE TRIGGER producer_gate BEFORE INSERT OR UPDATE OR DELETE ON kcml_effect_v1.state FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.producer_gate();
CREATE TRIGGER producer_gate BEFORE INSERT OR UPDATE OR DELETE ON kcml_effect_v1.evidence FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.producer_gate();
CREATE FUNCTION kcml_effect_v1.seal_phase(p_phase uuid) RETURNS bytea LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE ph kcml_retry_v1.phase;result bytea;
BEGIN
 SELECT * INTO STRICT ph FROM kcml_retry_v1.phase WHERE phase_run_id=p_phase;
 PERFORM 1 FROM public.generation_job WHERE id=ph.job_id FOR UPDATE;
 SELECT * INTO STRICT ph FROM kcml_retry_v1.phase WHERE phase_run_id=p_phase FOR UPDATE;
 SELECT exact_bytes INTO result FROM kcml_effect_v1.phase_seal WHERE phase_run_id=p_phase;
 IF FOUND THEN RETURN result;END IF;
 IF EXISTS(SELECT 1 FROM kcml_effect_v1.operation o LEFT JOIN kcml_effect_v1.state s ON s.operation_id=o.id AND s.sequence=o.current_sequence WHERE o.phase_run_id=p_phase AND(s.operation_id IS NULL OR s.state NOT IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL')))
 OR EXISTS(SELECT id FROM kcml_effect_v1.operation WHERE phase_run_id=p_phase EXCEPT SELECT operation_id FROM kcml_retry_v1.operation WHERE phase_run_id=p_phase)
 OR EXISTS(SELECT operation_id FROM kcml_retry_v1.operation WHERE phase_run_id=p_phase EXCEPT SELECT id FROM kcml_effect_v1.operation WHERE phase_run_id=p_phase)
 THEN RAISE EXCEPTION 'EFFECT_PHASE_PRODUCER_INCOMPLETE' USING ERRCODE='23514';END IF;
 result=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('phaseRunId',p_phase,'jobId',ph.job_id,'phaseDigest','sha256:'||encode(ph.source_digest,'hex'),'operations',coalesce((SELECT jsonb_agg(jsonb_build_object('operationId',o.id,'requestDigest','sha256:'||encode(o.request_digest,'hex'),'currentAttemptSequence',o.current_sequence::text,'state',o.state,'attempts',(SELECT jsonb_agg(to_jsonb(a) ORDER BY a.sequence)FROM kcml_effect_v1.attempt a WHERE a.operation_id=o.id),'evidence',(SELECT jsonb_agg(jsonb_build_object('attemptSequence',e.sequence::text,'evidenceSequence',e.evidence_sequence::text,'contentDigest','sha256:'||encode(e.content_digest,'hex'))ORDER BY e.sequence,e.evidence_sequence)FROM kcml_effect_v1.evidence e WHERE e.operation_id=o.id))ORDER BY o.id)FROM kcml_effect_v1.operation o WHERE o.phase_run_id=p_phase),'[]'))),'UTF8');
 INSERT INTO kcml_effect_v1.phase_seal VALUES(p_phase,result,sha256(result));RETURN result;
END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA kcml_effect_v1 FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
CREATE FUNCTION kcml_effect_v1.state_guard() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF (NEW.operation_id,NEW.sequence,NEW.state_id)IS DISTINCT FROM(OLD.operation_id,OLD.sequence,OLD.state_id)THEN RAISE EXCEPTION 'EFFECT_STATE_IDENTITY_IMMUTABLE' USING ERRCODE='23514';END IF;
 IF NEW.state_version<>OLD.state_version+1 THEN RAISE EXCEPTION 'EFFECT_STATE_VERSION' USING ERRCODE='23514';END IF;
 IF OLD.state IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL')THEN RAISE EXCEPTION 'EFFECT_TERMINAL_STATE_IMMUTABLE' USING ERRCODE='23514';END IF;
 IF NEW.state<>OLD.state AND NOT((OLD.state='INTENT_RECORDED' AND NEW.state IN('DISPATCHING','CONFIRMED_NOT_APPLIED')) OR(OLD.state='DISPATCHING' AND NEW.state IN('OUTCOME_RECORDED','RECONCILING'))OR(OLD.state='OUTCOME_RECORDED' AND NEW.state IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL','RECONCILING'))OR(OLD.state='RECONCILING' AND NEW.state IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL','UNKNOWN'))OR(OLD.state='UNKNOWN' AND NEW.state IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL')))THEN RAISE EXCEPTION 'EFFECT_STATE_EDGE_DENIED' USING ERRCODE='23514';END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_state_identity BEFORE UPDATE ON kcml_effect_v1.state FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.state_guard();
CREATE FUNCTION kcml_effect_v1.phase_frozen_guard() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$BEGIN
 IF EXISTS(SELECT 1 FROM kcml_effect_v1.phase_seal WHERE phase_run_id=OLD.phase_run_id)THEN RAISE EXCEPTION 'EFFECT_PHASE_SEALED' USING ERRCODE='23514';END IF;RETURN NEW;END $$;
CREATE TRIGGER full_producer_phase_frozen BEFORE UPDATE OR DELETE ON kcml_retry_v1.phase FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.phase_frozen_guard();
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
CREATE FUNCTION kcml_effect_v1.begin_phase(p_id uuid,p_parent uuid,p_plan bytea,p_spec_digest bytea) RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE g public.generation_job;v jsonb;
BEGIN
 SELECT * INTO STRICT g FROM public.generation_job WHERE id=p_parent FOR UPDATE;
 v=convert_from(p_plan,'UTF8')::jsonb;
 IF v->>'jobId'IS DISTINCT FROM p_parent::text OR v->>'planId'IS DISTINCT FROM g.current_plan_id::text OR p_spec_digest IS DISTINCT FROM g.approved_specification_digest OR g.active_phase_run_id IS DISTINCT FROM p_id OR EXISTS(SELECT 1 FROM kcml_retry_v1.phase WHERE phase_run_id=p_id)THEN RAISE EXCEPTION 'EFFECT_PHASE_PRODUCER_LINEAGE' USING ERRCODE='23514';END IF;
 INSERT INTO kcml_effect_v1.phase_run VALUES(p_id,p_parent,'RUNNING',p_plan,sha256(p_plan),p_spec_digest,NULL,NULL,g.coordinator_fencing_token,g.platform_incarnation_id,g.application_deployment_epoch);
END $$;
CREATE FUNCTION kcml_effect_v1.finish_failed_phase(p_id uuid,p_failed_source bytea) RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE ph kcml_effect_v1.phase_run;v jsonb;r jsonb;
BEGIN
 SELECT * INTO STRICT ph FROM kcml_effect_v1.phase_run WHERE id=p_id;
 PERFORM 1 FROM public.generation_job WHERE id=ph.parent_id FOR UPDATE;
 SELECT * INTO STRICT ph FROM kcml_effect_v1.phase_run WHERE id=p_id FOR UPDATE;
 v=convert_from(p_failed_source,'UTF8')::jsonb;
 IF ph.state='FAILED' THEN IF ph.failed_source_bytes IS DISTINCT FROM p_failed_source THEN RAISE EXCEPTION 'EFFECT_PHASE_RESULT_REPLAY_CONFLICT' USING ERRCODE='23514';END IF;RETURN;END IF;
 IF v->>'phaseRunId'IS DISTINCT FROM ph.id::text OR v->>'jobId'IS DISTINCT FROM ph.parent_id::text OR v->>'state'IS DISTINCT FROM 'FAILED' OR v->>'planDigest'IS DISTINCT FROM 'sha256:'||encode(ph.plan_digest,'hex') OR v->>'specificationDigest'IS DISTINCT FROM 'sha256:'||encode(ph.specification_digest,'hex') OR EXISTS(SELECT 1 FROM kcml_effect_v1.operation WHERE phase_run_id=p_id AND state NOT IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL')) THEN RAISE EXCEPTION 'EFFECT_PHASE_TERMINAL_SOURCE_INCOMPLETE' USING ERRCODE='23514';END IF;
 SELECT convert_from(exact_bytes,'UTF8')::jsonb INTO r FROM public.generation_frozen_bundle_v1 WHERE bundle_digest=decode(substr(v->>'resultDigest',8),'hex') AND bundle_kind='DOMAIN_POLICY' LIMIT 1;
 IF NOT FOUND OR r->>'jobId'IS DISTINCT FROM ph.parent_id::text OR r->>'phaseRunId'IS DISTINCT FROM ph.id::text OR r->>'outcome'IS DISTINCT FROM 'KNOWN_FAILURE' OR r->'failedNodeIds'IS DISTINCT FROM v->'failedNodeIds' OR jsonb_typeof(r->'errorCodes')IS DISTINCT FROM 'array' OR jsonb_array_length(r->'errorCodes')=0 THEN RAISE EXCEPTION 'EFFECT_PHASE_FAILURE_RESULT_UNAVAILABLE' USING ERRCODE='23514';END IF;
 INSERT INTO kcml_retry_v1.phase VALUES(ph.id,ph.parent_id,p_failed_source,sha256(p_failed_source));
 UPDATE kcml_effect_v1.phase_run SET state='FAILED',failed_source_bytes=p_failed_source,failed_source_digest=sha256(p_failed_source) WHERE id=ph.id;
END $$;
CREATE FUNCTION kcml_effect_v1.execution_phase_frozen() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$BEGIN
 IF OLD.state='FAILED' OR (NEW.id,NEW.parent_id,NEW.plan_bytes,NEW.plan_digest,NEW.specification_digest,NEW.start_fence,NEW.start_incarnation,NEW.start_epoch)IS DISTINCT FROM(OLD.id,OLD.parent_id,OLD.plan_bytes,OLD.plan_digest,OLD.specification_digest,OLD.start_fence,OLD.start_incarnation,OLD.start_epoch)THEN RAISE EXCEPTION 'EFFECT_PHASE_IMMUTABLE' USING ERRCODE='23514';END IF;RETURN NEW;END $$;
CREATE TRIGGER execution_phase_immutable BEFORE UPDATE ON kcml_effect_v1.phase_run FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.execution_phase_frozen();
REVOKE ALL ON ALL TABLES IN SCHEMA kcml_effect_v1 FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
CREATE FUNCTION kcml_effect_v1.strict_observation(p_bytes bytea) RETURNS jsonb LANGUAGE plpgsql IMMUTABLE SET search_path=pg_catalog AS $$
DECLARE v json;
BEGIN
 BEGIN v=convert_from(p_bytes,'UTF8')::json;
 EXCEPTION WHEN invalid_text_representation OR character_not_in_repertoire THEN RAISE EXCEPTION 'EFFECT_OBSERVATION_ENCODING_INVALID' USING ERRCODE='23514';END;
 IF json_typeof(v)IS DISTINCT FROM 'object'THEN RAISE EXCEPTION 'EFFECT_OBSERVATION_MASK_INVALID' USING ERRCODE='23514';END IF;
 IF (SELECT count(*)<>count(DISTINCT key) FROM json_each(v))THEN RAISE EXCEPTION 'EFFECT_OBSERVATION_DUPLICATE_KEY' USING ERRCODE='23514';END IF;
 RETURN v::jsonb;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
-- Concrete decision producer: source fencing change, not caller-failed flags.
CREATE FUNCTION kcml_effect_v1.produce_fenced_failure(p_phase uuid,p_source_template bytea) RETURNS bytea LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE ph kcml_effect_v1.phase_run;g public.generation_job;t jsonb;nodes jsonb;result bytea;source bytea;code bytea;
BEGIN
 SELECT * INTO STRICT ph FROM kcml_effect_v1.phase_run WHERE id=p_phase;
 SELECT * INTO STRICT g FROM public.generation_job WHERE id=ph.parent_id FOR UPDATE;
 SELECT * INTO STRICT ph FROM kcml_effect_v1.phase_run WHERE id=p_phase FOR UPDATE;
 IF ph.state='FAILED' THEN RETURN ph.failed_source_bytes;END IF;
 IF ph.start_fence>=g.coordinator_fencing_token THEN RAISE EXCEPTION 'EFFECT_FENCED_FAILURE_NOT_OBSERVED' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM kcml_effect_v1.operation WHERE phase_run_id=p_phase AND state NOT IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL'))THEN RAISE EXCEPTION 'EFFECT_PHASE_TERMINAL_SOURCE_INCOMPLETE' USING ERRCODE='23514';END IF;
 SELECT jsonb_agg(step_key ORDER BY step_key) INTO nodes FROM kcml_effect_v1.operation WHERE phase_run_id=p_phase;
 IF nodes IS NULL THEN RAISE EXCEPTION 'EFFECT_FAILED_NODE_SOURCE_UNAVAILABLE' USING ERRCODE='23514';END IF;
 t=convert_from(p_source_template,'UTF8')::jsonb;
 IF jsonb_typeof(t)IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(t))<>14 OR NOT t ?& ARRAY['phaseRunId','jobId','phase','attempt','state','resultDigest','failedNodeIds','planId','planDigest','authorityId','authorityDigest','specificationDigest','pendingSideEffectIds','completedAt'] THEN RAISE EXCEPTION 'EFFECT_FAILED_SOURCE_TEMPLATE_MASK' USING ERRCODE='23514';END IF;
 IF t->>'jobId'IS DISTINCT FROM ph.parent_id::text OR t->>'phaseRunId'IS DISTINCT FROM ph.id::text OR t->>'planDigest'IS DISTINCT FROM 'sha256:'||encode(ph.plan_digest,'hex') OR t->>'specificationDigest'IS DISTINCT FROM 'sha256:'||encode(ph.specification_digest,'hex')
 OR NOT EXISTS(SELECT 1 FROM public.generation_frozen_bundle_v1 WHERE bundle_kind='DOMAIN_POLICY' AND bundle_id=t->>'authorityId' AND bundle_digest=decode(substr(t->>'authorityDigest',8),'hex') AND convert_from(exact_bytes,'UTF8')::jsonb->>'specificationDigest'=t->>'specificationDigest' AND convert_from(exact_bytes,'UTF8')::jsonb->>'sourceJobId'=ph.parent_id::text)
 THEN RAISE EXCEPTION 'EFFECT_FAILED_SOURCE_AUTHORITY_UNAVAILABLE' USING ERRCODE='23514';END IF;
 result=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('jobId',ph.parent_id,'phaseRunId',ph.id,'failedNodeIds',nodes,'outcome','KNOWN_FAILURE','errorCodes',jsonb_build_array('FENCING_TOKEN_STALE'))),'UTF8');
 code=convert_to(pg_get_functiondef('kcml_effect_v1.produce_fenced_failure(uuid,bytea)'::regprocedure),'UTF8');
 PERFORM public.kcml_archive_publish_v1('DOMAIN_POLICY','known-technical-failure:'||ph.id::text,sha256(result),result,'server-compiled:produce_fenced_failure',sha256(code));
 t=t||jsonb_build_object('state','FAILED','resultDigest','sha256:'||encode(sha256(result),'hex'),'failedNodeIds',nodes,'pendingSideEffectIds','[]'::jsonb,'completedAt',to_char(clock_timestamp()AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'));
 source=convert_to(public.kcml_crypto_compact_sorted_json_v1(t),'UTF8');PERFORM kcml_effect_v1.finish_failed_phase(p_phase,source);RETURN source;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
