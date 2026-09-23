"""Forensic union of UI actions and canonical operations; gaps are explicit."""
import csv
import io
import json
from ssot_sources import ROOT, resources, resource_index
from operation_catalog import catalog


def build():
    rs=resource_index()
    def data(name):return json.loads(rs[name]['raw'])
    reg=data('ui/contracts/ui-control-registry.json')
    bindings=data('closure/contracts/ui-action-resolution.json')['bindings']
    overlay=data('closure/contracts/operation-overlay.json')
    universe=set(overlay['finalOperationIds'])
    base=catalog(rs)
    experience=data('ui/contracts/live-experience.json')
    placements={r['functionId']:(i,r) for i,r in enumerate(experience['dashboardSurfaceBindings'])}
    actions={(p['id'],a['id']):(p,a) for p in reg['pages'] for a in p['actions']}
    records=[]; reached=set(); specific=set()
    for index,b in enumerate(bindings):
        p,a=actions[(b['pageId'],b['actionId'])]
        ops=[b['canonicalOperationId']] if b.get('canonicalOperationId') else b.get('candidateOperationIds',[])
        ops+=b.get('followOnCanonicalOperations',[]);ops=sorted(set(ops)); reached.update(ops)
        if len(ops)<30: specific.update(ops)
        auth=b['pageId'].startswith('auth.')
        record={'functionId':'ui.'+a['id'],'label':a['label'],'source':f'ui/contracts/ui-control-registry.json#/pages/{reg["pages"].index(p)}/actions/{p["actions"].index(a)}',
          'bindingRef':f'closure/contracts/ui-action-resolution.json#/bindings/{index}',
          'operationIds':ops,'bindingKind':b['bindingKind'],'access':'AUTHENTICATION_FLOW' if auth else 'OWNER_FULL',
          'enabledWhen':a['enabledWhen'],'disabledWhen':a['disabledWhen'],'confirmation':a.get('confirmation'),
          'administrativeSurface':p['route'],'objectPanel':p['id']+'/'+a['id'],
          'dashboardTarget':'AUTHENTICATION_BOUNDARY' if auth else 'OBJECT_OR_WORKSPACE_DRAWER',
          'dashboardObserved':'EXPLICIT_PAGE_ACTION' if 'dashboard' in b['pageId'].lower() else 'NOT_IN_DASHBOARD_REFERENCE',
          'chatTarget':'AUTHENTICATION_BOUNDARY' if auth else 'LOCAL_UI_INTERACTION' if b['bindingKind']=='CLIENT_ONLY' else 'FORBIDDEN' if b['bindingKind']=='FORBIDDEN' else 'CANONICAL_COMMAND',
          'validationRefs':[base.get(o,{}).get('commandSchemaRef',base.get(o,{}).get('requestSchemaRef')) for o in ops],
          'auditEvents':{o:base.get(o,{}).get('auditEventTypes',base.get(o,{}).get('audit')) for o in ops},
          'mappingScope':'BROAD_DISPATCHER' if len(ops)>=30 else 'SPECIFIC_ACTION',
          'implementation':'NOT_PRESENT','status':'MAPPED_UI_BINDING'}
        placement_index,placement=placements[record['functionId']]
        record['surfaceBindingRef']='ui/contracts/live-experience.json#/dashboardSurfaceBindings/'+str(placement_index)
        record['dashboardTarget']=placement['dashboard']['panelId']
        record['objectPanel']=placement['dashboard']['entry']
        record['chatTarget']=placement['chat']['mode']
        records.append(record)
    operation_records=[]
    for oid in sorted(universe):
        op=base.get(oid,{})
        operation_records.append({'operationId':oid,'exposureClass':op.get('exposureClass','SOURCE_REVIEW_REQUIRED'),
            'uiFunctionIds':[r['functionId'] for r in records if oid in r['operationIds']],
            'status':'UI_BINDING_FOUND' if oid in reached else 'NO_EXPLICIT_UI_BINDING',
            'specificActionFound':oid in specific,
            'sourceContractKnown':bool(op), 'runtimeTested':False})
    report={'format':'KCML-FORENSIC-PARITY/1','source':'Canonical embedded registries; no invented operation identifiers',
        'functions':records,'operations':operation_records,
        'summary':{'functions':len(records),'operations':len(universe),'explicitlyReachedOperations':len(reached),
            'withoutExplicitUiBinding':len(universe-reached),
            'operationsWithSpecificAction':len(specific),'broadDispatcherOnly':len(reached-specific),
            'note':'Internal operations need no direct OWNER button. Unbound OWNER operations require semantic review; counts alone do not prove parity.'}}
    out=ROOT/'audit/generated/function-parity.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    stream=io.StringIO(newline='');w=csv.writer(stream,lineterminator='\n')
    w.writerow(['function_id','UI_function','canonical_operations','access','dashboard_target','dashboard_observed','object_panel','chat_target','validation_contract','audit_event','source_ref'])
    for r in records:w.writerow([r['functionId'],r['label'],'|'.join(r['operationIds']),r['access'],r['dashboardTarget'],r['dashboardObserved'],r['objectPanel'],r['chatTarget'],json.dumps(r['validationRefs'],ensure_ascii=False),json.dumps(r['auditEvents'],ensure_ascii=False),r['source']])
    (ROOT/'01_UI_CONTRACT/FUNCTION_PARITY.csv').write_text(stream.getvalue(),encoding='utf-8',newline='\n')
    return report


if __name__=='__main__':print(json.dumps(build()['summary']))
