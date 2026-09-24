"""Restore the 16 reference-backed UI actions to embedded SSOT registries."""
import argparse
import copy
import json
import subprocess
import sys

from ssot_sources import ROOT, SSOT, resource_index, replace_resource


EXPECTED = {
    "dashboard.contextChat", "dashboard.copy", "dashboard.detail", "dashboard.files",
    "dashboard.history", "dashboard.inputs", "dashboard.lastRun", "dashboard.logs",
    "dashboard.outputs", "dashboard.remove", "dashboard.restart", "dashboard.start",
    "dashboard.status", "dashboard.stop", "gen.editSpec", "gen.reviewSpec",
}


def previous_file(path):
    result = subprocess.run(["git", "show", "HEAD:" + path], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise ValueError("STARTING_PROJECTION_UNAVAILABLE:" + path)
    return result.stdout


def restore():
    current = resource_index()
    registry = json.loads(current["ui/contracts/ui-control-registry.json"]["raw"])
    bindings_doc = json.loads(current["closure/contracts/ui-action-resolution.json"]["raw"])
    experience = json.loads(current["ui/contracts/live-experience.json"]["raw"])
    old_registry = json.loads(previous_file("01_UI_CONTRACT/ui/contracts/ui-control-registry.json"))
    old_bindings_doc = json.loads(previous_file("01_UI_CONTRACT/closure/contracts/ui-action-resolution.json"))

    old_actions = {
        (page["id"], action["id"]): action
        for page in old_registry["pages"] for action in page["actions"]
        if action["id"] in EXPECTED
    }
    old_bindings = {
        (row["pageId"], row["actionId"]): row
        for row in old_bindings_doc["bindings"] if row["actionId"] in EXPECTED
    }
    seen = {action_id for _, action_id in old_actions}
    if seen != EXPECTED or set(old_bindings) != set(old_actions):
        raise ValueError("REFERENCE_ACTIONS_OR_BINDINGS_INCOMPLETE:" + repr(sorted(EXPECTED - seen)))

    old_action_order = [(page["id"], action["id"]) for page in old_registry["pages"] for action in page["actions"]]
    old_binding_order = [(row["pageId"], row["actionId"]) for row in old_bindings_doc["bindings"]]
    if len(old_action_order) != len(set(old_action_order)) or set(old_action_order) != set(old_binding_order):
        raise ValueError("STARTING_UI_REGISTRY_AND_BINDINGS_DO_NOT_FORM_A_BIJECTION")

    existing_registry = {
        (page["id"], action["id"])
        for page in registry["pages"] for action in page["actions"]
    }
    additions = sorted(set(old_actions) - existing_registry)
    by_page = {page["id"]: page for page in registry["pages"]}
    page_order = {page["id"]: i for i, page in enumerate(registry["pages"])}
    for page_id, action_id in sorted(additions, key=lambda item: (page_order[item[0]], item[1])):
        by_page[page_id]["actions"].append(copy.deepcopy(old_actions[(page_id, action_id)]))

    for page in registry["pages"]:
        old_positions = {action_id: index for index, (pid, action_id) in enumerate(old_action_order) if pid == page["id"]}
        if {action["id"] for action in page["actions"]} != set(old_positions):
            raise ValueError("ACTION_SET_DIFFERS_FROM_TRACKED_REFERENCE:" + page["id"])
        page["actions"].sort(key=lambda action: old_positions[action["id"]])

    current_bindings = {(row["pageId"], row["actionId"]): row for row in bindings_doc["bindings"]}
    for key in additions:
        current_bindings[key] = copy.deepcopy(old_bindings[key])
    if set(current_bindings) != set(old_binding_order):
        raise ValueError("CURRENT_BINDINGS_DIFFER_FROM_TRACKED_REFERENCE")
    bindings_doc["bindings"] = [current_bindings[key] for key in old_binding_order]

    # The experience map requires one explicit surface entry per UI action.
    # Reuse same-page presentation geometry and replace only stable identities,
    # action pointers and visible menu labels; do not invent another layout.
    old_surfaces = list(experience["dashboardSurfaceBindings"])
    for page_id, action_id in sorted(additions, key=lambda item: (page_order[item[0]], item[1])):
        page_index = page_order[page_id]
        page = by_page[page_id]
        action_index = next(i for i, item in enumerate(page["actions"]) if item["id"] == action_id)
        action_pointer = f"ui/contracts/ui-control-registry.json#/pages/{page_index}/actions/{action_index}"
        binding_index = len(bindings_doc["bindings"]) - len(additions) + sorted(additions, key=lambda item: (page_order[item[0]], item[1])).index((page_id, action_id))
        template = next((row for row in old_surfaces if row["pageId"] == page_id), None)
        if template is None:
            raise ValueError("NO_SAME_PAGE_SURFACE_TEMPLATE:" + page_id)
        row = copy.deepcopy(template)
        prior_action = row["actionId"]
        row["functionId"] = "ui." + action_id
        row["pageId"] = page_id
        row["actionId"] = action_id
        row["actionRef"] = action_pointer
        row["availabilityRef"] = action_pointer
        row["commandBindingRef"] = f"closure/contracts/ui-action-resolution.json#/bindings/{binding_index}"
        row["dashboard"]["contentSourceRef"] = f"ui/contracts/ui-control-registry.json#/pages/{page_index}"
        row["dashboard"]["entry"] = row["dashboard"]["entry"].replace(prior_action, action_id)
        row["dashboard"]["contextEntry"] = row["dashboard"]["contextEntry"].replace(prior_action, action_id)
        experience["dashboardSurfaceBindings"].append(row)

    surfaces = {(row["pageId"], row["actionId"]): row for row in experience["dashboardSurfaceBindings"]}
    if set(surfaces) != set(old_action_order):
        raise ValueError("EXPERIENCE_SURFACE_SET_DIFFERS_FROM_TRACKED_REFERENCE")
    experience["dashboardSurfaceBindings"] = [surfaces[key] for key in old_action_order]
    action_pointer_by_pair = {}
    for page_index, page in enumerate(registry["pages"]):
        for action_index, action in enumerate(page["actions"]):
            action_pointer_by_pair[(page["id"], action["id"])] = f"ui/contracts/ui-control-registry.json#/pages/{page_index}/actions/{action_index}"
    binding_index_by_pair = {key: index for index, key in enumerate(old_binding_order)}
    for row in experience["dashboardSurfaceBindings"]:
        key = (row["pageId"], row["actionId"])
        row["actionRef"] = action_pointer_by_pair[key]
        row["availabilityRef"] = action_pointer_by_pair[key]
        row["commandBindingRef"] = f"closure/contracts/ui-action-resolution.json#/bindings/{binding_index_by_pair[key]}"

    if additions or registry != json.loads(current["ui/contracts/ui-control-registry.json"]["raw"]):
        replace_resource("ui/contracts/ui-control-registry.json", registry, "KCML-UI-RESOURCE")
    if additions or bindings_doc != json.loads(current["closure/contracts/ui-action-resolution.json"]["raw"]):
        replace_resource("closure/contracts/ui-action-resolution.json", bindings_doc, "KCML-CLOSURE-RESOURCE")
    if additions or experience != json.loads(current["ui/contracts/live-experience.json"]["raw"]):
        replace_resource("ui/contracts/live-experience.json", experience, "KCML-EXPERIENCE-RESOURCE")
    return {"restored": len(additions), "actionIds": sorted(action_id for _, action_id in additions),
            "authorityEvidence": ["starting tracked UI projections at HEAD", "04_UI_VIEWS/en/768x1024/live-context-menu-en.png", "per-action purpose and target in starting UI registry/parity projection"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write merged action records into embedded SSOT resources")
    args = parser.parse_args()
    if not args.apply:
        print(json.dumps({"status": "NO_WRITE", "expectedActionCount": len(EXPECTED)}))
        raise SystemExit(0)
    result = restore()
    print(json.dumps(result, ensure_ascii=False))
