"""Snapshot completion obligations; inventory is neither semantic review nor acceptance.

Only coordinator should publish --output audit/SSOT_COMPLETION_REGISTER.json.
No source, projection, checkpoint or Git mutations are performed.
"""
import argparse
from collections import Counter
from contextlib import redirect_stdout
import hashlib
import io
import json
import re
from pathlib import Path
from phase1_schema_closure import build as schema_inventory
from ssot_sources import ROOT, SSOT


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build_register():
    raw = SSOT.read_bytes()
    source_hash = sha(raw)
    text = raw.decode('utf8')
    with redirect_stdout(io.StringIO()):
        inv, matrix = schema_inventory(text)
    obligations = []
    evidence = []
    ids = set()

    def add(identity, area, scope, authority, dependencies=(), state='OPEN', reason=None,
            level='SEMANTIC', repair=None, proof=(), blocker_kind='TECHNICAL'):
        if identity in ids:
            raise ValueError('DUPLICATE_OBLIGATION_ID:' + identity)
        ids.add(identity)
        obligations.append({'id': identity, 'area': area, 'scope': scope,
            'authoritativeSources': authority, 'dependencies': list(dependencies), 'state': state,
            'verificationLevel': level,
            'blocker': {'kind': blocker_kind, 'reason': reason} if state == 'BLOCKED' else None,
            'repair': repair, 'evidence': list(proof),
            'sourceBinding': {'ssotSha256': source_hash},
            'implementationAcceptance': 'NOT_EVALUATED'})

    def authority(pointer):
        path = pointer.split('#', 1)[0]
        origin = inv.origins.get(path, {})
        result = {'pointer': pointer, 'ssotSha256': source_hash}
        if origin.get('resourceSha256'):
            result['resourceSha256'] = origin['resourceSha256']
        elif path in inv.docs:
            result['decodedDocumentSha256'] = sha(json.dumps(inv.docs[path], sort_keys=True,
                ensure_ascii=False, separators=(',', ':')).encode())
        return result

    # Reports without an explicit SSOT binding are useful inventory, not current proofs.
    report_paths = [ROOT/'audit/phase1-operation-schema-matrix.json',
        ROOT/'audit/generated/phase1-contract-tests.json',
        ROOT/'audit/generated/repair-create-2026-09-30/create-request-tests.json',
        ROOT/'audit/generated/repair-2026-09-30/sql/literal-verification.json',
        ROOT/'audit/generated/repair-2026-09-30/lifecycle-review/field-review.json']
    loaded = {}
    for path in report_paths:
        if not path.exists():
            continue
        blob = path.read_bytes()
        report = json.loads(blob)
        declared = report.get('sourceDocumentSha256', report.get('sourceSha256'))
        fresh = declared == source_hash
        item = {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(blob),
            'declaredSSOTSha256': declared,
            'freshness': 'CURRENT_SOURCE' if fresh else 'STALE_SOURCE' if declared else 'UNBOUND_SOURCE',
            'reusableAsCurrentProof': False,
            'sourceScopeCurrent': fresh,
            'proofLimitation': 'SSOT equality alone does not bind all consumed validator/helper/environment inputs; coordinator must join runner evidence before VERIFIED'}
        evidence.append(item)
        loaded[item['path']] = (report, item)

    unresolved = {}
    for operation in matrix['operations']:
        oid = operation['operationId']
        all_boundaries = operation['boundaries'] + [b for r in operation['routes'] for b in r['boundaries']]
        for role in ('request', 'response', 'event'):
            selected = {b['reference']: b for b in all_boundaries if b['role'] == role}
            refs = [authority(ref) for ref in sorted(selected)] or [authority(operation['source'])]
            broken = [b for b in selected.values() if b['resolution'] != 'RESOLVED' or b.get('nestedReferenceFailures')]
            generic = any(b.get('concreteness') == 'GENERIC_ENVELOPE' for b in selected.values())
            unspecified = role == 'event' and operation['eventApplicability'] == 'UNSPECIFIED_NOT_ASSUMED_ABSENT'
            reason = ('Unresolved/conflicting schema reference or nested reference' if broken else
                'Explicit event applicability and payload invariants not established' if unspecified else
                'Generic domain boundary remains' if generic else
                'Resolved shape requires operation-specific semantic review')
            add('operation:' + oid + ':' + role, oid.split('.')[0],
                {'operationId': oid, 'boundary': role, 'references': sorted(selected),
                 'eventApplicability': operation['eventApplicability'] if role == 'event' else None},
                refs, state='BLOCKED' if broken or generic or unspecified else 'OPEN', reason=reason)
            for ref, b in selected.items():
                if b['resolution'] != 'RESOLVED':
                    key = (oid, ref)
                    unresolved[key] = b
        add('operation:' + oid + ':semantics', oid.split('.')[0],
            {'operationId': oid, 'coverage': 'Complete domain decision, error predicates, lifecycle and authority'},
            [authority(operation['source'])],
            ['operation:' + oid + ':' + role for role in ('request', 'response', 'event')])
        add('operation:' + oid + ':persistence-hydration', oid.split('.')[0],
            {'operationId': oid, 'coverage': 'producer → persisted artifact → reference → actual bytes → hydration → consumer → semantic postconditions; atomicity/replay/recovery'},
            [authority(operation['source'])], ['operation:' + oid + ':semantics'])

    for (oid, ref), boundary in sorted(unresolved.items()):
        add('reference:' + oid + ':' + sha(ref.encode())[:20], 'references',
            {'operationId': oid, 'reference': ref}, [authority(ref)],
            state='BLOCKED', reason=boundary['reason'], level='STRUCTURAL')

    life_path = 'audit/generated/repair-2026-09-30/lifecycle-review/field-review.json'
    if life_path in loaded:
        review, link = loaded[life_path]
        for field in review.get('remainingFields', []):
            add('state:' + field['operationId'] + ':' + field['field'], 'lifecycle',
                {'operationId': field['operationId'], 'field': field['field']},
                [authority(field['pointer']), {'section': field.get('authority'), 'ssotSha256': source_hash}],
                ['operation:' + field['operationId'] + ':response'], state='BLOCKED',
                reason=field.get('reason', 'Own authoritative lifecycle review required'), proof=[link])

    sql = inv.rs['database/operation-functions.sql']['raw'].decode()
    used = set(re.findall(r'\b(kcml_\w+_v1)\s*\(', sql))
    definitions = set()
    for path, item in inv.rs.items():
        if path.endswith('.sql'):
            definitions.update(re.findall(r'(?i)CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(\w+)', item['raw'].decode()))
    for helper in sorted(used - definitions):
        add('sql-helper:' + helper, 'SQL', {'helper': helper, 'coverage': 'Exact function definition, columns/constraints/locks/transaction/idempotency/outbox/recovery'},
            [authority('database/operation-functions.sql')], state='BLOCKED',
            reason='Called helper lacks definition in the effective direct SQL resource registry')

    errors_path = ROOT/'01_UI_CONTRACT/ui/contracts/error-message-registry.json'
    errors_raw = errors_path.read_bytes()
    errors = json.loads(errors_raw)
    pending_errors = 0
    for i, record in enumerate(errors['records']):
        incomplete = record['technical_condition']['predicateStatus'] != 'EXPLICIT' or bool(record.get('presentationCompleteness'))
        pending_errors += bool(incomplete)
        add('error-predicate:' + record['error_code'], 'errors',
            {'errorCode': record['error_code'], 'coverage': 'Producer predicate, exact failure/retry mapping and presentation'},
            [{'pointer': errors_path.relative_to(ROOT).as_posix() + '#/records/' + str(i),
              'projectionSha256': sha(errors_raw), 'normativeSection': record['technical_condition'].get('sourceSection'),
              'ssotSha256': source_hash}], state='BLOCKED' if incomplete else 'OPEN',
            reason='Code-specific predicate/retry or presentation review remains' if incomplete else None)

    # Preserve exact detector semantics used by verify_package, with stable content IDs.
    chars = list(text)
    for resource in inv.items:
        start, end = resource['match'].span()
        chars[start:end] = ['\n' if c == '\n' else ' ' for c in text[start:end]]
    prose = ''.join(chars)
    seen_lines = Counter()
    detector = re.compile(r'(?i)(předchozí verz|původn|opraven|doplněn|rozsah změn|výsledek revize|aktuální dodatek|stav po kapitola|nově přid|historick)')
    provenance = 0
    for line_number, line in enumerate(prose.splitlines(), 1):
        if not detector.search(line):
            continue
        content_id = sha(line.strip().encode())[:20]
        seen_lines[content_id] += 1
        provenance += 1
        add('provenance-detector:' + content_id + ':' + str(seen_lines[content_id]), 'provenance',
            {'line': line_number, 'detectedText': line, 'coverage': 'Resolve precedence/history overlap losslessly; detector hit is not proof of a defect'},
            [{'pointer': '00_SSOT/KajovoCMLNG_SSOT.md:' + str(line_number), 'lineSha256': sha(line.encode()), 'ssotSha256': source_hash}])

    families = inv.docs['r16/contracts/process-family-registry.json']['processFamilies']
    for i, family in enumerate(families):
        identity = family['id']
        add('process-family:' + identity, 'orchestration',
            {'processFamily': identity, 'coverage': 'Admission, lifecycle, cancellation, persistence/recovery and consumer handoffs'},
            [authority('r16/contracts/process-family-registry.json#/processFamilies/' + str(i))])
    area_sources = {'UI': 'closure/contracts/ui-action-resolution.json', 'browser': 'r10/database/browser-research.sql',
        'MCP': 'contracts/operation-contracts.json', 'agents': 'contracts/operation-contracts.json',
        'OpenAI': 'contracts/operation-contracts.json', 'monitoring': 'r16/contracts/monitor-repair-orchestration.json'}
    for area, path in area_sources.items():
        add('environment:' + area.lower(), area,
            {'coverage': 'Full mandatory cross-operation environment obligations; aggregate tracking item does not enumerate every field'},
            [authority(path)], state='OPEN')
    for action in ('dashboard.start', 'dashboard.stop', 'gen.editSpec'):
        add('ui-exposure:' + action, 'UI', {'action': action, 'coverage': 'Required OWNER exposure and exact inputs/results'},
            [authority('closure/contracts/ui-action-resolution.json')], state='BLOCKED',
            reason='Recorded exposure gap requires current-HEAD authoritative resolution; auxiliary historical review is not current proof')
    plan_path = ROOT/'audit/SSOT_GENERATION_P00_P12.md'
    plan = plan_path.read_bytes()
    for index in range(13):
        phase = 'P' + str(index).zfill(2)
        add('handoff:' + phase, 'generation-plan',
            {'phase': phase, 'coverage': 'All required outputs, exit criteria and persisted/hydrated consumer postconditions for this phase'},
            [{'pointer': plan_path.relative_to(ROOT).as_posix() + '#' + phase, 'planSha256': sha(plan),
              'precedenceSection': '73.7', 'ssotSha256': source_hash}])

    if SSOT.read_bytes() != raw:
        raise RuntimeError('SSOT_INPUT_CHANGED: regenerate from a stable source')
    return {'format': 'KCML-SSOT-COMPLETION-REGISTER/1', 'sourceDocumentSha256': source_hash,
        'sourceSnapshot': 'One canonical read; effective native resources and decoded capsules from this snapshot',
        'readiness': {'SSOT_CONTRACT_READY': 'BLOCKED', 'IMPLEMENTATION_PRODUCTION_ACCEPTANCE': 'NOT_EVALUATED'},
        'evidenceCandidates': evidence,
        'generatorBinding': {'path': 'scripts/completion_register.py', 'sha256': sha(Path(__file__).read_bytes()),
            'requirementsAuditSha256': sha((ROOT/'requirements-audit.txt').read_bytes())},
        'structuralInventory': matrix['summary'], 'obligations': obligations,
        'coverage': {'effectiveOperations': len(matrix['operations']), 'operationBoundaryObligations': len(matrix['operations']) * 3,
            'wholeOperationsSemanticallyVerified': 0, 'wholeOperationDenominator': len(matrix['operations']),
            'unresolvedReferenceObligationsDeduplicatedByOperationAndReference': len(unresolved),
            'errorPredicateRecords': len(errors['records']), 'errorPredicatesNeedingExplicitReview': pending_errors,
            'provenanceDetectorHits': provenance, 'processFamilies': len(families),
            'phaseHandoffs': 13, 'states': dict(Counter(o['state'] for o in obligations)),
            'levels': dict(Counter(o['verificationLevel'] for o in obligations)),
            'limitations': ['Inventory is not semantic review. No entire operation is marked VERIFIED by schema resolution.',
                'Overlapping obligations must not be added into a project completion percentage.',
                'Environment and P00–P12 entries are aggregate coverage obligations; exhaustive field-level review remains open.',
                'Historical/unbound report links remain labeled and cannot confer VERIFIED.',
                'Auxiliary SQL/state/UI reviews must be revalidated against this SSOT snapshot before integration.']}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'audit/generated/create-review-register/completion-register.json')
    args = parser.parse_args()
    report = build_register()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'sourceDocumentSha256': report['sourceDocumentSha256'], 'coverage': report['coverage']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
