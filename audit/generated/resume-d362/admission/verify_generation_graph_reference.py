"""Actual native reference graph + exact child-local projection tests, synthetic only."""
from generation_graph_fixtures import *
checks=[]
def positive(name,fn):
 try:fn();checks.append({'case':name,'passed':True})
 except Exception as e:checks.append({'case':name,'passed':False,'unexpected':type(e).__name__+':'+str(e)})
def negative(name,fn,code,pointer=None):
 try:fn();checks.append({'case':name,'passed':False,'actualCode':'ACCEPTED','expectedCode':code})
 except ContractFailure as e:checks.append({'case':name,'passed':e.code==code and (pointer is None or e.pointer==pointer),'actualCode':e.code,'actualPointer':e.pointer,'expectedCode':code,'expectedPointer':pointer})
 except Exception as e:checks.append({'case':name,'passed':False,'unexpected':type(e).__name__+':'+str(e),'expectedCode':code})
result=validator().specification(spec)
positive('native/43-artifacts-21-records-positive',lambda:validator().specification(spec))
positive('native/actual-schema-positive-and-negative-vectors-executed',lambda: True if result['schemaVectorsExecuted']>=2 else (_ for _ in ()).throw(AssertionError()))
positive('native/expected-generated-code-needs-no-premature-bytes',lambda: True if result['expectedArtifacts'] and result['implementationAcceptance']=='NOT_EVALUATED' else (_ for _ in ()).throw(AssertionError()))
negative('native/expected-code-is-not-implementation-acceptance',lambda:validator(stage='IMPLEMENTATION_ACCEPTANCE').specification(spec),'GENERATION_GRAPH_IMPLEMENTATION_EXPECTATION_UNMATERIALIZED','/repositoryPath')
for label,edit,code in [
 ('duplicate-requirement',lambda s:s['behavioralRequirements'].append(copy.deepcopy(s['behavioralRequirements'][0])),'GENERATION_GRAPH_DUPLICATE_REQUIREMENT'),
 ('unknown-dependency',lambda s:s['behavioralRequirements'][0]['dependsOn'].append('MissingRequirement'),'GENERATION_GRAPH_REQUIREMENT_DEPENDENCY_UNRESOLVED'),
 ('self-cycle',lambda s:s['behavioralRequirements'][0]['dependsOn'].append(REQ),'GENERATION_GRAPH_REQUIREMENT_CYCLE'),
 ('missing-acceptance',lambda s:s['behavioralRequirements'][0].update(acceptanceIds=['MissingAcceptance']),'GENERATION_GRAPH_ACCEPTANCE_UNRESOLVED'),
 ('missing-domain-coverage',lambda s:s['behavioralRequirements'][0].update(domainContractRefs=[]),'GENERATION_GRAPH_DOMAIN_CONTRACT_COVERAGE_MISSING'),
 ('unknown-capability-requirement',lambda s:s['capabilityDecision']['coverage'][0].update(requirementId='MissingRequirement'),'GENERATION_GRAPH_CAPABILITY_COVERAGE_MISSING'),
 ('duplicate-capability',lambda s:s['capabilityDecision']['coverage'].append(copy.deepcopy(s['capabilityDecision']['coverage'][0])),'GENERATION_GRAPH_CAPABILITY_DUPLICATE')]:
 s=copy.deepcopy(spec);edit(s);negative('native/'+label,lambda s=s:validator().specification(s),code)
# Original metadata/bytes witness remains valid; each mutation affects one boundary.
for i,(key,record) in enumerate(list(records.items())):
 if i>=5:break
 rs2=copy.deepcopy(records);rs2[key]['bytes']=rs2[key]['bytes']+b' '
 negative('native/actual-artifact-bytes-'+str(i),lambda rs2=rs2:validator(rs2).specification(spec),'GENERATION_GRAPH_ARTIFACT_BYTES_MISMATCH','/contentDigest')
key=spec['authorityModel']['artifact']['artifactId'];rs2=copy.deepcopy(records);rs2[key]['owner']='other-owner'
negative('native/actual-owner',lambda:validator(rs2).specification(spec),'GENERATION_GRAPH_ARTIFACT_OWNER_MISMATCH','/artifactId')
rs2=copy.deepcopy(records);rs2[key]['artifactRef']['provenanceDigest']='sha256:'+'f'*64
negative('native/ledger-reference-provenance',lambda:validator(rs2).specification(spec),'GENERATION_GRAPH_ARTIFACT_LEDGER_MISMATCH','/artifactId')
s=copy.deepcopy(spec);s['authorityModel']['recordDigest']='sha256:'+'f'*64
negative('native/domain-record-digest',lambda:validator().specification(s),'GENERATION_GRAPH_RECORD_DIGEST_MISMATCH','/recordDigest')
# TypedDocument/EvidenceRecord JSON_VALUE slots must honor their actual declared
# schema; generic envelope validity alone would accept these negatives.
for definition,payload_field in [('TypedDocument','document'),('EvidenceRecord','observations')]:
 matching=[(k,r) for k,r in records.items() if r.get('schema') and r['schema']['definition']==definition]
 if not matching:continue
 key,stored=matching[0];ref=copy.deepcopy(stored['artifactRef'])
 v=validator();v.requirementIds={REQ}
 positive('native/'+definition+'/actual-domain-positive',lambda v=v,ref=ref:v.artifact(ref))
 rs2=copy.deepcopy(records);value=source_json(rs2[key]['bytes']);value[payload_field]['syntheticValue']=None;raw=canonical(value)
 rs2[key]['bytes']=raw;rs2[key]['contentDigest']=digest(raw);rs2[key]['artifactRef']['contentDigest']=digest(raw);rs2[key]['artifactRef']['sizeBytes']=len(raw);mutant_ref=copy.deepcopy(rs2[key]['artifactRef']);v=validator(rs2);v.requirementIds={REQ}
 negative('native/'+definition+'/actual-selected-schema-null',lambda v=v,ref=mutant_ref:v.artifact(ref),'GENERATION_GRAPH_TYPED_CONTENT_INVALID','/value/syntheticValue')
