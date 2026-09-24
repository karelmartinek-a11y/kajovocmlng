"""Fail-closed structural checks for the Phase 4 UI projections and evidence."""
import json
import sys
from pathlib import Path

from phase4_ui_closure import ROOT, build_action_matrix, build_current_handoff
from regenerate_ui_projections import build_outputs
from ssot_sources import resource_index, SSOT


def run():
    checks = []

    def record(check_id, condition, detail):
        checks.append({"id": check_id, "status": "PASS" if condition else "FAIL", "detail": detail})

    outputs, projection_counts = build_outputs()
    stale = [relative for relative, expected in outputs.items()
             if not (ROOT / relative).exists() or (ROOT / relative).read_bytes() != expected]
    record("projections.exact-canonical-source", not stale, {"stale": stale, **projection_counts})

    generated = build_action_matrix()
    saved = json.loads((ROOT / "audit/phase4-ui-action-matrix.json").read_text(encoding="utf-8"))
    record("matrix.exact-current-source-inventory", saved == generated,
           {"canonical": generated["summary"]["canonicalRequiredActions"], "missingBindings": generated["summary"]["actionBindingsMissing"]})

    ids = [(row["pageId"], row["actionId"]) for row in generated["actions"]]
    record("actions.unique-and-resolved", len(ids) == len(set(ids)) and not generated["missingBindings"],
           {"actions": len(ids), "missing": generated["missingBindings"]})
    blocked = [row for row in generated["actions"] if row["status"] == "BLOCKED_EXPOSURE_OR_FACADE"]
    record("exposure.bypass-is-visible-not-hidden", len(blocked) == generated["summary"]["blockedExposureOrFacade"],
           {"blockedActions": [row["actionId"] for row in blocked]})
    blocked_ids = {row["actionId"] for row in blocked}
    record("direct-internal-and-maintenance-actions-remain-blocked",
           blocked_ids == {"dashboard.start", "dashboard.stop", "gen.editSpec"},
           {"blockedActionIds": sorted(blocked_ids)})
    monitoring = next((row for row in generated["actions"] if row["actionId"] == "monitoring.repair"), None)
    record("monitoring.repair-uses-owner-facade", bool(monitoring and monitoring["targetOperations"]
           and monitoring["targetOperations"][0]["operationId"] == "component.repair.request"
           and monitoring["targetOperations"][0]["exposure"] == "OWNER_COMMAND"),
           {"status": monitoring["status"] if monitoring else "missing"})
    registered_repair = next((row for row in generated["actions"] if row["actionId"] == "registered.repair"), None)
    record("dynamic-repair-excludes-automated-maintenance-target",
           bool(registered_repair and all(item.get("exposure", "").startswith("OWNER_")
                                          for item in registered_repair["targetOperations"])),
           {"status": registered_repair["status"] if registered_repair else "missing",
            "targets": [item["operationId"] for item in registered_repair["targetOperations"]] if registered_repair else []})
    promoted = generated["promotedActionEvidence"]
    summary = generated["summary"]
    record("historical-16-functions-preserved-and-promoted-with-evidence",
           len(promoted) == 16 and summary["startingHeadEmbeddedActions"] == 136
           and summary["startingHeadPhysicalProjectedActions"] == 152
           and summary["actionsPromotedIntoEmbeddedAuthority"] == 16
           and summary["currentProjectionExcess"] == 0
           and all(row["status"] == "PROMOTED_TO_AUTHORITY" and row["currentEmbeddedAction"] for row in promoted),
           {"promoted": len(promoted), "currentProjectionExcess": summary["currentProjectionExcess"]})
    matrix = json.loads((ROOT / "audit/phase4-current-handoff-matrix.json").read_text(encoding="utf-8"))
    rebuilt_matrix = build_current_handoff()
    record("current-handoff-matrix-exact-current-content-and-source",
           matrix == rebuilt_matrix
           and matrix.get("currentSourceIdentity", {}).get("ssotSha256") == "sha256:" + __import__("hashlib").sha256(SSOT.read_bytes()).hexdigest()
           and matrix.get("format") == "KCML-PHASE4-CURRENT-HANDOFF-MATRIX/1",
           {"exactRebuild": matrix == rebuilt_matrix,
            "sourceSha256": matrix.get("currentSourceIdentity", {}).get("ssotSha256"),
            "head": matrix.get("currentSourceIdentity", {}).get("head")})

    unresolved = json.loads((ROOT / "audit/phase4-unresolved.json").read_text(encoding="utf-8"))
    exposure_ids = {row["actionId"] for row in blocked}
    unresolved_exposure_ids = {row["id"] for row in unresolved.get("phase4BlockingItems", [])
                               if row.get("category") == "BLOCKED_EXPOSURE_OR_FACADE"}
    record("unresolved-summary-includes-every-exposure-blocker",
           exposure_ids == unresolved_exposure_ids,
           {"actionIds": sorted(exposure_ids), "reported": sorted(unresolved_exposure_ids)})
    record("operation-payload-semantics-not-overclaimed",
           generated["summary"]["fullySemanticallyVerified"] == 0
           and all(row["requestValueMapping"] == "NOT_DECLARED_AS_FIELD_MAPPING" for row in generated["actions"] if row["targetOperations"]),
           {"fullySemanticallyVerified": generated["summary"]["fullySemanticallyVerified"],
            "notVerifiedArgumentOrResponseMapping": generated["summary"]["notVerifiedArgumentOrResponseMapping"],
            "notVerifiedDynamicDispatch": generated["summary"]["notVerifiedDynamicDispatch"]})

    resources = resource_index()
    canonical = json.loads(resources["closure/contracts/ui-action-resolution.json"]["raw"])
    registry = json.loads(resources["ui/contracts/ui-control-registry.json"]["raw"])
    pairs = {(p["id"], a["id"]) for p in registry["pages"] for a in p["actions"]}
    binding_pairs = {(b["pageId"], b["actionId"]) for b in canonical["bindings"]}
    record("negative-missing-or-unmapped-action-is-detected", pairs == binding_pairs,
           {"unbound": sorted(pairs - binding_pairs), "orphanBindings": sorted(binding_pairs - pairs)})

    report = {"status": "PASS" if all(x["status"] == "PASS" for x in checks) else "FAIL",
              "scope": "Structural source/projection checks only; no production application or backend is present.",
              "checks": checks,
              "knownClosureBlockers": [row["actionId"] for row in blocked]}
    (ROOT / "audit/generated/phase4-ui-checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": len(checks), "failed": sum(x["status"] == "FAIL" for x in checks), "blockers": len(report["knownClosureBlockers"])}, ensure_ascii=False))
    return int(report["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(run())
