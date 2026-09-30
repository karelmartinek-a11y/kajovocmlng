"""12.44.2 exact persisted document events, not model outputs or read events."""
import argparse,copy,hashlib,json
from ssot_sources import SSOT,resources,resource_index
from phase1_repair_contracts import encoded
from author_resource_updates import rewrite
GEN='contracts/generation/generation-contracts.schema.json'
PATH='contracts/generation/document-events.schema.json'
IDENTITY='urn:kcml:generation-document-events:1'
CONTROL='scripts/ssot/ssot_control.py'
MANIFEST='contracts/execution/embedded-manifest.json'
EVENTS={'generation.spec.proposed':('SpecificationProposed','GenerationSpecification','specificationRevisionId','specificationDigest','revisionId','generation.spec.revision.read'),
        'generation.plan.created':('PlanCreated','GenerationPlan','planId','planDigest','planId','generation.plan.read')}

HELPER='''def validate_generation_document_event(doc,event:dict[str,Any],document:dict[str,Any],*,persisted_event:dict[str,Any],commit_snapshot:dict[str,Any],committed:bool)->dict[str,Any]:
    """12.44.2 producer -> exact read selector. Trusted arguments are server-owned."""
    doc.validate('SseEnvelope',event)
    bindings={'generation.spec.proposed':('GenerationSpecification','specificationRevisionId','specificationDigest','revisionId','generation.spec.revision.read'),
              'generation.plan.created':('GenerationPlan','planId','planDigest','planId','generation.plan.read')}
    require(event['type'] in bindings,'ARTIFACT_VALIDATION_FAILED','/type','Not a document publication event')
    definition,id_key,digest_key,path_key,operation=bindings[event['type']]
    payload=event['payload'];fields={id_key,digest_key}
    if definition=='GenerationPlan':fields.add('specificationDigest')
    require(isinstance(payload,dict) and set(payload)==fields,'ARTIFACT_VALIDATION_FAILED','/payload','Exact domain fields required')
    doc.validate('Uuid',payload[id_key]);doc.validate('Digest',payload[digest_key])
    doc.validate(definition,document)
    require(committed is True and event==persisted_event,'ARTIFACT_VALIDATION_FAILED','/commit','Only exact committed event may be published')
    require(event['objectId']==document['jobId']==commit_snapshot.get('jobId')
            and event['eventId']==commit_snapshot.get('eventSequence')
            and payload[id_key]==commit_snapshot.get('documentId')
            and payload[digest_key]==commit_snapshot.get('documentDigest')==semantic_digest(document),
            'ARTIFACT_VALIDATION_FAILED','/snapshot','Event/document/commit identity or digest mismatch')
    if definition=='GenerationPlan':
        doc.validate('Digest',payload['specificationDigest'])
        require(payload['planId']==document['planId'] and payload['specificationDigest']==document['specificationDigest']
                ==document['scopeLock']['approvedSpecificationDigest']==commit_snapshot.get('approvedSpecificationDigest'),
                'ARTIFACT_VALIDATION_FAILED','/payload','Plan does not reference the frozen approved specification')
    return {'operationId':operation,'pathParameters':{'id':event['objectId'],path_key:payload[id_key]},
            'persisted_job_id':event['objectId'],'persisted_document_id':payload[id_key],
            'persisted_document_digest':payload[digest_key]}


'''

def schema(bundle):
    ref=lambda name:{'$ref':bundle['$id']+'#/$defs/'+name}
    defs={}
    for kind,(name,document,id_key,digest_key,path_key,operation) in EVENTS.items():
        props={id_key:ref('Uuid'),digest_key:ref('Digest')}
        if name=='PlanCreated':props['specificationDigest']=ref('Digest')
        event=copy.deepcopy(bundle['$defs']['SseEnvelope'])
        event['properties']={k:ref(t) for k,t in [('eventId','Counter'),('objectId','Uuid'),('emittedAt','Timestamp')]}
        event['properties'].update(type={'const':kind},payload={'type':'object','properties':props,'required':list(props),'additionalProperties':False})
        event['description']='12.44.2: server committed immutable document, sequence and outbox; not a model receipt.'
        defs[name]=event
    # Server-owned allocation projection, not the whole plan.create command.
    defs['PlanAllocation']={'type':'object','additionalProperties':False,
        'properties':{key:ref(kind) for key,kind in [('jobId','Uuid'),('planId','Uuid'),('scopeLock','ScopeLock')]},
        'required':['jobId','planId','scopeLock']}
    return {'$schema':bundle['$schema'],'$id':IDENTITY,'$defs':defs,'oneOf':[{'$ref':'#/$defs/'+v[0]} for v in EVENTS.values()],
        'handoffs':{kind:{'producerOperationId':'generation.spec.propose' if kind=='generation.spec.proposed' else 'generation.plan.create',
            'producerRole':'server immutable document commit; specialist proposal is not a receipt',
            'eventMask':IDENTITY+'#/$defs/'+binding[0],'documentMask':bundle['$id']+'#/$defs/'+binding[1],
            'consumerOperationId':binding[5],
            'pathMapping':{'id':'objectId',binding[4]:'payload.'+binding[2]},
            'expectedDocumentDigest':'payload.'+binding[3],
            'authority':['12.19','12.23','12.44.2','49.5','51.10','56.10']} for kind,binding in EVENTS.items()}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=SSOT.read_text(encoding='utf8');items=list(resources(text));rs=resource_index(items)
    assert '#### 12.44.2 Přesné předání' in text
    updates={PATH:encoded(schema(json.loads(rs[GEN]['raw'])),rs[PATH]['raw'] if PATH in rs else b'{\n')}
    source=rs[CONTROL]['raw'].decode()
    if HELPER not in source:
        assert 'def validate_generation_document_event(' not in source
        source=source.replace('def validate_generation_approved_event(',HELPER+'def validate_generation_approved_event(')
    updates[CONTROL]=source.encode()
    native=json.loads(rs[MANIFEST]['raw'])
    for x in native['files']:
        if x['path']==CONTROL:x.update(sizeBytes=len(updates[CONTROL]),rawDigest='sha256:'+hashlib.sha256(updates[CONTROL]).hexdigest())
    updates[MANIFEST]=encoded(native,rs[MANIFEST]['raw'])
    m=json.loads(rs['manifest.json']['raw']);m['resources'][PATH]={'sizeBytes':len(updates[PATH]),'sha256':'sha256:'+hashlib.sha256(updates[PATH]).hexdigest()}
    updates['manifest.json']=encoded(m,rs['manifest.json']['raw'])
    updates={p:b for p,b in updates.items() if p not in rs or b!=rs[p]['raw']}
    if args.check:print(json.dumps({'pending':list(updates)}));return int(bool(updates))
    if updates:SSOT.write_text(rewrite(text,items,updates),encoding='utf8',newline='\n')
    print(json.dumps({'changed':list(updates),'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest()}));return 0

if __name__=='__main__':raise SystemExit(main())
