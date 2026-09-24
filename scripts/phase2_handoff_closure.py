"""Source-derived handoff census. Unknown semantics fail closed, never PASS.

Candidate source occurrences are kept separately from proved dataflow edges.
Equal kinds do not establish an execution dependency. --check compares the whole
regenerated matrix, so removing a row or discovered source cannot hide a gap.
"""
import argparse
import hashlib
import json
from collections import Counter
from ssot_sources import ROOT, SSOT
from phase1_schema_closure import Inventory, walk
from operation_catalog import catalog
from phase2_repair_handoffs import ADDITIONS, GEN, MAP

def digest(value):
    return 'sha256:'+hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def build(text):
    inv=Inventory(text); docs=inv.docs; ops=catalog(inv.rs)
    mapping=docs[MAP]; raw=docs['contracts/execution/raw-artifact-kinds.json']; gs=docs[GEN]
    orchestration='r11/contracts/orchestration.schema.json'
    edges=[]; slots=[]; candidates=[]
    def edge(identity,producer,consumer,source,kind=None,**kw):
        row=dict(id=identity,producer=producer,producerSlot=None,consumer=consumer,consumerSlot=None,
            artifactKind=kind,source=source,producerAuthority=None,consumerAuthority=None,
            sourceSchema=None,targetSchema=None,sourceSchemaVersion=None,targetSchemaVersion=None,
            sourceSchemaDigest=None,targetSchemaDigest=None,branch=None,state=None,transport=None,
            payload=None,cardinality=None,optional=None,nullable=None,adapter=None,
            classification='UNRESOLVED_ENDPOINT_CLASSIFICATION',status='NOT_VERIFIED',
            reason='No complete compatibility proof; absence is not a no-payload contract.',evidence=[])
        row.update(kw);edges.append(row);return row
    # Every specialist input definition is discovered, not a hardcoded role count.
    for definition,schema in docs[orchestration]['$defs'].items():
        inputs=schema.get('properties',{}).get('inputs',{})
        for name,value in inputs.get('properties',{}).items():
            variants=value.get('anyOf',[value]); kinds={v.get('properties',{}).get('kind',{}).get('const') for v in variants}
            kinds.discard(None)
            if not kinds:continue
            for kind in sorted(kinds):
                target=mapping.get(kind); loc=orchestration+'#/$defs/'+definition+'/properties/inputs/properties/'+name
                producer=ADDITIONS.get(kind,(None,None))[1]
                row=edge('specialist:'+definition+':'+name,producer,definition.removesuffix('Input'),loc,kind,
                    consumerSlot='inputs.'+name,consumerAuthority=loc,transport=value,
                    optional=name not in inputs.get('required',[]),nullable=any(v.get('type')=='null' for v in variants),cardinality=1,
                    targetSchema=GEN+'#/$defs/'+target if target else None,
                    targetSchemaVersion=gs['$id'],targetSchemaDigest=digest(gs['$defs'][target]) if target else None,
                    payload=target,status='BLOCKED_MISSING_CONTRACT' if not target and kind not in raw else 'NOT_VERIFIED',
                    reason='Missing kind-to-schema mapping.' if not target and kind not in raw else 'Content mapping exists; R11 reference hydration, accepted schema digests and guarded producer branch are not proved.',
                    evidence=[MAP+'#/'+kind,'r12/contracts/model-artifact-handoff.json#/rules'])
                if producer:
                    row.update(producerSlot='proposal',producerAuthority='contracts/generation/specialist-output-map.json#/'+producer,
                        sourceSchema=GEN+'#/$defs/'+ADDITIONS[kind][0],sourceSchemaVersion=gs['$id'],
                        sourceSchemaDigest=digest(gs['$defs'][ADDITIONS[kind][0]]),
                        branch='Non-null proposal, no questions, blocker null; server validation required',
                        classification='INTERNAL_HANDOFF_REQUIRING_MATERIALIZATION',
                        adapter='UNRESOLVED: native ArtifactRef vs R11 compact artifact reference')
                slots.append(row)
    # Dynamic generation plans select actual predecessors. Record slot obligations,
    # not a fictional Cartesian product of same-kind producers and consumers.
    path='contracts/generation/step-catalog.json'; steps=docs[path]
    producers={}
    for i,step in enumerate(steps):
        for slot,kind in step['outputSlots'].items():producers.setdefault(kind,[]).append({'nodeKind':step['kind'],'slot':slot,'source':path+f'#/{i}/outputSlots/{slot}'})
    for i,step in enumerate(steps):
        for direction in ['input','output']:
            for slot,kind in step[direction+'Slots'].items():
                loc=path+f'#/{i}/{direction}Slots/{slot}';definition=step[direction+'Definition']; target=mapping.get(kind)
                edge('step:'+step['kind']+':'+direction+':'+slot,step['kind'] if direction=='output' else None,
                    step['kind'] if direction=='input' else None,loc,kind,
                    producerSlot=slot if direction=='output' else None,consumerSlot=slot if direction=='input' else None,
                    producerAuthority=loc if direction=='output' else None,consumerAuthority=loc if direction=='input' else None,
                    targetSchema=GEN+'#/$defs/'+definition,state=step['phase'],transport='ArtifactRef',payload=target,
                    classification='DYNAMIC_PLAN_SLOT_OBLIGATION',
                    branch='GenerationPlan inputBindings ROOT_ARTIFACT or predecessor output, GEN-G07; successful outputs only',
                    producerCandidates=producers.get(kind,[]) if direction=='input' else [],
                    reason='Execution-specific predecessor/terminal classification not established by catalog ordering.',
                    evidence=['contracts/generation/semantic-validation-rules.json#/6'])
    path='r11/contracts/orchestration-graph.json'
    for i,r in enumerate(docs[path]['edges']):
        edge('orchestration:'+str(i),r['from'],r['to'],path+f'#/edges/{i}',branch=r['predicate'],
            classification='CONTROL_FLOW_NOT_ASSUMED_PAYLOAD',reason='Control edge is explicit; exact payload slots and enforced branch proof remain open.',
            evidence=[path+'#/repairLoop'])
    path='contracts/generation/integration-step-catalog.json'; saga=docs[path]; by={s['stepId']:s for s in saga}
    for i,r in enumerate(saga):
        for predecessor in r['requiredPredecessorStepIds']:
            edge('saga:'+predecessor+':'+r['stepId'],predecessor,r['stepId'],path+f'#/{i}',by[predecessor]['outputKind'],
                producerSlot='outputKind',consumerSlot='requiredPredecessorStepIds',
                branch=r['postconditionId'],state='INTEGRATING',classification='INTERNAL_PREDECESSOR_RECEIPT',
                evidence=['SSOT section '+r['authoritySection']],compensation=r['compensationId'])
    # Rebuild the Phase 1 event set from current operations/routes rather than
    # trusting the historical report to define inventory coverage.
    route_events={}
    for p,doc in docs.items():
        for ptr,v in walk(doc):
            if not isinstance(v,dict):continue
            if 'operationId' in v and 'requestSchema' in v and 'responseSchema' in v and v['operationId'] in ops:
                for role in ['request','response','event']:
                    key=role+'Schema'
                    if key not in v:continue
                    loc=p+'#'+ptr+'/'+key
                    if role=='event':route_events.setdefault(v['operationId'],[]).append(loc)
                    edge('boundary:'+loc,'EXTERNAL_CALLER' if role=='request' else v['operationId'],
                        v['operationId'] if role=='request' else 'CALLER' if role=='response' else None,loc,
                        sourceSchema=loc if role!='request' else None,targetSchema=loc if role=='request' else None,
                        classification='EXTERNAL_REQUEST' if role=='request' else 'RESPONSE_TO_CALLER' if role=='response' else 'EVENT_CONSUMER_UNRESOLVED',
                        transport='route '+role,payload='schema payload, including any encoded inner content',
                        reason='Domain and inner payload compatibility not proved; see Phase 1 unresolved boundaries.')
            # Generic discovery retains all candidate source families/capsules.
            keys=set(v)
            if (keys & {'inputSlots','outputSlots','consumerOperationId','producerOperationId','eventConsumers','consumers','producer','consumer','handoffs','inputBindings','acceptedSchemaDigests'} or {'from','to'}<=keys):
                candidates.append({'source':p+'#'+ptr,'keys':sorted(keys),'digest':digest(v),'status':'NOT_VERIFIED',
                    'reason':'Candidate occurrence, not necessarily an active edge; precedence and semantic review required.'})
    events=[]
    for name,op in sorted(ops.items()):
        # Include every operation boundary, including internal operations without
        # an HTTP route. Route rows are distinct source occurrences, not deducted.
        for role,keys in [('request',['requestSchemaRef','commandSchemaRef']),('response',['responseSchemaRef'])]:
            field=next((k for k in keys if k in op),None); ref=op.get(field) if field else None
            unresolved=False
            if isinstance(ref,dict) and 'schemaId' in ref:
                unresolved=ref['schemaId'] not in inv.ids
            elif isinstance(ref,str):
                try:inv.resolve(ref)
                except (ValueError,KeyError,IndexError):unresolved=True
            elif ref is None:unresolved=True
            edge('operation:'+name+':'+role,'OPERATION_CALLER' if role=='request' else name,
                name if role=='request' else 'OPERATION_CALLER',op['sourceRef']+'/'+str(field or role),
                classification='OPERATION_BOUNDARY',referenceMechanism=field,reference=ref,
                status='BLOCKED_MISSING_CONTRACT' if unresolved else 'NOT_VERIFIED',
                reason='Missing/unresolved operation schema reference.' if unresolved else 'Binding exists; full payload compatibility remains unverified.',
                evidence=[op['sourceRef']])
        if name in route_events or op.get('eventSchemaRef'):continue
        event_fields={k:v for k,v in op.items() if any(t in k.lower() for t in ['event','outbox','successor','terminal'])}
        row=edge('event-applicability:'+name,name,None,op['sourceRef'],classification='EVENT_APPLICABILITY_UNRESOLVED',
            status='BLOCKED_MISSING_CONTRACT',reason='No bound event schema found in effective operation/route; an explicit no-event rule or concrete event and consumer is required.',
            evidence=[op['sourceRef']],operationEventRelatedFields=event_fields)
        events.append(row)
    missing=[s for s in slots if s['artifactKind'] not in mapping and s['artifactKind'] not in raw]
    summary={'effectiveOperations':len(ops),'specialistInputPositions':len(slots),
        'r11MissingKindPositions':len(missing),'r11MissingKinds':len({s['artifactKind'] for s in missing}),
        'generationNodeKinds':len(steps),'integrationSteps':len(saga),
        'matrixRows':len(edges),'sourceCandidateOccurrences':len(candidates),'eventApplicabilityBlockers':len(events),
        'artifactKindsInModeledSlots':len({e['artifactKind'] for e in edges if e['artifactKind']}),
        'namedProducers':len({e['producer'] for e in edges if e['producer']}),
        'namedConsumers':len({e['consumer'] for e in edges if e['consumer']}),
        'statuses':dict(Counter(e['status'] for e in edges)),
        'schemaIdentityConflicts':len(inv.conflicts),'completeRelevantHandoffCoverageProven':False}
    repairs=[]
    for kind,(definition,role) in ADDITIONS.items():
        repairs.append({'kind':kind,'definition':definition,'producer':role,
            'mappingPresent':mapping.get(kind)==definition,
            'producerPayloadSource':GEN+'#/$defs/'+role+'Proposal/properties/proposal/anyOf/0',
            'consumerContentSource':MAP+'#/'+kind,
            'proof':'Producer non-null proposal directly references the same definition selected by ArtifactResolver.get through the map. No schema restriction is changed. This proves content-schema identity only, NOT materialization/compact-reference compatibility.',
            'testEvidence':'audit/generated/phase2-content-tests-after.json',
            'handoffStatus':'NOT_VERIFIED'})
    return {'format':'KCML-PHASE2-HANDOFF-MATRIX/1','status':'PARTIAL','summary':summary,'mappingRepairs':repairs,
        'countingRule':'Rows include input/output obligations and control edges; not a count of proven runtime handoffs. Named endpoint counts include external caller labels.',
        'edges':edges,'discoveredCandidates':candidates,
        'sources':[{'path':p,'origin':inv.origins.get(p),'parsed':True,'manualFullSemanticReview':False} for p in sorted(docs)],
        'conflictingSchemaIdentities':inv.conflicts}

