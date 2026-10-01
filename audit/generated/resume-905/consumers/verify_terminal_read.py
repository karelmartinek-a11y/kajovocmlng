import sys,copy,json,hashlib
from pathlib import Path
HERE=Path(__file__).parent;ROOT=HERE.parents[3]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'audit/generated/resume-d362/consumers')]
from owner_ui_native_contracts import OPS,validate_outcome,outcome_digest,canonical_digest,worker_request_schema
from owner_ui_terminal_read import read_terminal,digest,ContractFailure
ID='11111111-1111-4111-8111-111111111111';OTHER='22222222-2222-4222-8222-222222222222';THIRD='33333333-3333-4333-8333-333333333333';D='sha256:'+'a'*64
cases=[]
def event(r):return {'eventType':'OPERATION_TERMINAL','operationId':r['operationId'],'logicalOperationId':r['logicalOperationId'],'intentId':r['intentId'],'immutableEventId':THIRD,'sequence':'2','occurredAt':'2026-10-01T12:00:00Z','payloadDigest':canonical_digest(r),'payload':copy.deepcopy(r)}
def fixture(action):
 output={'dashboard.start':{'outcome':'RUNTIME_READY','runtimeInstanceId':ID,'runtimeGeneration':'2','readinessReceiptId':OTHER,'launchSnapshotDigest':D},'dashboard.stop':{'outcome':'RUNTIME_CLEANUP_COMPLETE','runtimeInstanceId':ID,'runtimeGeneration':'2','cleanupOperationId':THIRD,'cleanupReceiptId':OTHER,'cleanupState':'COMPLETE'},'gen.editSpec':{'outcome':'NEW_DRAFT','jobId':ID,'revisionId':OTHER,'state':'DRAFT','specificationDigest':D,'diffArtifactId':THIRD,'requirementCoverageArtifactId':ID}}[action]
 args={'runtimeInstanceId':ID,'expectedRuntimeGeneration':'2'} if action!='gen.editSpec' else {'jobId':ID,'expectedRevisionId':THIRD,'expectedSpecificationDigest':D}
 intent={'intentId':OTHER,'logicalOperationId':ID,'workerContextId':THIRD,'workerCommandId':OTHER,'workerOperationId':OPS[action][1],'targetSnapshotDigest':D,'arguments':args,'workerArguments':{'operationId':OPS[action][1],'workerContextId':THIRD,'intentId':OTHER,'parentLogicalOperationId':ID,'targetSnapshotDigest':D,'launchSnapshotDigest':D}}
 wa=intent['workerArguments'];wa['schemaVersion']='OWNER_INTENT_WORKER_REQUEST/1'
 if action!='gen.editSpec':
  wa.update(runtimeInstanceId=ID,runtimeGeneration='2')
  if action=='dashboard.stop':wa.pop('launchSnapshotDigest');wa['cleanupOperationId']=THIRD
 else:
  wa.pop('launchSnapshotDigest');wa.update(jobId=ID,ownerInputId=ID,baseRevisionId=THIRD,baseSpecificationDigest=D)
 r={'operationId':OPS[action][0],'logicalOperationId':ID,'intentId':OTHER,'status':'SUCCEEDED','terminal':True,'output':output,'error':None,'resultDigest':D,'idempotencyReplay':False};r['resultDigest']=outcome_digest(r)
 raw=json.dumps(output,separators=(',',':')).encode()
 worker={'commandId':OTHER,'workerContextId':THIRD,'parentLogicalOperationId':ID,'intentId':OTHER,'workerOperationId':OPS[action][1],'targetSnapshotDigest':D,'resultBytes':raw,'contentDigest':digest(raw)}
 kinds={'dashboard.start':[('readinessReceiptId','RUNTIME_READINESS')],'dashboard.stop':[('cleanupReceiptId','RUNTIME_CLEANUP_COMPLETE')],'gen.editSpec':[('revisionId','GENERATION_SPECIFICATION_REVISION'),('diffArtifactId','GENERATION_SPECIFICATION_DIFF'),('requirementCoverageArtifactId','GENERATION_REQUIREMENT_COVERAGE')]}[action]
 artifacts={output[k]:{'id':output[k],'kind':kind,'workerCommandId':OTHER,'workerContextId':THIRD,'bytes':b'{"fixture":"synthetic-not-domain-receipt"}','contentDigest':digest(b'{"fixture":"synthetic-not-domain-receipt"}')} for k,kind in kinds}
 return [r,event(r),intent,worker,artifacts]
