"""Synthetic domain-boundary tests; not runtime/DB commit evidence."""
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

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from close_generation_domain_payloads import APPROVAL_FIELDS, GEN, PATH, READS
from ssot_sources import ROOT, SSOT, resource_index, resources
from verify_phase2_handoffs import witness


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',action='store_true');args=parser.parse_args()
    raw=subprocess.check_output(['git','show','897da64:00_SSOT/KajovoCMLNG_SSOT.md']) if args.baseline else SSOT.read_bytes()
    rs=resource_index(resources(raw.decode()));bundle=json.loads(rs[GEN]['raw'])
    registry=Registry().with_resource(bundle['$id'],Resource.from_contents(bundle))
    validator=lambda s:Draft202012Validator(s,registry=registry,format_checker=FormatChecker())
    rows={r['routeId']:r for r in json.loads(rs[PATH]['raw'])['records']}
    module=types.ModuleType('domain_handoff_test');sys.modules[module.__name__]=module
    exec(compile(rs['scripts/ssot/ssot_control.py']['raw'],'SSOT:ssot_control.py','exec'),module.__dict__)
    with tempfile.TemporaryDirectory(prefix='kcml-domain-') as directory:
        snapshot=Path(directory)/'SSOT.md';snapshot.write_bytes(raw);doc=module.Document(snapshot)
    checks=[]
    def check(name,actual,expected):checks.append({'case':name,'actual':actual,'expected':expected,'passed':actual==expected})
    uid='00000000-0000-4000-8000-000000000001';digest='sha256:'+'a'*64
    command={k:('COMPLETED' if v is None else uid if v=='Uuid' else digest) for k,v in APPROVAL_FIELDS.items()}
    command['specificationRevisionId']='00000000-0000-4000-8000-000000000002'
    command['capabilitySnapshotId']='00000000-0000-4000-8000-000000000003'
    v=validator(rows['route.0234']['requestSchema']['properties']['body'])
    check('approval/exact-public-command',v.is_valid(command),True)
    bag={'schemaId':'urn:kcml:r9:semantic:route.0234:body','values':[]}
    check('approval/empty-generic-business-bag',v.is_valid(bag),False)
    for key in command:
        bad=copy.deepcopy(command);del bad[key];check('approval/missing/'+key,v.is_valid(bad),False)
        bad=copy.deepcopy(command);bad[key]=None;check('approval/null/'+key,v.is_valid(bad),False)
    for key,value in [('currentTurnStatus','RUNNING'),('specificationDigest','not-a-digest'),
                      ('authorityId',uid),('commit',{}),('scopeLock',{})]:
        bad={**command,key:value};check('approval/invalid-or-server-owned/'+key,v.is_valid(bad),False)
    defs=copy.deepcopy(bundle['$defs'])
    for key,value in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-25T00:00:00.000Z',
                      'RelPath':'fixture.json','JsonPointer':'','NonemptyJsonPointer':'/fixture'}.items():defs[key]={'const':value}
    admission=getattr(module,'validate_generation_approval_handoff',None)
    check('approval/snapshot-validator-present',admission is not None,True)
    if admission:
        specification=witness(defs['GenerationSpecification'],defs);specification['openQuestions']=[]
        actual_digest=module.semantic_digest(specification)
        current={'job_id':specification['jobId'],'job_state':'DISCUSSING','state_version':'0',
                 'turn_id':uid,'turn_status':'COMPLETED','specification_revision_id':command['specificationRevisionId'],
                 'specification_digest':actual_digest,'capability_snapshot_id':command['capabilitySnapshotId'],'capability_snapshot_digest':digest}
        request={'body':{**command,'specificationDigest':actual_digest},'pathParameters':{'id':specification['jobId']},
                 'guards':{'expectedStateVersion':'0','idempotencyKey':'fixture-key'}}
        def admitted(req,spec,snapshot):
            try:admission(doc,req,spec,**snapshot);return True
            except module.ContractFailure:return False
        check('approval/current-server-snapshot',admitted(request,specification,current),True)
        for field,newvalue in [('job_state','ANALYZING'),('turn_status','RUNNING'),('state_version','1'),
                               ('turn_id','00000000-0000-4000-8000-000000000099'),
                               ('specification_revision_id','00000000-0000-4000-8000-000000000099'),
                               ('capability_snapshot_id','00000000-0000-4000-8000-000000000099'),
                               ('capability_snapshot_digest','sha256:'+'b'*64)]:
            check('approval/stale/'+field,admitted(request,specification,{**current,field:newvalue}),False)
        changed=copy.deepcopy(specification);changed['jobId']='00000000-0000-4000-8000-000000000099'
        check('approval/wrong-job-document',admitted(request,changed,current),False)
        changed=copy.deepcopy(specification);changed['objective']['statement']='Changed business objective'
        check('approval/modified-document-remains-schema-valid',validator({'$ref':bundle['$id']+'#/$defs/GenerationSpecification'}).is_valid(changed),True)
        check('approval/modified-document-same-digest',admitted(request,changed,current),False)
        changed=copy.deepcopy(specification);changed['openQuestions']=[witness(defs['Question'],defs)]
        check('approval/open-question-document-is-schema-valid',validator({'$ref':bundle['$id']+'#/$defs/GenerationSpecification'}).is_valid(changed),True)
        question_digest=module.semantic_digest(changed)
        question_request=copy.deepcopy(request);question_request['body']['specificationDigest']=question_digest
        check('approval/open-question-blocks-even-matching-digest',admitted(question_request,changed,{**current,'specification_digest':question_digest}),False)
        retry=copy.deepcopy(request);retry['guards']['expectedStateVersion']='1'
        retry['guards']['idempotencyKey']='refreshed-command-key'
        check('approval/refreshed-new-command-recheck',admitted(retry,specification,{**current,'state_version':'1'}),True)
    for rid,definition in READS.items():
        sample=witness(defs[definition],defs)
        native=validator({'$ref':bundle['$id']+'#/$defs/'+definition})
        output=validator(rows[rid]['responseSchema']['properties']['output'])
        alias=f'urn:kcml:r9:semantic:{rid}:output'
        alias_registry=registry.with_resource(rows[rid]['responseSchema']['$id'],Resource.from_contents(rows[rid]['responseSchema'])).crawl()
        try:
            alias_valid=Draft202012Validator({'$ref':alias},registry=alias_registry,format_checker=FormatChecker()).is_valid(sample)
        except Exception:alias_valid=False
        check(rid+'/preserved-schema-identity-delivers-domain-document',alias_valid,True)
        check(rid+'/producer-native-document',native.is_valid(sample),True)
        check(rid+'/route-output-consumer-same-mask',output.is_valid(sample),True)
        check(rid+'/generic-slot-rejected',output.is_valid({'schemaId':f'urn:kcml:r9:semantic:{rid}:output','values':[]}),False)
        for key in bundle['$defs'][definition]['required']:
            bad=copy.deepcopy(sample);del bad[key];check(rid+'/missing/'+key,output.is_valid(bad),False)
        # An error read has no document to hand to precheck/plan validation.
        check(rid+'/failure-null-has-no-native-document',native.is_valid(None),False)
        check(rid+'/failure-null-output-permitted',output.is_valid(None),True)
        wrapper_schema=copy.deepcopy(rows[rid]['responseSchema']);wrapper_schema.pop('allOf',None)
        wrapper_schema['properties']['output']={'const':None}
        wrapper=witness(wrapper_schema,defs)
        wrapper.update(output=sample,status='SUCCEEDED',error=None,
                       logicalOperationId=uid,correlationId=uid,resultDigest=digest)
        full=validator(rows[rid]['responseSchema'])
        check(rid+'/success-wrapper',full.is_valid(wrapper),True)
        bad=copy.deepcopy(wrapper);bad['status']='FAILED'
        check(rid+'/failure-cannot-smuggle-document',full.is_valid(bad),False)
        bad=copy.deepcopy(wrapper);bad['output']=None
        check(rid+'/success-cannot-omit-document',full.is_valid(bad),False)
        handoff=getattr(module,'validate_generation_read_handoff',None)
        check(rid+'/handoff-validator-present',handoff is not None,True)
        if handoff:
            operation=rows[rid]['operationId'];params={'id':sample['jobId']}
            if definition=='GenerationPlan':params['planId']=sample['planId']
            check(rid+'/producer-to-consumer',handoff(doc,operation,params,wrapper),True)
            bad=copy.deepcopy(wrapper);bad.update(status='FAILED',output=None)
            check(rid+'/failed-read-not-consumed',handoff(doc,operation,params,bad),False)
            bad=copy.deepcopy(wrapper);bad.update(status='ACCEPTED',output=None)
            check(rid+'/pending-recovery-not-consumed',handoff(doc,operation,params,bad),False)
            for field in params:
                wrong={**params,field:'00000000-0000-4000-8000-000000000099'}
                try:handoff(doc,operation,wrong,wrapper);accepted=True
                except module.ContractFailure:accepted=False
                check(rid+'/wrong-identity/'+field,accepted,False)
            bad=copy.deepcopy(wrapper);bad['status']='FAILED'
            try:handoff(doc,operation,params,bad);accepted=True
            except module.ContractFailure:accepted=False
            check(rid+'/failure-document-injection',accepted,False)
    report={'sourceSha256':hashlib.sha256(raw).hexdigest(),'baselineCommit':'897da64' if args.baseline else None,
            'scope':__doc__,'resourceVersions':{p:rs[p]['sha256'] for p in [GEN,PATH]},
            'checked':len(checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,
            'remaining':'Events, trusted revision snapshot provenance/current DB guards and full recovery remain unclosed.'}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-897da64/generation-domain')
    out.mkdir(parents=True,exist_ok=True)
    (out/('domain-baseline.json' if args.baseline else 'domain-current.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:report[k] for k in ['sourceSha256','checked','failed']}))
    for c in checks:
        if not c['passed']:print(json.dumps(c))
    return int(bool(report['failed']))


if __name__=='__main__':raise SystemExit(main())
