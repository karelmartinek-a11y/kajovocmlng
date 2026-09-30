"""Actual domain witnesses and exact decoder/admission rejections; synthetic design proof."""
import base64,copy,hashlib,io,json,os,subprocess
from PIL import Image
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
from ssot_sources import ROOT,SSOT,resource_index
from create_operation_contracts import PATH,PAYLOAD,OPERATIONS,schema,specialize,decode_http,admit,ContractFailure,digest
from phase1_schema_closure import Inventory
UID='00000000-0000-4000-8000-000000000001'
UID2='00000000-0000-4000-8000-000000000002'
UID3='00000000-0000-4000-8000-000000000003'

def run():
 rs=resource_index();payload=json.loads(rs[PAYLOAD]['raw']);rows={r['operationId']:r for r in payload['records'] if r['operationId'] in OPERATIONS}
 inventory=Inventory(SSOT.read_text(encoding='utf8'))
 checks=[]
 def assert_case(name,fn,expected=True):
  try:actual=fn();checks.append({'case':name,'passed':actual==expected,'actual':actual,'expected':expected})
  except Exception as exc:checks.append({'case':name,'passed':False,'diagnostic':'UNEXPECTED_EXCEPTION','reason':str(exc)})
 def reject(name,fn,code,pointer=None):
  try:fn();checks.append({'case':name,'passed':False,'diagnostic':'ACCEPTED_INVALID'})
  except ContractFailure as exc:checks.append({'case':name,'passed':exc.code==code and (pointer is None or exc.pointer==pointer),'expectedCode':code,'actualCode':exc.code,'pointer':exc.pointer})
  except Exception as exc:checks.append({'case':name,'passed':False,'diagnostic':'UNRELATED_EXCEPTION','reason':str(exc)})
 headers=[('Content-Type','application/json'),('Idempotency-Key','create-fixture-key')]
 server={'owner':UID,'actor':'OWNER','authenticated':True,'recovery':'READY','targets':{UID2:{'objectId':UID2,'kind':'PLATFORM_COMPONENT'}},
  'jobs':{UID3:{'jobId':UID3}},'sourceOrigins':['https://example.test'],'openaiModels':['model-fixture'],'artifacts':{UID2:{'artifactId':UID2,'owner':UID,'immutable':True,'bytes':b'synthetic artifact bytes','contentSha256':hashlib.sha256(b'synthetic artifact bytes').hexdigest(),'mediaType':'text/plain'}},
  'stableNames':[],'valuePolicyTypes':['PASSWORD','API_KEY','GENERIC_TEXT','GENERIC_BINARY']}
 witnesses={'generation.job.create':{'intent':'Create a component that records an incoming message.', 'kind':'CREATE','targetKind':'PLATFORM_COMPONENT',
  'requestedModel':'model-fixture','sources':[{'kind':'TEXT','text':'Acknowledge the incoming message.'},{'kind':'FILE','artifactId':UID2},{'kind':'URL','url':'https://example.test/docs'}]},
  'secret.create':{'stableName':'FIXTURE_SECRET','displayName':'Fixture credential','type':'PASSWORD','value':{'encoding':'UTF8','text':'  Synthetic value\nbeze změny  '},'tags':['fixture'],'description':'Synthetic value only','expiration':'2026-12-31T00:00:00Z'}}
 def encode(body):return json.dumps(body,ensure_ascii=False).encode('utf8')
 def decode(oid,body=None,raw=None,query=None,hdrs=None):return decode_http(oid,'POST',rows[oid]['path'],query or [],headers if hdrs is None else hdrs,encode(body if body is not None else witnesses[oid]) if raw is None else raw)
 for oid,body in witnesses.items():
  prefix=oid+'/'
  native=decode(oid);assert_case(prefix+'positive-domain-decoder',lambda native=native,body=body:native['body']==body)
  assert_case(prefix+'positive-admission',lambda native=native:admit(native,server)['action']=='RESERVE_ATOMIC_CREATE')
  v=Draft202012Validator(rows[oid]['requestSchema'],registry=inventory.registry,format_checker=FormatChecker())
  envelope={'routeId':rows[oid]['routeId'],'operationId':oid,'pathParameters':{},'query':[],'body':body,
   'guards':{'idempotencyKey':'create-fixture-key','expectedStateVersion':None,'expectedRevisionId':None,'expectedReleaseId':None,
    'expectedBindingSetRevision':None,'expectedActivationEpoch':None,'deadlineAt':None,'clientRequestDigest':native['requestDigest']}}
  assert_case(prefix+'positive-route-native-body',lambda v=v,envelope=envelope:v.is_valid(envelope))
  for field in schema()['$defs'][OPERATIONS[oid]]['required']:
   bad=copy.deepcopy(body);del bad[field];reject(prefix+'missing/'+field,lambda bad=bad:decode(oid,bad),'SCHEMA_REQUIRED')
   bad=copy.deepcopy(body);bad[field]=None;reject(prefix+'null/'+field,lambda bad=bad:decode(oid,bad),'SCHEMA_TYPE' if field!='value' else 'SCHEMA_ONEOF')
  for field in schema()['$defs'][OPERATIONS[oid]]['properties']:
   if field in schema()['$defs'][OPERATIONS[oid]]['required']:continue
   # Discriminated FOLLOW_UP field is tested from its valid variant by the dedicated verifier.
   if field in ['followUpBasis','generationBasis']:continue
   bad=copy.deepcopy(body);bad[field]=None
   reject(prefix+'optional-null/'+field,lambda bad=bad:decode(oid,bad),'SCHEMA_TYPE')
  for field in ['schemaId','values','canonicalJson','authorityId','ownerId','jobId','secretId','state','stateVersion','contentDigest','fingerprint','encryptedValue','receipt']:
   reject(prefix+'extra-server-or-legacy/'+field,lambda field=field:decode(oid,{**body,field:'untrusted'}),'SCHEMA_ADDITIONALPROPERTIES')
  reject(prefix+'unknown-query',lambda:decode(oid,query=[('unknown','x')]),'UNKNOWN_QUERY_PARAMETER','/query')
  reject(prefix+'duplicate-http-header',lambda:decode(oid,hdrs=headers+[('IDEMPOTENCY-KEY','other')]),'DUPLICATE_HEADER','/headers/idempotency-key')
  reject(prefix+'missing-key',lambda:decode(oid,hdrs=headers[:1]),'IDEMPOTENCY_KEY_REQUIRED','/headers/idempotency-key')
  reject(prefix+'model-authority-header',lambda:decode(oid,hdrs=headers+[('X-Authority-Id',UID)]),'UNDECLARED_CREATE_GUARD_OR_AUTHORITY','/headers')
  reject(prefix+'bad-client-digest',lambda:decode(oid,hdrs=headers+[('X-KCML-Request-Digest','sha256:'+'0'*64)]),'CLIENT_DIGEST_MISMATCH','/headers/x-kcml-request-digest')
  encoded_positive=encode(body)
  first=next(iter(body));first_json=json.dumps(first).encode()
  duplicate_root=encoded_positive[:-1]+b', '+first_json+b': '+json.dumps(body[first],ensure_ascii=False).encode()+b'}'
  if oid=='secret.create':
   duplicate_nested=encoded_positive.replace(b'"encoding": "UTF8"',b'"encoding": "UTF8", "encoding": "UTF8"',1)
  else:duplicate_nested=encoded_positive.replace(b'"kind": "TEXT"',b'"kind": "TEXT", "kind": "TEXT"',1)
  nonfinite=encoded_positive.replace(json.dumps(body[first],ensure_ascii=False).encode(),b'NaN',1)
  invalid_utf8=encoded_positive.replace(json.dumps(body[first],ensure_ascii=False).encode(),b'"\xff"',1)
  for name,raw,code in [('malformed-json',encoded_positive[:-1],'INVALID_JSON'),('invalid-utf8',invalid_utf8,'INVALID_UTF8'),
    ('duplicate-root-key',duplicate_root,'DUPLICATE_JSON_KEY'),('duplicate-nested-key',duplicate_nested,'DUPLICATE_JSON_KEY'),
    ('nonfinite',nonfinite,'NONFINITE_JSON_NUMBER')]:reject(prefix+name,lambda raw=raw:decode(oid,raw=raw),code)
  reject(prefix+'wrong-root-type',lambda:decode(oid,raw=b'[]'),'SCHEMA_TYPE')
  reject(prefix+'auth',lambda:admit(native,{**server,'authenticated':False}),'AUTHENTICATION_REQUIRED')
  reject(prefix+'recovery',lambda:admit(native,{**server,'recovery':'RECOVERING'}),'RECOVERY_BARRIER')
  replay={'owner':UID,'operationId':oid,'key':native['idempotencyKey'],'requestDigest':native['requestDigest'],'outcome':'COMMITTED'}
  from create_replay_contract import locator,freeze_descriptor
  replay.update(locator=locator(native,UID),executionDescriptor=freeze_descriptor(native,server,'R9.1'))
  replay['executionDescriptorDigest']=digest(replay['executionDescriptor'])
  assert_case(prefix+'same-key-replay',lambda:admit(native,server,replay)=={'action':'REPLAY_RECEIPT','dispatchNew':False})
  assert_case(prefix+'unknown-never-new-dispatch',lambda:admit(native,server,{**replay,'outcome':'UNKNOWN'})=={'action':'RECONCILE_ORIGINAL_OPERATION','dispatchNew':False})
  assert_case(prefix+'failure-replayed',lambda:admit(native,server,{**replay,'outcome':'FAILED'})=={'action':'REPLAY_FAILURE','dispatchNew':False})
  reject(prefix+'replay-conflict',lambda:admit(native,server,{**replay,'requestDigest':'sha256:'+'0'*64}),'IDEMPOTENCY_CONFLICT')
  reject(prefix+'replay-wrong-owner',lambda:admit(native,server,{**replay,'owner':UID2}),'REPLAY_SCOPE_MISMATCH')
  reject(prefix+'invalid-outcome',lambda:admit(native,server,{**replay,'outcome':'MODEL_SAYS_DONE'}),'INVALID_REPLAY_OUTCOME')
  assert_case(prefix+'current-revision-does-not-change-frozen-replay',lambda:admit(native,{**server,'currentContractRevision':'R-next'},replay)=={'action':'REPLAY_RECEIPT','dispatchNew':False})
  for field,code,pointer in [('locator','REPLAY_LOCATOR_UNVERIFIED','/replay/locator'),('executionDescriptor','REPLAY_DESCRIPTOR_UNVERIFIED','/replay/executionDescriptor'),('executionDescriptorDigest','REPLAY_DESCRIPTOR_DIGEST_MISMATCH','/replay/executionDescriptorDigest')]:
   bad=copy.deepcopy(replay);bad.pop(field)
   reject(prefix+'missing-frozen-replay/'+field,lambda bad=bad:admit(native,server,bad),code,pointer)
  bad=copy.deepcopy(replay);bad['executionDescriptor']['stableBusinessTargetKey']='MODEL_TARGET';bad['executionDescriptorDigest']=digest(bad['executionDescriptor'])
  reject(prefix+'wrong-frozen-target',lambda bad=bad:admit(native,server,bad),'REPLAY_FROZEN_SCOPE_MISMATCH','/replay/executionDescriptor')

 oid='generation.job.create';body=witnesses[oid]
 reject('generation/blank-intent',lambda:decode(oid,{**body,'intent':'  '}),'EMPTY_INTENT','$.intent')
 reject('generation/unknown-kind',lambda:decode(oid,{**body,'kind':'AUTOMATIC_SUCCESS'}),'SCHEMA_ENUM')
 reject('generation/unknown-target-kind',lambda:decode(oid,{**body,'targetKind':'UNKNOWN_TARGET'}),'SCHEMA_ENUM')
 reject('generation/duplicate-source',lambda:decode(oid,{**body,'sources':body['sources']*2}),'SCHEMA_UNIQUEITEMS')
 reject('generation/duplicate-artifact-different-kind',lambda:decode(oid,{**body,'sources':[{'kind':'FILE','artifactId':UID2},{'kind':'IMAGE','artifactId':UID2}]}),'DUPLICATE_ARTIFACT_REFERENCE')
 reject('generation/client-artifact-digest',lambda:decode(oid,{**body,'sources':[{'kind':'FILE','artifactId':UID2,'contentDigest':'sha256:'+'0'*64}]}),'SCHEMA_ONEOF')
 reject('generation/unknown-source-kind',lambda:decode(oid,{**body,'sources':[{'kind':'JSON_BAG','data':{}}]}),'SCHEMA_ONEOF')
 update={**body,'kind':'UPDATE','targetObjectId':UID2,'generationBasis':{'basisKind':'UPDATE_TARGET_REVISION','snapshotId':UID3,'expectedDigest':'sha256:'+'0'*64}};native=decode(oid,update)
 assert_case('generation/update-positive-request-shape',lambda:native['body']==update)
 reject('generation/update-missing-own-admission',lambda:admit(native,server),'PARENT_TARGET_ADMISSION_POLICY_UNVERIFIED','$.kind')
 reject('generation/target-kind-mismatch',lambda:admit(native,{**server,'targets':{UID2:{'kind':'AI_AGENT'}}}),'TARGET_KIND_MISMATCH','$.targetKind')
 reject('generation/unknown-target',lambda:admit(native,{**server,'targets':{}}),'TARGET_UNRESOLVED','$.targetObjectId')
 image=decode(oid,{**body,'sources':[body['sources'][0],{'kind':'IMAGE','artifactId':UID2}]})
 reject('generation/missing-artifact',lambda:admit(image,{**server,'artifacts':{}}),'ARTIFACT_UNRESOLVED','$.sources[1].artifactId')
 buffer=io.BytesIO();Image.new('RGB',(1,1),(40,80,120)).save(buffer,format='PNG');png=buffer.getvalue()
 image_server=copy.deepcopy(server);image_server['artifacts'][UID2].update(bytes=png,contentSha256=hashlib.sha256(png).hexdigest(),mediaType='image/png')
 assert_case('generation/image-actual-bytes-positive',lambda:admit(image,image_server)['dispatchNew'])
 for name,key,value,code in [('bytes-digest','contentSha256','0'*64,'ARTIFACT_BYTES_DIGEST_MISMATCH'),
   ('identity','artifactId',UID3,'ARTIFACT_IDENTITY_MISMATCH'),('media-type','mediaType','text/plain','ARTIFACT_MEDIA_TYPE_MISMATCH')]:
  bad=copy.deepcopy(image_server);bad['artifacts'][UID2][key]=value
  reject('generation/artifact-'+name,lambda bad=bad:admit(image,bad),code)
 credential_request=decode('generation.job.create',{**witnesses['generation.job.create'],'credential':' synthetic owner input '})
 assert_case('generation/direct-credential-positive',lambda:admit(credential_request,{**server,'ephemeralCredentialPolicyVerified':True})['dispatchNew'])
 reject('generation/direct-credential-no-policy',lambda:admit(credential_request,server),'EPHEMERAL_CREDENTIAL_POLICY_UNVERIFIED','$.credential')
 reject('generation/invalid-unicode-scalar',lambda:decode('generation.job.create',raw=encode(witnesses['generation.job.create']).replace(b'Create a component',b'\\ud800')),'INVALID_UNICODE')
 object_request=decode('generation.job.create',{**witnesses['generation.job.create'],'sources':[{'kind':'OBJECT_REF','objectId':UID2}]})
 assert_case('generation/object-reference-positive',lambda:admit(object_request,server)['dispatchNew'])
 reject('generation/object-reference-missing',lambda:admit(object_request,{**server,'targets':{}}),'OBJECT_REFERENCE_UNRESOLVED','$.sources[0].objectId')
 credential_source=decode('generation.job.create',{**witnesses['generation.job.create'],'sources':[{'kind':'CREDENTIAL_REF','stableName':'EXISTING_SECRET'}]})
 assert_case('generation/credential-reference-positive',lambda:admit(credential_source,{**server,'stableNames':['EXISTING_SECRET'],'credentialSourceContexts':['EXISTING_SECRET']})['dispatchNew'])
 reject('generation/credential-reference-no-context',lambda:admit(credential_source,{**server,'stableNames':['EXISTING_SECRET']}),'SECRET_USE_CONTEXT_UNVERIFIED','$.sources[0]')
 for kind in ['UPDATE','RETRY','REPAIR']:
  candidate={**witnesses['generation.job.create'],'kind':kind,'targetObjectId':UID2,'parentJobId':UID3}
  if kind=='UPDATE':candidate['generationBasis']={'basisKind':'UPDATE_TARGET_REVISION','snapshotId':UID3,'expectedDigest':'sha256:'+'0'*64}
  elif kind=='RETRY':candidate['generationBasis']={'basisKind':'RETRY_FAILED_TECHNICAL_PART','phaseRunId':UID3,'expectedDigest':'sha256:'+'0'*64,'planId':UID3,'expectedPlanDigest':'sha256:'+'0'*64,'approvedRevisionId':UID3,'expectedSpecificationDigest':'sha256:'+'0'*64,'authorityId':UID3,'expectedAuthorityDigest':'sha256:'+'0'*64}
  else:candidate['generationBasis']={'basisKind':'REPAIR_MONITORING_EVIDENCE','monitoringArtifactId':UID3,'expectedDigest':'sha256:'+'0'*64,'snapshotId':UID3,'expectedTargetDigest':'sha256:'+'0'*64,'approvedRevisionId':UID3,'expectedSpecificationDigest':'sha256:'+'0'*64,'authorityId':UID3,'expectedAuthorityDigest':'sha256:'+'0'*64}
  native_candidate=decode('generation.job.create',candidate)
  assert_case('generation/'+kind+'/valid-request-shape',lambda n=native_candidate:n['body']['kind']==kind)
  reject('generation/'+kind+'/missing-own-policy',lambda n=native_candidate:admit(n,server),'PARENT_TARGET_ADMISSION_POLICY_UNVERIFIED','$.kind')
  reject('generation/'+kind+'/boolean-cannot-authorize',lambda n=native_candidate:admit(n,{**server,'parentTargetPolicyVerified':True,'kindPolicyVerified':True}),'PARENT_TARGET_ADMISSION_POLICY_UNVERIFIED','$.kind')
 oid='secret.create';body=witnesses[oid]
 assert_case('secret/byte-preservation',lambda:decode(oid)['body']['value']['text'].encode()==body['value']['text'].encode())
 binary={**body,'type':'GENERIC_BINARY','value':{'encoding':'BASE64','base64':base64.b64encode(b'\0\xff\x01').decode()}}
 assert_case('secret/binary-positive',lambda:admit(decode(oid,binary),server)['dispatchNew'])
 reject('secret/bad-type',lambda:decode(oid,{**body,'type':'UNKNOWN_SECRET'}),'SCHEMA_ENUM')
 reject('secret/type-encoding-mismatch',lambda:decode(oid,{**body,'type':'GENERIC_BINARY'}),'SCHEMA_CONST')
 reject('secret/bad-base64',lambda:decode(oid,{**binary,'value':{'encoding':'BASE64','base64':'@@@='}}),'SCHEMA_ONEOF')
 reject('secret/base64-nonzero-padding-bits',lambda:decode(oid,{**binary,'value':{'encoding':'BASE64','base64':'AB=='}}),'NONCANONICAL_BASE64','$.value.base64')
 reject('secret/duplicate-tag',lambda:decode(oid,{**body,'tags':['duplicate','duplicate']}),'SCHEMA_UNIQUEITEMS')
 reject('secret/name-collision',lambda:admit(decode(oid),{**server,'stableNames':['FIXTURE_SECRET']}),'STABLE_NAME_UNAVAILABLE','$.stableName')
 reject('secret/undefined-type-policy-blocks',lambda:admit(decode(oid,{**body,'type':'CERTIFICATE'}),server),'TYPE_SPECIFIC_POLICY_UNVERIFIED','$.type')
 for reserved in ['KCML_OWNER_API_KEY','PASS']:
  reject('secret/reserved/'+reserved,lambda reserved=reserved:admit(decode(oid,{**body,'stableName':reserved}),server),'RESERVED_CREDENTIAL_REQUIRES_SPECIAL_CONTRACT','$.stableName')
 assert_case('authoring/idempotent',lambda:specialize(payload)==payload)
 baseline=subprocess.check_output(['git','show','aaab5a1:00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT).decode()
 from ssot_sources import resources
 old=json.loads(resource_index(resources(baseline))[PAYLOAD]['raw'])
 unchanged=all(r==o for r,o in zip(payload['records'],old['records']) if r['operationId'] not in OPERATIONS)
 assert_case('authoring/unrelated-routes-byte-shape-preserved',lambda:unchanged)
 report={'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'scope':__doc__,'witnesses':witnesses,
  'checked':len(checks),'failed':sum(not r['passed'] for r in checks),'checks':checks,
  'boundaries':{o:{'request':'EXPLICIT_DOMAIN_SHAPE_AND_DECODER','response':'EXPLICIT_CREATE_OUTPUT_ERROR_UNION','event':'EXPLICIT_AGGREGATE_CREATE_RECEIPT_EVENT','runtime':'NOT_EVALUATED'} for o in OPERATIONS},
  'remaining':'Exact type-specific policies for structured/cryptographic secrets, parent/target state guards, full persistence/artifact parsing/consumer pipeline, full HTTP error adapter, exact request policies and complete consumer pipeline remain mandatory; no whole-operation closure claim.'}
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/repair-create-2026-09-30');out.mkdir(parents=True,exist_ok=True)
 (out/'create-request-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['sourceDocumentSha256','checked','failed']}))
 for r in checks:
  if not r['passed']:print(json.dumps(r))
 return int(bool(report['failed']))
if __name__=='__main__':raise SystemExit(run())
