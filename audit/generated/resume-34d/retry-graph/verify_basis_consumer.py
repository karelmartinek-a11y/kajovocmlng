from graph_current_fixtures import *
from generation_basis_consumer import consume_inherited_basis
from ssot_sources import SSOT
checks=[]
SID='00000000-0000-4000-8000-000000000901'
def factory(kind='RETRY'):
 r=repo();r.records[SID]={'recordId':SID,'jobId':JOB,'owner':'synthetic-owner','bytes':source_raw,'contentDigest':digest(source_raw),'schema':address('ApprovedGenerationSpecification')}
 frozen=[{'recordId':SID,'contentDigest':digest(source_raw),'schema':address('ApprovedGenerationSpecification')}]
 b={'kind':kind,'generationBasis':{'approvedRevisionId':SID,'expectedSpecificationDigest':digest(source_raw)}}
 if kind=='RETRY':b['parentJobId']=JOB
 return b,r,frozen

def run(f):return consume_inherited_basis(f[0],f[1],domain_map,raw_kinds,CHILD,f[2],[gb])
def pos(name,f):
 try:
  result=run(f);checks.append({'case':name,'passed':result['graph']['hydratedArtifactCount']==43 and result['dispatchPermitted']is False and result['approvalCreated']is False and source_json(result['childSpecificationBytes'])['jobId']==CHILD})
 except Exception as e:checks.append({'case':name,'passed':False,'unexpected':str(e)})
def neg(name,f,expected):
 try:run(f);checks.append({'case':name,'passed':False,'actual':'ACCEPTED'})
 except ContractFailure as e:checks.append({'case':name,'passed':e.code==expected,'actual':e.code,'expected':expected})
for kind in ['RETRY','REPAIR']:pos(kind+'/native-source-graph-child-local-hydration',factory(kind))
f=factory();f[2].append(copy.deepcopy(f[2][0]));neg('duplicate-frozen-identity',f,'GENERATION_CONSUMER_FROZEN_IDENTITY_DUPLICATE')
f=factory();f[1].records[SID]['bytes']+=b' ';neg('actual-source-bytes-tamper',f,'GENERATION_BASIS_BYTES_DIGEST_MISMATCH')
f=factory();f[2][0]['contentDigest']='sha256:'+'f'*64;neg('frozen-digest-conflict',f,'GENERATION_CONSUMER_FROZEN_SOURCE_DRIFT')
f=factory();f[0]['parentJobId']=CHILD;neg('wrong-source-job',f,'GENERATION_CONSUMER_SOURCE_JOB_MISMATCH')
f=factory();f[0]['generationBasis']['approvedRevisionId']=CHILD;neg('source-not-frozen',f,'GENERATION_CONSUMER_SOURCE_NOT_FROZEN')
f=factory();key=f[1].records[SID]['recordId'];f[1].records.pop(key);neg('source-missing',f,'GENERATION_CONSUMER_FROZEN_BYTES_UNAVAILABLE')
# Full graph may remain byte-schema-valid while its exact dependency DAG cycles.
f=factory();doc=source_json(source_raw);doc['behavioralRequirements'][0]['dependsOn']=[REQ];newraw=canonical(doc);f[1].records[SID]['bytes']=newraw;f[1].records[SID]['contentDigest']=digest(newraw);f[0]['generationBasis']['expectedSpecificationDigest']=digest(newraw);f[2][0]['contentDigest']=digest(newraw);neg('actual-native-graph-self-cycle',f,'GENERATION_GRAPH_REQUIREMENT_CYCLE')
report={'inputCommit':PIN,'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'checks':checks,'checkCount':len(checks),'failedCount':sum(not c['passed']for c in checks),'wholeOperationClosed':False,'scope':'Actual native approved source graph hydratation to child-local specification for RETRY/REPAIR. UPDATE needs authoritative target revision→source spec join; no caller assertion supplied as that join. No OWNER approval or dispatch authority is created. Raw future code remains explicit DesignArtifactExpectation.','remaining':['Source/delegation/Secret-use predicates and actual monitoring→repair classification not executed by generic graph validation','Graph rule/verification obligation declaration closure and producer archive need own exact contracts','UPDATE immutable target revision→actual source specification producer join remains mandatory'],'supportSha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),OUT/'generation_basis_consumer.py',OUT/'generation_graph_current.py',OUT/'graph_current_fixtures.py',ROOT/'scripts/generation_admission_contracts.py']}}
(OUT/'basis-consumer-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':report['checkCount'],'failed':report['failedCount']}));sys.exit(bool(report['failedCount']))
