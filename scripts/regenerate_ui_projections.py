"""Rebuild human and CSV views from canonical UI registry. No duplicate authority."""
from pathlib import Path
import json,csv
from ssot_resources import ROOT,sync_ui
C=ROOT/'01_UI_CONTRACT'
r=json.loads((C/'ui/contracts/ui-control-registry.json').read_text())
b=json.loads((C/'closure/contracts/ui-action-resolution.json').read_text());bs={x['actionId']:x for x in b['bindings']}
fields=['pageId','route','pageTitle','controlKind','controlId','label','inputType','inputProfile','required','validation','editableWhen','source','operationBinding','enabledWhen','disabledWhen','confirmation','purpose']
rows=[];parity=[];md=['# KájovoCML NG — UI katalog','', 'Odvozený pohled `ui/contracts/ui-control-registry.json`. Backend vazby určuje `closure/contracts/ui-action-resolution.json`.','']
for p in r['pages']:
 md+=['## '+p['title'],'',f"`{p['id']}` · `{p['route']}`",'',p['purpose'],'','| Akce | Backend | Dashboard | Chat |','|---|---|---|---|']
 for kind,items in [('field',p['fields']),('action',p['actions'])]:
  for a in items:
   row=dict(pageId=p['id'],route=p['route'],pageTitle=p['title'],controlKind=kind,controlId=a['id'],label=a['label'],inputType=a.get('type',''),inputProfile=a.get('inputProfile',''),required=a.get('required',''),validation=a.get('validation',''),editableWhen=a.get('editableWhen',''),source=a.get('source',''),operationBinding=a.get('operationBinding',''),enabledWhen=a.get('enabledWhen',''),disabledWhen=a.get('disabledWhen',''),confirmation=a.get('confirmation',''),purpose=a['purpose']);rows.append(row)
 for a in p['actions']:
  bind=bs[a['id']];op=bind.get('canonicalOperationId') or ' / '.join(bind.get('candidateOperationIds',[])) or bind['bindingKind']
  md.append(f"| `{a['id']}` — {a['label']} | `{op}` | {a['dashboard']['availability']} | {a['chat']['availability']} |")
  parity.append(dict(page_id=p['id'],ui_function=a['id'],label_cs=a['label'],binding_kind=bind['bindingKind'],backend_operation=op,permission=a['permission'],dashboard=a['dashboard']['availability'],dashboard_surface=a['dashboard']['surface'],chat=a['chat']['availability'],validation='canonical operation payload + shared validationPipeline',audit=a['auditContract']['event'],enabled_when=a['enabledWhen'],disabled_when=a['disabledWhen'],confirmation=a['confirmation']))
 md+=['']
with (C/'UI_CONTROLS.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
with (C/'UI_FUNCTION_PARITY.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(parity[0]));w.writeheader();w.writerows(parity)
(C/'UI_CATALOG.md').write_text('\n'.join(md)+'\n')
coverage=json.loads((C/'ui/audit/ui-coverage.json').read_text());coverage['actionCount']=len(parity);coverage['controlCount']=len(rows);coverage['scope']='STRUCTURAL_UI_REGISTRY_ONLY_SEMANTIC_READINESS_IN_PACKAGE_AUDIT';(C/'ui/audit/ui-coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
sync_ui();print(json.dumps({'actions':len(parity),'controls':len(rows)}))
