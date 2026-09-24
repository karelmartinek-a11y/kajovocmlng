"""Capture actual return codes for the Phase 1 handoff. Nonzero stays nonzero."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import subprocess
import sys
from ssot_sources import ROOT, SSOT, load_resource


def main():
    if '--embedded-r9' in sys.argv:
        resource=load_resource('verify_r9.py')
        sys.argv=['verify_r9.py',str(SSOT)]
        exec(compile(resource['raw'],'SSOT:verify_r9.py','exec'),{'__name__':'__main__'})
        return 0
    commands=[
        ['scripts/phase1_schema_closure.py','--baseline'],
        ['scripts/phase1_schema_closure.py'],
        ['scripts/verify_schema_references.py'],
        ['scripts/verify_phase1_contracts.py','--baseline'],
        ['scripts/verify_phase1_contracts.py'],
        ['scripts/phase1_repair_contracts.py','--check'],
        ['scripts/phase1_repair_contracts.py','--verify-from-baseline'],
        ['scripts/run_baseline_gates.py'],
        ['scripts/phase1_run_checks.py','--embedded-r9'],
        ['scripts/project_experience.py','--check'],
        ['scripts/verify_preserved_policy.py'],
        ['scripts/verify_experience.py'],
        ['scripts/build_parity.py'],
        ['scripts/phase1_search_history.py'],
    ]
    previous=[]
    if '--schemas-only' in sys.argv:
        previous=json.loads((ROOT/'audit/generated/phase1-checks.json').read_text(encoding='utf8'))['commands']
        commands=commands[:5]+[['scripts/phase1_search_history.py']]
    def run(args):
        command=[sys.executable,*args]
        try:
            result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8',
                                  errors='replace',env={**os.environ,'PYTHONUTF8':'1'},timeout=1800)
            record={'command':'python '+' '.join(args),'exitCode':result.returncode,
                    'stdout':result.stdout.strip(),'stderr':result.stderr.strip()}
        except subprocess.TimeoutExpired as exc:
            record={'command':'python '+' '.join(args),'exitCode':None,'error':'TIMEOUT: '+str(exc)}
        print(json.dumps({'command':record['command'],'exitCode':record['exitCode']}),flush=True)
        return record
    with ThreadPoolExecutor(max_workers=2) as executor:
        results=list(executor.map(run,commands))
    # Inventory sees the newly regenerated projections and fixtures.
    results.append(run(['scripts/audit_inventory.py']))
    if previous:
        updated={r['command']:r for r in results}
        results=[updated.pop(r['command'],r) for r in previous]+list(updated.values())
    result={'scope':'Actual commands; failing closure/negative probes remain failing.',
            'ssotSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'commands':results,
            'nonzeroCommands':sum(r['exitCode']!=0 for r in results)}
    (ROOT/'audit/generated/phase1-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'nonzeroCommands':result['nonzeroCommands']}))
    return int(bool(result['nonzeroCommands']))


if __name__=='__main__':sys.exit(main())
