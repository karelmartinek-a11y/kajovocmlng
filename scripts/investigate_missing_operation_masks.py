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
from close_mcp_list_operation_masks import OPERATIONS as MCP_LIST_OPERATIONS, NATIVE
from phase1_schema_closure import build
from ssot_sources import ROOT, SSOT


def authority_sections(lines):
    """Keep numbered chapter punctuation and descendants of a cited chapter.

    An empty citation to section 12 must not hide the actual 12.1-12.33 text.
    This extracts evidence; it does not assign authority by document order.
    """
    headings=[]
    for i,line in enumerate(lines):
        match=re.match(r'^(#{1,6})\s+(\d+(?:\.\d+)*)(?:\.)?\s+(.+)',line)
        if match:headings.append((i,len(match.group(1)),match.group(2),match.group(3)))
    sections={}
    for index,(start,depth,number,title) in enumerate(headings):
        end=next((i for i,d,_,_ in headings[index+1:] if d<=depth),len(lines))
        sections.setdefault(number,[]).append({'line':start+1,'title':title,
            'text':'\n'.join(lines[start:end]).strip()})
    return sections


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
    sections = authority_sections(lines)
    operations = {o['operationId']: o for o in matrix['operations']}
    records = {o['operationId']: o for o in inv.docs['contracts/operation-contracts.json']['records']}
    rows = []
    directory = ROOT / os.environ.get('KCML_AUDIT_OUTPUT', 'audit/generated')
    scoped_path=directory/'read-boundary-evidence.json'
    scoped_investigations={}
    if scoped_path.exists():
        scoped=json.loads(scoped_path.read_text(encoding='utf8'))
        if scoped['sourceSha256']!=hashlib.sha256(raw).hexdigest():
            raise ValueError('Stale scoped read-boundary evidence; regenerate for current SSOT')
        scoped_investigations={r['operationId']:r for r in scoped['nextIndividuallyInvestigated']}
    for oid, old in sorted(wanted.items()):
        op = operations[oid]
        source_sections = [s['section'] for s in records[oid].get('authoritySourceRefs', [])]
        if oid in OPERATIONS:
            source_sections += ['56.8', '56.9', '56.12', '56.4']
        if oid in MCP_LIST_OPERATIONS:
            source_sections += ['10.3', '10.4', '10.7', '10.11', '10.14', '10.16.1']
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
                        'DETERMINISTIC_DERIVATION_FROM_PINNED_NATIVE_PROTOCOL' if oid in MCP_LIST_OPERATIONS else
                        'INVESTIGATION_OPEN'),
                     'ownerDecisionRequired': False if oid in OPERATIONS or oid in MCP_LIST_OPERATIONS else None,
                     'nativeProtocolBinding': ({'artifact':NATIVE,'requestDefinition':MCP_LIST_OPERATIONS[oid][1]+'Request',
                         'responseDefinition':MCP_LIST_OPERATIONS[oid][1]+'ResultResponse',
                         'failureDefinition':'JSONRPCErrorResponse','sourceSections':['10.3','10.4','10.7','10.11','10.14','10.16.1'],
                         'proofScript':'scripts/verify_read_boundary_completion.py',
                         'notWholeProcessClosure':True} if oid in MCP_LIST_OPERATIONS else None),
                     'remaining': 'Transport headers, request-scoped SSE, current cache context, real snapshot persistence and recovery integration remain separate obligations.' if oid in MCP_LIST_OPERATIONS else
                        'Content hydration and runtime guards remain separate obligations.' if oid in OPERATIONS else
                        'Read authoritative sections and related schemas; decide semantic equivalence '
                        'and complete input/output coverage before assigning one of the four final categories.'})
        if oid in scoped_investigations:
            rows[-1]['currentIndividualInvestigation']=scoped_investigations[oid]
            rows[-1]['individualInvestigationEvidence']=scoped_path.relative_to(ROOT).as_posix()
            rows[-1]['ownerDecisionRequired']=scoped_investigations[oid]['ownerDecisionRequired']
            rows[-1]['remaining']=scoped_investigations[oid]['concreteRemaining']
        if oid.startswith(('generation.','runtime.')) and oid not in OPERATIONS:
            rows[-1]['previousIndividualInvestigation']={
                'report':'audit/SSOT_CONTINUATION_897da64.md',
                'notCurrentClosureEvidence':True,
                'instruction':'Continue the per-operation analysis already recorded there; current authority excerpts above remain the source.'}
    result = {'sourceSha256': hashlib.sha256(raw).hexdigest(), 'baselineCommit': 'e025079',
              'scope': __doc__, 'baselineOperations': len(wanted), 'currentSummary': matrix['summary'],
              'reviewedOperationBindings': len(OPERATIONS)+len(MCP_LIST_OPERATIONS),
              'unclassifiedOperations': len(wanted)-len(OPERATIONS)-len(MCP_LIST_OPERATIONS), 'operations': rows}
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
