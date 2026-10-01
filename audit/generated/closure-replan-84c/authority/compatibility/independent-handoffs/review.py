from pathlib import Path
import sys,os,json,copy,hashlib,importlib
ROOT=Path('/workspace/kajovocmlng');OWN=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT
source=hashlib.sha256(SSOT.read_bytes()).hexdigest();g=importlib.import_module('verify_generation_chain_handoffs');p=importlib.import_module('verify_producer_archive_handoffs');cases=[]
def run(m,label,file):
 out=OWN/label;os.environ['KCML_AUDIT_OUTPUT']=str(out);code=m.main();q=json.loads((out/file).read_text());return code,q
code,q=run(g,'generation-positive','generation-chain-tests.json');assert code==0 and q['checked']==21;cases.append({'case':'generation-original14-plus7-bindings-positive','passed':True})
original=g.PROOF;w=json.loads((ROOT/original).read_text());target=next(iter(w['supportSha256']))
for label,change,expected in [('corrupt-support',lambda q:q['supportSha256'].__setitem__(target,'0'*64),'consumed-support:'+target),('missing-support-map',lambda q:q.pop('supportSha256'),'all-named-consumed-support')]:
 v=copy.deepcopy(w);change(v);f=OWN/(label+'.json');f.write_text(json.dumps(v,indent=2)+'\n');g.PROOF=str(f.relative_to(ROOT));code,q=run(g,label,'generation-chain-tests.json');fails={c['case']for c in q['checks']if not c['passed']};assert code==1 and q['status']=='BLOCKED'and expected in fails;cases.append({'case':label,'passed':True,'requiredDiagnostic':expected})
g.PROOF=original
code,q=run(p,'producer-positive','producer-archive-chain-tests.json');assert code==0 and q['checked']==123;cases.append({'case':'producer-complete8-current-positive','passed':True})
mapfile=ROOT/p.PROOF_MAPPING;mapping=json.loads(mapfile.read_text());assert set(mapping)=={'joined','retry','archive','aad','secret','ui','preroot','retry-stage'}
for label,name in mapping.items():
 report=json.loads((ROOT/name).read_text());assert report.get('sourceDocumentSha256',report.get('sourceSha256'))==source
cases.append({'case':'all8-proof-labels-same-116e','passed':True})
# Simulate selected map becoming unavailable between module import and main,
# without touching the shared file read by the coordinator's final runner.
oldexists=Path.exists
Path.exists=lambda self:False if self==mapfile else oldexists(self)
try:code,q=run(p,'missing-selected-map-after-import','producer-archive-chain-tests.json')
finally:Path.exists=oldexists
cases.append({'case':'missing-selected-map-after-import','passed':code==1 and q['status']=='BLOCKED','actualStatus':q['status'],'actualExit':code,'finding':'A selected evidence mapping must remain available at execution, not only import time.'})
assert source==hashlib.sha256(SSOT.read_bytes()).hexdigest()
(OWN/'independent-review.json').write_text(json.dumps({'sourceSha256':source,'cases':cases,'checked':len(cases),'failed':sum(not c['passed']for c in cases),'proofMappingSha256':hashlib.sha256(mapfile.read_bytes()).hexdigest(),'wholeOperationClosed':False,'implementationAcceptance':'NOT_EVALUATED'},indent=2)+'\n');print(json.dumps(cases[-1]))
