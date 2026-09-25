"""Record focused checks and current matrix against continuation input 897da64."""
import hashlib
import json
import os
import subprocess
import sys
import time
from ssot_sources import ROOT,SSOT,resource_index,resources

def main():
    raw=SSOT.read_bytes();source=hashlib.sha256(raw).hexdigest()
    out=ROOT/'audit/generated/continuation-897da64/generation-domain';out.mkdir(parents=True,exist_ok=True)
    commands=[(['scripts/verify_generation_domain_payloads.py','--baseline'],1),
              (['scripts/verify_generation_domain_payloads.py'],0),
              (['scripts/close_generation_domain_payloads.py','--check'],0),
              (['scripts/verify_portable_manifests.py'],0),
              (['scripts/verify_native_manifest_continuation.py'],0),
              (['scripts/verify_saga_handoffs.py'],0),
              (['scripts/verify_generation_operation_masks.py'],0),
              (['scripts/verify_route_guard_counters.py'],0),
              (['scripts/project_experience.py','--check'],0),
              (['scripts/investigate_missing_operation_masks.py'],0)]
    rs=resource_index(resources(raw.decode()))
    report={'baselineCommit':'897da64','sourceSha256':source,'scope':__doc__,
            'resourceVersions':{p:r['sha256'] for p,r in rs.items()},
            'baselineCounts':{'unresolvedOperationReferences':250,'operationsWithUnresolvedReferences':125,'genericRoutes':505},
            'commands':[],'allCommandsFinished':False,'packageStatus':'BLOCKED'}
    for args,expected in commands:
        print('RUN '+' '.join(args),flush=True);started=time.monotonic()
        result=subprocess.run([sys.executable,*args],cwd=ROOT,text=True,capture_output=True,encoding='utf8',errors='replace',
            env={**os.environ,'PYTHONUTF8':'1','KCML_AUDIT_OUTPUT':out.relative_to(ROOT).as_posix()})
        report['commands'].append({'command':'python '+' '.join(args),'exitCode':result.returncode,'expectedExitCode':expected,
            'sourceSha256':source,'inputCommit':'897da64' if '--baseline' in args else None,
            'scriptSha256':hashlib.sha256((ROOT/args[0]).read_bytes()).hexdigest(),
            'seconds':round(time.monotonic()-started,3),'stdout':result.stdout,'stderr':result.stderr})
        (out/'commands.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
        print('EXIT '+str(result.returncode),flush=True)
        if SSOT.read_bytes()!=raw:raise ValueError('Input changed during group tests')
    report['allCommandsFinished']=True
    matrix=json.loads((out/'current-operation-schema-matrix.json').read_text(encoding='utf8'))
    report['currentSummary']=matrix['summary'];report['delta']={k:matrix['summary'][k]-v for k,v in report['baselineCounts'].items()}
    (out/'commands.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({'sourceSha256':source,'delta':report['delta']}))
    return int(any(c['exitCode']!=c['expectedExitCode'] for c in report['commands']))

if __name__=='__main__':raise SystemExit(main())
