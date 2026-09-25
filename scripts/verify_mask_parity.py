"""Fail-closed census of explicit operation masks and producer/consumer handoffs.

This checks the current embedded SSOT, not historical audit assertions. Matching
digests alone do not establish semantic or transport compatibility.
"""

import hashlib
import json
import sys
from collections import Counter

from phase1_schema_closure import build as build_boundaries
from phase2_handoff_closure import build as build_handoffs
from ssot_sources import ROOT, SSOT


def audit():
    raw = SSOT.read_bytes()
    text = raw.decode("utf-8")
    inventory, boundaries = build_boundaries(text)
    handoffs = build_handoffs(text)
    integrity = [
        {"path": item["path"], "line": item["line"], "declared": item["declared"].get("sha256"),
         "actual": item["sha256"]}
        for item in inventory.items
        if item["declared"].get("sha256") and item["declared"]["sha256"] != item["sha256"]
    ]
    operation_gaps = []
    for operation in boundaries["operations"]:
        entries = operation["boundaries"] + [
            boundary for route in operation["routes"] for boundary in route["boundaries"]
        ]
        roles = {entry["role"] for entry in entries}
        if not {"request", "response"} <= roles:
            operation_gaps.append({"operationId": operation["operationId"],
                                   "reason": "MISSING_REQUEST_OR_RESPONSE_BOUNDARY",
                                   "roles": sorted(roles), "source": operation["source"]})
        if operation["eventApplicability"] == "UNSPECIFIED_NOT_ASSUMED_ABSENT":
            operation_gaps.append({"operationId": operation["operationId"],
                                   "reason": "EVENT_APPLICABILITY_UNSPECIFIED",
                                   "source": operation["source"]})
    edge_groups = Counter()
    edge_gaps = []
    for edge in handoffs["edges"]:
        produced = edge.get("sourceSchemaDigest")
        accepted = edge.get("targetSchemaDigest")
        if produced and accepted:
            relation = "MATCHING_DIGEST" if produced == accepted else "DIFFERENT_DIGEST"
        elif produced or accepted:
            relation = "ONE_DIGEST_MISSING"
        else:
            relation = "BOTH_DIGESTS_MISSING"
        edge_groups[relation] += 1
        # An equal digest is only a necessary condition. The source matrix's
        # separate transport, adapter and branch status remains authoritative.
        if relation != "MATCHING_DIGEST" or edge["status"] != "VERIFIED":
            edge_gaps.append({"id": edge["id"], "source": edge["source"],
                              "producer": edge.get("producer"), "consumer": edge.get("consumer"),
                              "sourceSchema": edge.get("sourceSchema"),
                              "targetSchema": edge.get("targetSchema"),
                              "sourceSchemaDigest": produced, "targetSchemaDigest": accepted,
                              "digestRelation": relation, "handoffStatus": edge["status"],
                              "reason": edge.get("reason")})
    report = {
        "status": "BLOCKED" if (integrity or inventory.unparsed or operation_gaps or edge_gaps or
                               any(boundaries["summary"][key] for key in (
                                   "unresolvedOperationReferences", "genericRoutes",
                                   "unreviewedConcreteBoundaryDefinitions", "nestedReferenceFailures",
                               "conflictingSchemaIdentities"))) else "NOT_CERTIFIED_SEMANTIC_REVIEW_REQUIRED",
        "source": "00_SSOT/KajovoCMLNG_SSOT.md",
        "sourceSha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "sourceLineCount": len(text.splitlines()),
        "embeddedResources": len(inventory.items),
        "unparsedResources": inventory.unparsed,
        "resourceDigestMismatches": integrity,
        "operationBoundarySummary": boundaries["summary"],
        "operationGaps": operation_gaps,
        "handoffSummary": handoffs["summary"],
        "handoffDigestRelations": dict(sorted(edge_groups.items())),
        "handoffGaps": edge_gaps,
        "scope": "Mechanická inventura každého vloženého resource, efektivní operace a modelované předávky. "
                 "Rovnost digestů je nutná, ale neprokazuje správný transport, adapter ani obchodní význam. "
                 "Nejde o ruční sémantické přečtení všech řádků.",
    }
    destination = ROOT / "audit/generated/mask-parity.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = audit()
    print(json.dumps({"status": result["status"], "sourceSha256": result["sourceSha256"],
                      "operations": result["operationBoundarySummary"]["operations"],
                      "handoffDigestRelations": result["handoffDigestRelations"],
                      "resourceDigestMismatches": len(result["resourceDigestMismatches"])}))
    # No per-contract semantic signoffs exist in this repository. Even a future
    # structurally clean census must not be advertised as a complete audit.
    sys.exit(1)
