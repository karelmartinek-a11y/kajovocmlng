"""Synthetic immutable FOLLOW_UP admission proof; no database/concurrency runtime claim."""
import copy
import hashlib
import json
import os
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from ssot_sources import ROOT, SSOT, resource_index
from create_operation_contracts import ContractFailure, decode_http, admit, digest
from follow_up_contracts import request_schema, frozen_basis_schema, admit_follow_up, hydrate_frozen_basis

OWNER='00000000-0000-4000-8000-000000000001'
JOB='00000000-0000-4000-8000-000000000002'
SNAPSHOT='00000000-0000-4000-8000-000000000003'
REVISION='00000000-0000-4000-8000-000000000004'
ARTIFACT='00000000-0000-4000-8000-000000000005'
OTHER='00000000-0000-4000-8000-000000000006'

def fixture(basis_kind='INITIAL_REQUEST',state='DISCUSSING'):
 from generation_follow_up_fixtures import factory
 return factory(basis_kind,OWNER,JOB,SNAPSHOT,REVISION,ARTIFACT,OTHER,state)

def domain_state(server):
 return {k:server.get(k) for k in ['jobs','sourceSnapshots','publicationReceipts','finalOutputDeclarations']}|{'repositoryRecords':server['generationBasisRepository'].records}


def main():
 source=hashlib.sha256(SSOT.read_bytes()).hexdigest()
 support={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['scripts/follow_up_contracts.py','scripts/verify_follow_up_contracts.py','scripts/create_operation_contracts.py','scripts/generation_follow_up_fixtures.py','scripts/generation_admission_contracts.py']}
 checks=[];matrix=[]
 def check(name,actual,expected=True):checks.append({'case':name,'passed':actual==expected,'actual':actual,'expected':expected})
 def reject(name,body,server,code,pointer):
  try:admit_follow_up(body,server);checks.append({'case':name,'passed':False,'diagnostic':'ACCEPTED_INVALID','expectedCode':code,'expectedPointer':pointer})
  except ContractFailure as exc:checks.append({'case':name,'passed':exc.code==code and exc.pointer==pointer,'expectedCode':code,'actualCode':exc.code,'expectedPointer':pointer,'actualPointer':exc.pointer})
  except Exception as exc:checks.append({'case':name,'passed':False,'diagnostic':'UNRELATED_EXCEPTION','exceptionType':type(exc).__name__,'reason':str(exc)})
 def reject_hydration(name,descriptor,server,code):
  try:hydrate_frozen_basis(descriptor,server);checks.append({'case':name,'passed':False,'diagnostic':'ACCEPTED_INVALID','expectedCode':code})
  except ContractFailure as exc:checks.append({'case':name,'passed':exc.code==code and exc.pointer=='','expectedCode':code,'actualCode':exc.code,'expectedPointer':'','actualPointer':exc.pointer})
  except Exception as exc:checks.append({'case':name,'passed':False,'diagnostic':'UNRELATED_EXCEPTION','exceptionType':type(exc).__name__,'reason':str(exc)})
 def reject_call(name,fn,code,pointer):
  try:fn();checks.append({'case':name,'passed':False,'diagnostic':'ACCEPTED_INVALID','expectedCode':code,'expectedPointer':pointer})
  except ContractFailure as exc:checks.append({'case':name,'passed':exc.code==code and exc.pointer==pointer,'expectedCode':code,'actualCode':exc.code,'expectedPointer':pointer,'actualPointer':exc.pointer})
  except Exception as exc:checks.append({'case':name,'passed':False,'diagnostic':'UNRELATED_EXCEPTION','exceptionType':type(exc).__name__,'reason':str(exc)})
 models=json.loads(resource_index()['contracts/execution/model-catalog.json']['raw'])
 lifecycle=next(m for m in models if m['modelId']=='model.generation-job')
 states=lifecycle['states']
 validator=Draft202012Validator(request_schema(),format_checker=FormatChecker())
 def error_tree(error):
  yield error
  for child in error.context:yield from error_tree(child)
 for basis_kind in ['INITIAL_REQUEST','SPECIFICATION_REVISION','PUBLISHED_FINAL_OUTPUT']:
  body,server,key=fixture(basis_kind)
  check(basis_kind+'/positive-basis-schema',validator.is_valid(body['followUpBasis']))
  for state in states:
   b,s,k=fixture(basis_kind,state)
   try:
    frozen=admit_follow_up(b,s)
    check(basis_kind+'/'+state+'/positive-admission',isinstance(frozen,dict))
    matrix.append({'kind':'FOLLOW_UP','sourceState':state,'basisKind':basis_kind,'availability':'IMMUTABLE_AVAILABLE_CONSISTENT_SUFFICIENT_PUBLISHED_IF_FINAL','decision':'ALLOW','reason':'Approved frozen basis; parent terminality is not a global prerequisite.'})
   except Exception as exc:checks.append({'case':basis_kind+'/'+state+'/positive-admission','passed':False,'diagnostic':'UNEXPECTED_EXCEPTION','reason':str(exc)})
  for field in validator.schema.get('oneOf',[]):
   if field.get('properties',{}).get('basisKind',{}).get('const')!=basis_kind:continue
   for required in field.get('required',[]):
    invalid=copy.deepcopy(body['followUpBasis']);del invalid[required]
    errors=[child for error in validator.iter_errors(invalid) for child in error_tree(error)]
    check(basis_kind+'/schema/missing/'+required,any(e.validator=='required' and e.message==repr(required)+' is a required property' for e in errors))
  for extra in ['values','canonicalJson','serverReceipt','authorityId','snapshotId','bytes']:
   bad={**body['followUpBasis'],extra:'untrusted'}
   errors=[child for error in validator.iter_errors(bad) for child in error_tree(error)]
   check(basis_kind+'/schema/extra/'+extra,any(e.validator=='additionalProperties' and extra in e.message for e in errors))
  for field in body['followUpBasis']:
   bad={**body['followUpBasis'],field:None}
   errors=[child for error in validator.iter_errors(bad) for child in error_tree(error)]
   check(basis_kind+'/schema/null/'+field,any(e.validator==('const' if field=='basisKind' else 'type') and list(e.absolute_path)==[field] for e in errors))
  source_before=copy.deepcopy(domain_state(server))
  frozen=admit_follow_up(body,server);unchanged=copy.deepcopy(frozen)
  check(basis_kind+'/admission-never-mutates-source',domain_state(server)==source_before)
  for later_state in ['COMPLETED','FAILED','CANCELLED']:
   server['jobs'][JOB]['state']=later_state
   server['sourceSnapshots'][key]['bytes']=b'Later replacement must not rewrite frozen output.'
   check(basis_kind+'/frozen-after-parent-'+later_state,frozen==unchanged)
  body,server,key=fixture(basis_kind)
  expected_bytes=server['sourceSnapshots'][key]['bytes']
  before=admit_follow_up(body,server)['frozenBasis']
  frozen_validator=Draft202012Validator(frozen_basis_schema(),format_checker=FormatChecker())
  check(basis_kind+'/server-frozen-descriptor-schema',frozen_validator.is_valid(before))
  for field in before:
   bad=copy.deepcopy(before);del bad[field]
   errors=[child for error in frozen_validator.iter_errors(bad) for child in error_tree(error)]
   check(basis_kind+'/server-descriptor-missing/'+field,any(e.validator=='required' and e.message==repr(field)+' is a required property' for e in errors))
  bad={**before,'currentSourceState':'COMPLETED'}
  errors=[child for error in frozen_validator.iter_errors(bad) for child in error_tree(error)]
  check(basis_kind+'/server-descriptor-forbids-moving-state',any(e.validator=='additionalProperties' and 'currentSourceState' in e.message for e in errors))
  digest_input={k:v for k,v in before.items() if k!='lineageDigest'}
  lineage='sha256:'+hashlib.sha256(json.dumps(digest_input,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  check(basis_kind+'/server-lineage-digest-exact',before['lineageDigest'],lineage)
  server['jobs'][JOB]['state']='CANCELLED'
  check(basis_kind+'/fresh-admission-same-immutable-lineage-after-parent-cancel',admit_follow_up(body,server)['frozenBasis']==before)
  check(basis_kind+'/hydration-positive',hydrate_frozen_basis(before,server)==expected_bytes)
  for state in states:
   server['jobs'][JOB]['state']=state
   server['jobs'][JOB]['currentRevisionId']=OTHER
   server['sourceSnapshots'][key].update(available=False,consistent=False,sufficient=False)
   check(basis_kind+'/hydration-frozen-after-source-'+state,hydrate_frozen_basis(before,server)==expected_bytes)
  for name,mutator,code in [('extra-descriptor',lambda d,s:d.update(currentSourceState='COMPLETED'),'FOLLOW_UP_FROZEN_DESCRIPTOR_INVALID'),('wrong-lineage-digest',lambda d,s:d.update(lineageDigest='sha256:'+'0'*64),'FOLLOW_UP_FROZEN_LINEAGE_DIGEST_MISMATCH'),('missing-snapshot',lambda d,s:s['sourceSnapshots'].clear(),'FOLLOW_UP_FROZEN_SNAPSHOT_UNAVAILABLE'),('duplicate-snapshot',lambda d,s:s['sourceSnapshots'].update({('duplicate',):copy.deepcopy(s['sourceSnapshots'][key])}),'FOLLOW_UP_FROZEN_SNAPSHOT_UNAVAILABLE'),('source-owner',lambda d,s:s['sourceSnapshots'][key].update(owner=OTHER),'FOLLOW_UP_SOURCE_OWNER_MISMATCH'),('source-id',lambda d,s:s['sourceSnapshots'][key].update(jobId=OTHER),'FOLLOW_UP_FROZEN_IDENTITY_MISMATCH'),('mutable-snapshot',lambda d,s:s['sourceSnapshots'][key].update(immutable=False),'FOLLOW_UP_BASIS_NOT_IMMUTABLE'),('missing-bytes',lambda d,s:s['sourceSnapshots'][key].pop('bytes'),'FOLLOW_UP_BASIS_BYTES_UNAVAILABLE'),('changed-actual-bytes',lambda d,s:s['sourceSnapshots'][key].update(bytes=b'changed later'),'FOLLOW_UP_BASIS_BYTES_DIGEST_MISMATCH')]:
   d,s=copy.deepcopy(before),copy.deepcopy(server)
   hydrate_frozen_basis(d,s)
   mutator(d,s)
   reject_hydration(basis_kind+'/hydration/'+name,d,s,code)
  if basis_kind=='PUBLISHED_FINAL_OUTPUT':
   for name,mutator,code in [('receipt-missing',lambda s:s['publicationReceipts'].clear(),'FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED'),('receipt-unknown',lambda s:s['publicationReceipts'][OTHER].update(outcome='UNKNOWN'),'FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED'),('receipt-identity',lambda s:s['publicationReceipts'][OTHER].update(artifactId=REVISION),'FOLLOW_UP_PUBLICATION_RECEIPT_MISMATCH')]:
    s=copy.deepcopy(server);hydrate_frozen_basis(before,s);mutator(s)
    reject_hydration(basis_kind+'/hydration/'+name,before,s,code)
  body,server,key=fixture(basis_kind)
  payload=json.loads(resource_index()['contracts/payload-contracts.json']['raw'])
  route=next(r for r in payload['records'] if r['operationId']=='generation.job.create')
  headers=[('Content-Type','application/json'),('Idempotency-Key','synthetic-follow-up-'+basis_kind)]
  def decode(value,query=None,raw=None):
   return decode_http('generation.job.create','POST',route['path'],[] if query is None else query,headers,json.dumps(value,ensure_ascii=False).encode() if raw is None else raw)
  native=decode(body)
  admitted=admit(native,server)
  check(basis_kind+'/integrated-http-positive',native['body'],body)
  check(basis_kind+'/integrated-native-admission',admitted['frozenBasis'],admit_follow_up(body,server)['frozenBasis'])
  missing=copy.deepcopy(body);missing.pop('followUpBasis')
  reject_call(basis_kind+'/http-missing-basis',lambda:decode(missing),'SCHEMA_REQUIRED','$')
  missing=copy.deepcopy(body);missing.pop('parentJobId')
  reject_call(basis_kind+'/http-missing-parent',lambda:decode(missing),'SCHEMA_REQUIRED','$')
  reject_call(basis_kind+'/http-basis-on-create',lambda:decode({**body,'kind':'CREATE'}),'SCHEMA_NOT','$')
  reject_call(basis_kind+'/http-unknown-query',lambda:decode(body,[('unrecognized','x')]),'UNKNOWN_QUERY_PARAMETER','/query')
  raw=json.dumps(body).encode()
  duplicate=raw.replace(b'"basisKind":',b'"basisKind": "'+basis_kind.encode()+b'", "basisKind":',1)
  reject_call(basis_kind+'/http-duplicate-nested-basis-key',lambda:decode(body,raw=duplicate),'DUPLICATE_JSON_KEY','/followUpBasis/basisKind')
  from create_replay_contract import locator, freeze_descriptor
  descriptor=freeze_descriptor(native,server,'SYNTHETIC_CURRENT_CONTRACT_REVISION')
  replay={'owner':OWNER,'operationId':'generation.job.create','key':native['idempotencyKey'],'requestDigest':native['requestDigest'],'outcome':'COMMITTED','locator':locator(native,OWNER),'executionDescriptor':descriptor,'executionDescriptorDigest':digest(descriptor)}
  original_frozen=copy.deepcopy(admitted['frozenBasis'])
  server['jobs'][JOB]['state']='CANCELLED';server['sourceSnapshots'][key]['available']=False
  check(basis_kind+'/committed-replay-before-fresh-eligibility',admit(native,server,replay),{'action':'REPLAY_RECEIPT','dispatchNew':False})
  check(basis_kind+'/original-frozen-result-is-detached',admitted['frozenBasis'],original_frozen)
  conflict=copy.deepcopy(native);conflict['requestDigest']='sha256:'+'0'*64
  reject_call(basis_kind+'/replay-digest-conflict',lambda:admit(conflict,server,replay),'IDEMPOTENCY_CONFLICT','')
 # The concrete rejection table is added alongside the authored admission module;
 # every mutation starts with an admitted domain witness.
 for name,mutator,code,pointer in rejection_cases():
  body,server,key=fixture(name.split('/')[0] if name.split('/')[0] in ['INITIAL_REQUEST','SPECIFICATION_REVISION','PUBLISHED_FINAL_OUTPUT'] else 'INITIAL_REQUEST')
  admit_follow_up(body,server)
  mutator(body,server,key)
  reject(name,body,server,code,pointer)
 # Replace the six obsolete caller-like validity-flag mutants with actual
 # source bytes/domain violations. Every negative first admits a valid witness.
 native_replacements=[]
 for basis_kind in ['INITIAL_REQUEST','SPECIFICATION_REVISION','PUBLISHED_FINAL_OUTPUT']:
  for category in ['consistent','sufficient']:
   body,server,key=fixture(basis_kind);admit_follow_up(body,server)
   record=server['sourceSnapshots'][key];value=json.loads(record['bytes'])
   if category=='consistent':
    if basis_kind=='INITIAL_REQUEST':
     raw=b'{"intent":"synthetic first","intent":"synthetic second","kind":"CREATE"}'
     code='GENERATION_BASIS_DUPLICATE_JSON_KEY';pointer='/intent';violation='Actual duplicate source JSON key'
    else:
     value['jobId']=OTHER;raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
     code='GENERATION_BASIS_DOCUMENT_JOB_MISMATCH';pointer='';violation='Valid native document belongs to another source job'
   else:
    field={'INITIAL_REQUEST':'intent','SPECIFICATION_REVISION':'behavioralRequirements','PUBLISHED_FINAL_OUTPUT':'artifacts'}[basis_kind]
    value.pop(field);raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    code='GENERATION_BASIS_SCHEMA_INVALID';pointer='';violation='Actual source is missing required domain '+field
   record['bytes']=raw;record['contentDigest']='sha256:'+hashlib.sha256(raw).hexdigest();body['followUpBasis']['expectedDigest']=record['contentDigest']
   if basis_kind=='PUBLISHED_FINAL_OUTPUT':
    server['publicationReceipts'][OTHER]['contentDigest']=record['contentDigest']
    receipt=server['generationBasisRepository'].records[OTHER];rv=json.loads(receipt['bytes']);rv['contentDigest']=record['contentDigest'];receipt['bytes']=json.dumps(rv,sort_keys=True,separators=(',',':')).encode();receipt['contentDigest']='sha256:'+hashlib.sha256(receipt['bytes']).hexdigest()
   name=basis_kind+'/native-'+category
   reject(name,body,server,code,pointer)
   native_replacements.append({'historicalCase':basis_kind+'/'+category+'/FOLLOW_UP_BASIS_'+('INCONSISTENT' if category=='consistent' else 'INSUFFICIENT'),'replacementCase':name,'expectedDiagnostic':code,'violation':violation,'disposition':'REPLACED_VALIDITY_FLAG_WITH_POSITIVE_DERIVED_ACTUAL_NATIVE_BYTES'})
 for state in states:
  for availability in ['MISSING','INCONSISTENT','INSUFFICIENT','UNPUBLISHED']:
   body,server,key=fixture('PUBLISHED_FINAL_OUTPUT',state);admit_follow_up(body,server)
   pointer='$.followUpBasis'
   if availability=='MISSING':server['sourceSnapshots'][key]['available']=False;code='FOLLOW_UP_BASIS_UNAVAILABLE'
   elif availability=='INCONSISTENT':
    record=server['sourceSnapshots'][key];record['bytes']=b'{"broken":';record['contentDigest']='sha256:'+hashlib.sha256(record['bytes']).hexdigest();body['followUpBasis']['expectedDigest']=record['contentDigest'];server['publicationReceipts'][OTHER]['contentDigest']=record['contentDigest'];code='GENERATION_BASIS_JSON_INVALID';pointer=''
   elif availability=='INSUFFICIENT':server['finalOutputDeclarations'].clear();code='GENERATION_FINAL_OUTPUT_DECLARATION_UNAVAILABLE';pointer=''
   else:server['publicationReceipts'][OTHER]['outcome']='UNKNOWN';code='FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED'
   reject('matrix/'+state+'/'+availability,body,server,code,pointer)
 for kind in ['CREATE','UPDATE','RETRY','REPAIR']:
  matrix.append({'kind':kind,'sourceState':'NOT_REVIEWED_IN_THIS_PROOF','availability':'NOT_REVIEWED_IN_THIS_PROOF','decision':'OPEN','reason':'Requires its own kind-specific authority; FOLLOW_UP approval is not borrowed.'})
 authored_matrix=__import__('follow_up_contracts').matrix()
 check('decision-matrix/exact-universe',authored_matrix['rowCount'],5*len(states)*5)
 check('decision-matrix/followup-universe',authored_matrix['followUpRowCount'],len(states)*5)
 check('decision-matrix/other-kinds-remain-open',all(row['status']=='OPEN' for row in authored_matrix['rows'] if row['kind']!='FOLLOW_UP'))
 check('decision-matrix/no-terminal-only-shortcut',all(row['decision'].startswith('ALLOW_IF_') for row in authored_matrix['rows'] if row['kind']=='FOLLOW_UP' and row['basisAvailability']=='AVAILABLE_IMMUTABLE'))
 changed=hashlib.sha256(SSOT.read_bytes()).hexdigest()!=source or any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=digest for p,digest in support.items())
 if changed:check('source-input-stability',False)
 report={'sourceDocumentSha256':source,'supportSha256':support,'scope':__doc__,'proofKind':'DESIGN_REFERENCE_MODEL','implementationAcceptance':'NOT_EVALUATED','authority':'Owner approval of explicit frozen FOLLOW_UP admission; generation-job states contracts/execution/model-catalog.json model.generation-job / authoritySection 49.15','checked':len(checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'nativeCoverageReplacements':native_replacements,'matrix':matrix,'matrixCoverage':{'reviewedKind':'FOLLOW_UP','sourceStateCount':len(states),'basisKindCount':3,'positiveCells':len(states)*3,'authoredMatrixCells':authored_matrix['rowCount'],'specifiedFollowUpCells':authored_matrix['followUpRowCount'],'otherKinds':'OPEN; not semantically reviewed by this proof'},'remaining':['Actual-byte reference hydration is tested, but database atomic locking, SQL persistence, real artifact-store hydration, independent job identity and runtime shared-resource coordination are not evidenced by a pure reference function.','Concrete failure/unpublished availability matrix uses explicit rejection witnesses; no full-operation closure assertion.']}
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/follow-up-tests');out.mkdir(parents=True,exist_ok=True)
 (out/'follow-up-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['sourceDocumentSha256','checked','failed']}))
 for c in checks:
  if not c['passed']:print(json.dumps(c))
 return int(bool(report['failed']))

def rejection_cases():
 cases=[]
 def add(name,mutator,code,pointer='$.followUpBasis'):cases.append((name,mutator,code,pointer))
 add('wrong-kind',lambda b,s,k:b.update(kind='RETRY'),'FOLLOW_UP_KIND_REQUIRED','$.kind')
 add('missing-parent',lambda b,s,k:b.pop('parentJobId'),'FOLLOW_UP_PARENT_REQUIRED','$.parentJobId')
 add('invalid-parent',lambda b,s,k:b.update(parentJobId='latest'),'FOLLOW_UP_PARENT_REQUIRED','$.parentJobId')
 add('auth',lambda b,s,k:s.update(authenticated=False),'AUTHENTICATION_REQUIRED','')
 add('model-authority-not-owner',lambda b,s,k:s.update(actor='MODEL'),'AUTHENTICATION_REQUIRED','')
 add('missing-owner',lambda b,s,k:s.pop('owner'),'AUTHENTICATION_REQUIRED','')
 add('atomic-snapshot-unverified',lambda b,s,k:s.update(atomicGenerationAdmission=False),'FOLLOW_UP_ATOMIC_ADMISSION_UNVERIFIED','')
 add('parent-missing',lambda b,s,k:s['jobs'].clear(),'PARENT_JOB_UNRESOLVED','$.parentJobId')
 add('parent-identity',lambda b,s,k:s['jobs'][JOB].update(jobId=OTHER),'PARENT_JOB_IDENTITY_MISMATCH','$.parentJobId')
 add('parent-owner',lambda b,s,k:s['jobs'][JOB].update(owner=OTHER),'FOLLOW_UP_SOURCE_OWNER_MISMATCH','$.parentJobId')
 add('unknown-parent-state',lambda b,s,k:s['jobs'][JOB].update(state='RUNNING'),'FOLLOW_UP_SOURCE_STATE_INVALID','$.parentJobId')
 for kind in ['INITIAL_REQUEST','SPECIFICATION_REVISION','PUBLISHED_FINAL_OUTPUT']:
  prefix=kind+'/'
  add(prefix+'missing',lambda b,s,k:s['sourceSnapshots'].clear(),'FOLLOW_UP_BASIS_UNAVAILABLE')
  for field,value,code in [('available',False,'FOLLOW_UP_BASIS_UNAVAILABLE'),('jobId',OTHER,'FOLLOW_UP_BASIS_IDENTITY_MISMATCH'),('basisKind','CURRENT','FOLLOW_UP_BASIS_IDENTITY_MISMATCH'),('owner',OTHER,'FOLLOW_UP_SOURCE_OWNER_MISMATCH'),('snapshotId','current','FOLLOW_UP_SNAPSHOT_IDENTITY_INVALID'),('immutable',False,'FOLLOW_UP_BASIS_NOT_IMMUTABLE'),('bytes','not bytes','FOLLOW_UP_BASIS_BYTES_UNAVAILABLE'),('bytes',b'Changed after lock','FOLLOW_UP_BASIS_BYTES_DIGEST_MISMATCH'),('contentDigest','sha256:'+'0'*64,'FOLLOW_UP_BASIS_BYTES_DIGEST_MISMATCH')]:
   add(prefix+field+'/'+code,lambda b,s,k,field=field,value=value:s['sourceSnapshots'][k].update({field:value}),code)
  add(prefix+'wrong-client-digest',lambda b,s,k:b['followUpBasis'].update(expectedDigest='sha256:'+'0'*64),'FOLLOW_UP_BASIS_DIGEST_CONFLICT','$.followUpBasis.expectedDigest')
  for extra in ['current','clientReceipt','authorityId']:
   add(prefix+'extra-'+extra,lambda b,s,k,extra=extra:b['followUpBasis'].update({extra:'untrusted'}),'FOLLOW_UP_BASIS_INVALID')
  if kind!='INITIAL_REQUEST':
   field='revisionId' if kind=='SPECIFICATION_REVISION' else 'artifactId'
   add(prefix+'wrong-record-selector',lambda b,s,k,field=field:s['sourceSnapshots'][k].update({field:OTHER}),'FOLLOW_UP_BASIS_IDENTITY_MISMATCH','$.followUpBasis.'+field)
  if kind=='PUBLISHED_FINAL_OUTPUT':
   add(prefix+'missing-final-declaration',lambda b,s,k:s['finalOutputDeclarations'].clear(),'GENERATION_FINAL_OUTPUT_DECLARATION_UNAVAILABLE','')
   add(prefix+'no-server-receipt',lambda b,s,k:s['publicationReceipts'].clear(),'FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED')
   add(prefix+'uncommitted-receipt',lambda b,s,k:s['publicationReceipts'][OTHER].update(outcome='UNKNOWN'),'FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED')
   for field,value in [('receiptId',SNAPSHOT),('jobId',OTHER),('artifactId',REVISION),('contentDigest','sha256:'+'0'*64)]:
    add(prefix+'receipt-'+field,lambda b,s,k,field=field,value=value:s['publicationReceipts'][OTHER].update({field:value}),'FOLLOW_UP_PUBLICATION_RECEIPT_MISMATCH')
 return cases

if __name__=='__main__':raise SystemExit(main())
