"""Actual native ArtifactResolver authority handoff against the actual pinned native map."""
import copy,json,sys,types
from generation_admission_fixtures import *
module=types.ModuleType('generation_admission_native_control');sys.modules[module.__name__]=module
exec(compile(rs['scripts/ssot/ssot_control.py']['raw'],'SSOT:scripts/ssot/ssot_control.py','exec'),module.__dict__)
class FrozenInput:
 def read_bytes(self):return source
native=module.Document(FrozenInput())
ref=spec['authorityModel'];root=OUT/'authority-artifact-fixture';root.mkdir(exist_ok=True)
(root/ref['artifact']['path']).write_bytes(records[NATIVE_AUTHORITY]['bytes'])
checks=[]
def positive(name,fn):
 try:result=fn();checks.append({'case':name,'passed':result==native_authority})
 except Exception as e:checks.append({'case':name,'passed':False,'unexpected':type(e).__name__+':'+str(e)})
def reject(name,fn,code,pointer):
 try:fn();checks.append({'case':name,'passed':False,'actual':'ACCEPTED'})
 except module.ContractFailure as e:checks.append({'case':name,'passed':e.code==code and e.pointer==pointer,'actualCode':e.code,'actualPointer':e.pointer,'expectedCode':code,'expectedPointer':pointer})
 except Exception as e:checks.append({'case':name,'passed':False,'unexpected':type(e).__name__+':'+str(e)})
def resolver(reference):return module.ArtifactResolver(native,root,{reference['artifact']['artifactId']:reference['artifact']})
assert native.kind_to_schema['GENERATION_AUTHORITY']=='GenerationAuthority'
positive('native/pinned-map-hydrates-actual-authority-bytes',lambda:resolver(ref).record(ref))
del native.kind_to_schema['GENERATION_AUTHORITY']
reject('native/required-map-entry-mutation-rejected',lambda:resolver(ref).record(ref),'CONTRACT_PACK_REFERENCE_INVALID','/kind')
native.kind_to_schema['GENERATION_AUTHORITY']='GenerationAuthority'
r=copy.deepcopy(ref);r['artifact']['kind']='APPROVED_SPECIFICATION'
reject('native/wrong-kind',lambda:resolver(r).record(r),'CONTRACT_PACK_REFERENCE_INVALID','/schema')
r=copy.deepcopy(ref);r['artifact']['sizeBytes']+=1
reject('native/wrong-byte-size',lambda:resolver(r).record(r),'ARTIFACT_VALIDATION_FAILED','/contentDigest')
r=copy.deepcopy(ref);r['recordDigest']='sha256:'+'f'*64
reject('native/wrong-domain-record-digest',lambda:resolver(r).record(r),'CONTRACT_PACK_DRIFT','/recordDigest')
report={'inputCommit':PIN,'ssotSha256':hashlib.sha256(source).hexdigest(),'proofKind':'ACTUAL_EMBEDDED_RESOLVER_SYNTHETIC_NATIVE_BYTES',
 'mapChanged':False,'artifactMapBaseSha256':rs['contracts/generation/artifact-schema-map.json']['sha256'],
 'checks':checks,'checkCount':len(checks),'failedCount':sum(not c['passed'] for c in checks),'productionAcceptance':'NOT_EVALUATED',
 'sourceBindings':{'control':rs['scripts/ssot/ssot_control.py']['sha256'],'domainRecordMap':rs['contracts/generation/domain-record-schema-map.json']['sha256'],'schemaBundle':rs['contracts/generation/generation-contracts.schema.json']['sha256']},
 'scope':'Actual existing GENERATION_AUTHORITY map entry and native domain record hydration. No SQL/publisher/runtime claim.'}
(OUT/'native-authority-handoff-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failed':report['failedCount']}))
for c in checks:
 if not c['passed']:print(json.dumps(c))
sys.exit(1 if report['failedCount'] else 0)
