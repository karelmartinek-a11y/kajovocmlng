"""Read-only bounded evidence reuse, not activation of OWNER UI exposures."""
import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;OLD=ROOT/'audit/generated/resume-d362/consumers';sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((OLD/'owner-ui-native-contract-tests.json').read_text());bindings=json.loads((OLD/'third-wave-bindings.json').read_text());rs=resource_index();checks=[]
for name,expected in report['supportingFiles'].items():checks.append({'file':str((OLD/name).relative_to(ROOT)),'same':sha(OLD/name)==expected})
checks.append({'resource':'contracts/generation/generation-contracts.schema.json','same':rs['contracts/generation/generation-contracts.schema.json']['sha256']==bindings['consumedResourceSHA256']['contracts/generation/generation-contracts.schema.json']})
prior=json.loads((OLD/'native-evidence-reuse-after-role-fix.json').read_text());checks.append({'report':'owner-ui-native-contract-tests.json','same':sha(OLD/'owner-ui-native-contract-tests.json')==prior['reportSHA256']})
assert all(x['same']for x in checks),checks
result={'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'status':'VALID_FOR_SAME_BOUNDED_NATIVE_SCOPE','reusedChecks':report['checks'],'inputChecks':checks,'oldReport':str((OLD/'owner-ui-native-contract-tests.json').relative_to(ROOT)),'oldReportSha256':sha(OLD/'owner-ui-native-contract-tests.json'),'wholeExposuresClosed':0,'newExecution':False,'scope':'Actual native HTTP/worker-mask/typed success/error/event reference relationship checks only. Neither production authentication nor protected storage/root/worker publication/read SQL proved. Visual96/128 not rerun because renderer/view sources unchanged.'}
(HERE/'ui-native-evidence-reuse.json').write_text(json.dumps(result,indent=2)+'\n');print('Native',report['checks'],'bounded checks validly reused')
