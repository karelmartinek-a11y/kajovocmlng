"""Build Phase 4 UI-action and current handoff evidence from active SSOT sources."""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from ssot_sources import ROOT, SSOT, resource_index, resources as parse_resources
from operation_catalog import catalog
from phase2_handoff_closure import build as build_handoff_matrix


SPECIAL_IDS = {
    "dashboard.contextChat", "dashboard.copy", "dashboard.detail", "dashboard.files",
    "dashboard.history", "dashboard.inputs", "dashboard.lastRun", "dashboard.logs",
    "dashboard.outputs", "dashboard.remove", "dashboard.restart", "dashboard.start",
    "dashboard.status", "dashboard.stop", "gen.editSpec", "gen.reviewSpec",
}


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def git_bytes(ref):
    result = subprocess.run(["git", "show", ref], cwd=ROOT, capture_output=True)
    return result.stdout if result.returncode == 0 else None


def build_action_matrix():
    resources = resource_index()
    registry = json.loads(resources["ui/contracts/ui-control-registry.json"]["raw"])
    bindings_doc = json.loads(resources["closure/contracts/ui-action-resolution.json"]["raw"])
    binding_rows = bindings_doc["bindings"]
    binding_index = {(row["pageId"], row["actionId"]): (i, row) for i, row in enumerate(binding_rows)}
    operations = catalog(resources)
    actions = []
    missing_bindings = []
    for page_index, page in enumerate(registry["pages"]):
        for action_index, action in enumerate(page["actions"]):
            found = binding_index.get((page["id"], action["id"]))
            if not found:
                missing_bindings.append(page["id"] + "." + action["id"])
                continue
            binding_index_value, binding = found
            operation_ids = []
            if binding.get("canonicalOperationId"):
                operation_ids.append(binding["canonicalOperationId"])
            operation_ids.extend(binding.get("candidateOperationIds", []))
            operation_ids.extend(binding.get("followOnCanonicalOperations", []))
            operation_ids = sorted(set(operation_ids))
            operation_details = []
            for operation_id in operation_ids:
                operation = operations.get(operation_id)
                if operation is None:
                    operation_details.append({"operationId": operation_id, "status": "BLOCKED_MISSING_OPERATION"})
                    continue
                operation_details.append({
                    "operationId": operation_id,
                    "status": "RESOLVED",
                    "exposure": operation.get("exposureClass"),
                    "source": operation.get("sourceRef"),
                    "requestSchema": operation.get("requestSchemaRef") or operation.get("commandSchemaRef"),
                    "responseSchema": operation.get("responseSchemaRef"),
                    "eventSchema": operation.get("eventSchemaRef"),
                })
            forbidden_exposure = [
                x["operationId"] for x in operation_details
                if x.get("exposure") in {"INTERNAL_PROTOCOL", "AUTOMATED_MAINTENANCE"}
            ]
            missing_ops = [x["operationId"] for x in operation_details if x.get("status") == "BLOCKED_MISSING_OPERATION"]
            if missing_ops:
                status = "BLOCKED_MISSING_OPERATION"
            elif forbidden_exposure:
                status = "BLOCKED_EXPOSURE_OR_FACADE"
            elif binding["bindingKind"] in {"CLIENT_ONLY", "FORBIDDEN", "NAVIGATION", "LOCAL_UI"}:
                status = "STATIC_LOCAL_BINDING"
            elif binding.get("candidateOperationIds"):
                status = "NOT_VERIFIED_DYNAMIC_DISPATCH_AND_ARGUMENT_MAPPING"
            elif operation_ids:
                status = "NOT_VERIFIED_ARGUMENT_MAPPING_AND_RESPONSE_USE"
            else:
                status = "NOT_VERIFIED_ACTION_SEMANTICS"
            actions.append({
                "actionId": action["id"],
                "pageId": page["id"],
                "pageRoute": page["route"],
                "pageActionPointer": f"ui/contracts/ui-control-registry.json#/pages/{page_index}/actions/{action_index}",
                "bindingPointer": f"closure/contracts/ui-action-resolution.json#/bindings/{binding_index_value}",
                "label": action["label"],
                "purpose": action["purpose"],
                "bindingKind": binding["bindingKind"],
                "requiredRole": action.get("permission"),
                "availability": action.get("enabledWhen"),
                "unavailability": action.get("disabledWhen"),
                "targetOperations": operation_details,
                "argumentProfile": binding.get("argumentProfile"),
                "declaredPageFields": [
                    {"id": field["id"], "type": field.get("type"), "required": field.get("required"),
                     "source": field.get("source"), "inputProfile": field.get("inputProfile"),
                     "validation": field.get("validation")}
                    for field in page["fields"]
                ],
                "requestValueMapping": "NOT_DECLARED_AS_FIELD_MAPPING",
                "responseAndEventUse": "NOT_PROVEN_BY_STATIC_REGISTRY",
                "resultingUiStates": "See page, action guards, acceptance and live-experience state contract; action-specific mapping not proven.",
                "status": status,
            })

    # Capture the 152-action tracked projection as it existed at the starting HEAD.
    # It is comparison evidence only, never promoted to authority.
    old_raw = git_bytes("HEAD:01_UI_CONTRACT/closure/contracts/ui-action-resolution.json")
    old_ids = set()
    old_bindings = []
    if old_raw:
        old_bindings = json.loads(old_raw).get("bindings", [])
        old_ids = {row["actionId"] for row in old_bindings}
    canonical_ids = {action["actionId"] for action in actions}
    head_ssot_raw = git_bytes("HEAD:00_SSOT/KajovoCMLNG_SSOT.md")
    head_resources = resource_index(parse_resources(head_ssot_raw.decode("utf-8"))) if head_ssot_raw else {}
    starting_registry = json.loads(head_resources["ui/contracts/ui-control-registry.json"]["raw"]) if head_resources else {"pages": []}
    starting_ids = {action["id"] for page in starting_registry["pages"] for action in page["actions"]}
    promoted_ids = sorted((old_ids & SPECIAL_IDS) - starting_ids)
    legacy_extra_ids = sorted(old_ids - canonical_ids)
    legacy_details = []
    old_controls_raw = git_bytes("HEAD:01_UI_CONTRACT/ui/contracts/ui-control-registry.json")
    old_control_index = {}
    if old_controls_raw:
        old_registry = json.loads(old_controls_raw)
        old_control_index = {
            (page["id"], action["id"]): (pi, ai, action)
            for pi, page in enumerate(old_registry["pages"])
            for ai, action in enumerate(page["actions"])
        }
    old_binding_index = {(row["pageId"], row["actionId"]): row for row in old_bindings}
    for action_id in sorted(set(legacy_extra_ids) | set(promoted_ids)):
        found = next(((key, value) for key, value in old_control_index.items() if key[1] == action_id), None)
        binding = next((row for row in old_bindings if row["actionId"] == action_id), None)
        legacy_details.append({
            "actionId": action_id,
            "formerProjectionControl": (f"ui/contracts/ui-control-registry.json#/pages/{found[1][0]}/actions/{found[1][1]}" if found else None),
            "formerProjectionBinding": f"closure/contracts/ui-action-resolution.json#/bindings/{old_bindings.index(binding)}" if binding else None,
            "formerPurpose": found[1][2].get("purpose") if found else None,
            "formerOperationBinding": found[1][2].get("operationBinding") if found else None,
            "formerBindingKind": binding.get("bindingKind") if binding else None,
            "formerOperationIds": ([binding["canonicalOperationId"]] if binding and binding.get("canonicalOperationId") else binding.get("candidateOperationIds", []) if binding else []),
            "sourceOfFunctionalRequirement": "Starting tracked UI control purpose and operation parity; dashboard features are also visibly present in the existing live reference screenshot. The matched records have been promoted to embedded SSOT and explicit experience placements.",
            "startingEmbeddedAction": action_id in starting_ids,
            "currentEmbeddedAction": action_id in canonical_ids,
            "referenceScreenshot": "04_UI_VIEWS/en/768x1024/live-context-menu-en.png" if action_id.startswith("dashboard.") else None,
            "status": "PROMOTED_TO_AUTHORITY" if action_id in promoted_ids and action_id in canonical_ids else "BLOCKED_REQUIREMENT_AUTHORITY_UNRESOLVED",
        })

    named_exposure_findings = []
    for page_id, action_id in [
        ("generation", "gen.editSpec"), ("dashboard", "dashboard.start"),
        ("dashboard", "dashboard.stop"), ("monitoring", "monitoring.repair"),
    ]:
        old_binding = old_binding_index.get((page_id, action_id))
        current = next((row for row in actions if (row["pageId"], row["actionId"]) == (page_id, action_id)), None)
        named_exposure_findings.append({
            "pageId": page_id,
            "actionId": action_id,
            "startingHeadOperation": (old_binding.get("canonicalOperationId") if old_binding and old_binding.get("canonicalOperationId") else old_binding.get("candidateOperationIds") if old_binding else None),
            "startingHeadBindingKind": old_binding.get("bindingKind") if old_binding else None,
            "currentAuthoritativeTarget": [item["operationId"] for item in current["targetOperations"]] if current else [],
            "currentStatus": current["status"] if current else "ABSENT_FROM_CURRENT_CANONICAL_UI_REGISTRY",
            "resolution": (
                "Rebound to OWNER component.repair.request because the canonical action uses COMPONENT.REPAIR and sibling OWNER repair actions use the same facade; payload mapping still needs verification."
                if page_id == "monitoring" and current and current["targetOperations"] and current["targetOperations"][0]["operationId"] == "component.repair.request"
                else "Historical projection-only action has no current SSOT requirement or placement; kept unresolved and not restored from projection evidence."
                if current is None
                else "Current exposure or action mapping remains unresolved; no role relabeling applied."
            ),
        })

    duplicate_ids = len(actions) - len({row["actionId"] for row in actions})
    screen_rows = list(csv.DictReader((ROOT / "01_UI_CONTRACT/UI_SCREEN_MATRIX.csv").open(encoding="utf-8-sig", newline="")))
    page_inventory = [{
        "pageId": row["page_id"], "title": row["title"], "route": row["route"],
        "fieldCount": int(row["fields"]), "actionCount": int(row["actions"]),
        "requiredStates": row["required_states"].split("|"),
        "panels": row["panels"].split("|"), "referenceFile": row["reference_file"],
        "source": "01_UI_CONTRACT/UI_SCREEN_MATRIX.csv (generated projection; counts checked against embedded ui-control-registry.json)"
    } for row in screen_rows]
    summary = {
        "startingHeadEmbeddedActions": len(starting_ids),
        "canonicalActionBindings": len(binding_rows),
        "currentGeneratedActionProjection": len(actions),
        "startingHeadPhysicalProjectedActions": len(old_ids),
        "startingHeadProjectionExcess": len(old_ids - starting_ids),
        "actionsPromotedIntoEmbeddedAuthority": len(promoted_ids),
        "currentProjectionExcess": len(legacy_extra_ids),
        "canonicalRequiredActions": len(actions),
        "actionBindingsMissing": len(missing_bindings),
        "duplicateActionIds": duplicate_ids,
        "staticLocalBindings": sum(row["status"] == "STATIC_LOCAL_BINDING" for row in actions),
        "fullySemanticallyVerified": 0,
        "blockedExposureOrFacade": sum(row["status"] == "BLOCKED_EXPOSURE_OR_FACADE" for row in actions),
        "notVerifiedArgumentOrResponseMapping": sum(row["status"] == "NOT_VERIFIED_ARGUMENT_MAPPING_AND_RESPONSE_USE" for row in actions),
        "notVerifiedDynamicDispatch": sum(row["status"] == "NOT_VERIFIED_DYNAMIC_DISPATCH_AND_ARGUMENT_MAPPING" for row in actions),
    }
    return {
        "format": "KCML-PHASE4-UI-ACTION-MATRIX/1",
        "sourceAuthority": "Embedded KCML-UI-RESOURCE and KCML-CLOSURE-RESOURCE blocks in 00_SSOT/KajovoCMLNG_SSOT.md; physical registries are generated projections.",
        "comparisonRule": "Starting-HEAD projections are read with git show for the recorded comparison only. Current action inventory comes exclusively from current SSOT resources.",
        "summary": summary,
        "uiInventory": {
            "pages": page_inventory,
            "pageCount": len(page_inventory),
            "dialogCatalog": "01_UI_CONTRACT/UI_DIALOG_CATALOG.md",
            "dialogInputTemplates": "01_UI_CONTRACT/DIALOG_INPUT_MATRIX.csv",
            "dialogInputTemplateCount": sum(1 for _ in csv.DictReader((ROOT / "01_UI_CONTRACT/DIALOG_INPUT_MATRIX.csv").open(encoding="utf-8-sig", newline=""))),
            "referenceOnly": True,
        },
        "actions": actions,
        "missingBindings": missing_bindings,
        "staleProjectionExtras": [row for row in legacy_details if row["status"] == "BLOCKED_REQUIREMENT_AUTHORITY_UNRESOLVED"],
        "promotedActionEvidence": [row for row in legacy_details if row["status"] == "PROMOTED_TO_AUTHORITY"],
        "namedExposureReview": named_exposure_findings,
    }


