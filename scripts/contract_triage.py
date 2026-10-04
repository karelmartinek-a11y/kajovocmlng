"""Classify remaining SSOT contract work without pretending structural evidence is semantic closure.

This is a planning/triage view over the existing authoritative audits. It does not
change SSOT, grant readiness, or convert unknowns into OWNER decisions.

Buckets:
- AUTO_DERIVABLE: repository already contains an explicit deterministic derivation.
- PATTERN_REVIEW: there is a concrete reusable route/boundary pattern, but semantic
  equivalence still needs one grouped review before generation is allowed.
- OWNER_DECISION: existing investigation explicitly proves ownerDecisionRequired=True.
- INVESTIGATE: no safe derivation has been established yet.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from phase1_schema_closure import build as build_phase1
from phase2_handoff_closure import build as build_phase2
from ssot_sources import ROOT, SSOT


OUT = ROOT / "audit/generated/contract-triage.json"
INVESTIGATION = ROOT / "audit/generated/missing-operation-investigation.json"


def regenerate_investigation() -> dict:
    result = subprocess.run(
        [sys.executable, "scripts/investigate_missing_operation_masks.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            "investigate_missing_operation_masks.py failed\n"
            + result.stdout
            + "\n"
            + result.stderr
        )
    return json.loads(INVESTIGATION.read_text(encoding="utf8"))


def boundary_rows(operation: dict) -> list[dict]:
    rows = list(operation.get("boundaries", []))
    for route in operation.get("routes", []):
        for boundary in route.get("boundaries", []):
            rows.append({**boundary, "routeId": route.get("routeId")})
    return rows


def open_boundary(boundary: dict) -> bool:
    return (
        boundary.get("resolution") != "RESOLVED"
        or boundary.get("concreteness") == "GENERIC_ENVELOPE"
        or bool(boundary.get("nestedReferenceFailures"))
    )


def reusable_exact_route_patterns(operation: dict) -> list[dict]:
    """Find conservative pattern candidates, never automatic closure.

    A candidate requires exactly one concrete resolved route boundary for the same
    role while the operation-level boundary of that role is still open. This is
    useful evidence for grouped review, but it does not assume route == operation.
    """
    result = []
    operation_open_roles = {
        b.get("role")
        for b in operation.get("boundaries", [])
        if open_boundary(b)
    }
    for role in sorted(r for r in operation_open_roles if r in {"request", "response"}):
        candidates = []
        for route in operation.get("routes", []):
            for b in route.get("boundaries", []):
                if (
                    b.get("role") == role
                    and b.get("resolution") == "RESOLVED"
                    and b.get("concreteness") != "GENERIC_ENVELOPE"
                    and not b.get("nestedReferenceFailures")
                ):
                    candidates.append(
                        {
                            "routeId": route.get("routeId"),
                            "reference": b.get("reference"),
                            "target": b.get("target"),
                            "targetIdentity": b.get("targetIdentity"),
                        }
                    )
        if len(candidates) == 1:
            result.append(
                {
                    "kind": "SINGLE_CONCRETE_ROUTE_BOUNDARY",
                    "role": role,
                    "candidate": candidates[0],
                    "warning": "Candidate for grouped semantic review; not proof that transport route shape equals operation contract.",
                }
            )
    return result


def classify_operation(operation: dict, investigation: dict | None) -> tuple[str, list[str], list[dict]]:
    reasons: list[str] = []
    patterns: list[dict] = []

    if investigation:
        explicit = investigation.get("classification")
        owner = investigation.get("ownerDecisionRequired")
        if owner is True:
            return "OWNER_DECISION", ["Existing individual investigation explicitly marks ownerDecisionRequired=true."], []
        if explicit in {
            "EXACT_DEFINITION_EXISTS",
            "DETERMINISTIC_DERIVATION_FROM_EXPLICIT_CATALOG",
            "DETERMINISTIC_DERIVATION_FROM_PINNED_NATIVE_PROTOCOL",
        }:
            return "AUTO_DERIVABLE", [f"Existing investigation classification: {explicit}."], []

    patterns = reusable_exact_route_patterns(operation)
    if patterns:
        reasons.append(
            "At least one open operation boundary has exactly one concrete route-level boundary of the same role."
        )
        reasons.append(
            "This is only a reusable-pattern candidate; one grouped semantic proof is required before automating it."
        )
        return "PATTERN_REVIEW", reasons, patterns

    reasons.append("No repository-backed deterministic derivation or explicit OWNER decision was established.")
    return "INVESTIGATE", reasons, []


def main() -> int:
    raw = SSOT.read_bytes()
    source_sha = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf8")

    investigation = regenerate_investigation()
    if investigation.get("sourceSha256") != source_sha:
        raise RuntimeError("Regenerated investigation is stale against current SSOT")

    _, phase1 = build_phase1(text)
    phase2 = build_phase2(text)

    investigations = {row["operationId"]: row for row in investigation.get("operations", [])}
    rows = []
    counts = Counter()
    open_boundaries_total = 0
    event_applicability_open = 0

    for op in phase1["operations"]:
        boundaries = boundary_rows(op)
        open_boundaries = [b for b in boundaries if open_boundary(b)]
        event_open = op.get("eventApplicability") == "UNSPECIFIED_NOT_ASSUMED_ABSENT"
        if not open_boundaries and not event_open:
            continue

        bucket, reasons, patterns = classify_operation(op, investigations.get(op["operationId"]))
        counts[bucket] += 1
        open_boundaries_total += len(open_boundaries)
        event_applicability_open += int(event_open)

        rows.append(
            {
                "operationId": op["operationId"],
                "bucket": bucket,
                "reasons": reasons,
                "patterns": patterns,
                "openBoundaryCount": len(open_boundaries),
                "eventApplicabilityOpen": event_open,
                "openBoundaries": [
                    {
                        k: b.get(k)
                        for k in (
                            "role",
                            "routeId",
                            "reference",
                            "resolution",
                            "concreteness",
                            "reason",
                            "target",
                            "targetIdentity",
                            "nestedReferenceFailures",
                        )
                        if b.get(k) is not None
                    }
                    for b in open_boundaries
                ],
                "authoritySourceRefs": op.get("authoritySourceRefs", []),
                "investigationClassification": investigations.get(op["operationId"], {}).get("classification"),
                "ownerDecisionRequired": investigations.get(op["operationId"], {}).get("ownerDecisionRequired"),
            }
        )

    handoff_statuses = Counter(edge.get("status") for edge in phase2["edges"])
    handoff_classes = Counter(edge.get("classification") for edge in phase2["edges"] if edge.get("status") != "VERIFIED")

    report = {
        "format": "KCML-CONTRACT-TRIAGE/1",
        "source": "00_SSOT/KajovoCMLNG_SSOT.md",
        "sourceSha256": source_sha,
        "scope": __doc__,
        "safetyRule": "Unknown means INVESTIGATE. Triage never grants CONTRACT CLOSED, IMPLEMENTATION READY, or production acceptance.",
        "summary": {
            "effectiveOperations": phase1["summary"]["operations"],
            "operationsNeedingContractWork": len(rows),
            "openBoundaryOccurrences": open_boundaries_total,
            "eventApplicabilityOpenOperations": event_applicability_open,
            "operationBuckets": dict(sorted(counts.items())),
            "phase1": phase1["summary"],
            "phase2": phase2["summary"],
            "handoffStatuses": dict(sorted(handoff_statuses.items(), key=lambda x: str(x[0]))),
            "openHandoffClassifications": dict(sorted(handoff_classes.items(), key=lambda x: str(x[0]))),
        },
        "executionOrder": [
            "AUTO_DERIVABLE: materialize in batches with existing deterministic rules and run negative tests.",
            "PATTERN_REVIEW: prove each pattern family once, encode the rule, then batch-generate all matching members.",
            "INVESTIGATE: group by authority/domain and resolve semantics; do not escalate merely because discovery failed.",
            "OWNER_DECISION: present only the minimal undecidable questions already evidenced by individual investigation.",
        ],
        "operations": sorted(rows, key=lambda r: (r["bucket"], r["operationId"])),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")

    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
