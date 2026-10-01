DO $$DECLARE c text;BEGIN SELECT conname INTO STRICT c FROM pg_constraint WHERE conrelid='kcml_effect_v1.checkpoint'::regclass AND confrelid='kcml_effect_v1.attempt'::regclass AND contype='f';EXECUTE format('ALTER TABLE kcml_effect_v1.checkpoint ALTER CONSTRAINT %I DEFERRABLE INITIALLY DEFERRED',c);SELECT conname INTO STRICT c FROM pg_constraint WHERE conrelid='kcml_effect_v1.state'::regclass AND confrelid='kcml_effect_v1.attempt'::regclass AND contype='f';EXECUTE format('ALTER TABLE kcml_effect_v1.state ALTER CONSTRAINT %I DEFERRABLE INITIALLY DEFERRED',c);END $$;
CREATE FUNCTION kcml_effect_v1.compile_prepared_checkpoint(o kcml_effect_v1.operation,a kcml_effect_v1.attempt) RETURNS bytea LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE g public.generation_job;c kcml_effect_v1.checkpoint_context;n bigint;v jsonb;pending jsonb;completed jsonb;watermark bigint;bytes bytea;
BEGIN
 SELECT * INTO STRICT g FROM public.generation_job WHERE id=o.parent_id;
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
 SELECT coalesce(jsonb_agg(jsonb_build_object('operationId',x.id,'attemptSequence',x.current_sequence::text,'state',x.state)ORDER BY x.id),'[]') INTO pending FROM (SELECT * FROM kcml_effect_v1.operation WHERE parent_id=g.id AND id<>o.id UNION ALL SELECT o.*) x WHERE x.parent_id=g.id AND x.state NOT IN('CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL');
 SELECT coalesce(jsonb_agg(x.step_key ORDER BY x.step_key),'[]') INTO completed FROM (SELECT * FROM kcml_effect_v1.operation WHERE parent_id=g.id AND id<>o.id UNION ALL SELECT o.*) x WHERE x.parent_id=g.id AND x.state='CONFIRMED_APPLIED';
 SELECT coalesce(max(aggregate_sequence),0) INTO watermark FROM public.domain_event WHERE aggregate_id=g.id;
 RETURN convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('parentId',g.id,'stateVersion',g.state_version::text,'incarnation',a.incarnation,'fence',a.parent_fence::text,'sequence',n::text,'operationId',o.id,
 'state',g.state,'substate',g.current_phase,'approvedRevisionId',c.approved_revision_id,'specificationDigest','sha256:'||encode(c.specification_digest,'hex'),'planId',c.plan_id,'planDigest','sha256:'||encode(c.plan_digest,'hex'),'agentGraphRef',c.agent_graph_ref,
 'bindingSnapshotRef',c.binding_snapshot_ref,'activationEpoch',c.activation_epoch::text,'completedStepKeys',completed,'eventWatermark',watermark::text,'pendingSideEffects',pending,'providerHandles',c.provider_handles,'eventCursors',c.event_cursors,
 'workspaceRefs',c.workspace_refs,'browserRefs',c.browser_refs,'budgetSnapshotRef',c.budget_snapshot_ref,'cancellationVersion',g.cancellation_version::text,'deadline',to_char(a.deadline AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'))),'UTF8');
END $$;
CREATE FUNCTION kcml_effect_v1.write_prepared_checkpoint(o kcml_effect_v1.operation,a kcml_effect_v1.attempt,p_id uuid,p_phase text,p_raw bytea) RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE g public.generation_job;n bigint;expected bytea;item record;
BEGIN
 SELECT * INTO STRICT g FROM public.generation_job WHERE id=o.parent_id;
 SELECT last_sequence+1 INTO STRICT n FROM kcml_effect_v1.checkpoint_head WHERE parent_id=g.id;
 expected=kcml_effect_v1.compile_prepared_checkpoint(o,a);
 IF p_raw IS NOT NULL AND p_raw IS DISTINCT FROM expected THEN RAISE EXCEPTION 'EFFECT_CHECKPOINT_FULL_MASK' USING ERRCODE='23514';END IF;
 FOR item IN SELECT * FROM (VALUES(o.phase_run_id,'PHASE'),(p_id,'CHECKPOINT'))v(id,kind)ORDER BY id LOOP
 IF item.kind='PHASE' THEN
  PERFORM 1 FROM kcml_effect_v1.phase_run WHERE id=o.phase_run_id AND parent_id=g.id FOR UPDATE;
 ELSE
  INSERT INTO kcml_effect_v1.checkpoint(id,parent_id,sequence,parent_state_version,parent_fence,incarnation,epoch,operation_id,attempt_sequence,phase,exact_bytes,content_digest)
  VALUES(p_id,g.id,n,g.state_version,a.parent_fence,a.incarnation,a.epoch,o.id,a.sequence,p_phase,expected,sha256(expected));
 END IF;END LOOP;
 UPDATE kcml_effect_v1.checkpoint_head SET last_sequence=n,latest_id=p_id WHERE parent_id=g.id;
END $$;
CREATE OR REPLACE FUNCTION kcml_effect_v1.record_intent(
 p_op uuid,p_phase uuid,p_parent uuid,p_logical uuid,p_step text,p_attempt uuid,p_outbox uuid,p_event uuid,p_checkpoint uuid,
 p_request bytea,p_binding uuid,p_revision uuid,p_target_key text,p_fence bigint,p_cancel bigint,p_deadline timestamptz,
 p_concurrency_key bytea,p_concurrency_owner uuid,p_concurrency_fence bigint,p_classifier_digest bytea,p_checkpoint_bytes bytea)
RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE g public.generation_job;prior kcml_effect_v1.operation;payload bytea;o kcml_effect_v1.operation;a kcml_effect_v1.attempt;c kcml_effect_v1.concurrency_claim;sid uuid=gen_random_uuid();
BEGIN
 SELECT * INTO STRICT g FROM public.generation_job WHERE id=p_parent FOR UPDATE;
 PERFORM 1 FROM kcml_effect_v1.phase_run WHERE id=p_phase AND parent_id=p_parent;
 IF NOT FOUND THEN RAISE EXCEPTION 'EFFECT_PHASE_PARENT_IDENTITY' USING ERRCODE='23514';END IF;
 IF NOT EXISTS(SELECT 1 FROM kcml_effect_v1.phase_run WHERE id=p_phase AND state='RUNNING') OR g.active_phase_run_id IS DISTINCT FROM p_phase THEN RAISE EXCEPTION 'EFFECT_PHASE_NOT_EXECUTING' USING ERRCODE='23514';END IF;
 SELECT * INTO prior FROM kcml_effect_v1.operation WHERE id=p_op;
 IF FOUND THEN
  IF (prior.phase_run_id,prior.parent_id,prior.logical_operation_id,prior.step_key,prior.request_bytes,prior.target_binding_id,prior.target_revision_id,prior.target_key,prior.classifier_digest)
  IS DISTINCT FROM(p_phase,p_parent,p_logical,p_step,p_request,p_binding,p_revision,p_target_key,p_classifier_digest) THEN RAISE EXCEPTION 'EFFECT_INTENT_REPLAY_CONFLICT' USING ERRCODE='23514';END IF;
  RETURN;
 END IF;
 IF p_cancel IS DISTINCT FROM g.cancellation_version THEN RAISE EXCEPTION 'EFFECT_FENCE_INVALID' USING ERRCODE='23514';END IF;
 SELECT * INTO c FROM kcml_effect_v1.concurrency_claim WHERE key_digest=p_concurrency_key FOR UPDATE;
 IF p_fence IS DISTINCT FROM g.coordinator_fencing_token OR p_cancel IS DISTINCT FROM g.cancellation_version OR g.coordinator_lease_owner_id IS NULL OR g.coordinator_lease_expires_at<=clock_timestamp() OR p_deadline<=clock_timestamp() OR g.state IN('CANCELLED','COMPLETED','FAILED') OR c.owner_id IS DISTINCT FROM p_concurrency_owner OR c.fence IS DISTINCT FROM p_concurrency_fence OR c.expires_at<=clock_timestamp() OR NOT EXISTS(SELECT 1 FROM public.platform_incarnation WHERE platform_incarnation_id=g.platform_incarnation_id) OR NOT EXISTS(SELECT 1 FROM public.application_deployment_head WHERE platform_incarnation_id=g.platform_incarnation_id AND application_deployment_epoch=g.application_deployment_epoch) THEN RAISE EXCEPTION 'EFFECT_FENCE_INVALID' USING ERRCODE='23514';END IF;
 INSERT INTO kcml_effect_v1.checkpoint_head VALUES(g.id,0,NULL)ON CONFLICT DO NOTHING;
 PERFORM 1 FROM kcml_effect_v1.checkpoint_head WHERE parent_id=g.id FOR UPDATE;
 o.id=p_op;o.phase_run_id=p_phase;o.parent_id=p_parent;o.logical_operation_id=p_logical;o.step_key=p_step;o.request_bytes=p_request;o.request_digest=sha256(p_request);o.target_binding_id=p_binding;o.target_revision_id=p_revision;o.target_key=p_target_key;o.current_sequence=1;o.state='INTENT_RECORDED';o.classifier_id='CAS_READ_BACK_V1';o.classifier_digest=p_classifier_digest;
 a.operation_id=p_op;a.sequence=1;a.id=p_attempt;a.dispatch_outbox_id=p_outbox;a.parent_fence=p_fence;a.incarnation=g.platform_incarnation_id;a.epoch=g.application_deployment_epoch;a.cancellation_version=p_cancel;a.deadline=p_deadline;a.concurrency_key_digest=p_concurrency_key;a.concurrency_owner=p_concurrency_owner;a.concurrency_fence=p_concurrency_fence;
 PERFORM kcml_effect_v1.write_prepared_checkpoint(o,a,p_checkpoint,'PRE',p_checkpoint_bytes);
 INSERT INTO kcml_effect_v1.operation VALUES(p_op,p_phase,p_parent,p_logical,p_step,p_request,sha256(p_request),p_binding,p_revision,p_target_key,1,'INTENT_RECORDED','CAS_READ_BACK_V1',p_classifier_digest);
 IF sid<p_attempt THEN
 INSERT INTO kcml_effect_v1.state(operation_id,sequence,state,state_version,last_evidence_sequence,state_id)VALUES(p_op,1,'INTENT_RECORDED',1,0,sid);
 END IF;
 INSERT INTO kcml_effect_v1.attempt VALUES(p_op,1,p_attempt,p_outbox,p_fence,g.platform_incarnation_id,g.application_deployment_epoch,p_cancel,p_deadline,p_concurrency_key,p_concurrency_owner,p_concurrency_fence);
 IF sid>=p_attempt THEN
 INSERT INTO kcml_effect_v1.state(operation_id,sequence,state,state_version,last_evidence_sequence,state_id)VALUES(p_op,1,'INTENT_RECORDED',1,0,sid);
 END IF;
 payload=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('operationId',p_op,'attemptId',p_attempt,'requestDigest','sha256:'||encode(sha256(p_request),'hex'),'targetBindingId',p_binding,'targetRevisionId',p_revision)),'UTF8');
 INSERT INTO public.domain_event VALUES(p_event,p_op,'SIDE_EFFECT',p_logical,1,'side.effect.intent.recorded','urn:kcml:side-effect-intent:1',sha256(kcml_effect_v1.event_mask('INTENT')),payload,sha256(payload),p_logical,NULL,clock_timestamp());
 INSERT INTO public.transactional_outbox(id,event_id,logical_operation_id,aggregate_id,purpose,consumer_scope,available_at,state,payload_digest,is_dispatch_authority,side_effect_operation_id,side_effect_attempt_sequence,target_idempotency_key,immutable_request_digest,concurrency_key_digest)
 VALUES(p_outbox,p_event,p_logical,p_op,'SIDE_EFFECT_DISPATCH','generation-effect-dispatch',clock_timestamp(),'READY',sha256(payload),true,p_op,1,p_target_key,sha256(p_request),p_concurrency_key);
