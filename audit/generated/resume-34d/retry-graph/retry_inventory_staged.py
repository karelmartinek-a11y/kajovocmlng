"""Exact RETRY source phase side-effect ledger content validator, reference only.

physical_rows is a trusted table scan, not client JSON. Complete PostgreSQL scan,
FK and locking proofs remain required; no 'complete/valid' boolean is accepted.
"""
from generation_admission_contracts import *

def schemas():
 uid=UID;d=DIGEST;c={'$ref':GEN+'#/$defs/Counter'};pc={'$ref':GEN+'#/$defs/PositiveCounter'}
 state={'$ref':GEN+'#/$defs/SourceEnum154'}
 link={'operationId':uid,'operationDigest':d,'attemptId':uid,'attemptDigest':d,'attemptStateId':uid,'attemptStateDigest':d}
 inventory=closed({'inventoryId':uid,'jobId':uid,'phaseRunId':uid,'phaseRunDigest':d,'capturedAt':{'$ref':GEN+'#/$defs/Timestamp'},'operations':{'type':'array','items':closed(link)}})
 operation=closed({'operationId':uid,'jobId':uid,'phaseRunId':uid,'nodeId':{'$ref':GEN+'#/$defs/Id'},'currentAttemptId':uid,'currentAttemptSequence':pc,'currentAttemptStateId':uid,'currentAttemptStateVersion':pc,'state':state,'requestDigest':d,
 'retryClass':{'$ref':GEN+'#/$defs/RetryClass'},'sideEffectClass':{'$ref':GEN+'#/$defs/SideEffectClass'},'targetBindingId':uid,'targetBindingRevisionId':uid,'targetIdempotencyKey':{'type':'string','minLength':1}})
 attempt=closed({'attemptId':uid,'operationId':uid,'jobId':uid,'phaseRunId':uid,'attemptSequence':pc,'requestDigest':d,'targetBindingId':uid,'targetBindingRevisionId':uid,'targetIdempotencyKey':{'type':'string','minLength':1}})
 projection=closed({'attemptStateId':uid,'operationId':uid,'attemptId':uid,'attemptSequence':pc,'state':state,'stateVersion':pc,'evidenceId':{'anyOf':[uid,{'type':'null'}]},'evidenceDigest':{'anyOf':[d,{'type':'null'}]}})
 evidence=closed({'evidenceId':uid,'operationId':uid,'attemptId':uid,'jobId':uid,'phaseRunId':uid,'requestDigest':d,'targetBindingId':uid,'targetBindingRevisionId':uid,'targetIdempotencyKey':{'type':'string','minLength':1},
 'outcome':{'enum':['CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL','UNKNOWN']},'recordedAt':{'$ref':GEN+'#/$defs/Timestamp'},'classifierId':{'$ref':GEN+'#/$defs/Id'},'classifierDigest':d,'observationSchema':{'$ref':GEN+'#/$defs/SchemaArtifact'},'observations':{'$ref':GEN+'#/$defs/JsonValue'}})
 return {'PhaseSideEffectInventory':inventory,'SourceSideEffectOperation':operation,'SourceSideEffectAttempt':attempt,'SourceSideEffectAttemptState':projection,'SourceSideEffectOutcomeEvidence':evidence}

INVENTORY_SCHEMA_ID='urn:kcml:generation-retry-inventory:1'

def bundle():return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':INVENTORY_SCHEMA_ID,'$defs':schemas()}

