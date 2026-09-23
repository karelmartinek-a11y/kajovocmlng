"""Run the five gate families required by SSOT 73.7, without modifying sources."""
import hashlib
import json
import subprocess
import sys
from ssot_sources import ROOT, SSOT, resources, safe_path

GATES = ['r10/scripts/verify_r10.py', 'r16/scripts/verify_r16.py',
         'ui/scripts/verify_ui.py', 'closure/scripts/verify_final_closure.py', 'r17/scripts/verify_r17.py']


def run():
    items = {r['path']: r for r in resources() if r['path'] in GATES}
    results = []
    for name in GATES:
        if name not in items:
            results.append({'gate': name, 'status': 'FAIL', 'reason': 'MISSING_RESOURCE'}); continue
        item = items[name]
        if item['sha256'] != item['declared']['sha256']:
            results.append({'gate': name, 'status': 'FAIL', 'reason': 'SCRIPT_HASH_MISMATCH'}); continue
        target = safe_path(ROOT / '.cache/gates', name)
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(item['raw'])
        result = subprocess.run([sys.executable, str(target), str(SSOT)], cwd=ROOT,
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
        results.append({'gate': name, 'status': 'PASS' if result.returncode == 0 else 'FAIL',
            'scriptSha256': item['sha256'], 'exitCode': result.returncode,
            'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()})
    report = {'ssotSha256': hashlib.sha256(SSOT.read_bytes()).hexdigest(), 'checks': results,
        'scope': 'Legacy assertions only. Does not certify new requirements, runtime or whole-package closure.'}
    out = ROOT / 'audit/generated/baseline-gates.json'; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    r = run(); print(json.dumps([(x['gate'], x['status']) for x in r['checks']]))
    sys.exit(any(x['status'] != 'PASS' for x in r['checks']))
