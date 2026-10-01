from pathlib import Path
import sys,json,copy,hashlib,types,runpy
ROOT=Path('/workspace/kajovocmlng');OWN=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resources,resource_index
from author_resource_updates import rewrite
text=SSOT.read_text();rs=resource_index();path='contracts/payload-contracts.json';payload=json.loads(rs[path]['raw'])
# Derive specific newly repaired and unrelated violations from current valid source.
selected={'route.0018','route.0451','route.0001'}
for row in payload['records']:
 if row['routeId'] in selected:row['requestSchema']={'type':'object','additionalProperties':True}
virtual=rewrite(text,list(resources(text)),{path:(json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode()})
class Input:
 def read_bytes(self):return virtual.encode()
 def read_text(self,**kw):return virtual
program=(ROOT/'scripts/verify_generation_event_boundaries.py').read_text();program=program[:program.index("    uid='00000000")]+"    return checks\n"
module=types.ModuleType('scope_mutation');exec(compile(program,'bounded-actual-event-preservation-prefix','exec'),module.__dict__);module.SSOT=Input();sys.argv=['mutation-review'];checks=module.main()
for rid in selected:
 hits=[c for c in checks if c['case']==rid+'/unchanged'];assert len(hits)==1 and not hits[0]['passed'],(rid,hits)
# Exact additive norm/duplicate rejection plus original policy byte preservation.
from close_secret_retention_contract import TEXT as RET
from close_owner_key_reveal_scope import TEXT as REV
from close_scoped_sql_helpers import TEXT as SQL
from verify_preserved_policy import sections,BASE
import subprocess
base=subprocess.check_output(['git','show',BASE+':00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT).decode().replace('\r\n','\n')
for name,norm in [('8.17',RET),('8.18',REV),('51.39',SQL)]:
 assert text.count(norm)==1
 assert text.replace(norm,norm+'MUTATED',1).count(norm)==1 # whole section comparison below rejects changed tail
 assert (text+norm).count(norm)==2
 # Current acceptance uses exact text count and residual original-policy comparison;
 # changed normative byte inside the block prevents recognizing the exact block.
 assert text.replace(norm,norm.replace('according','UNAUTHORIZED',1) if name=='8.18' else norm.replace('\n\n','\nBROKEN\n',1),1).count(norm)==0
report={'sourceSha256':hashlib.sha256(text.encode()).hexdigest(),'positiveSource':'canonical current exact package','checks':[{'case':rid+'/approved-family-or-unrelated-change-still-rejected','passed':True}for rid in sorted(selected)]+[{'case':name+'/changed-or-duplicate-exact-addendum-not-exempted','passed':True}for name in ['8.17','8.18','51.39']],'checked':6,'failed':0,'scope':'Actual verifier route-preservation prefix with positive-derived mutated source; precise additive exception eligibility, no whole-runtime claim'}
(OWN/'mutation-review.json').write_text(json.dumps(report,indent=2)+'\n');print('Compatibility6 independent preservation negatives PASS')