def verify_matrix(stored,current):
    if stored!=current:raise ValueError('MATRIX_COVERAGE_OR_CONTENT_DRIFT')

def main():
    p=argparse.ArgumentParser();p.add_argument('--entry',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    text=(ROOT/'.cache/phase2-entry/SSOT.md').read_text(encoding='utf8') if a.entry else SSOT.read_text(encoding='utf8')
    matrix=build(text);suffix='-before' if a.entry else ''
    dest=ROOT/f'audit/phase2-handoff-matrix{suffix}.json'
    if a.check:
        stored=json.loads(dest.read_text(encoding='utf8'))
        verify_matrix(stored,matrix)
        print('Matrix exactly reproduces source-derived inventory; closure remains PARTIAL.')
    else:
        dest.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        if not a.entry:
            unresolved={'status':'PARTIAL','summary':matrix['summary'],
                'items':[e for e in matrix['edges'] if e['status'] not in ['VERIFIED','FIXED_AND_VERIFIED','NOT_APPLICABLE_WITH_EVIDENCE']],
                'coverageBlocker':'All discovered candidates require active-authority/dataflow classification; full graph not established.',
                'phase1Remaining':json.loads((ROOT/'audit/phase1-unresolved.json').read_text(encoding='utf8'))['summary']}
            (ROOT/'audit/phase2-unresolved.json').write_text(json.dumps(unresolved,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(matrix['summary']))
    return 1  # Intentionally fail closed until complete coverage and proofs exist.

if __name__=='__main__':raise SystemExit(main())