def run(a,f):
 r,ev,i,w,arts=f
 return read_terminal(a,r,ev,i,lambda kind,identifier: w if kind=='worker_command_result' else arts.get(identifier),validate_outcome,worker_request_schema(a))
def neg(name,code,a,f):
 try:run(a,f)
 except ContractFailure as e:
  assert e.code==code,(name,e.code,code);cases.append({'id':name,'status':'PASS','diagnostic':e.code});return
 raise AssertionError(name+' accepted')
for action in OPS:
 f=fixture(action);assert run(action,f)['effectSemanticHydration']=='REQUIRED_NOT_PROVED_BY_THIS_ADAPTER';assert run(action,f)['display']=='BLOCKED_PENDING_EFFECT_HYDRATION';cases.append({'id':action+'/bounded-positive','status':'PASS'})
 for field in ['commandId','workerContextId','parentLogicalOperationId','intentId','workerOperationId','targetSnapshotDigest']:
  bad=copy.deepcopy(f);bad[3][field]='wrong';neg(action+'/'+field,'OWNER_UI_WORKER_COMMAND_BINDING_MISMATCH',action,bad)
 bad=copy.deepcopy(f);bad[3]['resultBytes']+=b' ';neg(action+'/actual-result-bytes','OWNER_UI_WORKER_RESULT_DIGEST_MISMATCH',action,bad)
 bad=copy.deepcopy(f);bad[4].clear();neg(action+'/missing-actual-artifact','OWNER_UI_EFFECT_ARTIFACT_UNAVAILABLE',action,bad)
 bad=copy.deepcopy(f);next(iter(bad[4].values()))['workerContextId']=OTHER;neg(action+'/wrong-artifact-context','OWNER_UI_EFFECT_ARTIFACT_BINDING_MISMATCH',action,bad)
 bad=copy.deepcopy(f);next(iter(bad[4].values()))['bytes']+=b' ';neg(action+'/artifact-byte-corruption','OWNER_UI_EFFECT_ARTIFACT_DIGEST_MISMATCH',action,bad)
 if action in ['dashboard.start','dashboard.stop']:
  for field,value in [('runtimeInstanceId',THIRD),('runtimeGeneration','3')]:
   bad=copy.deepcopy(f);bad[2]['workerArguments'][field]=value
   neg(action+'/wrong-worker-argument-'+field,'OWNER_UI_WORKER_ARGUMENT_BINDING_MISMATCH',action,bad)
 # Prior native validator accepted self-consistent wrong-target success; replay
 # receipt/event/result digests must all be valid to isolate this exact defect.
 bad=copy.deepcopy(f);out=bad[0]['output'];out['jobId' if action=='gen.editSpec' else 'runtimeInstanceId']=THIRD
 bad[0]['resultDigest']=outcome_digest(bad[0]);bad[1]=event(bad[0]);raw=json.dumps(out,separators=(',',':')).encode();bad[3].update(resultBytes=raw,contentDigest=digest(raw))
 retained={'workerOperationId':bad[3]['workerOperationId'],'parentLogicalOperationId':ID,'intentId':OTHER,'bytes':raw,'contentDigest':digest(raw)}
 assert validate_outcome(action,bad[0],bad[1],retained_worker_receipt=retained)=='DISPLAY_CANONICAL_OUTCOME'
 neg(action+'/reproduced-old-wrong-target','OWNER_UI_WORKER_TARGET_MISMATCH',action,bad)
report={'pinnedCommit':'905555e47f3547516439a699e262df62cbbec229','sourceSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'checks':len(cases),'failed':0,'cases':cases,'scope':'Pure retained worker-command/context/target and actual artifact byte adapter. No trusted producer, PostgreSQL atomicity, effect semantic hydration, readiness/cleanup or public catalog activation proved.','wholeExposuresClosed':0,'implementationAcceptance':'NOT_EVALUATED','supportingFiles':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in [HERE/'owner_ui_terminal_read.py',HERE/'verify_terminal_read.py',ROOT/'audit/generated/resume-d362/consumers/owner_ui_native_contracts.py',ROOT/'audit/generated/resume-d362/consumers/ui_facade_pipeline_reference.py']}}
(HERE/'terminal-read-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'PASS')