END $$;
CREATE OR REPLACE FUNCTION kcml_effect_v1.confirm_cas_v1(p_op uuid,p_sequence bigint,p_checkpoint uuid,p_checkpoint_bytes bytea,p_event uuid,p_outbox uuid) RETURNS text LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE o kcml_effect_v1.operation;s kcml_effect_v1.state;e kcml_effect_v1.evidence;outcome text;code bytea;payload bytea;a kcml_effect_v1.attempt;projected kcml_effect_v1.operation;
BEGIN
 PERFORM kcml_effect_v1.fence_guard(p_op,p_sequence);
 SELECT * INTO STRICT s FROM kcml_effect_v1.state WHERE operation_id=p_op AND sequence=p_sequence;
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
 SELECT * INTO STRICT a FROM kcml_effect_v1.attempt WHERE operation_id=p_op AND sequence=p_sequence;
 INSERT INTO kcml_effect_v1.checkpoint_head VALUES(o.parent_id,0,NULL)ON CONFLICT DO NOTHING;
 PERFORM 1 FROM kcml_effect_v1.checkpoint_head WHERE parent_id=o.parent_id FOR UPDATE;
 projected=o;projected.state=outcome;
 PERFORM kcml_effect_v1.write_prepared_checkpoint(projected,a,p_checkpoint,'POST',p_checkpoint_bytes);
 PERFORM 1 FROM kcml_effect_v1.operation WHERE id=p_op FOR UPDATE;
 PERFORM 1 FROM kcml_effect_v1.state WHERE operation_id=p_op AND sequence=p_sequence FOR UPDATE;
 IF s.state='DISPATCHING' THEN
 UPDATE kcml_effect_v1.state SET state='OUTCOME_RECORDED',state_version=state_version+1 WHERE operation_id=p_op AND sequence=p_sequence;
 UPDATE kcml_effect_v1.operation SET state='OUTCOME_RECORDED' WHERE id=p_op;END IF;
 UPDATE kcml_effect_v1.state SET state=outcome,state_version=state_version+1,outcome_digest=e.content_digest WHERE operation_id=p_op AND sequence=p_sequence;
 UPDATE kcml_effect_v1.operation SET state=outcome WHERE id=p_op;
 SELECT exact_bytes INTO p_checkpoint_bytes FROM kcml_effect_v1.checkpoint WHERE id=p_checkpoint;
 payload=convert_to(public.kcml_crypto_compact_sorted_json_v1(jsonb_build_object('operationId',o.id,'attemptSequence',p_sequence::text,'outcome',outcome,'evidenceDigest','sha256:'||encode(e.content_digest,'hex'),'checkpointId',p_checkpoint,'checkpointDigest','sha256:'||encode(sha256(p_checkpoint_bytes),'hex'))),'UTF8');
 INSERT INTO public.domain_event VALUES(p_event,o.id,'SIDE_EFFECT',o.logical_operation_id,2,'side.effect.outcome.recorded','urn:kcml:side-effect-outcome:1',sha256(kcml_effect_v1.event_mask('OUTCOME')),payload,sha256(payload),o.logical_operation_id,NULL,clock_timestamp());
 INSERT INTO public.transactional_outbox(id,event_id,logical_operation_id,aggregate_id,purpose,consumer_scope,available_at,state,payload_digest) VALUES(p_outbox,p_event,o.logical_operation_id,o.id,'SIDE_EFFECT_CONTINUATION','generation-effect-continuation',clock_timestamp(),'READY',sha256(payload));
 RETURN outcome;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;

