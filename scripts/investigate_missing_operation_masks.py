"""Continue the e025079 missing-reference worklist with current source evidence.

Discovery is not semantic classification: undecided rows remain INVESTIGATION_OPEN,
never OWNER_REQUIRED merely because no identity or route was found.
"""
import hashlib
import json
import os
import re
import subprocess

from close_generation_operation_masks import OPERATIONS, CATALOG, SAGA, GEN
from phase1_schema_closure import build
from ssot_sources import ROOT, SSOT


def main():
    raw = SSOT.read_bytes()
    text = raw.decode('utf8')
    inv, matrix = build(text)
    baseline = json.loads(subprocess.check_output([
        'git', 'show', 'e025079:audit/phase1-operation-schema-matrix.json']))
    wanted = {o['operationId']: o for o in baseline['operations']
              if any(b['resolution'] == 'UNRESOLVED' for b in o['boundaries'])}
    # Exclude embedded resources from prose search, preserving physical lines.
    spans = [(r['match'].start(), r['match'].end()) for r in inv.items]
    prose, cursor = [], 0
    for start, end in sorted(spans):
        prose.extend([text[cursor:start], '\n' * text[start:end].count('\n')])
        cursor = end
    prose.append(text[cursor:])
    lines = ''.join(prose).splitlines()
    headings = [(i, re.match(r'^#{1,6}\s+(\d+(?:\.\d+)*)\s+(.+)', line))
                for i, line in enumerate(lines)]
    headings = [(i, m.group(1), m.group(2)) for i, m in headings if m]
    sections = {}
    for index, (start, number, title) in enumerate(headings):
        end = headings[index+1][0] if index+1 < len(headings) else len(lines)
        sections.setdefault(number, []).append({'line': start+1, 'title': title,
            'text': '\n'.join(lines[start:end]).strip()})
    operations = {o['operationId']: o for o in matrix['operations']}
    records = {o['operationId']: o for o in inv.docs['contracts/operation-contracts.json']['records']}
    rows = []
    for oid, old in sorted(wanted.items()):
        op = operations[oid]
        source_sections = [s['section'] for s in records[oid].get('authoritySourceRefs', [])]
        if oid in OPERATIONS:
            source_sections += ['56.8', '56.9', '56.12', '56.4']
        excerpts = {s: sections.get(s, []) for s in source_sections}
        refs = sorted(set(re.findall(r'urn:kcml:[^\s"`<>]+',
                                    '\n'.join(e['text'] for v in excerpts.values() for e in v))))
        exact_mentions = [{'line': i+1, 'text': line.strip()} for i, line in enumerate(lines)
                          if oid in line and re.search(r'(?<![\w.])'+re.escape(oid)+r'(?![\w.])', line)]
        rows.append({'operationId': oid, 'operationSource': op['source'],
                     'baselineMissingReferences': [b for b in old['boundaries'] if b['resolution']=='UNRESOLVED'],
                     'currentBoundaries': op['boundaries'], 'currentRoutes': op['routes'],
                     'authoritySections': excerpts, 'exactProseMentions': exact_mentions,
                     'schemaReferencesInAuthorityText': refs,
                     'explicitStepBindings': [r for r in inv.docs[CATALOG] if r['canonicalOperationId']==oid],
                     'explicitSagaBindings': [r for r in inv.docs[SAGA] if r['operationId']==oid],
                     'classification': ('EXACT_DEFINITION_EXISTS' if oid in
                        ('generation.workspace.validate', 'generation.activation.switch') else
                        'DETERMINISTIC_DERIVATION_FROM_EXPLICIT_CATALOG' if oid in OPERATIONS else
                        'INVESTIGATION_OPEN'),
                     'ownerDecisionRequired': False if oid in OPERATIONS else None,
                     'remaining': 'Content hydration and runtime guards remain separate obligations.' if oid in OPERATIONS else
                        'Read authoritative sections and related schemas; decide semantic equivalence '
                        'and complete input/output coverage before assigning one of the four final categories.'})
    result = {'sourceSha256': hashlib.sha256(raw).hexdigest(), 'baselineCommit': 'e025079',
              'scope': __doc__, 'baselineOperations': len(wanted), 'currentSummary': matrix['summary'],
              'reviewedOperationBindings': len(OPERATIONS),
              'unclassifiedOperations': len(wanted)-len(OPERATIONS), 'operations': rows}
    directory = ROOT / os.environ.get('KCML_AUDIT_OUTPUT', 'audit/generated')
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory/'missing-operation-investigation.json'
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    (directory/'current-operation-schema-matrix.json').write_text(
        json.dumps({'sourceSha256': result['sourceSha256'], **matrix}, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k:result[k] for k in ('sourceSha256','baselineOperations','currentSummary',
                                          'reviewedOperationBindings','unclassifiedOperations')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
