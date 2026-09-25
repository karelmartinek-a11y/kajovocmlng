"""12.44.1 explicit read failure; preserves existing error shape/taxonomy.

Synthetic contract and handoff evidence only. Error-code applicability and
HTTP mapping remain separate semantic investigation, not closed by this test.
"""
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
from referencing import Registry,Resource
from ssot_sources import ROOT,SSOT,resources,resource_index
from close_generation_domain_payloads import GEN,PATH,READS,READ_FAILURE_RULE
from verify_phase2_handoffs import witness

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',action='store_true');args=p.parse_args()
    base=subprocess.check_output(['git','show','5d72ccd:00_SSOT/KajovoCMLNG_SSOT.md'])
    raw=base if args.baseline else SSOT.read_bytes();rs=resource_index(resources(raw.decode()))
    old=resource_index(resources(base.decode()));bundle=json.loads(rs[GEN]['raw'])
    records=json.loads(rs[PATH]['raw'])['records'];previous=json.loads(old[PATH]['raw'])['records']
    expected=copy.deepcopy(previous)
    for row in expected:
        if row['routeId'] in READS:row['responseSchema']['allOf'].append(READ_FAILURE_RULE)
    registry=Registry().with_resource(bundle['$id'],Resource.from_contents(bundle))
    validator=lambda s:Draft202012Validator(s,registry=registry,format_checker=FormatChecker())
    checks=[]
    def check(name,actual,expected=True):checks.append({'case':name,'actual':actual,'expected':expected,'passed':actual==expected})
    check('only-two-explicit-failure-rules-added',records==expected)
    check('native-masks-unchanged',rs[GEN]['raw']==old[GEN]['raw'])
    module=types.ModuleType('read_error_test');sys.modules[module.__name__]=module
    exec(compile(rs['scripts/ssot/ssot_control.py']['raw'],'SSOT:ssot_control.py','exec'),module.__dict__)
    check('native-predicates-unchanged',rs['scripts/ssot/ssot_control.py']['raw']==old['scripts/ssot/ssot_control.py']['raw'])
    with tempfile.TemporaryDirectory(prefix='kcml-read-errors-') as directory:
        file=Path(directory)/'SSOT.md';file.write_bytes(raw);doc=module.Document(file)
    defs=copy.deepcopy(bundle['$defs'])
    for key,value in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-25T00:00:00.000Z',
                      'RelPath':'fixture.json','JsonPointer':'','NonemptyJsonPointer':'/fixture'}.items():defs[key]={'const':value}
    uid='00000000-0000-4000-8000-000000000001'
    for row in records:
        rid=row['routeId']
        if rid not in READS:continue
        value=witness(defs[READS[rid]],defs);digest=module.semantic_digest(value)
        revision='00000000-0000-4000-8000-000000000002'
        key='revisionId' if rid=='route.0232' else 'planId'
        document_id=revision if key=='revisionId' else value['planId']
        path={'id':value['jobId'],key:document_id}
        snapshot={'persisted_job_id':value['jobId'],'persisted_document_id':document_id,'persisted_document_digest':digest}
        response={'routeId':rid,'operationId':row['operationId'],'logicalOperationId':uid,'correlationId':uid,
            'status':'SUCCEEDED','terminal':True,'output':value,'error':None,'resultDigest':digest}
        v=validator(row['responseSchema'])
        handoff=lambda r:module.validate_generation_read_handoff(doc,row['operationId'],path,r,**snapshot)
        check(rid+'/exact-document',v.is_valid(response))
        check(rid+'/exact-document-consumed',handoff(response))
        for status in ['FAILED','CANCELLED']:
            # The existing R9 error taxonomy is retained, not invented here.
            error={'stableCode':'ARTIFACT_VALIDATION_FAILED','classification':'VALIDATION','retryDirective':'DO_NOT_RETRY',
                   'message':'Synthetic invalid immutable document','detailsDigest':None}
            failure={**response,'status':status,'output':None,'error':error}
            check(rid+'/'+status+'/typed-error',v.is_valid(failure))
            check(rid+'/'+status+'/no-downstream-document',handoff(failure),False)
            for invalid in [None,{},'error',False,0,[]]:
                check(rid+'/'+status+'/reject-error/'+str(invalid),v.is_valid({**failure,'error':invalid}),False)
            for field in error:
                damaged={k:v for k,v in error.items() if k!=field}
                check(rid+'/'+status+'/missing-error-field/'+field,v.is_valid({**failure,'error':damaged}),False)
            for field,invalid in [('stableCode',''),('retryDirective','RETRY_RANDOMLY'),('classification','SUCCESS'),('detailsDigest',12)]:
                check(rid+'/'+status+'/invalid-error-field/'+field,v.is_valid({**failure,'error':{**error,field:invalid}}),False)
            check(rid+'/'+status+'/error-cannot-carry-document',v.is_valid({**failure,'output':value}),False)
            check(rid+'/'+status+'/refetch-recovery-schema',v.is_valid(response))
            check(rid+'/'+status+'/refetch-recovery-handoff',handoff(response))
    report={'sourceSha256':hashlib.sha256(raw).hexdigest(),'baselineCommit':'5d72ccd','baseline':args.baseline,
        'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'resourceVersions':{p:rs[p]['sha256'] for p in [GEN,PATH,'scripts/ssot/ssot_control.py']},
        'scope':__doc__,'checks':checks,'checked':len(checks),'failed':sum(not c['passed'] for c in checks),
        'wholeRoutesClosed':[]}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-5d72ccd/read-errors');out.mkdir(parents=True,exist_ok=True)
    (out/('read-errors-baseline.json' if args.baseline else 'read-errors-current.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:report[k] for k in ['sourceSha256','baseline','checked','failed']}));return int(bool(report['failed']))

if __name__=='__main__':raise SystemExit(main())
