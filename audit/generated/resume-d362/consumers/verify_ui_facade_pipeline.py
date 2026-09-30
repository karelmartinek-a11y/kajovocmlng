import copy,json,hashlib
from pathlib import Path
from ui_facade_pipeline_reference import *
from verify_phase2_handoffs import witness
OUT=Path(__file__).parent
ID='11111111-1111-4111-8111-111111111111';OTHER='22222222-2222-4222-8222-222222222222';CTX='33333333-3333-4333-8333-333333333333'
manifest={k:(ID if v.get('format')=='uuid' else 'sha256:'+'a'*64 if v.get('pattern')==DIGEST['pattern'] else '2' if v.get('pattern')==COUNTER['pattern'] else 'fixture') for k,v in launch_snapshot_schema()['properties'].items()}
manifest.update(componentId=ID,runtimeInstanceId=OTHER)
raw=json.dumps(manifest,separators=(',',':')).encode()
root={'componentId':ID,'runtimeInstanceId':OTHER,'expectedComponentStateVersion':'2','expectedRuntimeGeneration':'2','expectedActivationEpoch':'2','launchSnapshotBytes':raw,'launchSnapshotDigest':'sha256:'+hashlib.sha256(raw).hexdigest()}
checks=[]
def neg(name,code,fn):
 try:fn()
 except ContractFailure as e:
  assert e.code==code,(name,e.code,code);checks.append({'id':name,'diagnostic':code,'status':'PASS'});return
 raise AssertionError(name+' accepted')
def setup(action,body,rr):
 descriptor={'actionId':action,'targetId':body.get('componentId',body.get('jobId'))}
 return {'roots':{descriptor['targetId']:copy.deepcopy(rr)},'contexts':{CTX:{'id':CTX,'operationId':action,'requestDigest':request_digest(action,body),'descriptor':descriptor,'descriptorDigest':canonical_digest(descriptor)}},'locators':{},'commands':{},'events':[],'outbox':[],'audit':[]}
def call(db,a,b,crash=None):return admit(db,a,b,locator='same',command_id=ID,logical_id=OTHER,context_id=CTX,crash=crash)
for action,direction in [('dashboard.start','START'),('dashboard.stop','STOP')]:
 body={'schemaVersion':'RUNTIME_OWNER_INTENT/1','action':direction,'componentId':ID,'expectedComponentStateVersion':'2','runtimeInstanceId':OTHER,'expectedRuntimeGeneration':'2','expectedActivationEpoch':'2'}
 db=setup(action,body,root);receipt=call(db,action,body);assert receipt['status']=='ACCEPTED' and not receipt['runtimeReady'];assert read_receipt(db,OTHER)==receipt;checks.append({'id':action+'/atomic-positive','status':'PASS'})
 before=copy.deepcopy(db);assert call(db,action,body)==receipt and db==before;checks.append({'id':action+'/replay-no-extra-publication','status':'PASS'})
 bad={**body,'expectedComponentStateVersion':'3'};neg(action+'/replay-conflict','IDEMPOTENCY_CONFLICT',lambda:call(db,action,bad))
 db=setup(action,body,root);before=copy.deepcopy(db);neg(action+'/rollback','OWNER_FACADE_REFERENCE_ROLLBACK',lambda:call(db,action,body,'BEFORE_COMMIT'));assert db==before
 for field in ['expectedComponentStateVersion','expectedRuntimeGeneration','expectedActivationEpoch']:
  db=setup(action,body,root);db['roots'][ID][field]='3';neg(action+'/'+field,'STATE_VERSION_CONFLICT',lambda:call(db,action,body))
 db=setup(action,body,root);db['roots'][ID]['launchSnapshotBytes']+=b' ';neg(action+'/actual-byte-digest','OWNER_FACADE_LAUNCH_SNAPSHOT_DIGEST_MISMATCH',lambda:call(db,action,body))
 db=setup(action,body,root);invalid=b'{"componentId":"bad"}';db['roots'][ID].update(launchSnapshotBytes=invalid,launchSnapshotDigest='sha256:'+hashlib.sha256(invalid).hexdigest());neg(action+'/digest-valid-invalid-manifest','OWNER_FACADE_LAUNCH_SNAPSHOT_INVALID',lambda:call(db,action,body))
 db=setup(action,body,root);changed=copy.deepcopy(manifest);changed['componentId']=OTHER;encoded=json.dumps(changed,separators=(',',':')).encode();db['roots'][ID].update(launchSnapshotBytes=encoded,launchSnapshotDigest='sha256:'+hashlib.sha256(encoded).hexdigest());neg(action+'/digest-valid-wrong-manifest-identity','OWNER_FACADE_MANIFEST_TARGET_MISMATCH',lambda:call(db,action,body))
 db=setup(action,body,root);duplicate=b'{"componentId":"x","componentId":"y"}';db['roots'][ID].update(launchSnapshotBytes=duplicate,launchSnapshotDigest='sha256:'+hashlib.sha256(duplicate).hexdigest());neg(action+'/duplicate-json-actual-decoder','DUPLICATE_JSON_KEY',lambda:call(db,action,body))
 db=setup(action,body,root);call(db,action,body);db['outbox'][0]['intentDigest']='sha256:'+'0'*64;neg(action+'/outbox-link','OWNER_FACADE_OUTBOX_INTENT_MISMATCH',lambda:read_receipt(db,OTHER))
 db=setup(action,body,root);call(db,action,body);db['audit'].clear();neg(action+'/missing-audit','OWNER_FACADE_ATOMIC_LINK_INCOMPLETE',lambda:read_receipt(db,OTHER))
 db=setup(action,body,root);bad={**body,'executionContext':'AUTOMATED_MAINTENANCE'};neg(action+'/forged-worker-context','OWNER_FACADE_INPUT_INVALID',lambda:call(db,action,bad))
