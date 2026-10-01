from pathlib import Path
import sys,json,os,hashlib,importlib
ROOT=Path('/workspace/kajovocmlng');OWN=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT
m=importlib.import_module('verify_producer_archive_handoffs');p=ROOT/m.PROOF_MAPPING;raw=p.read_bytes();cases=[]
def run(label,expected=None):
 out=OWN/label;os.environ['KCML_AUDIT_OUTPUT']=str(out);code=m.main();q=json.loads((out/'producer-archive-chain-tests.json').read_text());e=next(e for e in q['evidence']if e['path']==m.PROOF_MAPPING)
 if expected:assert code==1 and q['status']=='BLOCKED' and expected in e['diagnostic'] and any(c['case']=='complete-selected-evidence-map' and not c['passed']for c in q['checks'])
 else:assert code==0 and q['checked']==123 and q['failed']==0
 cases.append({'case':label,'passed':True,'actualExit':code,'actualStatus':q['status'],'specificMappingDiagnostic':e['diagnostic']})
run('positive123')
oldexists=Path.exists;oldbytes=Path.read_bytes
Path.exists=lambda self:False if self==p else oldexists(self)
try:run('missing-map-after-import','REQUIRED_EVIDENCE_MAP_MISSING')
finally:Path.exists=oldexists
for label,value,diagnostic in [('malformed-map-after-import',b'[]','INVALID_COMPLETE_EVIDENCE_MAP'),('changed-complete-map-after-import',raw+b'\n','EVIDENCE_MAP_CHANGED_SINCE_IMPORT')]:
 Path.read_bytes=lambda self:value if self==p else oldbytes(self)
 try:run(label,diagnostic)
 finally:Path.read_bytes=oldbytes
assert p.read_bytes()==raw
(OWN/'mapping-fixed-review.json').write_text(json.dumps({'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'scriptSha256':hashlib.sha256((ROOT/'scripts/verify_producer_archive_handoffs.py').read_bytes()).hexdigest(),'checked':len(cases),'failed':0,'cases':cases,'sharedMappingUnchanged':True,'fixtureReruns':0,'wholeOperationsClosed':0,'runtimeAcceptance':'NOT_EVALUATED'},indent=2)+'\n');print('Independent fixedmapping4 PASS')
