"""Scoped current evidence for three generation routes and four MCP list pairs.

This continues the existing dossier. It is not a new inventory or closure oracle.
"""
import hashlib
import json
import os
import subprocess
from ssot_sources import ROOT,SSOT,resource_index,resources
from close_mcp_list_operation_masks import OPERATIONS,PATH,NATIVE,ARTIFACT
from investigate_missing_operation_masks import authority_sections
from acceptance_gates import DESIGN,PRODUCTION


def main():
    raw=SSOT.read_bytes();text=raw.decode();rs=resource_index(resources(text))
    baseline=subprocess.check_output(['git','show','664d617:00_SSOT/KajovoCMLNG_SSOT.md'])
    old=resource_index(resources(baseline.decode()))
    before=json.loads(old[PATH]['raw']);after=json.loads(rs[PATH]['raw'])
    old_defs=before.pop('$defs');new_defs=after.pop('$defs')
    assert before==after,'Non-schema operation record changed'
    assert all(new_defs[k]==v for k,v in old_defs.items()),'Previous schema repair changed'
    added=set(new_defs)-set(old_defs)
    expected={op+':'+role for op in OPERATIONS for role in ['command','response']}|{'mcp.native.2026-07-28'}
    assert added==expected,'Unexpected schema additions'
    manifest=json.loads(rs['manifest.json']['raw'])
    for resource_path in [PATH,NATIVE]:
        entry=manifest['resources'][resource_path]
        assert entry['sizeBytes']==len(rs[resource_path]['raw'])
        assert entry['sha256']=='sha256:'+rs[resource_path]['sha256']
    sections=authority_sections(text.splitlines())
    excerpts={s:sections[s] for s in ['12.19','12.21','12.23','12.44','26.15','49.5','10.3','10.4','10.7','10.11','10.14','10.16.1']}
    records=json.loads(rs['contracts/payload-contracts.json']['raw'])['records']
    rows={r['routeId']:r for r in records};indices={r['routeId']:i for i,r in enumerate(records)}
    generation=[]
    operations_by_id={r['operationId']:r for r in after['records']}
    for rid in ['route.0234','route.0232','route.0237']:
        row=rows[rid];approve=rid=='route.0234'
        generation.append({'routeId':rid,'operationId':row['operationId'],'status':'BLOCKED','subtractFromGenericRoutes':False,
            'operationRecordEvidence':{key:operations_by_id[row['operationId']][key] for key in
                ['sideEffectClass','possibleEffectTrigger','outboxPurposes','auditEventTypes','authoritySourceRefs']},
            'request':{'source':f'contracts/payload-contracts.json#/records/{indices[rid]}/requestSchema',
                'proven':'12.44.3 wire request: exact path, empty query, approval six-field body plus CAS; read body null; OWNER Bearer/session and conditional CSRF.',
                'contract':'contracts/generation/http-design.schema.json#/transportBindings/'+rid,
                'remaining':'Compose public admission with current coordinator/phase context.' if approve else None},
            'response':{'source':f'contracts/payload-contracts.json#/records/{indices[rid]}/responseSchema',
                'proven':'12.44.3 exact persisted approval receipt or native immutable document; success meta; explicit failure masks and HTTP status; no ACCEPTED-as-success.',
                'remaining':'Complete phase/fence/checkpoint error dispatch and receipt-to-native-commit composition.' if approve else 'Compose transport response validator with consistent repository snapshot and native read predicate in the complete route gate.'},
            'event':{'source':f'contracts/payload-contracts.json#/records/{indices[rid]}/eventSchema',
                'eventApplicability':row.get('eventApplicability'),
                'effectiveSchema':row['eventSchema'],
                'sourceSections':['12.21','12.44','26.15','49.5'] if approve else ['12.44','26.15','49.5'],
                'proven':'OWNER 12.44.1: exact aggregate approval envelope and pointer/digest; no second lifecycle stream.' if approve else 'OWNER 12.44.1: request/response only; rejecting eventSchema; audit separate.',
                'missingMeaning':None,
                'remainingVerification':'Integrate abstract atomic phase model with native committed event/receipt predicates.' if approve else 'Payloads and exact stream-to-read selectors now defined in document-events.schema.json and checked by native predicates; whole route coverage gate remains separate.',
                'noSchemaSubstitution':'SseEnvelope.payload is JsonValue; referencing it alone would not close the domain mask.'}})
    handoffs=[{'producer':'Persisted immutable '+kind,'consumer':op+' response -> native '+definition+' validator',
               'sameMask':definition,'checks':'trusted job + persisted document ID + canonical content digest; failure/cancel/pending is not a document',
               'failureRecovery':'No downstream document on failure; a new confirmed read must match the trusted persisted snapshot.',
               'remaining':'Complete route-level composition/coverage; lack of deployed repository is not a design blocker',
               'productionObligations':'Actual PostgreSQL consistent snapshot, immutable triggers/composite FK, exact lookup and deployed failure/retry integration'}
              for kind,op,definition in [('specification revision','generation.spec.revision.read','GenerationSpecification'),('plan','generation.plan.read','GenerationPlan')]]
    for op,(method,native,field) in OPERATIONS.items():
        handoffs.append({'producer':method+' server response','consumer':'list client -> immutable discovery snapshot admission',
            'requestMask':'urn:kcml:r9:operation:'+op+':command','responseMask':'urn:kcml:r9:operation:'+op+':response',
            'sameMask':NATIVE+'#/$defs/'+native+'ResultResponse',
            'checks':'exact RPC ID type/value; complete result; typed '+field+' entries; TTL/cacheScope; empty nextCursor retained; no MRTR/Tasks',
            'failureRecovery':'Protocol error is not a snapshot; MCP_CURSOR_INVALID requires discarding traversal and starting without cursor (10.7). Read-only disconnect may abort, then a fresh request (10.3.1/10.12).',
            'eventBoundary':'No dedicated HTTP route. Request-scoped SSE under 10.3.1 is distinct from replayable aggregate events, and remains an integration obligation.',
            'remaining':'HTTP admission/header parity; actual persisted snapshot/cache key context and bounded refetch/aggregate consistency; notification/cancellation integration'})
    report={'sourceSha256':hashlib.sha256(raw).hexdigest(),'baselineCommit':'664d617',
        'resourceVersions':{p:rs[p]['sha256'] for p in [PATH,NATIVE,ARTIFACT,'contracts/payload-contracts.json','scripts/ssot/ssot_control.py']},
        'status':'BLOCKED','wholeRoutesClosed':[], 'operationRecordsAndPreviousSchemasUnchanged':True,
        'readinessGates':{DESIGN:{'status':'BLOCKED','reason':'Remaining design composition/error-dispatch obligations are explicit per route; not missing live infrastructure'},
                         PRODUCTION:{'status':'NOT_EVALUATED','reason':'No running application; real DB/queue/SSE/provider/UI and fault tests remain mandatory during implementation'}},
        'historicalCorrection':{'report':'audit/SSOT_CONTINUATION_5d72ccd.md',
            'meaning':'Its real DB/outbox/SSE integration work belongs to IMPLEMENTATION_PRODUCTION_ACCEPTANCE, not by itself to SSOT_CONTRACT_READY. Historical file/hash unchanged.'},
        'newOperationMasks':{k:new_defs[k] for k in sorted(added) if k!='mcp.native.2026-07-28'},
        'sourceExcerpts':excerpts,'generationRoutes':generation,'handoffs':handoffs,
        'nextIndividuallyInvestigated':[
            {'operationId':'mcp.prompts.get','classification':'INVESTIGATION_OPEN','ownerDecisionRequired':False,
             'source':'10.11/10.14; native GetPromptRequestParams/GetPromptResultResponse/InputRequiredResult',
             'concreteRemaining':'Native arguments is a string map, not the exact selected immutable prompt argument contract. Prove name/revision binding and domain argument validation, allowed resource references, MRTR state/recognized responses before binding the whole pair.'},
            {'operationId':'mcp.resources.read','classification':'INVESTIGATION_OPEN','ownerDecisionRequired':False,
             'source':'10.7/10.11/10.14; native ReadResourceRequestParams/ReadResourceResultResponse/InputRequiredResult',
             'concreteRemaining':'Resolve URI/template to exact revision/MIME/output contract. Text/blob wire content alone is not proof of domain content compatibility; MRTR and cache exclusions must also be implemented.'}]}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-7006785/design');out.mkdir(parents=True,exist_ok=True)
    (out/'read-boundary-evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({'sourceSha256':report['sourceSha256'],'previousDefinitionsPreserved':len(old_defs),'addedOperationMasks':len(added)-1,'wholeRoutesClosed':0}));return 0


if __name__=='__main__':raise SystemExit(main())
