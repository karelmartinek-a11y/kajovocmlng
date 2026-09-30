"""Bind config.rollback.state to the authoritative configuration apply lifecycle."""
import argparse,hashlib,json,re
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite
PATH='closure/contracts/operation-payloads.json'
OVERLAY='closure/contracts/operation-overlay.json'

def authority(text,items):
    spans=[r['match'].span() for r in items]
    headings=[m for m in re.finditer(r'^### 49\.23 .*$',text,re.M) if not any(a<=m.start()<b for a,b in spans)]
    if len(headings)!=1:raise ValueError('CONFIG_LIFECYCLE_AUTHORITY_AMBIGUOUS')
    start=headings[0].start();end=re.search(r'^### ',text[headings[0].end():],re.M)
    if end is None:raise ValueError('CONFIG_LIFECYCLE_SECTION_END_MISSING')
    stop=headings[0].end()+end.start();section=text[start:stop]
    models=[json.loads(m[1]) for m in re.finditer(r'^```json\n(.*?)^```',section,re.M|re.S)]
    models=[m for m in models if m.get('modelId')=='model.configuration-change']
    if len(models)!=1:raise ValueError('CONFIG_APPLY_MODEL_AMBIGUOUS')
    model=models[0]
    if not model['states'] or len(set(model['states']))!=len(model['states']):raise ValueError('INVALID_STATE_UNIVERSE')
    return model,{'section':'49.23','startLine':text.count('\n',0,start)+1,
        'endLine':text.count('\n',0,stop)+1,'sectionSha256':hashlib.sha256(section.encode()).hexdigest(),
        'modelId':model['modelId'],'statePointer':'/states'},section

def expected(text,items):
    rs=resource_index(items);model,source,section=authority(text,items)
    operations=json.loads(rs[OVERLAY]['raw'])['operations']
    op=next(r for r in operations if r['operationId']=='config.rollback')
    if op['aggregateRoot']!='CONFIGURATION_APPLY_RUN' or 'new configuration apply run' not in op['purpose']:
        raise ValueError('CONFIG_ROLLBACK_AGGREGATE_AUTHORITY_CHANGED')
    payload=json.loads(rs[PATH]['raw']);row=next(r for r in payload['records'] if r['operationId']=='config.rollback')
    state=row['responseSchema']['properties']['state']
    state['enum']=model['states']
    state['$comment']='SSOT 49.23 model.configuration-change /states; configuration_apply_run per 25.16 and config.rollback aggregateRoot/purpose; section sha256:'+source['sectionSha256']
    return (json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode(),source,section

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=SSOT.read_text(encoding='utf8');items=list(resources(text));rs=resource_index(items)
    raw,source,section=expected(text,items);physical=ROOT/'01_UI_CONTRACT'/PATH
    if args.check:
        exact=rs[PATH]['raw']==raw and physical.read_bytes()==raw
        print(json.dumps({'status':'PASS' if exact else 'BLOCKED','source':source,'projectionExact':exact}))
        return int(not exact)
    SSOT.write_text(rewrite(text,items,{PATH:raw}),encoding='utf8',newline='\n');physical.write_bytes(raw)
    out=ROOT/'audit/generated/repair-2026-09-30/config-state';out.mkdir(parents=True,exist_ok=True)
    (out/'authority-49.23.md').write_text(section,encoding='utf8')
    (out/'authority.json').write_text(json.dumps(source,indent=2)+'\n')
    print(json.dumps({'resource':PATH,'operation':'config.rollback','source':source}))
    return 0
if __name__=='__main__':raise SystemExit(main())
