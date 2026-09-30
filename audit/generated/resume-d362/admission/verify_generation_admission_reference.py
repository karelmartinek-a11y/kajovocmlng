from generation_admission_fixtures import *
checks=[]
def positive(name,fn):
 try:result=fn();checks.append({'case':name,'passed':True});return result
 except Exception as e:checks.append({'case':name,'passed':False,'unexpected':type(e).__name__+':'+str(e)});return None
def negative(name,fn,code,pointer=None):
 try:fn();checks.append({'case':name,'passed':False,'expectedCode':code,'actualCode':'ACCEPTED'})
 except ContractFailure as e:checks.append({'case':name,'passed':e.code==code and (pointer is None or pointer==e.pointer),'expectedCode':code,'actualCode':e.code,'expectedPointer':pointer,'actualPointer':e.pointer})
 except Exception as e:checks.append({'case':name,'passed':False,'expectedCode':code,'unexpected':type(e).__name__+':'+str(e)})
for kind,body in bodies.items():
 p=positive(kind+'/native-positive',lambda:select_generation_basis(body,repo()))
 positive(kind+'/discussion-only',lambda: True if p and p['decision']=='ADMIT_DISCUSSION' else (_ for _ in ()).throw(AssertionError()))
 for selector_field in body['generationBasis']:
  b=copy.deepcopy(body);del b['generationBasis'][selector_field]
  negative(kind+'/missing/'+selector_field,lambda b=b:select_generation_basis(b,repo()),'GENERATION_REQUEST_INVALID')
 for change in [None,False,[],42]:
  b=copy.deepcopy(body);b['generationBasis']=change
  negative(kind+'/basis-type/'+str(change),lambda b=b:select_generation_basis(b,repo()),'GENERATION_REQUEST_INVALID')
 b=copy.deepcopy(body);b['generationBasis']['serverAuthority']=AUTH
 negative(kind+'/extra-server-authority',lambda:select_generation_basis(b,repo()),'GENERATION_REQUEST_INVALID')
 b=copy.deepcopy(body);b['generationBasis']['expectedDigest']='sha256:'+'f'*64
 negative(kind+'/digest-conflict',lambda:select_generation_basis(b,repo()),'GENERATION_BASIS_DIGEST_CONFLICT')
 def with_record(key,mutate,refresh=False):
  rs=copy.deepcopy(records);mutate(rs[key]);return repo(rs)
 key={'UPDATE':SNAP,'RETRY':RUN,'REPAIR':MON}[kind]
 negative(kind+'/bytes-unavailable',lambda key=key:select_generation_basis(body,with_record(key,lambda r:r.pop('bytes'))),'GENERATION_BASIS_BYTES_UNAVAILABLE')
 negative(kind+'/bytes-digest-mismatch',lambda key=key:select_generation_basis(body,with_record(key,lambda r:r.update(bytes=r['bytes']+b' '))),'GENERATION_BASIS_BYTES_DIGEST_MISMATCH')
 negative(kind+'/owner',lambda key=key:select_generation_basis(body,with_record(key,lambda r:r.update(owner='other-owner'))),'GENERATION_BASIS_OWNER_MISMATCH')
 negative(kind+'/record-identity',lambda key=key:select_generation_basis(body,with_record(key,lambda r:r.update(recordId=ids(99)))),'GENERATION_BASIS_IDENTITY_MISMATCH')
 def wrongdef(r):r['schema']['definition']='GenerationAuthority'
 negative(kind+'/wrong-definition',lambda key=key:select_generation_basis(body,with_record(key,wrongdef)),'GENERATION_BASIS_DEFINITION_MISMATCH')
 # Flags can never bypass a malformed actual document.
 rs=copy.deepcopy(records);rs[key]['bytes']=b'{"valid":true,"consistent":true,"sufficient":true}'
 rs[key]['contentDigest']=digest(rs[key]['bytes']);b=copy.deepcopy(body);b['generationBasis']['expectedDigest']=rs[key]['contentDigest']
 negative(kind+'/valid-flags-not-content',lambda:select_generation_basis(b,repo(rs)),'GENERATION_BASIS_SCHEMA_INVALID')
# Mutate semantically valid typed snapshots and recompute the exact selector digest.
def changed(kind,key,edit):
 rs=copy.deepcopy(records);doc=strict_json(rs[key]['bytes']);edit(doc);rs[key]['bytes']=canonical(doc);rs[key]['contentDigest']=digest(rs[key]['bytes']);b=copy.deepcopy(bodies[kind]);b['generationBasis']['expectedDigest']=rs[key]['contentDigest'];return b,repo(rs)