# Assert source is actually accepted before deriving each projection rejection.
projection=project_inherited_specification(source_raw,JOB,CHILD,digest(source_raw),repo().registry)
positive('projection/native-child-same-job-shape',lambda:validate({'$ref':GEN+'#/$defs/ApprovedGenerationSpecification'},source_json(projection['bytes']),repo().registry))
positive('projection/exact-all-fields-except-jobId',lambda:True if {k:v for k,v in source_json(projection['bytes']).items() if k!='jobId'}=={k:v for k,v in spec.items() if k!='jobId'} else (_ for _ in ()).throw(AssertionError()))
positive('projection/original-bytes-and-digest-retained',lambda:True if source_raw==canonical(spec) and projection['sourceSpecificationDigest']==digest(source_raw) else (_ for _ in ()).throw(AssertionError()))
positive('projection/creates-no-approval-or-authority',lambda:True if not projection['approvalCreated'] and not projection['executionAuthorityCreated'] else (_ for _ in ()).throw(AssertionError()))
sensitive=copy.deepcopy(spec);sensitive['behavioralRequirements'][0]['statement']='  synthetic exact α\n\t\u0000 tail  '
raw=canonical(sensitive);p=project_inherited_specification(raw,JOB,CHILD,digest(raw),repo().registry)
positive('projection/synthetic-text-exact-no-trim-or-normalization',lambda:True if source_json(p['bytes'])['behavioralRequirements'][0]['statement'].encode()==sensitive['behavioralRequirements'][0]['statement'].encode() else (_ for _ in ()).throw(AssertionError()))
negative('projection/same-job',lambda:project_inherited_specification(source_raw,JOB,JOB,digest(source_raw),repo().registry),'GENERATION_CHILD_JOB_IDENTITY_NOT_DISTINCT','/jobId')
negative('projection/wrong-source-digest',lambda:project_inherited_specification(source_raw,JOB,CHILD,'sha256:'+'f'*64,repo().registry),'GENERATION_CHILD_SOURCE_DIGEST_MISMATCH')
negative('projection/wrong-source-job',lambda:project_inherited_specification(source_raw,CHILD,JOB,digest(source_raw),repo().registry),'GENERATION_CHILD_SOURCE_JOB_MISMATCH','/jobId')
# Invalid stored JSON is tested on the actual accepted native source boundary.
raw=b'{"jobId":"one","jobId":"two"}'
negative('projection/duplicate-actual-json-key',lambda:project_inherited_specification(raw,JOB,CHILD,digest(raw),repo().registry),'GENERATION_BASIS_DUPLICATE_JSON_KEY','/jobId')
raw=source_raw+b' '
negative('projection/noncanonical-source',lambda:project_inherited_specification(raw,JOB,CHILD,digest(raw),repo().registry),'GENERATION_CHILD_SOURCE_NONCANONICAL')
report={'inputCommit':PIN,'ssotSha256':hashlib.sha256(source).hexdigest(),'proofKind':'BOUNDED_NATIVE_REFERENCE_GRAPH_AND_IDENTITY_ONLY_PROJECTION','checkCount':len(checks),'failedCount':sum(not c['passed'] for c in checks),'checks':checks,
 'actualPositiveCoverage':{'artifacts':result['hydratedArtifactCount'],'nativeDomainRecords':result['hydratedRecordCount'],'schemaVectorsExecuted':result['schemaVectorsExecuted'],'requirements':len(spec['behavioralRequirements']),'productionGraphs':0},
 'supportSha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),OUT/'generation_graph_reference.py',OUT/'generation_graph_fixtures.py',OUT/'generation_admission_reference.py',ROOT/'scripts/verify_phase2_handoffs.py']},
 'sourceBindings':{p:rs[p]['sha256'] for p in ['contracts/generation/generation-contracts.schema.json','contracts/generation/domain-record-schema-map.json','contracts/generation/artifact-schema-map.json','contracts/execution/raw-artifact-kinds.json']},
 'unverified':result['unverified'],'readiness':'BLOCKED_FULL_OPERATION_NOT_CLOSED','implementationAcceptance':'NOT_EVALUATED'}
(OUT/'generation-graph-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failed':report['failedCount'],'nativeArtifacts':result['hydratedArtifactCount'],'nativeRecords':result['hydratedRecordCount']}))
for c in checks:
 if not c['passed']:print(json.dumps(c))
sys.exit(1 if report['failedCount'] else 0)
