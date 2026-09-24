"""Run relevant Phase 1/2/3 checks in an isolated projection without rewriting their evidence."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ssot_sources import ROOT, SSOT, resource_index, resources


def run():
    rs = resource_index()
    temp = Path(tempfile.mkdtemp(prefix='phase3-checks-', dir=ROOT/'.cache'))
    shutil.copytree(ROOT/'scripts', temp/'scripts', ignore=shutil.ignore_patterns('__pycache__'))
    (temp/'00_SSOT').mkdir()
    shutil.copy2(SSOT, temp/'00_SSOT/KajovoCMLNG_SSOT.md')
    shutil.copytree(ROOT/'01_UI_CONTRACT', temp/'01_UI_CONTRACT')
    shutil.copytree(ROOT/'audit', temp/'audit', ignore=shutil.ignore_patterns('generated'))
    (temp/'audit/generated').mkdir(parents=True, exist_ok=True)
    (temp/'.cache').mkdir(exist_ok=True)
    # The following executable validators are authoritative embedded resources.
    for name in ('r11/scripts/verify_r11.py', 'scripts/ssot/ssot_control.py', 'scripts/ssot/audit_checks.py'):
        target = temp/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(rs[name]['raw'])
    jobs = [
        ['scripts/verify_schema_references.py'],
        ['scripts/verify_phase1_contracts.py'],
        ['scripts/phase1_repair_contracts.py', '--check'],
        ['scripts/phase2_repair_handoffs.py', '--check'],
        ['scripts/verify_phase2_handoffs.py'],
        ['scripts/project_experience.py', '--check'],
        ['scripts/verify_experience.py'],
        ['scripts/verify_observability.py'],
        ['scripts/phase2_handoff_closure.py', '--check'],
        ['r11/scripts/verify_r11.py', '00_SSOT/KajovoCMLNG_SSOT.md'],
        ['scripts/ssot/ssot_control.py', '00_SSOT/KajovoCMLNG_SSOT.md', '--check'],
        ['scripts/verify_phase3_semantics.py'],
    ]
    results = []
    for job in jobs:
        process = subprocess.run([sys.executable, *job], cwd=temp, capture_output=True,
            text=True, encoding='utf-8', errors='replace', timeout=1800)
        row = {'command': 'python '+' '.join(job), 'exitCode': process.returncode,
               'stdout': process.stdout.strip(), 'stderr': process.stderr.strip()}
        results.append(row)
        print(json.dumps({'command': row['command'], 'exitCode': row['exitCode']}), flush=True)
    report = {'scope': 'Isolated copies; original Phase 1/2 generated evidence was not overwritten.',
              'workspace': str(temp), 'checks': results,
              'nonzero': [r for r in results if r['exitCode']]}
    dest = ROOT/'audit/generated/phase3-existing-checks.json'
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'nonzero': len(report['nonzero']), 'output': str(dest)}))
    return int(bool(report['nonzero']))


if __name__ == '__main__':
    raise SystemExit(run())
