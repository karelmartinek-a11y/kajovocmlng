"""Server-only SQL scan hydration. Invoke while scan's DB transaction remains open.

Not an HTTP boundary: no client flag or model-supplied member list is authority.
The transaction adapter must call exact canonical SQL scanner and retain its lock
through child admission/frozen evidence persistence. This helper validates bytes.
"""
import copy
from generation_admission_contracts import canonical,digest,source_json,fail,validate,LOCAL_DEFINITIONS
from generation_retry_inventory import INVENTORY_SCHEMA_ID,verify_retry_inventory

def _hydrate_locked_scan(repo,scan,inventory_id,captured_at,inventory_bundle_digest,plan,classifiers,*,stage):
 scan=copy.deepcopy(scan)
 if set(scan)!={'phaseBytes','phaseDigest','rows'}:fail('GENERATION_RETRY_SCAN_DECODER_INVALID')
 raw=bytes.fromhex(scan['phaseBytes']);rd='sha256:'+scan['phaseDigest']
 if digest(raw)!=rd:fail('GENERATION_RETRY_SCAN_PHASE_BYTES_MISMATCH')
 phase=source_json(raw);validate(LOCAL_DEFINITIONS['FailedTechnicalPhaseRun'],phase,repo.registry,'GENERATION_RETRY_SCAN_PHASE_INVALID');physical={};entries=[]
 for row in scan['rows']:
  if set(row)!={'operationId','operationBytes','operationDigest','attemptId','attemptBytes','attemptDigest','stateId','stateBytes','stateDigest','evidenceId','evidenceBytes','evidenceDigest'}:fail('GENERATION_RETRY_SCAN_DECODER_INVALID')
  for prefix,definition in [('operation','SourceSideEffectOperation'),('attempt','SourceSideEffectAttempt'),('state','SourceSideEffectAttemptState'),('evidence','SourceSideEffectOutcomeEvidence')]:
   key=row[prefix+'Id']
   if key is None or row[prefix+'Bytes'] is None:fail('GENERATION_RETRY_EFFECT_EVIDENCE_UNAVAILABLE')
   raw=bytes.fromhex(row[prefix+'Bytes']);dg='sha256:'+row[prefix+'Digest']
   if digest(raw)!=dg:fail('GENERATION_RETRY_SCAN_MEMBER_BYTES_MISMATCH')
   repo.records[key]={'recordId':key,'jobId':phase['jobId'],'owner':repo.owner,'bytes':raw,'contentDigest':dg,
    'schema':{'schemaId':INVENTORY_SCHEMA_ID,'bundleDigest':inventory_bundle_digest,'definition':definition}}
  if row['operationId'] in physical:fail('GENERATION_RETRY_INVENTORY_DUPLICATE_OPERATION')
  physical[row['operationId']]='sha256:'+row['operationDigest']
  entries.append({'operationId':row['operationId'],'operationDigest':'sha256:'+row['operationDigest'],'attemptId':row['attemptId'],'attemptDigest':'sha256:'+row['attemptDigest'],'attemptStateId':row['stateId'],'attemptStateDigest':'sha256:'+row['stateDigest']})
 value={'inventoryId':inventory_id,'jobId':phase['jobId'],'phaseRunId':phase['phaseRunId'],'phaseRunDigest':rd,'capturedAt':captured_at,'operations':entries};raw=canonical(value);dg=digest(raw)
 repo.records[inventory_id]={'recordId':inventory_id,'jobId':phase['jobId'],'owner':repo.owner,'bytes':raw,'contentDigest':dg,'schema':{'schemaId':INVENTORY_SCHEMA_ID,'bundleDigest':inventory_bundle_digest,'definition':'PhaseSideEffectInventory'}}
 result=verify_retry_inventory(repo,phase,rd,plan,inventory_id,dg,physical,classifiers,stage=stage)
 return {'inventoryId':inventory_id,'inventoryDigest':dg,'inventoryBytes':raw,'contentDecision':result,'frozenConsumedRecords':copy.deepcopy(repo.consulted)}

def hydrate_locked_scan(repo,scan,inventory_id,captured_at,inventory_bundle_digest,plan,classifiers):
 """Preserved execution-validation API. Does not authorize external dispatch."""
 return _hydrate_locked_scan(repo,scan,inventory_id,captured_at,inventory_bundle_digest,plan,classifiers,stage='EXECUTION_DISPATCH')

def hydrate_locked_scan_for_admission(repo,scan,inventory_id,captured_at,inventory_bundle_digest,plan,classifiers):
 """Server-selected discussion admission; no caller stage or dispatch authority."""
 return _hydrate_locked_scan(repo,scan,inventory_id,captured_at,inventory_bundle_digest,plan,classifiers,stage='ADMISSION_DISCUSSION')