# Complete native specification domain witness, with actual typed JSON hydration.
bundle=json.loads(resource_index()['contracts/generation/generation-contracts.schema.json']['raw']);defs=copy.deepcopy(bundle['$defs'])
for k,v in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-30T12:00:00Z','RelPath':'fixture.json','JsonPointer':'','NonemptyJsonPointer':'/fixture'}.items():defs[k]={'const':v}
spec=witness(defs['GenerationSpecification'],defs);spec['jobId']=ID
validate_schema({**bundle,'$ref':'#/$defs/GenerationSpecification'},spec,'FIXTURE_INVALID')
raw=json.dumps(spec,ensure_ascii=False,separators=(',',':')).encode();rr={'jobId':ID,'revisionId':OTHER,'stateVersion':'2','specificationBytes':raw,'specificationDigest':canonical_digest(spec)}
body={'schemaVersion':'SPECIFICATION_OWNER_INPUT/1','variant':'OWNER_TEXT','jobId':ID,'expectedStateVersion':'2','expectedRevisionId':OTHER,'expectedSpecificationDigest':canonical_digest(spec),'text':'Synthetic OWNER edit; preserve exact spaces  '}
db=setup('gen.editSpec',body,rr);receipt=call(db,'gen.editSpec',body);assert receipt['createdRevisionId'] is None and receipt['status']=='ACCEPTED';assert db['commands'][OTHER]['intent']['arguments']['text']==body['text'];checks.append({'id':'edit/pending-owner-input-not-server-proposal','status':'PASS'})
body2={k:v for k,v in body.items() if k!='text'};body2.update(variant='SPECIFICATION_CANDIDATE',candidate=copy.deepcopy(spec));db=setup('gen.editSpec',body2,rr);receipt=call(db,'gen.editSpec',body2);assert receipt['decision']=='NO_DUPLICATE_REVISION';checks.append({'id':'edit/same-canonical-no-new-revision','status':'PASS'})
wrong=copy.deepcopy(body2);wrong['candidate']['jobId']=OTHER;db=setup('gen.editSpec',wrong,rr);neg('edit/wrong-candidate-job','OWNER_FACADE_CANDIDATE_JOB_MISMATCH',lambda:call(db,'gen.editSpec',wrong))
db=setup('gen.editSpec',body,rr);db['roots'][ID]['specificationBytes']=b'{}';neg('edit/invalid-real-specification','OWNER_FACADE_BASE_SPECIFICATION_INVALID',lambda:call(db,'gen.editSpec',body))
report={'inputCommit':'d362487999bd795d4723c2a930e93fc7aa8aa295','scope':'Staged OWNERintent atomic reference, exact launch/spec bytes and CAS, receipt/event/outbox/audit links; worker execution and actual authentication not proved','checks':len(checks),'failed':0,'cases':checks,'exposureClosed':0,'implementationProductionAcceptance':'NOT_EVALUATED','sourceDocumentSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'consumedGenerationSchemaDigest':canonical_digest(bundle),'supportingFiles':{f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in ['ui_facade_pipeline_reference.py','verify_ui_facade_pipeline.py','generation_consumer_reference.py']}}
(OUT/'ui-facade-pipeline-tests.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'ui-facade-native-inputs.proposed.json').write_text(json.dumps({'inputSchemas':schemas(),'launchSnapshotSchema':launch_snapshot_schema(),'activationStatus':'REVIEW_ONLY_NOT_NORMATIVE'},indent=2)+'\n');print(len(checks),'PASS')