def build_current_handoff():
    text = SSOT.read_text(encoding="utf-8")
    matrix = build_handoff_matrix(text)
    resources = resource_index()
    source_resources = [
        {"path": path, "sha256": "sha256:" + hashlib.sha256(item["raw"]).hexdigest()}
        for path, item in sorted(resources.items())
    ]
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout.strip()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout.strip()
    matrix["format"] = "KCML-PHASE4-CURRENT-HANDOFF-MATRIX/1"
    matrix["historicalPhase2MatrixPreserved"] = "audit/phase2-handoff-matrix.json"
    matrix["currentSourceIdentity"] = {
        "head": head,
        "branch": branch,
        "ssotPath": "00_SSOT/KajovoCMLNG_SSOT.md",
        "ssotSha256": sha(text.encode("utf-8")),
        "sourceIdentityIncludesUncommittedContent": True,
        "embeddedResourceCount": len(source_resources),
        "embeddedResourceDigestManifestSha256": sha(json.dumps(source_resources, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")),
        "embeddedResourceDigests": source_resources,
        "matrixBuilder": "scripts/phase2_handoff_closure.py::build",
        "refreshRule": "Regenerated from the current working-tree SSOT, not copied from the historical Phase 2 matrix. The historical content-test result was not inherited as current proof.",
    }
    return matrix


def write_outputs():
    actions = build_action_matrix()
    handoffs = build_current_handoff()
    phase1 = json.loads((ROOT / "audit/phase1-unresolved.json").read_text(encoding="utf-8"))
    phase2 = json.loads((ROOT / "audit/phase2-unresolved.json").read_text(encoding="utf-8"))
    phase3 = json.loads((ROOT / "audit/phase3-unresolved.json").read_text(encoding="utf-8"))
    unresolved = {
        "status": "PARTIAL",
        "phase1Status": phase1.get("status", "PARTIAL"),
        "phase2Status": phase2.get("status", "PARTIAL"),
        "phase3Status": phase3.get("status", "PARTIAL"),
        "phase4BlockingItems": [
            {"id": row["actionId"], "category": "BLOCKED_EXPOSURE_OR_FACADE", "evidence": row}
            for row in actions["actions"] if row["status"] == "BLOCKED_EXPOSURE_OR_FACADE"
        ] + [
            {"id": row["actionId"], "category": "STALE_PROJECTION_EXTRA_WITHOUT_CURRENT_REQUIREMENT_AUTHORITY", "evidence": row}
            for row in actions["staleProjectionExtras"]
        ],
        "exposureReview": actions["namedExposureReview"],
        "currentExposureBlockers": [
            {"id": row["actionId"], "pageId": row["pageId"], "targetOperations": row["targetOperations"], "status": row["status"]}
            for row in actions["actions"] if row["status"] == "BLOCKED_EXPOSURE_OR_FACADE"
        ],
        "uiActionNotVerified": [
            {"actionId": row["actionId"], "pageId": row["pageId"], "status": row["status"], "requestValueMapping": row["requestValueMapping"], "targetOperations": row["targetOperations"]}
            for row in actions["actions"] if row["status"].startswith("NOT_VERIFIED") or row["status"].startswith("BLOCKED")
        ],
        "phase1Phase2Dependencies": {
            "phase1UnresolvedSummary": phase1.get("summary"),
            "phase2UnresolvedSummary": phase2.get("summary"),
            "phase3UnresolvedSummary": phase3.get("summary"),
            "historicalEventBoundaries": "See audit/phase1-unresolved.json and audit/phase2-unresolved.json; not reclassified by UI audit.",
            "stateDictionariesAndHydration": "See audit/phase3-unresolved.json; remain dependencies for UI display and handoff actions where used.",
        },
        "technology": {
            "authoritativeVersionConflictCorrected": True,
            "physicalStackExtrasNotSpecifiedByEmbeddedContract": ["@radix-ui/react-dropdown-menu", "@tanstack/react-virtual", "dompurify"],
            "noLockfileOrProductPackageManifest": True,
            "productionUbuntuBuildAndProductBrowserIntegration": "NOT_RUN; repository contains reference prototypes, not a production app.",
        },
    }
    outputs = {
        ROOT / "audit/phase4-ui-action-matrix.json": actions,
        ROOT / "audit/phase4-current-handoff-matrix.json": handoffs,
        ROOT / "audit/phase4-unresolved.json": unresolved,
    }
    for path, data in outputs.items():
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return actions, handoffs, unresolved


if __name__ == "__main__":
    result = write_outputs()
    print(json.dumps({"actions": result[0]["summary"], "handoffs": result[1]["summary"], "unresolvedPhase4": len(result[2]["phase4BlockingItems"])}, ensure_ascii=False))
