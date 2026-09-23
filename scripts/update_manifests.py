from pathlib import Path
import json,hashlib
from ssot_resources import ROOT
excluded={'.git','.cache','__pycache__','node_modules'}
def files():return sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(x in excluded for x in p.relative_to(ROOT).parts))
ps=[p for p in files() if p.name not in ['PACKAGE_MANIFEST.json','FILE_MANIFEST_SHA256']]
def authority(p):
 n=str(p.relative_to(ROOT))
 if n.startswith('00_SSOT/') or n.startswith('01_UI_CONTRACT/ui/contracts/') and not n.endswith('ui-control-registry.json'):return 'NORMATIVE'
 if n.startswith('01_UI_CONTRACT/closure/') or n.startswith('01_UI_CONTRACT/ui/'):return 'SSOT_EMBEDDED_PROJECTION'
 if n.startswith(('04_UI_VIEWS/','05_DIALOG_VIEWS/','06_UI_OVERVIEWS/')) or n.endswith('.csv'):return 'DERIVED_VIEW'
 if n.startswith('audit/'):return 'CURRENT_AUDIT_EVIDENCE'
 return 'SUPPORTING_SOURCE'
a=json.loads((ROOT/'audit/final-audit.json').read_text())
d={'format':'KCML-PACKAGE-MANIFEST/1','sourceBranch':'main','canonicalSSOT':'00_SSOT/KajovoCMLNG_SSOT.md','packageStatus':a['status'],'freezePerformed':False,'inventoryExclusions':['.git','.cache','__pycache__','node_modules'],'selfReferencePolicy':'PACKAGE_MANIFEST inventory excludes itself and FILE_MANIFEST_SHA256; FILE_MANIFEST_SHA256 hashes all files except itself; Git commit binds that final manifest.','files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'authority':authority(p)} for p in ps]}
(ROOT/'PACKAGE_MANIFEST.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
lines=[hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT)) for p in files() if p.name!='FILE_MANIFEST_SHA256'];(ROOT/'FILE_MANIFEST_SHA256').write_text('\n'.join(lines)+'\n');print(json.dumps({'manifestEntries':len(lines),'status':a['status']}))
