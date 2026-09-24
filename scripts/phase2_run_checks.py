"""Run existing checks in an isolated projection; preserve Phase 1 evidence."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from ssot_sources import ROOT, SSOT, resource_index, resources

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--entry',action='store_true'); args=parser.parse_args()
    text=(ROOT/'.cache/phase2-entry/SSOT.md').read_text(encoding='utf8') if args.entry else SSOT.read_text(encoding='utf8')
    rs=resource_index(resources(text))
    directory=Path(tempfile.mkdtemp(prefix='checks-',dir=ROOT/'.cache'))
    shutil.copytree(ROOT/'scripts',directory/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
    (directory/'00_SSOT').mkdir(); (directory/'00_SSOT/KajovoCMLNG_SSOT.md').write_text(text,encoding='utf8',newline='\n')
    (directory/'audit/generated').mkdir(parents=True)
    jobs=[['scripts/verify_schema_references.py'],['scripts/verify_phase1_contracts.py'],['scripts/run_baseline_gates.py']]
    for name in ['r11/scripts/verify_r11.py','scripts/ssot/ssot_control.py']:
        path=directory/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(rs[name]['raw'])
        jobs.append([name,'00_SSOT/KajovoCMLNG_SSOT.md']+(['--check'] if name.endswith('ssot_control.py') else []))
    checks=[]
    for job in jobs:
        result=subprocess.run([sys.executable,*job],cwd=directory,capture_output=True,text=True,encoding='utf8',errors='replace')
        checks.append({'command':'python '+' '.join(job),'exitCode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        print(json.dumps({'command':job[0],'exitCode':result.returncode}),flush=True)
    artifacts={p.name:json.loads(p.read_text(encoding='utf8')) for p in (directory/'audit/generated').glob('*.json')}
    suffix='before' if args.entry else 'after'
    (ROOT/f'audit/generated/phase2-checks-{suffix}.json').write_text(json.dumps({'checks':checks,'artifacts':artifacts},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return int(any(c['exitCode'] for c in checks))

from pathlib import Path
if __name__=='__main__':
    raise SystemExit(main())
