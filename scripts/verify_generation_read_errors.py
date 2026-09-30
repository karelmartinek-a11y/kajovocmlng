"""12.44.1 read failures composed with authored 12.44.3 HTTP masks.

Synthetic contract and handoff evidence only. Complete error applicability is
a separate DESIGN obligation; deployed HTTP integration is PRODUCTION evidence.
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
from generation_http_contract import PATH as HTTP,specialize as specialize_http,CASES
from close_generation_document_events import PATH as DOCUMENT_EVENTS,HELPER as DOCUMENT_HELPER
from verify_phase2_handoffs import witness

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',action='store_true');args=p.parse_args()
    base=subprocess.check_output(['git','show','5d72ccd:00_SSOT/KajovoCMLNG_SSOT.md'])
    raw=base if args.baseline else SSOT.read_bytes();rs=resource_index(resources(raw.decode()))
    old=resource_index(resources(base.decode()));bundle=json.loads(rs[GEN]['raw'])
    payload=json.loads(rs[PATH]['raw']);records=payload['records']
    previous=json.loads(old[PATH]['raw'])
    from create_operation_contracts import PATH as CREATE_DESIGN, specialize as specialize_creates
    if CREATE_DESIGN in rs:previous=specialize_creates(previous)
    expected=copy.deepcopy(previous)
    for row in expected['records']:
        if row['routeId'] in READS:row['responseSchema']['allOf'].append(READ_FAILURE_RULE)
    if HTTP in rs:expected=specialize_http(expected,bundle)
    registry=Registry().with_resource(bundle['$id'],Resource.from_contents(bundle))
    if HTTP in rs:
        http=json.loads(rs[HTTP]['raw'])
        registry=registry.with_resource(http['$id'],Resource.from_contents(http))
    validator=lambda s:Draft202012Validator(s,registry=registry,format_checker=FormatChecker())
    checks=[]
    def check(name,actual,expected=True):checks.append({'case':name,'actual':actual,'expected':expected,'passed':actual==expected})
    check('exact-read-failure-and-authored-http-composition',records==expected['records'])
    old_rows={r['routeId']:r for r in previous['records']}
    check('same-route-universe',{r['routeId'] for r in records}==set(old_rows))
    for row in records:
        if row['routeId'] not in set(READS)|{'route.0234'}:
            check(row['routeId']+'/unchanged',row==old_rows[row['routeId']])
    # Precise technical create-error catalog additions are authoritative12.48/12.49,
    # not a reason to roll every native mask back to the historical snapshot.
    native_expected=json.loads(old[GEN]['raw'])
    if 'contracts/create-completion.json' in rs:
        from create_completion_contracts import ERRORS
        catalog=json.loads(rs['contracts/create-completion.json']['raw'])
        check('create-error-predicates-exact-current-authoring',catalog['errorPredicates']==__import__('create_completion_contracts').contract()['errorPredicates'])
        codes=native_expected['$defs']['SourceEnum110']['enum']
        for error in ERRORS:
            if error['stableCode'] not in codes:codes.append(error['stableCode'])
    check('native-masks-exact-with-scoped-create-error-extension',bundle==native_expected)
    # Independent mutations preserve the same valid positive bundle and prove
    # this composition cannot silently accept an unrelated mask change.
    for mutation in ['missing-original-error','unknown-error','unrelated-counter-change']:
        damaged=copy.deepcopy(native_expected)
        if mutation=='missing-original-error':damaged['$defs']['SourceEnum110']['enum'].pop(0)
        elif mutation=='unknown-error':damaged['$defs']['SourceEnum110']['enum'].append('MODEL_UNDECLARED_SUCCESS')
        else:damaged['$defs']['Counter']={'type':'number'}
        check('native-composition-reject/'+mutation,damaged==native_expected,False)

    module=types.ModuleType('read_error_test');sys.modules[module.__name__]=module
    exec(compile(rs['scripts/ssot/ssot_control.py']['raw'],'SSOT:ssot_control.py','exec'),module.__dict__)
    expected_native=old['scripts/ssot/ssot_control.py']['raw'].decode()
    if DOCUMENT_EVENTS in rs:
        expected_native=expected_native.replace('def validate_generation_approved_event(',
            DOCUMENT_HELPER+'def validate_generation_approved_event(')
    check('native-predicates-exact-document-event-addition',
        rs['scripts/ssot/ssot_control.py']['raw'].decode()==expected_native)
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
        if HTTP in rs:
            response['resultDigest']=module.semantic_digest({k:response[k] for k in ['status','output','error']})
            response['meta']=witness(defs['ApiConcurrencyEnvelope'],defs)
            response['meta'].update(logicalOperationId=uid,correlationId=uid,resultDigest=response['resultDigest'])
        v=validator(row['responseSchema'])
        handoff=lambda r:module.validate_generation_read_handoff(doc,row['operationId'],path,r,**snapshot)
        check(rid+'/exact-document',v.is_valid(response))
        check(rid+'/exact-document-consumed',handoff(response))
        for status in ['FAILED','CANCELLED']:
            # Preserve the historical fixture without projecting HTTP into a
            # baseline that predates it. Current cases use the authored taxonomy.
            error={'stableCode':'ARTIFACT_VALIDATION_FAILED','classification':'VALIDATION','retryDirective':'DO_NOT_RETRY',
                   'message':'Synthetic invalid immutable document','detailsDigest':None}
            if HTTP in rs:
                code='API_READ_CANCELLED' if status=='CANCELLED' else 'API_IMMUTABLE_DOCUMENT_INVALID'
                classification,_,retry,action,_,_=CASES[code]
                details={'fieldPaths':['/output'],'reason':'Synthetic invalid immutable document'}
                error={'stableCode':code,'classification':classification,'retryDirective':retry,
                    'message':'Synthetic invalid immutable document','detailsDigest':module.semantic_digest(details),
                    'details':details,'currentSnapshot':None,'nextAction':action}
            failure={**response,'status':status,'output':None,'error':error}
            if HTTP in rs:
                failure['meta']=None
                failure['resultDigest']=module.semantic_digest({k:failure[k] for k in ['status','output','error']})
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
            if HTTP in rs:
                check(rid+'/'+status+'/reject-legacy-generic-error',v.is_valid({**failure,'error':{
                    'stableCode':'ARTIFACT_VALIDATION_FAILED','classification':'VALIDATION','retryDirective':'DO_NOT_RETRY',
                    'message':'Synthetic invalid immutable document','detailsDigest':None}}),False)
                check(rid+'/'+status+'/error-cannot-carry-success-meta',v.is_valid({**failure,'meta':response['meta']}),False)
            check(rid+'/'+status+'/refetch-recovery-schema',v.is_valid(response))
            check(rid+'/'+status+'/refetch-recovery-handoff',handoff(response))
    report={'sourceSha256':hashlib.sha256(raw).hexdigest(),'baselineCommit':'5d72ccd','baseline':args.baseline,
        'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'resourceVersions':{p:rs[p]['sha256'] for p in [GEN,PATH,'scripts/ssot/ssot_control.py',HTTP] if p in rs},
        'scope':__doc__,'checks':checks,'checked':len(checks),'failed':sum(not c['passed'] for c in checks),
        'wholeRoutesClosed':[]}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-7006785/design');out.mkdir(parents=True,exist_ok=True)
    (out/('read-errors-baseline.json' if args.baseline else 'read-errors-current.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:report[k] for k in ['sourceSha256','baseline','checked','failed']}));return int(bool(report['failed']))

if __name__=='__main__':raise SystemExit(main())
