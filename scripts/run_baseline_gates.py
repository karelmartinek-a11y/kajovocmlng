"""Run the five gate families required by SSOT 73.7, without modifying sources."""
import hashlib
import json
import subprocess
import sys
from ssot_sources import ROOT, SSOT, resources, safe_path

from final_gate_set import FINAL_GATE_FAMILIES,run_final_gates
GATES=[name for family,name in FINAL_GATE_FAMILIES]

def run():
    results=run_final_gates(list(resources()),ROOT,SSOT)
    report = {'ssotSha256': hashlib.sha256(SSOT.read_bytes()).hexdigest(), 'checks': results,
        'scope': 'Exact effective §73.7 five-family gate execution only; no full semantic/manual/runtime certification.'}
    out = ROOT / 'audit/generated/baseline-gates.json'; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    r = run(); print(json.dumps([(x['gate'], x['status']) for x in r['checks']]))
    sys.exit(any(x['status'] != 'PASS' for x in r['checks']))