-- This migration allocates explicit stable child kinds. Parent identity derives
-- from the existing canonical generation_job FK; ownership is never inferred
-- from relation names or aggregate labels.
ALTER TABLE kcml_effect_v1.phase_run ADD COLUMN primary_parent_uuid uuid GENERATED ALWAYS AS(parent_id) STORED NOT NULL;
ALTER TABLE kcml_effect_v1.operation ADD COLUMN primary_parent_uuid uuid GENERATED ALWAYS AS(parent_id) STORED NOT NULL;
ALTER TABLE kcml_effect_v1.checkpoint ADD COLUMN primary_parent_uuid uuid GENERATED ALWAYS AS(parent_id) STORED NOT NULL;
ALTER TABLE kcml_effect_v1.checkpoint_head ADD COLUMN primary_parent_uuid uuid GENERATED ALWAYS AS(parent_id) STORED NOT NULL;
ALTER TABLE kcml_effect_v1.attempt ADD COLUMN primary_parent_uuid uuid NOT NULL REFERENCES public.generation_job(id);
ALTER TABLE kcml_effect_v1.state ADD COLUMN primary_parent_uuid uuid NOT NULL REFERENCES public.generation_job(id);
ALTER TABLE kcml_effect_v1.evidence ADD COLUMN primary_parent_uuid uuid NOT NULL REFERENCES public.generation_job(id);
CREATE FUNCTION kcml_effect_v1.derive_primary_parent() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$DECLARE p uuid;BEGIN
 SELECT parent_id INTO STRICT p FROM kcml_effect_v1.operation WHERE id=NEW.operation_id;
 IF NEW.primary_parent_uuid IS NOT NULL AND NEW.primary_parent_uuid IS DISTINCT FROM p THEN RAISE EXCEPTION 'EFFECT_PRIMARY_PARENT_CONFLICT' USING ERRCODE='23514';END IF;
 NEW.primary_parent_uuid=p;RETURN NEW;END $$;
