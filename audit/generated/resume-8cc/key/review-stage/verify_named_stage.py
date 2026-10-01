"""Independent actual-byte stage reproduction; no PG scan-completeness assertion."""
from pathlib import Path
import sys,json,hashlib,copy,importlib.util
HERE=Path(__file__).parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(1,str(ROOT/'audit/generated/resume-d362/admission'))
from generation_retry_inventory_fixtures import fixture,ids,INVENTORY,ib,CLASSIFIER_ID,OBS_SCHEMA,OBS_RECEIPT
from generation_admission_contracts import canonical,digest,source_json,ContractFailure
import generation_locked_retry as current
from generation_locked_retry import hydrate_locked_scan_for_admission,hydrate_locked_scan as execution
spec=importlib.util.spec_from_file_location('author_candidate',ROOT/'audit/generated/resume-8cc/native/generation_locked_retry_admission.py');author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author)
checks=[]
def put(repo,key,v):
 rec=repo.records[key];rec['bytes']=canonical(v);rec['contentDigest']=digest(rec['bytes']);return rec['contentDigest']
FAIL_SOURCE=b'''def classify(observation, operation, attempt):
    if observation['requestDigest'] != operation['requestDigest'] or observation['targetIdempotencyKey'] != operation['targetIdempotencyKey']:
        return 'UNKNOWN'
    if observation['failureCode'] == 'SYNTHETIC_FINAL_REJECT' and observation['appliedOperationId'] is None and observation['beforeVersion'] == observation['afterVersion'] and observation['beforeValueDigest'] == observation['afterValueDigest']:
        return 'FAILED_FINAL'
    return 'UNKNOWN'
'''
def witness(state):
 f=list(fixture());repo,phase,rd,plan,ind,physical,classifiers=f
 evidence=source_json(repo.records[ids(523)]['bytes'])
 if state=='CONFIRMED_APPLIED':evidence['observations'].update(afterVersion='8',appliedOperationId=ids(520))
 if state=='FAILED_FINAL':
  schema=source_json(repo.records[OBS_SCHEMA]['bytes']);schema['required'].append('failureCode');schema['properties']['failureCode']={'enum':['SYNTHETIC_FINAL_REJECT']};schema_digest=put(repo,OBS_SCHEMA,schema)
  pub=source_json(repo.records[OBS_RECEIPT]['bytes']);pub['contentDigest']=schema_digest;put(repo,OBS_RECEIPT,pub)
  evidence['observationSchema']['bundle']['contentDigest']=schema_digest;evidence['observationSchema']['bundle']['sizeBytes']=len(repo.records[OBS_SCHEMA]['bytes']);evidence['observationSchema']['nativeSchemaDigest']=schema_digest
  evidence['observations']['failureCode']='SYNTHETIC_FINAL_REJECT';repo.records[CLASSIFIER_ID]['bytes']=FAIL_SOURCE;repo.records[CLASSIFIER_ID]['contentDigest']=digest(FAIL_SOURCE);evidence['classifierDigest']=digest(FAIL_SOURCE)
  ns={};exec(compile(FAIL_SOURCE,'independent-declared-synthetic-final-receipt-classifier','exec'),ns);classifiers[evidence['classifierId']]={'sourceRecordId':CLASSIFIER_ID,'activeSourceDigest':digest(FAIL_SOURCE),'evaluate':ns['classify']}
 evidence['outcome']=state;ed=put(repo,ids(523),evidence)
 projection=source_json(repo.records[ids(522)]['bytes']);projection.update(state=state,evidenceDigest=ed);put(repo,ids(522),projection)
 operation=source_json(repo.records[ids(520)]['bytes']);operation['state']=state;put(repo,ids(520),operation)
 scan={'phaseBytes':canonical(phase).hex(),'phaseDigest':rd[7:],'rows':[{}]}
 for prefix,key in [('operation',ids(520)),('attempt',ids(521)),('state',ids(522)),('evidence',ids(523))]:
  rec=repo.records[key];scan['rows'][0].update({prefix+'Id':key,prefix+'Bytes':rec['bytes'].hex(),prefix+'Digest':rec['contentDigest'][7:]})
 return repo,scan,plan,classifiers

