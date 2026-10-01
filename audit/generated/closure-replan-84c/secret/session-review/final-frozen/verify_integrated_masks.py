from pathlib import Path
import sys,json,hashlib
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
source=SSOT.read_bytes();r=resource_index();expected=json.loads((OUT/'operation-mask-delta.json').read_text());payload=json.loads(r['contracts/payload-contracts.json']['raw']);catalog=json.loads(r['contracts/operation-contracts.json']['raw']);checks=[]
def check(i,b):checks.append({'id':i,'status':'PASS'if b else'FAIL'})
for op in expected['operations']:
 row=next(x for x in payload['records']if x['operationId']==op['operationId'])
 for field in ['requestSchema','responseSchema','eventSchema']:check('integrated-exact-boundary/'+op['operationId']+'/'+field,row[field]==op[field])
 check('integrated-event-applicability/'+op['operationId'],row['eventApplicability']==('NOT_APPLICABLE'if op['operationId'].endswith('list')else'AGGREGATE_STREAM'))
 for role,field in [('command','requestSchema'),('response','responseSchema'),('event','eventSchema')]:
  schema=dict(op[field]);schema['$id']='urn:kcml:r9:operation:'+op['operationId']+':'+role;check('integrated-native-registry/'+op['operationId']+'/'+role,catalog['$defs'][op['operationId']+':'+role]==schema)
profile=json.loads(r['contracts/owner-session-family.json']['raw']);check('boundary-only-publication-status',profile['publicationStatus']=='COORDINATOR_REVIEWED_BOUNDARY_DEFINITIONS');check('shared-obligations-remain-open',all(x['status']=='OPEN'for x in profile['sharedObligations']))
schema=json.loads(r['contracts/owner-session-family.schema.json']['raw']);check('separate-exact-admission-no-command-mask',schema['$defs']['AdmissionFailure']==expected['admissionFailureSchema'])
for name in ['contracts/owner-session-family.json','contracts/owner-session-family.schema.json','closure/contracts/owner-session-family-map.json','contracts/payload-contracts.json','contracts/operation-contracts.json']:check('actual-projection-byte-equality/'+name,(ROOT/'01_UI_CONTRACT'/name).read_bytes()==r[name]['raw'])
assert source==SSOT.read_bytes();report={'sourceSha256':hashlib.sha256(source).hexdigest(),'sourceUnchanged':True,'packageSha256':hashlib.sha256((OUT/'operation-mask-delta.json').read_bytes()).hexdigest(),'checked':len(checks),'failed':sum(x['status']=='FAIL'for x in checks),'checks':checks,'consumedSourceDigests':{name:r[name]['sha256']for name in ['contracts/payload-contracts.json','contracts/operation-contracts.json','contracts/owner-session-family.json','contracts/owner-session-family.schema.json','closure/contracts/owner-session-family-map.json']},'scope':'Actual integrated source/projection/native-registry exact equality to independently reviewed boundary package; no app runtime or whole operation proof','wholeOperationsClosed':0,'implementationAcceptance':'NOT_EVALUATED'};(OUT/'integrated-masks-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':len(checks),'failed':report['failed']}));raise SystemExit(report['failed']!=0)