b,r=changed('UPDATE',SNAP,lambda d:d.update(objectId=ids(99)))
negative('UPDATE/target-identity',lambda:select_generation_basis(b,r),'GENERATION_TARGET_SNAPSHOT_MISMATCH')
b,r=changed('RETRY',RUN,lambda d:d.update(failedNodeIds=['NotInPlan']))
negative('RETRY/failed-node-not-in-plan',lambda:select_generation_basis(b,r),'GENERATION_RETRY_FAILED_PART_MISMATCH')
b,r=changed('RETRY',RUN,lambda d:d.update(pendingSideEffectIds=[ids(99)]))
negative('RETRY/unknown-side-effects',lambda:select_generation_basis(b,r),'GENERATION_BASIS_SCHEMA_INVALID','/pendingSideEffectIds')
b,r=changed('RETRY',RUN,lambda d:d.update(state='SUCCEEDED'))
negative('RETRY/success-not-failure',lambda:select_generation_basis(b,r),'GENERATION_BASIS_SCHEMA_INVALID','/state')
b,r=changed('RETRY',RUN,lambda d:d.update(authorityDigest='sha256:'+'f'*64))
negative('RETRY/authority-digest-conflict',lambda:select_generation_basis(b,r),'GENERATION_RETRY_LINEAGE_MISMATCH')
# MON changed bytes need matching publication receipt, otherwise unrelated receipt rejection.
def changed_monitor(edit):
 b,r=changed('REPAIR',MON,edit);receipt=strict_json(r.records[MREC]['bytes']);receipt['contentDigest']=b['generationBasis']['expectedDigest'];r.records[MREC]['bytes']=canonical(receipt);r.records[MREC]['contentDigest']=digest(r.records[MREC]['bytes']);return b,r
b,r=changed_monitor(lambda d:d.update(subjectDigest='sha256:'+'f'*64))
negative('REPAIR/subject-target',lambda:select_generation_basis(b,r),'GENERATION_REPAIR_MONITORING_TARGET_MISMATCH')
b,r=changed_monitor(lambda d:d['observations'].update(failureCount=0))
negative('REPAIR/actual-observation',lambda:select_generation_basis(b,r),'MONITORING_OBSERVATION_INVALID','/observations/failureCount')
b,r=changed_monitor(lambda d:d['observationSchema'].update(nativeSchemaDigest='sha256:'+'f'*64))
negative('REPAIR/observation-schema-digest',lambda:select_generation_basis(b,r),'MONITORING_OBSERVATION_SCHEMA_DIGEST_MISMATCH')
rs=copy.deepcopy(records);receipt=strict_json(rs[MREC]['bytes']);receipt['outcome']='UNKNOWN';rs[MREC]['bytes']=canonical(receipt);rs[MREC]['contentDigest']=digest(rs[MREC]['bytes'])
negative('REPAIR/publication-unknown',lambda:select_generation_basis(bodies['REPAIR'],repo(rs)),'GENERATION_BASIS_UNPUBLISHED')
for basis,key in [('INITIAL_REQUEST',INITIAL),('SPECIFICATION_REVISION',SPEC),('PUBLISHED_FINAL_OUTPUT',MON)]:
 body={'kind':'FOLLOW_UP','parentJobId':JOB,'followUpBasis':{'basisKind':basis,'expectedDigest':records[key]['contentDigest']}}
 if basis=='SPECIFICATION_REVISION':body['followUpBasis']['revisionId']=key
 if basis=='PUBLISHED_FINAL_OUTPUT':body['followUpBasis']['artifactId']=key
 positive('FOLLOW_UP/'+basis+'/actual-native-content',lambda body=body,key=key:validate_follow_up_content(body,key,repo()))
 for raw,code,pointer in [(b'{"intent":"one","intent":"two"}','GENERATION_BASIS_DUPLICATE_JSON_KEY','/intent'),(b'{"intent":','GENERATION_BASIS_JSON_INVALID','')]:
  rs=copy.deepcopy(records);rs[key]['bytes']=raw;rs[key]['contentDigest']=digest(raw);b=copy.deepcopy(body);b['followUpBasis']['expectedDigest']=digest(raw)
  negative('FOLLOW_UP/'+basis+'/'+code,lambda:validate_follow_up_content(b,key,repo(rs)),code,pointer)