def run(name,state,fn,expected=None,decision=None,mutate=None):
 repo,scan,plan,classifiers=witness(state)
 if mutate:mutate(repo,scan,classifiers)
 try:
  r=fn(repo,scan,INVENTORY,'2026-10-01T00:00:00.000Z',ib,plan,classifiers);diag=None
  ok=expected is None and r['contentDecision']['permitsExternalDispatch']is False and (decision is None or r['contentDecision']['selectedTechnicalPartEffectDecisions'][0]['decision']==decision)
 except ContractFailure as e:diag=e.code;ok=diag==expected
 except Exception as e:diag=type(e).__name__+':'+str(e);ok=False
 checks.append({'case':name,'passed':ok,'expectedDiagnostic':expected,'actualDiagnostic':diag})
for state,decision,error in [('CONFIRMED_APPLIED','PRESERVE_CONFIRMED_EFFECT_NO_REPEAT','GENERATION_RETRY_CONFIRMED_EFFECT_REPEAT_FORBIDDEN'),('FAILED_FINAL','PRESERVE_FINAL_FAILURE_NO_AUTOMATIC_DISPATCH','GENERATION_RETRY_FINAL_EFFECT_POLICY_UNRESOLVED')]:
 run('original-default-'+state,state,current.hydrate_locked_scan,error)
 run('candidate-explicit-discussion-'+state,state,lambda *args:author.hydrate_locked_scan(*args,stage='ADMISSION_DISCUSSION'),decision=decision)
 run('integrated-discussion-'+state,state,hydrate_locked_scan_for_admission,decision=decision)
 run('integrated-execution-'+state,state,execution,error)
run('not-applied-discussion','CONFIRMED_NOT_APPLIED',hydrate_locked_scan_for_admission,decision='REUSE_KNOWN_NOT_APPLIED_OPERATION_AND_TARGET_KEY')
run('not-applied-execution-still-no-dispatch-authority','CONFIRMED_NOT_APPLIED',execution,decision='REUSE_KNOWN_NOT_APPLIED_OPERATION_AND_TARGET_KEY')
run('classifier-digest-mutation','FAILED_FINAL',hydrate_locked_scan_for_admission,'GENERATION_RETRY_OUTCOME_CLASSIFIER_DIGEST_MISMATCH',mutate=lambda repo,scan,classifiers:repo.records[CLASSIFIER_ID].update(bytes=FAIL_SOURCE+b'\n'))
run('actual-scan-byte-mutation','CONFIRMED_APPLIED',hydrate_locked_scan_for_admission,'GENERATION_RETRY_SCAN_MEMBER_BYTES_MISMATCH',mutate=lambda repo,scan,classifiers:scan['rows'][0].update(evidenceBytes=scan['rows'][0]['evidenceBytes']+'20'))
report={'status':'PASS'if all(c['passed']for c in checks)else'BLOCKED','checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'sourceDocumentSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'authority':'SSOT §12.51.2 paragraph hydrate_locked_scan server-selected ADMISSION_DISCUSSION; §12.51 creates DISCUSSING, §49.8 execution requirements retained','recommendation':'Integrated named admission entry point preserves original hydrate_locked_scan execution API; caller HTTP/model never selects stage. Mandatory keyword-stage author candidate retains the same discussion/execution semantics.','integrationStatus':'ACTUAL_ROOT_MODULE_REPRODUCED','classificationScope':'Actual declared synthetic readback/final-reject observations and classifier source bytes. No systemd, PostgreSQL phase lock/completeness or every production classifier proof.','wholeOperationClosed':False,'classifierSha256':digest(FAIL_SOURCE),'supportSha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),HERE/'generation_locked_retry_named.py',ROOT/'scripts/generation_locked_retry.py',ROOT/'scripts/generation_retry_inventory.py',ROOT/'audit/generated/resume-8cc/native/generation_locked_retry_admission.py']}}
(HERE/'integrated-stage-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}))