CREATE TRIGGER a_primary_parent BEFORE INSERT ON kcml_effect_v1.attempt FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.derive_primary_parent();
CREATE TRIGGER a_primary_parent BEFORE INSERT ON kcml_effect_v1.state FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.derive_primary_parent();
CREATE TRIGGER a_primary_parent BEFORE INSERT ON kcml_effect_v1.evidence FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.derive_primary_parent();
CREATE FUNCTION kcml_effect_v1.primary_parent_immutable() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN IF NEW.primary_parent_uuid IS DISTINCT FROM OLD.primary_parent_uuid THEN RAISE EXCEPTION 'EFFECT_PRIMARY_PARENT_IMMUTABLE' USING ERRCODE='23514';END IF;RETURN NEW;END $$;
CREATE TRIGGER primary_parent_immutable BEFORE UPDATE ON kcml_effect_v1.state FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.primary_parent_immutable();
CREATE TRIGGER primary_parent_immutable BEFORE UPDATE ON kcml_effect_v1.checkpoint_head FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.primary_parent_immutable();
-- Explicit new kind SIDE_EFFECT_EVENT_IMMUTABLE ordinal160. The shared event
-- table remains universal; exact one-to-one immutable subtype gives this kind
-- a NOT NULL physical parent column without guessing other event ownership.
CREATE TABLE kcml_effect_v1.event_identity(event_id uuid PRIMARY KEY REFERENCES public.domain_event(id) DEFERRABLE INITIALLY DEFERRED,primary_parent_uuid uuid NOT NULL REFERENCES public.generation_job(id),operation_id uuid NOT NULL REFERENCES kcml_effect_v1.operation(id));
CREATE TRIGGER event_identity_immutable BEFORE UPDATE OR DELETE ON kcml_effect_v1.event_identity FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.immutable();
CREATE FUNCTION kcml_effect_v1.side_effect_event_parent() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $$DECLARE p uuid;BEGIN
 IF NEW.aggregate_kind='SIDE_EFFECT' THEN SELECT parent_id INTO STRICT p FROM kcml_effect_v1.operation WHERE id=NEW.aggregate_id;INSERT INTO kcml_effect_v1.event_identity VALUES(NEW.id,p,NEW.aggregate_id);END IF;RETURN NEW;END $$;
