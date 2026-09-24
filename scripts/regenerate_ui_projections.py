"""Build human-readable UI projections from authoritative SSOT resources."""
import argparse
import csv
import io
import json
import sys

from ssot_sources import ROOT, resource_index


def build_outputs():
    resources = resource_index()

    def load(path):
        return json.loads(resources[path]["raw"])

    registry = load("ui/contracts/ui-control-registry.json")
    bindings_doc = load("closure/contracts/ui-action-resolution.json")
    bindings = {
        (row["pageId"], row["actionId"]): row
        for row in bindings_doc["bindings"]
    }
    controls = []
    parity = []
    catalog = [
        "# KájovoCML NG — UI katalog",
        "",
        "Odvozený pohled kanonického vloženého registru. Backendové vazby určuje vložený registr `closure/contracts/ui-action-resolution.json`.",
        "",
    ]

    fields = [
        "pageId", "route", "pageTitle", "controlKind", "controlId", "label",
        "inputType", "inputProfile", "required", "validation", "editableWhen",
        "source", "operationBinding", "enabledWhen", "disabledWhen",
        "confirmation", "purpose",
    ]
    action_count = 0
    for page_index, page in enumerate(registry["pages"]):
        catalog.extend([f"## {page['title']}", "", f"`{page['id']}` · `{page['route']}`", "", page["purpose"], "", "| Akce | Backend | Dashboard | Chat |", "|---|---|---|---|"])
        for kind, entries in (("field", page["fields"]), ("action", page["actions"])):
            for item in entries:
                controls.append({
                    "pageId": page["id"], "route": page["route"], "pageTitle": page["title"],
                    "controlKind": kind, "controlId": item["id"], "label": item["label"],
                    "inputType": item.get("type", ""), "inputProfile": item.get("inputProfile", ""),
                    "required": item.get("required", ""), "validation": item.get("validation", ""),
                    "editableWhen": item.get("editableWhen", ""), "source": item.get("source", ""),
                    "operationBinding": item.get("operationBinding", ""),
                    "enabledWhen": item.get("enabledWhen", ""), "disabledWhen": item.get("disabledWhen", ""),
                    "confirmation": item.get("confirmation", ""), "purpose": item["purpose"],
                })
        for action in page["actions"]:
            binding = bindings.get((page["id"], action["id"]))
            if binding is None:
                raise ValueError(f"ACTION_BINDING_MISSING:{page['id']}.{action['id']}")
            if binding.get("canonicalOperationId"):
                target = binding["canonicalOperationId"]
            elif binding.get("candidateOperationIds"):
                target = " / ".join(binding["candidateOperationIds"])
            else:
                target = binding["bindingKind"]
            dashboard = action.get("dashboard", {}).get("availability", "NOT_DECLARED_IN_ACTION_RECORD")
            chat = action.get("chat", {}).get("availability", "NOT_DECLARED_IN_ACTION_RECORD")
            catalog.append(
                f"| `{action['id']}` — {action['label']} | `{target}` | "
                f"{dashboard} | {chat} |"
            )
            parity.append({
                "page_id": page["id"], "ui_function": action["id"], "label_cs": action["label"],
                "binding_kind": binding["bindingKind"], "backend_operation": target,
                "permission": action.get("permission", "NOT_DECLARED_IN_ACTION_RECORD"),
                "dashboard": dashboard, "dashboard_surface": action.get("dashboard", {}).get("surface", "NOT_DECLARED_IN_ACTION_RECORD"),
                "chat": chat,
                "validation": "See binding and operation schema; semantic payload validation not proven by this projection",
                "audit": action.get("auditContract", {}).get("event", "NOT_DECLARED_IN_ACTION_RECORD"),
                "enabled_when": action["enabledWhen"],
                "disabled_when": action["disabledWhen"], "confirmation": action["confirmation"],
            })
            action_count += 1
        catalog.append("")

    control_csv = io.StringIO(newline="")
    writer = csv.DictWriter(control_csv, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(controls)
    parity_csv = io.StringIO(newline="")
    writer = csv.DictWriter(parity_csv, fieldnames=list(parity[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(parity)

    screen_path = ROOT / "01_UI_CONTRACT/UI_SCREEN_MATRIX.csv"
    screen_rows = list(csv.DictReader(screen_path.open(encoding="utf-8-sig", newline="")))
    page_by_id = {page["id"]: page for page in registry["pages"]}
    if {row["page_id"] for row in screen_rows} != set(page_by_id):
        raise ValueError("SCREEN_MATRIX_PAGE_SET_DRIFT")
    for row in screen_rows:
        page = page_by_id[row["page_id"]]
        row["fields"] = str(len(page["fields"]))
        row["actions"] = str(len(page["actions"]))
    screen_csv = io.StringIO(newline="")
    screen_writer = csv.DictWriter(screen_csv, fieldnames=list(screen_rows[0]), lineterminator="\n")
    screen_writer.writeheader()
    screen_writer.writerows(screen_rows)

    outputs = {
        "01_UI_CONTRACT/closure/contracts/ui-action-resolution.json": resources["closure/contracts/ui-action-resolution.json"]["raw"],
        "01_UI_CONTRACT/ui/contracts/ui-control-registry.json": resources["ui/contracts/ui-control-registry.json"]["raw"],
        "01_UI_CONTRACT/ui/contracts/live-experience.json": resources["ui/contracts/live-experience.json"]["raw"],
        "01_UI_CONTRACT/ui/scripts/verify_ui.py": resources["ui/scripts/verify_ui.py"]["raw"],
        "01_UI_CONTRACT/UI_CONTROLS.csv": control_csv.getvalue().encode("utf-8-sig"),
        "01_UI_CONTRACT/UI_FUNCTION_PARITY.csv": parity_csv.getvalue().encode("utf-8"),
        "01_UI_CONTRACT/UI_SCREEN_MATRIX.csv": screen_csv.getvalue().encode("utf-8"),
        "01_UI_CONTRACT/UI_CATALOG.md": ("\n".join(catalog) + "\n").encode("utf-8"),
        "01_UI_CONTRACT/ui/audit/ui-coverage.json": resources["ui/audit/ui-coverage.json"]["raw"],
    }
    return outputs, {"actions": action_count, "controls": len(controls)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if any generated projection is stale")
    args = parser.parse_args()
    outputs, counts = build_outputs()
    stale = []
    for relative, data in outputs.items():
        path = ROOT / relative
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                stale.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    result = {"status": "FAIL" if stale else "PASS", **counts, "projections": sorted(outputs), "stale": stale}
    print(json.dumps(result, ensure_ascii=False))
    return bool(stale)


if __name__ == "__main__":
    sys.exit(main())
