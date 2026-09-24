"""Run Phase 1–4 relevant checks in an isolated tree; preserve all earlier evidence."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ssot_sources import ROOT, SSOT, resource_index


def main():
    temp = Path(tempfile.mkdtemp(prefix="phase4-regression-", dir=ROOT / ".cache"))
    shutil.copytree(ROOT / "scripts", temp / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    (temp / "00_SSOT").mkdir()
    shutil.copy2(SSOT, temp / "00_SSOT/KajovoCMLNG_SSOT.md")
    shutil.copytree(ROOT / "01_UI_CONTRACT", temp / "01_UI_CONTRACT")
    shutil.copytree(ROOT / "audit", temp / "audit", ignore=shutil.ignore_patterns("generated"))
    (temp / "audit/generated").mkdir(parents=True, exist_ok=True)
    (temp / ".cache").mkdir(exist_ok=True)
    resources = resource_index()
    for name in ("r11/scripts/verify_r11.py", "scripts/ssot/ssot_control.py", "scripts/ssot/audit_checks.py"):
        target = temp / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(resources[name]["raw"])

    jobs = [
        ["scripts/verify_schema_references.py"],
        ["scripts/verify_phase1_contracts.py"],
        ["scripts/phase1_repair_contracts.py", "--check"],
        ["scripts/phase2_repair_handoffs.py", "--check"],
        ["scripts/verify_phase2_handoffs.py"],
        ["scripts/project_experience.py", "--check"],
        ["scripts/verify_experience.py"],
        ["scripts/verify_observability.py"],
        ["scripts/phase2_handoff_closure.py", "--check"],
        ["r11/scripts/verify_r11.py", "00_SSOT/KajovoCMLNG_SSOT.md"],
        ["scripts/ssot/ssot_control.py", "00_SSOT/KajovoCMLNG_SSOT.md", "--check"],
        ["scripts/verify_phase3_semantics.py"],
        ["scripts/regenerate_ui_projections.py", "--check"],
        ["01_UI_CONTRACT/ui/scripts/verify_ui.py"],
    ]
    checks = []
    for job in jobs:
        result = subprocess.run([sys.executable, *job], cwd=temp, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=1800)
        checks.append({"command": "python " + " ".join(job), "exitCode": result.returncode,
                       "stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
        print(json.dumps({"command": job[0], "exitCode": result.returncode}), flush=True)
    report = {
        "scope": "Isolated copy of current SSOT and UI projections; previous Phase 1–3 reports and generated evidence were not overwritten.",
        "workspace": str(temp),
        "checks": checks,
        "nonzero": [row for row in checks if row["exitCode"]],
    }
    destination = ROOT / "audit/generated/phase4-regression-checks.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": len(checks), "nonzero": len(report["nonzero"]), "output": str(destination)}, ensure_ascii=False))
    return int(bool(report["nonzero"]))


if __name__ == "__main__":
    raise SystemExit(main())
