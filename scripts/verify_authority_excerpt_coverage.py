"""Regression: dotted chapter headings and cited descendants are not omitted."""
import hashlib
import json
import os

from investigate_missing_operation_masks import authority_sections
from ssot_sources import ROOT, SSOT


def main():
    lines=['## 12. Generator','chapter intro','### 12.1 Input','required input',
           '#### 12.1.1 Detail','exact field','### 12.2 Output','server receipt',
           '## 13. Next','unrelated','## 12. Second occurrence','separate source']
    sections=authority_sections(lines)
    cases={
        'dotted_chapter_exists':'12' in sections,
        'descendant_in_chapter':'required input' in sections['12'][0]['text'],
        'nested_descendant_in_subsection':'exact field' in sections['12.1'][0]['text'],
        'sibling_excluded':'server receipt' not in sections['12.1'][0]['text'],
        'next_chapter_excluded':'unrelated' not in sections['12'][0]['text'],
        'duplicate_source_not_overwritten':len(sections['12'])==2,
        'physical_line_preserved':sections['12.1'][0]['line']==3,
    }
    actual=authority_sections(SSOT.read_text(encoding='utf8').splitlines())
    cases['actual_generation_source_present']=any('### 12.1 ' in s['text'] for s in actual.get('12',[]))
    report={'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),
            'scope':__doc__,'cases':cases,'checked':len(cases),'failed':sum(not v for v in cases.values())}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-997e835/native-integrity-final')
    out.mkdir(parents=True,exist_ok=True)
    (out/'authority-excerpt-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))
    return int(bool(report['failed']))


if __name__=='__main__':raise SystemExit(main())
