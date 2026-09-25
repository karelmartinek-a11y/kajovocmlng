"""Synthetic OWNER 12.44.1 mask/handoff regressions; not DB or SSE integration."""
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
from close_generation_event_boundaries import PATH,GEN,CONTROL,READS
from close_generation_domain_payloads import changed_payload
from phase1_schema_closure import route_event_applicability
from verify_phase2_handoffs import witness

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',action='store_true');args=p.parse_args()
    old_raw=subprocess.check_output(['git','show','2d2eea4:00_SSOT/KajovoCMLNG_SSOT.md'])
    raw=old_raw if args.baseline else SSOT.read_bytes();rs=resource_index(resources(raw.decode()))
    old=resource_index(resources(old_raw.decode()))
    bundle=json.loads(rs[GEN]['raw']);rows={r['routeId']:r for r in json.loads(rs[PATH]['raw'])['records']}
    old_rows={r['routeId']:r for r in json.loads(old[PATH]['raw'])['records']}
    expected_rows={r['routeId']:r for r in changed_payload(old)['records']}
    registry=Registry().with_resource(bundle['$id'],Resource.from_contents(bundle))
    validator=lambda s:Draft202012Validator(s,registry=registry,format_checker=FormatChecker())
    checks=[]
    def check(name,actual,expected=True):checks.append({'case':name,'actual':actual,'expected':expected,'passed':actual==expected})
    check('same-route-universe',rows.keys()==old_rows.keys())
    for rid,row in rows.items():
        if rid in READS|{'route.0234'}:
            for role in ['requestSchema','responseSchema']:check(rid+'/'+role+'-explicit-domain-delta',row[role]==expected_rows[rid][role])
        else:check(rid+'/unchanged',row==old_rows[rid])
    uid='00000000-0000-4000-8000-000000000001';revision='00000000-0000-4000-8000-000000000002'
    digest='sha256:'+'a'*64
    for rid in sorted(READS):
        row=rows[rid];v=validator(row['eventSchema'])
        check(rid+'/explicit-inapplicability',route_event_applicability(row)=='NOT_APPLICABLE')
        legacy={'routeId':rid,'operationId':row['operationId'],'eventType':'ACCEPTED','logicalOperationId':uid,
            'correlationId':uid,'sequence':'1','payload':{'schemaId':f'urn:kcml:r9:semantic:{rid}:event-payload','values':[]},'payloadDigest':digest}
        for i,value in enumerate([legacy,{},None,[],True,0,'generation.plan.created']):check(rid+'/reject/'+str(i),v.is_valid(value),False)
        bad={**row,'eventApplicability':'NOT_APPLICABLE','eventSchema':old_rows[rid]['eventSchema']}
        try:route_event_applicability(bad);accepted=True
        except ValueError:accepted=False
        check(rid+'/validator-rejects-generic-schema-under-NOT_APPLICABLE',accepted,False)
        bad={k:v for k,v in bad.items() if k!='eventSchema'}
        try:route_event_applicability(bad);accepted=True
        except ValueError:accepted=False
        check(rid+'/validator-rejects-absent-schema-under-NOT_APPLICABLE',accepted,False)
    defs=copy.deepcopy(bundle['$defs'])
    for key,value in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-25T00:00:00.000Z',
                      'RelPath':'fixture.json','JsonPointer':'','NonemptyJsonPointer':'/fixture'}.items():defs[key]={'const':value}
    spec=witness(defs['GenerationSpecification'],defs);spec['openQuestions']=[]
    module=types.ModuleType('event_handoff_test');sys.modules[module.__name__]=module
    exec(compile(rs[CONTROL]['raw'],'SSOT:ssot_control.py','exec'),module.__dict__)
    with tempfile.TemporaryDirectory(prefix='kcml-events-') as directory:
        file=Path(directory)/'SSOT.md';file.write_bytes(raw);doc=module.Document(file)
    event={'eventId':'1','type':'generation.spec.approved','objectId':spec['jobId'],
        'emittedAt':'2026-09-25T00:00:00.000Z','payload':{'specificationRevisionId':revision,'specificationDigest':module.semantic_digest(spec)}}
    v=validator(rows['route.0234']['eventSchema'])
    check('approval/exact-event',v.is_valid(event))
    legacy={'routeId':'route.0234','operationId':'generation.spec.approve','eventType':'ACCEPTED',
        'logicalOperationId':uid,'correlationId':uid,'sequence':'1','payloadDigest':digest,
        'payload':{'schemaId':'urn:kcml:r9:semantic:route.0234:event-payload','values':[]}}
    check('approval/reject-original-generic-lifecycle',v.is_valid(legacy),False)
    for key in event:
        bad=copy.deepcopy(event);del bad[key];check('approval/missing/'+key,v.is_valid(bad),False)
        bad=copy.deepcopy(event);bad[key]=None;check('approval/null/'+key,v.is_valid(bad),False)
    for key in event['payload']:
        for invalid in [None,0,{},'invalid']:
            bad=copy.deepcopy(event);bad['payload'][key]=invalid;check('approval/payload-type/'+key+'/'+str(invalid),v.is_valid(bad),False)
        bad=copy.deepcopy(event);del bad['payload'][key];check('approval/payload-missing/'+key,v.is_valid(bad),False)
    for kind in ['ACCEPTED','PROGRESS','WAITING_FOR_INPUT','RECONCILING','TERMINAL','generation.spec.proposed']:
        check('approval/no-lifecycle-coercion/'+kind,v.is_valid({**event,'type':kind}),False)
    for key,value in [('eventId',1),('eventId','01'),('eventId','9223372036854775808'),('objectId','not-a-job'),
                      ('emittedAt','2026-99-25T00:00:00.000Z'),('payload',{'schemaId':'urn:kcml:r9:semantic:route.0234:event-payload','values':[]})]:
        check('approval/invalid/'+key+'/'+str(value),v.is_valid({**event,key:value}),False)
    check('approval/no-client-status',v.is_valid({**event,'status':'SUCCEEDED'}),False)
    check('approval/no-receipt-in-payload',v.is_valid({**event,'payload':{**event['payload'],'commit':{}}}),False)
    helper=getattr(module,'validate_generation_approved_event',None);delivery=getattr(module,'generation_event_delivery_action',None)
    check('approval/persisted-handoff-validator-present',helper is not None)
    check('approval/delivery-validator-present',delivery is not None)
    if helper and delivery:
        scoped_delivery=delivery
        delivery=lambda doc,e,**kw:scoped_delivery(doc,e,stream_job_id=event['objectId'],**kw)
        try:scoped_delivery(doc,event,stream_job_id='00000000-0000-4000-8000-000000000099',last_sequence='0');accepted=True
        except module.ContractFailure:accepted=False
        check('recovery/cursor-from-another-job',accepted,False)
        snapshot={'jobId':event['objectId'],'state':'ANALYZING','eventSequence':'1',**event['payload']}
        def admitted(e=event,s=spec,persisted=event,snap=snapshot,committed=True):
            try:helper(doc,e,s,persisted_event=persisted,commit_snapshot=snap,committed=committed);return True
            except module.ContractFailure:return False
        check('handoff/persisted-approval',admitted())
        check('handoff/crash-before-commit',admitted(committed=False),False)
        check('handoff/unknown-effect-not-committed',admitted(committed=None),False)
        check('handoff/missing-snapshot',admitted(snap={}),False)
        for key,value in [('jobId',uid),('state','DISCUSSING'),('eventSequence','2'),('specificationRevisionId',uid),('specificationDigest',digest)]:
            if snapshot[key]==value:value='00000000-0000-4000-8000-000000000099'
            check('handoff/snapshot-mismatch/'+key,admitted(snap={**snapshot,key:value}),False)
        check('handoff/delivery-timestamp-not-rewritten',admitted(e={**event,'emittedAt':'2026-09-25T00:00:01.000Z'}),False)
        modified=copy.deepcopy(spec);modified['objective']['statement']='Different valid specification'
        check('handoff/schema-valid-modification',validator({'$ref':bundle['$id']+'#/$defs/GenerationSpecification'}).is_valid(modified))
        check('handoff/wrong-immutable-bytes',admitted(s=modified),False)
        check('recovery/outbox-redelivery-identical',admitted())
        check('recovery/apply-next',delivery(doc,event,last_sequence='0'),'APPLY')
        check('recovery/deduplicate',delivery(doc,event,last_sequence='1',previous_event_digest=module.semantic_digest(event)),'DUPLICATE')
        check('recovery/missing-inbox-history',delivery(doc,event,last_sequence='1'),'REPLAY_REQUIRED')
        try:delivery(doc,event,last_sequence='1',previous_event_digest=digest);accepted=True
        except module.ContractFailure:accepted=False
        check('recovery/duplicate-changed-digest',accepted,False)
        check('recovery/gap-no-apply',delivery(doc,{**event,'eventId':'3'},last_sequence='1'),'REPLAY_REQUIRED')
        paths={'id':event['objectId'],'revisionId':event['payload']['specificationRevisionId']}
        persisted={'persisted_job_id':snapshot['jobId'],'persisted_document_id':snapshot['specificationRevisionId'],
                   'persisted_document_digest':snapshot['specificationDigest']}
        read=lambda status,output:module.validate_generation_read_handoff(doc,'generation.spec.revision.read',paths,{'status':status,'output':output},**persisted)
        check('event-to-read/exact-pointer-digest',read('SUCCEEDED',spec))
        for status in ['FAILED','CANCELLED','ACCEPTED']:check('event-to-read/no-document/'+status,read(status,None),False)
        try:read('SUCCEEDED',modified);accepted=True
        except module.ContractFailure:accepted=False
        check('event-to-read/reject-changed-digest',accepted,False)
        check('event-to-read/refetch-exact-immutable-recovery',read('SUCCEEDED',spec))
    report={'sourceSha256':hashlib.sha256(raw).hexdigest(),'baseline':args.baseline,'baselineCommit':'2d2eea4',
        'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':__doc__,
        'resourceVersions':{p:rs[p]['sha256'] for p in [PATH,GEN,CONTROL]},'checks':checks,
        'checked':len(checks),'failed':sum(not c['passed'] for c in checks),'wholeRoutesClosed':[],
        'remaining':['Real DB atomic approval/outbox/inbox integration and snapshot provenance',
            'SSE Last-Event-ID bounded replay/resync integration', 'Proposed/plan.created exact payload -> immutable read mapping',
            'Read/approval request transport; approval public response; complete failure masks']}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-2d2eea4/events');out.mkdir(parents=True,exist_ok=True)
    (out/('events-baseline.json' if args.baseline else 'events-current.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:report[k] for k in ['sourceSha256','checked','failed','baseline']}));return int(bool(report['failed']))

if __name__=='__main__':raise SystemExit(main())
