from pathlib import Path
import sys,json,hashlib
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
from owner_session_family_contracts import contracts
package=contracts(resource_index());package['sourceSha256']=hashlib.sha256(SSOT.read_bytes()).hexdigest()
(OUT/'operation-mask-delta.json').write_text(json.dumps(package,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'operations':len(package['operations']),'boundaries':6,'wholeClosed':0}))
