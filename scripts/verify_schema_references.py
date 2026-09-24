"""Resolve operation, route and event schemas, including scoped nested refs.

Domain closure is a separate (stricter) phase1_schema_closure check.
Dependencies are mandatory; import or resolution failures cannot yield PASS.
"""
import json
import sys
from ssot_sources import ROOT, SSOT
from phase1_schema_closure import build, pointer


def resolve(value, fragment):
    return pointer(value, fragment)


def run():
    _, matrix = build(SSOT.read_text(encoding='utf8'))
    checks=[]
    for op in matrix['operations']:
        boundaries = op['boundaries'] + [b for r in op['routes'] for b in r['boundaries']]
        for b in boundaries:
            checks.append({'operationId':op['operationId'], **b,
                           'status':'PASS' if b['resolution']=='RESOLVED' and not b.get('nestedReferenceFailures') else 'FAIL'})
    result={'scope':'Effective operation bindings, request/response/event schemas, dialect and scoped nested refs; not semantic completeness.',
            'checks':checks,'checked':len(checks),'failed':sum(c['status']=='FAIL' for c in checks),
            'unparsedResources':matrix['unparsedResources']}
    (ROOT/'audit/generated/schema-reference-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return result


if __name__=='__main__':
    report=run()
    print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
    sys.exit(bool(report['failed'] or report['unparsedResources'] or not report['checked']))
