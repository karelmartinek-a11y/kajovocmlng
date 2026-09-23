"""Check typed history projections and absence-of-data semantics."""
import copy
import json
import sys
from datetime import datetime
from jsonschema import Draft202012Validator, FormatChecker
from ssot_sources import ROOT, load_resource


def run():
    contract=json.loads(load_resource('ui/contracts/live-experience.json')['raw'])['observability']
    schemas=[contract['querySchema'],contract['responseSchema']]
    for schema in schemas:Draft202012Validator.check_schema(schema)
    query_validator,result_validator=[Draft202012Validator(s,format_checker=FormatChecker()) for s in schemas]
    query={'fromInclusive':'2026-09-23T00:00:00Z','toExclusive':'2026-09-24T00:00:00Z','timezone':'Europe/Prague',
           'runId':None,'correlationId':None,'componentId':None,'operationId':None,'clientId':None,
           'channel':'ALL','severity':[],'cursor':None,'limit':100}
    result={'items':[],'nextCursor':None,'snapshotWatermark':'snapshot-1',
            'resolvedInterval':{k:query[k] for k in ['fromInclusive','toExclusive','timezone']},
            'coverageFrom':None,'coverageTo':None,'completeness':'UNAVAILABLE','missingSources':['audit-store'],
            'provenanceRefs':[]}
    checks=[]
    def check(name,ok):checks.append({'id':name,'status':'PASS' if ok else 'FAIL'})
    check('query.valid-fixture',not list(query_validator.iter_errors(query)))
    check('result.unavailable-explicit',not list(result_validator.iter_errors(result)))
    for name,patch in [('bad-date',{'fromInclusive':'yesterday'}),('unbounded-page',{'limit':501}),
                       ('unknown-filter',{'arbitrarySql':'SELECT 1'}),('invalid-channel',{'channel':'UNKNOWN'})]:
        bad={**query,**patch};check('query.reject-'+name,bool(list(query_validator.iter_errors(bad))))
    bad={**result,'completeness':'COMPLETE'}
    check('result.reject-complete-without-coverage',bool(list(result_validator.iter_errors(bad))))
    bad={**result,'missingSources':[]}
    check('result.reject-unavailable-without-source',bool(list(result_validator.iter_errors(bad))))
    complete={**result,'completeness':'COMPLETE','coverageFrom':query['fromInclusive'],'coverageTo':query['toExclusive'],
              'missingSources':[],'provenanceRefs':['coverage-audit-1']}
    check('result.empty-complete-with-evidence',not list(result_validator.iter_errors(complete)))
    bad={**complete,'completeness':'PARTIAL'}
    check('result.reject-partial-without-missing-source',bool(list(result_validator.iter_errors(bad))))
    def interval_valid(value):return datetime.fromisoformat(value['fromInclusive']) < datetime.fromisoformat(value['toExclusive'])
    check('semantic.ordered-interval',interval_valid(query))
    check('semantic.empty-interval-rejected',not interval_valid({**query,'toExclusive':query['fromInclusive']}))
    report={'scope':'Schema fixtures and reference semantic checks, not a live history backend query. IANA-zone admission and cursor signing remain product integration checks.', 'checks':checks}
    (ROOT/'audit/generated/observability-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    report=run();print(json.dumps(report));sys.exit(any(c['status']=='FAIL' for c in report['checks']))