CREATE TRIGGER side_effect_event_parent BEFORE INSERT ON public.domain_event FOR EACH ROW EXECUTE FUNCTION kcml_effect_v1.side_effect_event_parent();
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
-- PostgreSQL computes stored generated columns after BEFORE triggers: ignore
-- only that redundant computed field, while original parent_id stays immutable.
CREATE OR REPLACE FUNCTION kcml_effect_v1.operation_immutable_scope() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN
 IF TG_OP='DELETE' OR (to_jsonb(NEW)-ARRAY['state','current_sequence','primary_parent_uuid'])IS DISTINCT FROM(to_jsonb(OLD)-ARRAY['state','current_sequence','primary_parent_uuid']) THEN RAISE EXCEPTION 'EFFECT_IMMUTABLE_OPERATION_SCOPE' USING ERRCODE='55000';END IF;RETURN NEW;END $$;
CREATE OR REPLACE FUNCTION kcml_effect_v1.primary_parent_immutable() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN
 IF TG_TABLE_NAME='checkpoint_head' THEN IF NEW.parent_id IS DISTINCT FROM OLD.parent_id THEN RAISE EXCEPTION 'EFFECT_PRIMARY_PARENT_IMMUTABLE' USING ERRCODE='23514';END IF;
 ELSE IF NEW.primary_parent_uuid IS DISTINCT FROM OLD.primary_parent_uuid THEN RAISE EXCEPTION 'EFFECT_PRIMARY_PARENT_IMMUTABLE' USING ERRCODE='23514';END IF;END IF;RETURN NEW;END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;

