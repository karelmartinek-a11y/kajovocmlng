from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path('scripts').resolve()))
from ssot_sources import resource_index,SSOT
out=Path('audit/generated/resume-d362/sql-lifecycle'); resources=resource_index()
names=['closure/contracts/operation-payloads.json','closure/contracts/operation-overlay.json','database/operation-functions.sql']
bindings={n:resources[n]['sha256'] for n in names}
payload=json.loads(resources[names[0]]['raw']);overlay=json.loads(resources[names[1]]['raw'])
fields={('owner.mfa.reset','enrollmentState'):{'type':'string','const':'ENROLLMENT_REQUIRED'},('chat.turn.steer','checkpointDisposition'):{'type':'string','const':'STEERING_COMMITTED'},('acceptance.run.start','state'):{'type':'string','const':'QUEUED'},('acceptance.run.cancel','state'):{'type':'string','enum':['CANCEL_REQUESTED','RECONCILING','MANUAL_REVIEW','CANCELLED']},('acceptance.run.cancel','cleanupStatus'):{'type':'string','enum':['PENDING','COMPLETE','FAILED']},('acceptance.run.cancel','reconciliationStatus'):{'type':'string','enum':['PENDING','COMPLETE','UNKNOWN','MANUAL_REVIEW']}}
patch=[]
for i,r in enumerate(payload['records']):
 for (op,field),mask in fields.items():
  if r['operationId']==op:
   patch.append({'op':'replace','path':f'/records/{i}/responseSchema/properties/{field}','value':mask,'operationId':op,'oldValue':r['responseSchema']['properties'][field]})
(out/'field-patch.json').write_text(json.dumps({'sourceHead':'d362487999bd795d4723c2a930e93fc7aa8aa295','sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'resourceBindings':bindings,'resource':names[0],'patch':patch},indent=2)+'\n')
(out/'operation-overlay.json').write_text(json.dumps([r for r in overlay['operations'] if r['operationId'] in {x[0] for x in fields}],indent=2)+'\n')
(out/'operation-functions.sql').write_bytes(resources[names[2]]['raw'])