# Immutable frozen byte loading ignores later mutable current pointers.
r=repo();before=select_generation_basis(bodies['UPDATE'],r);r.records['current_target']={'revisionId':ids(99)}
positive('UPDATE/moving-current-pointer-ignored',lambda:True if select_generation_basis(bodies['UPDATE'],r)==before else (_ for _ in ()).throw(AssertionError()))
negative('registry/bundle-bytes-digest',lambda:repo(bs={gb:gen_raw+b' ',lb:local_raw}),'GENERATION_SCHEMA_BUNDLE_DIGEST_MISMATCH')
# Each additional mutation starts from its own valid native witness.
r=repo();closure=select_generation_basis(bodies['RETRY'],r)
required={REV,AUTH,APP,NATIVE_AUTHORITY,RUN,PLAN,resultdig}
positive('RETRY/consulted-dependency-closure',lambda:True if required <= {x['recordId'] for x in closure['frozenInputs']} else (_ for _ in ()).throw(AssertionError()))
r=repo();closure=select_generation_basis(bodies['REPAIR'],r)
required={REV,AUTH,APP,NATIVE_AUTHORITY,SNAP,MON,MREC,SCHEMA,SREC}
positive('REPAIR/consulted-dependency-closure',lambda:True if required <= {x['recordId'] for x in closure['frozenInputs']} else (_ for _ in ()).throw(AssertionError()))
rs2=copy.deepcopy(records);changed_spec=strict_json(rs2[REV]['bytes']);changed_spec['jobId']=ids(99);rs2[REV]['bytes']=canonical(changed_spec);rs2[REV]['contentDigest']=digest(rs2[REV]['bytes']);b=copy.deepcopy(bodies['REPAIR']);b['generationBasis']['expectedSpecificationDigest']=rs2[REV]['contentDigest']
negative('REPAIR/document-job-vs-repository-job',lambda:select_generation_basis(b,repo(rs2)),'GENERATION_BASIS_DOCUMENT_JOB_MISMATCH')
rs2=copy.deepcopy(records);changed_auth=strict_json(rs2[AUTH]['bytes']);changed_auth['authority']['secretPurposeIds']=['DifferentPurpose'];rs2[AUTH]['bytes']=canonical(changed_auth);rs2[AUTH]['contentDigest']=digest(rs2[AUTH]['bytes']);b=copy.deepcopy(bodies['REPAIR']);b['generationBasis']['expectedAuthorityDigest']=rs2[AUTH]['contentDigest']
negative('REPAIR/actual-authority-content-mismatch',lambda:select_generation_basis(b,repo(rs2)),'GENERATION_APPROVED_AUTHORITY_CONTENT_MISMATCH')
rs2=copy.deepcopy(records);rs2[SCHEMA]['schema']['bundleDigest']='sha256:'+'f'*64
negative('REPAIR/schema-meta-bundle-unresolved',lambda:select_generation_basis(bodies['REPAIR'],repo(rs2)),'GENERATION_BASIS_SCHEMA_BUNDLE_UNAVAILABLE')
r=repo();r.targetHeads[TARGET]={'snapshotId':ids(99),'contentDigest':targetdig}
negative('REPAIR/stale-current-target-head',lambda:select_generation_basis(bodies['REPAIR'],r),'GENERATION_REPAIR_CURRENT_TARGET_SNAPSHOT_MISMATCH')
# Native UUID/digest shape is insufficient to assert latest approved target lineage.
rs2=copy.deepcopy(records);newtarget=strict_json(rs2[SNAP]['bytes']);newtarget['lastApprovedAuthorityId']=ids(99);rs2[SNAP]['bytes']=canonical(newtarget);rs2[SNAP]['contentDigest']=digest(rs2[SNAP]['bytes']);b=copy.deepcopy(bodies['REPAIR']);b['generationBasis']['expectedTargetDigest']=rs2[SNAP]['contentDigest'];r=repo(rs2);r.targetHeads[TARGET]={'snapshotId':SNAP,'contentDigest':rs2[SNAP]['contentDigest']}
negative('REPAIR/wrong-last-approved-authority',lambda:select_generation_basis(b,r),'GENERATION_REPAIR_LAST_APPROVED_LINEAGE_MISMATCH')
report={'inputCommit':PIN,'ssotSha256':hashlib.sha256(source).hexdigest(),'schemaBundleSha256':rs['contracts/generation/generation-contracts.schema.json']['sha256'] if 'contracts/generation/generation-contracts.schema.json' in rs else hashlib.sha256(gen_raw).hexdigest(),'proofKind':'DESIGN_REFERENCE_SYNTHETIC_NATIVE_BYTES',
 'supportSha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'generation_admission_reference.py',OUT/'generation_admission_fixtures.py',Path(__file__),ROOT/'scripts/create_operation_contracts.py',ROOT/'scripts/follow_up_contracts.py',ROOT/'scripts/verify_phase2_handoffs.py',ROOT/'scripts/ssot_sources.py']},
 'environment':{'interpreter':sys.executable,'python':sys.version,'jsonschemaVersion':__import__('importlib.metadata',fromlist=['version']).version('jsonschema'),'formatChecker':'jsonschema.FormatChecker installed dependency baseline'},
 'checks':checks,'checkCount':len(checks),'failedCount':sum(not c['passed'] for c in checks),'runtimeAcceptance':'NOT_EVALUATED',
 'scopeExclusions':['SQL roles/locking/atomic persistence are separate required fixture proofs','Native specification schema is validated; all ContractRecordRef graphs and implementation predicate executions remain separate §12.20 obligations','All selectors and local record masks are technical proposals pending coordinator normative materialization','Monitoring observed schema proves actual observation shape; the exact consumer repair-policy semantic predicate still requires declared consumer/implementation binding']}
(OUT/'generation-admission-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'generation-admission.schema.json').write_text(json.dumps(local_bundle(),ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failed':report['failedCount']}))
for c in checks:
 if not c['passed']:print(json.dumps(c))
sys.exit(1 if report['failedCount'] else 0)