def verify_retry_inventory(repo,run,run_digest,plan,inventory_id,inventory_digest,physical_rows,outcome_verifiers,stage='EXECUTION_DISPATCH'):
 if stage not in ['ADMISSION_DISCUSSION','EXECUTION_DISPATCH']:fail('GENERATION_RETRY_STAGE_INVALID')
 if inventory_id not in repo.records:fail('GENERATION_RETRY_INVENTORY_UNAVAILABLE')
 if not isinstance(physical_rows,dict):fail('GENERATION_RETRY_PHYSICAL_SCAN_UNVERIFIED')
 if not isinstance(outcome_verifiers,dict):fail('GENERATION_RETRY_OUTCOME_CLASSIFIER_UNRESOLVED')
 inventory,_=repo.hydrate(inventory_id,inventory_digest,'PhaseSideEffectInventory',run['jobId'])
 if (inventory['inventoryId'],inventory['phaseRunId'],inventory['phaseRunDigest'])!=(inventory_id,run['phaseRunId'],run_digest):fail('GENERATION_RETRY_INVENTORY_PHASE_MISMATCH')
 entries=inventory['operations'];ids=[e['operationId'] for e in entries]
 if len(ids)!=len(set(ids)):fail('GENERATION_RETRY_INVENTORY_DUPLICATE_OPERATION')
 # Every actual scanned row is parsed from its current persisted bytes. Do not
 # filter solely on unverified metadata or believe an inventory rowCount flag.
 scanned={}
 for operation_id,digest_hint in physical_rows.items():
  op,_=repo.hydrate(operation_id,digest_hint,'SourceSideEffectOperation')
  if op['operationId']!=operation_id:fail('GENERATION_RETRY_OPERATION_IDENTITY_MISMATCH')
  if op['phaseRunId']==run['phaseRunId']:
   if op['jobId']!=run['jobId']:fail('GENERATION_RETRY_OPERATION_PRODUCER_FK_MISMATCH')
   scanned[operation_id]=(op,digest_hint)
 if set(ids)!=set(scanned):fail('GENERATION_RETRY_INVENTORY_INCOMPLETE')
 nodes={n['nodeId']:n for n in plan['nodes']};failed=set(run['failedNodeIds']);decisions=[]
 for item in entries:
  op,op_digest=scanned[item['operationId']]
  if item['operationDigest']!=op_digest:fail('GENERATION_RETRY_OPERATION_SNAPSHOT_DRIFT')
  if op['nodeId'] not in nodes:fail('GENERATION_RETRY_OPERATION_NODE_UNRESOLVED')
  if (op['retryClass'],op['sideEffectClass'])!=(nodes[op['nodeId']]['retryClass'],nodes[op['nodeId']]['sideEffectClass']):fail('GENERATION_RETRY_OPERATION_POLICY_DRIFT')
  attempt,_=repo.hydrate(item['attemptId'],item['attemptDigest'],'SourceSideEffectAttempt',run['jobId'])
  current,_=repo.hydrate(item['attemptStateId'],item['attemptStateDigest'],'SourceSideEffectAttemptState')
  if (op['currentAttemptId'],op['currentAttemptSequence'])!=(item['attemptId'],attempt['attemptSequence']):fail('GENERATION_RETRY_CURRENT_ATTEMPT_DRIFT')
  # These fields are the server's locked operation/current-state JOIN snapshot,
  # not an inventory-selected historical state pointer or new operation columns.
  if (op['currentAttemptStateId'],op['currentAttemptStateVersion'])!=(current['attemptStateId'],current['stateVersion']):fail('GENERATION_RETRY_CURRENT_ATTEMPT_STATE_DRIFT')
  if (attempt['attemptId'],attempt['operationId'],attempt['phaseRunId'],current['attemptStateId'],current['operationId'],current['attemptId'],current['attemptSequence'],current['state'])!=(item['attemptId'],op['operationId'],run['phaseRunId'],item['attemptStateId'],op['operationId'],item['attemptId'],attempt['attemptSequence'],op['state']):fail('GENERATION_RETRY_ATTEMPT_STATE_DRIFT')
  if (attempt['requestDigest'],attempt['targetBindingId'],attempt['targetBindingRevisionId'],attempt['targetIdempotencyKey'])!=(op['requestDigest'],op['targetBindingId'],op['targetBindingRevisionId'],op['targetIdempotencyKey']):fail('GENERATION_RETRY_ATTEMPT_BINDING_DRIFT')
  if op['state'] in ['INTENT_RECORDED','DISPATCHING','OUTCOME_RECORDED','RECONCILING','UNKNOWN']:fail('GENERATION_RETRY_EFFECT_RECONCILIATION_REQUIRED')
  if current['evidenceId'] is None or current['evidenceDigest'] is None:fail('GENERATION_RETRY_EFFECT_EVIDENCE_UNAVAILABLE')
  evidence,_=repo.hydrate(current['evidenceId'],current['evidenceDigest'],'SourceSideEffectOutcomeEvidence',run['jobId'])
  if (evidence['evidenceId'],evidence['operationId'],evidence['attemptId'],evidence['phaseRunId'],evidence['requestDigest'],evidence['targetBindingId'],evidence['targetBindingRevisionId'],evidence['targetIdempotencyKey'],evidence['outcome'])!=(current['evidenceId'],op['operationId'],attempt['attemptId'],run['phaseRunId'],op['requestDigest'],op['targetBindingId'],op['targetBindingRevisionId'],op['targetIdempotencyKey'],op['state']):fail('GENERATION_RETRY_OUTCOME_EVIDENCE_DRIFT')
  # Observed domain receipt/read-back is parsed under its exact frozen schema.
  observations=repo.observation(evidence)
  implementation=outcome_verifiers.get(evidence['classifierId'])
  if implementation is None:fail('GENERATION_RETRY_OUTCOME_CLASSIFIER_UNRESOLVED')
  if not isinstance(implementation,dict) or set(implementation)!= {'sourceRecordId','activeSourceDigest','evaluate'}:fail('GENERATION_RETRY_OUTCOME_CLASSIFIER_DECLARATION_INVALID')
  source_record=repo.records.get(implementation['sourceRecordId'])
  if source_record is None or not isinstance(source_record.get('bytes'),bytes):fail('GENERATION_RETRY_OUTCOME_CLASSIFIER_BYTES_UNAVAILABLE')
  raw=source_record['bytes']
  if source_record.get('contentDigest')!=digest(raw) or digest(raw)!=evidence['classifierDigest'] or digest(raw)!=implementation.get('activeSourceDigest'):fail('GENERATION_RETRY_OUTCOME_CLASSIFIER_DIGEST_MISMATCH')
  # Production binds a compiled server consumer from its declared source
  # registry. No dynamic OWNER/model code execution path is introduced here.
  function=implementation.get('evaluate')
  if not callable(function):fail('GENERATION_RETRY_OUTCOME_CLASSIFIER_IMPLEMENTATION_INVALID')
  repo.consulted[implementation['sourceRecordId']]=source_record
  try:
   actual=function(observations,op,attempt)
  except Exception:
   # Execution failure is unavailable policy evidence, never a domain rejection
   # or successful negative proof; sensitive exception text is not exposed.
   fail('GENERATION_RETRY_OUTCOME_CLASSIFIER_EXECUTION_FAILED')
  if actual not in ['CONFIRMED_APPLIED','CONFIRMED_NOT_APPLIED','FAILED_FINAL','UNKNOWN'] or actual!=evidence['outcome']:fail('GENERATION_RETRY_OUTCOME_CLASSIFIER_MISMATCH')
  if op['nodeId'] in failed:
   if op['state']=='CONFIRMED_APPLIED':
    if stage=='EXECUTION_DISPATCH':fail('GENERATION_RETRY_CONFIRMED_EFFECT_REPEAT_FORBIDDEN')
    decisions.append({'operationId':op['operationId'],'decision':'PRESERVE_CONFIRMED_EFFECT_NO_REPEAT','sourceAttemptId':attempt['attemptId']});continue
   if op['state']=='FAILED_FINAL':
    if stage=='EXECUTION_DISPATCH':fail('GENERATION_RETRY_FINAL_EFFECT_POLICY_UNRESOLVED')
    decisions.append({'operationId':op['operationId'],'decision':'PRESERVE_FINAL_FAILURE_NO_AUTOMATIC_DISPATCH','sourceAttemptId':attempt['attemptId']});continue
   if op['retryClass']=='NO_AUTOMATIC_RETRY':
    if stage=='EXECUTION_DISPATCH':fail('GENERATION_RETRY_MANUAL_DISPATCH_POLICY_UNRESOLVED')
    decisions.append({'operationId':op['operationId'],'decision':'ADMIT_DISCUSSION_WITH_NO_AUTOMATIC_RETRY','sourceAttemptId':attempt['attemptId']});continue
   decisions.append({'operationId':op['operationId'],'decision':'REUSE_KNOWN_NOT_APPLIED_OPERATION_AND_TARGET_KEY','sourceAttemptId':attempt['attemptId']})
  else:decisions.append({'operationId':op['operationId'],'decision':'DO_NOT_REPEAT_UNSELECTED_PART'})
 return {'stage':stage,'permitsExternalDispatch':False,'decision':'SOURCE_PHASE_EFFECT_INVENTORY_CONTENT_VALIDATED','operationCount':len(entries),'selectedTechnicalPartEffectDecisions':decisions,
 'pendingSideEffectListIsNotAuthority':True,'postgresqlCompletenessProof':'REQUIRED_LOCKED_PHASE_FK_TABLE_SCAN','runtimeAcceptance':'NOT_EVALUATED'}
