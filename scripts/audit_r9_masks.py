"""Audit přímo aktuální vložený R9 katalog v kanonickém SSOT.

Nevychází z dříve vygenerovaných auditních matic. Syntaktická a strukturální
kontrola není potvrzením úplné sémantiky jednotlivých operací.
"""

import hashlib
import json
import sys
from collections import Counter

from ssot_sources import ROOT, SSOT, resources


def unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicitní JSON člen: " + key)
        value[key] = item
    return value


def nodes(value, pointer=""):
    if isinstance(value, dict):
        yield pointer, value
        for key, child in value.items():
            yield from nodes(child, pointer + "/" + key.replace("~", "~0").replace("/", "~1"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from nodes(child, pointer + "/" + str(index))


def generic_locations(schema):
    found = []
    for pointer, node in nodes(schema):
        properties = node.get("properties", {}) if isinstance(node, dict) else {}
        if isinstance(properties, dict) and {"schemaId", "values"} <= set(properties):
            slot = properties["values"].get("items", {}).get("properties", {}).get("slot", {})
            found.append({"pointer": pointer, "slotEnum": slot.get("enum"),
                          "slotConst": slot.get("const"), "slotPattern": slot.get("pattern")})
    return found


def record_lines(raw, first_property, expected):
    lines = raw.decode("utf-8").splitlines()
    starts = [index + 1 for index, line in enumerate(lines[:-1])
              if line == "    {" and lines[index + 1].startswith('      "' + first_property + '":')]
    if len(starts) != expected:
        raise ValueError(f"Počet fyzických záznamů {first_property}: {len(starts)} != {expected}")
    return starts


def audit():
    text = SSOT.read_text(encoding="utf-8")
    embedded = [item for item in resources(text) if item["family"] == "KCML-R9-RESOURCE"]
    by_path = {item["path"]: item for item in embedded}
    if len(by_path) != len(embedded):
        raise ValueError("Duplicitní cesta R9 resource")
    digests = []
    documents = {}
    for path, item in by_path.items():
        declared = item["declared"]
        if declared.get("sha256") != item["sha256"] or int(declared["bytes"]) != len(item["raw"]):
            digests.append({"path": path, "line": item["line"], "declared": declared,
                            "actualSha256": item["sha256"], "actualBytes": len(item["raw"])})
        if path.endswith(".json"):
            documents[path] = json.loads(item["raw"], object_pairs_hook=unique_pairs)
    operations = documents["contracts/operation-contracts.json"]["records"]
    routes = documents["contracts/payload-contracts.json"]["records"]
    operation_lines = record_lines(by_path["contracts/operation-contracts.json"]["raw"],
                                   "acceptanceGateIds", len(operations))
    route_lines = record_lines(by_path["contracts/payload-contracts.json"]["raw"],
                               "authContract", len(routes))
    ids = {node["$id"] for document in documents.values() for _, node in nodes(document)
           if isinstance(node, dict) and isinstance(node.get("$id"), str)}
    missing = []
    for index, operation in enumerate(operations):
        for role, field in (("request", "commandSchemaRef"), ("response", "responseSchemaRef")):
            ref = operation.get(field)
            if isinstance(ref, dict) and isinstance(ref.get("schemaId"), str) and ref["schemaId"] not in ids:
                missing.append({"operationId": operation["operationId"], "role": role,
                                "schemaId": ref["schemaId"],
                                "decodedResourceLine": operation_lines[index],
                                "source": f"contracts/operation-contracts.json#/records/{index}/{field}"})
    route_rows = []
    role_generic = Counter()
    nullable_bodies = 0
    for index, route in enumerate(routes):
        roles = {}
        for role in ("request", "response", "event"):
            schema = route.get(role + "Schema")
            if not isinstance(schema, dict):
                roles[role] = {"missingSchema": True, "genericLocations": []}
                continue
            found = generic_locations(schema)
            role_generic[role] += bool(found)
            roles[role] = {"schemaId": schema.get("$id"), "genericLocations": found,
                           "explicitDomainSlots": bool(found) and all(
                               location["slotEnum"] or location["slotConst"] for location in found)}
        body = route.get("requestSchema", {}).get("properties", {}).get("body", {})
        nullable = any(variant.get("type") == "null" for variant in body.get("oneOf", []))
        nullable_bodies += nullable
        route_rows.append({"routeId": route["routeId"], "operationId": route["operationId"],
                           "method": route["method"],
                           "decodedResourceLine": route_lines[index],
                           "source": f"contracts/payload-contracts.json#/records/{index}",
                           "bodyAcceptsNull": nullable, "roles": roles})
    report = {
        "status": "BLOCKED",
        "source": "00_SSOT/KajovoCMLNG_SSOT.md",
        "sourceSha256": "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "r9Resources": [{"path": item["path"], "ssotLine": item["line"],
                         "decodedLines": len(item["raw"].splitlines()), "bytes": len(item["raw"]),
                         "sha256": item["sha256"]} for item in embedded],
        "digestMismatches": digests,
        "operationCount": len(operations), "routeCount": len(routes),
        "missingOperationSchemaRefs": missing,
        "routesWithGenericSlotContainerByRole": dict(role_generic),
        "routesWithNullableBody": nullable_bodies,
        "routeMethodCounts": dict(Counter(route["method"] for route in routes)),
        "routes": route_rows,
        "interpretation": "Trojice schémat pro route existuje, avšak volný slot/value/canonicalJson "
                          "není úplná doménová maska. Bez explicitních polí, variant, povinnosti, "
                          "nullability a totožné přijímací masky nelze prohlásit kontrakt za uzavřený.",
    }
    output = ROOT / "audit/generated/current-r9-mask-inventory.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = audit()
    print(json.dumps({key: result[key] for key in (
        "status", "operationCount", "routeCount", "routesWithGenericSlotContainerByRole",
        "routesWithNullableBody")}, ensure_ascii=False))
    print("unresolved operation schema refs:", len(result["missingOperationSchemaRefs"]),
          "R9 digest mismatches:", len(result["digestMismatches"]))
    sys.exit(result["status"] != "PASS")
