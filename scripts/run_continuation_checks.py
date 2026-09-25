"""Record scoped continuation checks without overwriting the 997e835 evidence."""
import hashlib
import json
import os
import subprocess
import sys
import time

from ssot_sources import ROOT, SSOT, resource_index, resources


def main():
    raw = SSOT.read_bytes()
    ssot_hash = hashlib.sha256(raw).hexdigest()
    output = ROOT/'audit/generated/continuation-997e835'
    output.mkdir(parents=True,exist_ok=True)
    original = resource_index(resources(subprocess.check_output([
        'git','show','997e835:00_SSOT/KajovoCMLNG_SSOT.md']).decode()))
    current = resource_index(resources(raw.decode()))
    changed = [{'path':p,'beforeSha256':original[p]['sha256'],'afterSha256':r['sha256']}
               for p,r in current.items() if r['sha256']!=original[p]['sha256']]
    commands = [(['scripts/verify_saga_handoffs.py','--baseline'],1),
                (['scripts/verify_saga_handoffs.py'],0),
                (['scripts/close_generation_operation_masks.py','--check'],0),
                (['scripts/verify_generation_operation_masks.py'],0),
                (['scripts/project_experience.py','--check'],0),
                (['scripts/investigate_missing_operation_masks.py'],0)]
    report = {'baselineCommit':'997e835','sourceSha256':ssot_hash,
              'scope':__doc__,'changedResources':changed,'commands':[],
              'baselineCounts':{'unresolvedOperationReferences':252,
                                'operationsWithUnresolvedReferences':126,'genericRoutes':505},
              'allCommandsFinished':False,'packageStatus':'BLOCKED'}
    for args,expected in commands:
        print('RUN '+' '.join(args),flush=True)
        started=time.monotonic()
        result=subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,text=True,encoding='utf8',
            errors='replace',env={**os.environ,'PYTHONUTF8':'1','KCML_AUDIT_OUTPUT':output.relative_to(ROOT).as_posix()})
        report['commands'].append({'command':'python '+' '.join(args),'exitCode':result.returncode,
            'expectedExitCode':expected,'durationSeconds':round(time.monotonic()-started,3),
            'currentSsotSha256':ssot_hash,'inputCommit':'997e835' if '--baseline' in args else None,
            'scriptSha256':hashlib.sha256((ROOT/args[0]).read_bytes()).hexdigest(),
            'stdout':result.stdout,'stderr':result.stderr})
        (output/'commands.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print('EXIT '+str(result.returncode)+' '+args[0],flush=True)
        if SSOT.read_bytes()!=raw:raise ValueError('SSOT changed during tests')
    report['allCommandsFinished']=True
    matrix=json.loads((output/'current-operation-schema-matrix.json').read_text(encoding='utf8'))
    report['currentSummary']=matrix['summary']
    report['delta']={k:matrix['summary'][k]-v for k,v in report['baselineCounts'].items()}
    (output/'commands.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'sourceSha256':ssot_hash,'delta':report['delta']}))
    return int(any(r['exitCode']!=r['expectedExitCode'] for r in report['commands']))


if __name__=='__main__':
    raise SystemExit(main())
