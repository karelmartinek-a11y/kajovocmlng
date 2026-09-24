"""Generate non-authoritative UI projections from the embedded canonical contract."""
import csv
import io
import json
from ssot_sources import ROOT, load_resource

PATH = 'ui/contracts/live-experience.json'


def project(check=False):
    item = load_resource(PATH, 'KCML-EXPERIENCE-RESOURCE')
    contract = json.loads(item['raw'])
    outputs = {'01_UI_CONTRACT/' + PATH: item['raw']}
    # Both contracts are embedded in the canonical experience resource so the
    # standalone files consumed by the UI are reproducible projections. They
    # are deliberately distinct from the presentation/experience schemas.
    outputs['01_UI_CONTRACT/ui/contracts/live-event.schema.json'] = (
        json.dumps(contract['liveStreamSchema'], ensure_ascii=False, indent=2)+'\n').encode()
    outputs['01_UI_CONTRACT/ui/contracts/history-query.schema.json'] = (
        json.dumps(contract['observability']['historyQuerySchema'], ensure_ascii=False, indent=2)+'\n').encode()
    errors=load_resource('ui/contracts/error-presentation.json','KCML-ERRORS-RESOURCE')
    error_contract=json.loads(errors['raw'])
    outputs['01_UI_CONTRACT/ui/contracts/error-presentation.json']=errors['raw']
    outputs['01_UI_CONTRACT/ui/contracts/error-presentation.schema.json']=load_resource('ui/contracts/error-presentation.schema.json')['raw']
    all_messages=dict(contract['messages'])
    for entry in error_contract['entries']+error_contract.get('providerErrors',[])+[error_contract['fallback']]:
        all_messages[entry['messageKey']]={'cs':entry['user_message_cs'],'en':entry['user_message_en']}
    for locale in ('cs','en'):
        outputs['01_UI_CONTRACT/ui/locales/' + locale + '.json'] = (
            json.dumps({k:v[locale] for k,v in all_messages.items()},ensure_ascii=False,indent=2)+'\n').encode()
    stream = io.StringIO(newline=''); writer = csv.writer(stream,lineterminator='\n')
    writer.writerow(['view_id','state_id','component_ids','operation_ids','event_contract','viewports','sample_data'])
    for view in contract['views']:
        writer.writerow([view['id'],view['state'], '|'.join(view['components']), '|'.join(view['operations']),
                         'KCML-LIVE-EVENT/1','|'.join(contract['viewports']),'DEMONSTRATION_ONLY'])
    outputs['01_UI_CONTRACT/LIVE_VIEW_MATRIX.csv'] = stream.getvalue().encode('utf-8')
    for path, raw in outputs.items():
        out = ROOT/path
        if check:
            if not out.exists() or out.read_bytes() != raw: raise ValueError('STALE_PROJECTION:'+path)
        else:
            out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(raw)
    return outputs


if __name__ == '__main__':
    import sys
    print(json.dumps({'projections':list(project('--check' in sys.argv))}))
