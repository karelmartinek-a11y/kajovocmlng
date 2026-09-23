"""Boundary fixtures for the approved retry contract, not a runtime scheduler."""
import hashlib
import json
import sys
from ssot_sources import ROOT, load_resource


def run():
    contract = json.loads(load_resource('ui/contracts/error-presentation.json')['raw'])
    policy = contract['defaultRetryProfile']
    checks=[]
    def check(name, condition):
        checks.append({'id':name,'status':'PASS' if condition else 'FAIL'})
    def eligible(index, deadline=100000, retry_after=0, authorized=True, effect_known=True,
                 same_input=True, human=False, cancelled=False):
        if not authorized or not effect_known or not same_input or human or cancelled:
            return None
        if index < 0 or index >= policy['maxRetries']:
            return None
        seed='fixture-run-001'
        jitter=int.from_bytes(hashlib.sha256((seed+':'+str(index)).encode()).digest()[:8],'big') % (policy['jitterMaxMs']+1)
        at=max(1000+policy['retryDelaysMs'][index]+jitter, retry_after)
        return at if at < deadline else None
    check('profile.exact-approved-bounds',policy['maxRetries']==3 and policy['maxAttempts']==4 and policy['retryDelaysMs']==[500,1000,2000] and policy['jitterMaxMs']==250)
    check('retry.three-retries-only',all(eligible(i) is not None for i in range(3)) and eligible(3) is None)
    check('retry.fixed-seed-golden-vector',[eligible(i) for i in range(3)]==[1565,2024,3225])
    check('retry.provider-lower-bound',eligible(0,retry_after=5000)==5000)
    check('retry.exact-deadline-rejected',eligible(0,deadline=5000,retry_after=5000) is None)
    for guard,kwargs in [('no-authority',{'authorized':False}),('unknown-effect',{'effect_known':False}),
                         ('changed-input',{'same_input':False}),('human-intervention',{'human':True}),
                         ('cancelled',{'cancelled':True})]:
        check('retry.denies-'+guard,eligible(0,**kwargs) is None)
    check('fallback.no-retry',contract['fallback']['automatic_retry_policy']['mode']=='DO_NOT_RETRY')
    result={'scope':'Contract boundary reference fixtures; no scheduler implementation or external operation executed.', 'checks':checks}
    (ROOT/'audit/generated/retry-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    report=run();print(json.dumps(report));sys.exit(any(c['status']=='FAIL' for c in report['checks']))
