#!/usr/bin/env python3
from pathlib import Path
import re,json,hashlib,sys
ROOT = Path(__file__).resolve().parents[3]
p = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / '00_SSOT/KajovoCMLNG_SSOT.md'
b=p.read_bytes(); t=b.decode('utf-8')
# Flat normative prvopis: UI contract is verified directly in this document.
fence=chr(96)*3
fp=re.escape(fence)
pat=re.compile(r'^<!-- KCML-UI-RESOURCE path="([^"]+)" kind="([^"]+)" bytes="(\d+)" sha256="([0-9a-f]{64})" encoding="plain" -->\n'+fp+r'([^\n]*)\n(.*?)\n'+fp+r'\n<!-- KCML-UI-RESOURCE-END -->$',re.S|re.M)
res={}
for x in pat.finditer(t):
 path,kind,n,sha,lang,body=x.groups(); raw=(body+'\n').encode('utf-8'); assert len(raw)==int(n); assert hashlib.sha256(raw).hexdigest()==sha; res[path]=(kind,body+'\n')
required={'ui/contracts/ui-control-registry.json','ui/contracts/ui-acceptance.json','ui/audit/ui-coverage.json','ui/scripts/verify_ui.py'}
assert set(res)==required,(set(res)^required)
registry=json.loads(res['ui/contracts/ui-control-registry.json'][1])
acceptance=json.loads(res['ui/contracts/ui-acceptance.json'][1])
coverage=json.loads(res['ui/audit/ui-coverage.json'][1])
assert coverage['navigationSectionsExpected']==17 and len(coverage['navigationSectionIds'])==17
assert coverage['unresolved']==[]
assert acceptance['blocking'] and len(acceptance['gates'])>=30
pages=registry['pages']; assert len(pages)>=19
for page in pages:
 assert page['id'] and page['title'] and page['route'] and page['purpose']
 assert page['panels'] and page['actions']
 for f in page['fields']:
  assert f['id'] and f['label'] and f['purpose'] and f['validation'] and f['editableWhen']
  if f.get('inputProfile'): assert f['inputProfile'] in registry['shared']['inputProfiles']
 for a in page['actions']:
  assert a['id'] and a['label'] and a['purpose'] and a['operationBinding'] and a['enabledWhen'] and a['disabledWhen']
assert any(a['operationBinding']=='FORBIDDEN' for p in pages for a in p['actions'])
assert len(re.findall(r'^```',t,re.M))>0
print(json.dumps({'status':'PASS','canonicalPrvopisBytes':len(b),'pages':len(pages),'navSections':17,'acceptanceGates':len(acceptance['gates']),'resources':len(res),'unresolved':0},sort_keys=True))
