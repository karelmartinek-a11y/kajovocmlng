from pathlib import Path
import json,hashlib
HERE=Path(__file__).parent
source=(HERE/'verify_scoped_generation_links.py').read_text().split("test('generation-full-positive",1)[0]
g={'__file__':str(HERE/'verify_locator_initial_scope_review.py')};exec(compile(source,'own disposable final SQL fixture','exec'),g)
base=g['base'];g['test']('actual-joined-positive',base)
for name,before,after in [('foreign-caller',g['ns']['owner'],'99999999-9999-4999-8999-999999999999'),('wrong-family',"'GENERATION'","'CONFIG'"),('wrong-authority',"'OWNER_FULL'","'INTERNAL'"),('wrong-business-target',"'generation_job'","'another_target'"),('wrong-frozen-revision',g['ns']['b'](g['ns']['scope']),g['ns']['b'](bytes(32)))]:
 wrong=base.copy();wrong['locator']=wrong['locator'].replace(before,after);g['test']('locator-'+name,wrong,'GENERATION_CREATE_ATOMIC_CLOSURE_INCOMPLETE')
report={'scope':'Independent initial-commit exact stable locator scope joins in current full foundations; distinct from postcommit immutability.','checks':g['cases'],'failed':sum(not c['passed']for c in g['cases']),'eventsSha256':hashlib.sha256((HERE.parent/'events/generation-event-storage-proposed.sql').read_bytes()).hexdigest(),'wholeOperationClosed':False}
(HERE/'locator-initial-scope-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(g['cases']),'failed':report['failed']}))