CREATE OR REPLACE FUNCTION kcml_effect_v1.dispatch_guard(p_op uuid,p_sequence bigint) RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE s kcml_effect_v1.state;a kcml_effect_v1.attempt;
BEGIN
 PERFORM kcml_effect_v1.fence_guard(p_op,p_sequence);
 PERFORM 1 FROM kcml_effect_v1.operation WHERE id=p_op FOR UPDATE;
 SELECT * INTO STRICT s FROM kcml_effect_v1.state WHERE operation_id=p_op AND sequence=p_sequence FOR UPDATE;
 IF NOT EXISTS(SELECT 1 FROM kcml_effect_v1.operation o JOIN kcml_effect_v1.phase_run p ON p.id=o.phase_run_id JOIN public.generation_job g ON g.id=o.parent_id WHERE o.id=p_op AND g.active_phase_run_id=p.id AND p.state='RUNNING') THEN RAISE EXCEPTION 'EFFECT_PHASE_NOT_EXECUTING' USING ERRCODE='23514';END IF;
 IF s.state IS DISTINCT FROM 'INTENT_RECORDED' THEN RAISE EXCEPTION 'EFFECT_DISPATCH_STATE_INVALID' USING ERRCODE='23514';END IF;
 SELECT * INTO STRICT a FROM kcml_effect_v1.attempt WHERE operation_id=p_op AND sequence=p_sequence;
 UPDATE kcml_effect_v1.state SET state='DISPATCHING',state_version=state_version+1 WHERE operation_id=p_op AND sequence=p_sequence;
 UPDATE kcml_effect_v1.operation SET state='DISPATCHING' WHERE id=p_op;
 UPDATE public.transactional_outbox SET state='DISPATCH_AUTHORIZED',state_version=state_version+1 WHERE id=a.dispatch_outbox_id;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kcml_effect_v1 FROM PUBLIC;
