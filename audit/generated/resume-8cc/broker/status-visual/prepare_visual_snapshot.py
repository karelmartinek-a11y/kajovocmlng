from pathlib import Path
import shutil,json,hashlib,re,sys
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;SNAP=OUT/'snapshot'
consumed={}
def copy(path):
 src=ROOT/path;dst=SNAP/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);consumed[path]=hashlib.sha256(src.read_bytes()).hexdigest()
for dir in ['03_UI_REFERENCE','02_BRAND']:
 for src in (ROOT/dir).rglob('*'):
  if src.is_file():copy(src.relative_to(ROOT).as_posix())
for path in ['00_SSOT/KajovoCMLNG_SSOT.md','requirements-audit.txt','scripts/ssot_sources.py','scripts/render_reference.mjs','01_UI_CONTRACT/ui/contracts/live-experience.json','01_UI_CONTRACT/ui/contracts/ui-control-registry.json','01_UI_CONTRACT/closure/contracts/ui-action-resolution.json']:copy(path)
(SNAP/'06_UI_OVERVIEWS').mkdir(exist_ok=True);(SNAP/'audit/generated').mkdir(parents=True,exist_ok=True)
p=SNAP/'03_UI_REFERENCE/pages/secrets.html';s=p.read_text();assert '<label>Stav</label>'not in s
needle='<div class="fieldgrid">';assert s.count(needle)==1
field='<div class="field" data-field="secret.status"><label>Stav</label><div class="input" role="status" data-readonly="true" data-source="SERVER_PROJECTION" data-record-status="INACTIVE">INACTIVE</div><div class="help"><code>TEXT_1</code> &middot; odvozený stav rootu, nikoli lifecycle vybrané verze</div></div>'
s=s.replace(needle,needle+field,1).replace('active v7','vybraná v1 · CREATED').replace('<label>Input / projection fields</label><b>10</b>','<label>Input / projection fields</label><b>11</b>').replace('<label>Canonical state</label><b>READY</b>','<label>Stav vybraného rootu</label><b>INACTIVE</b>')
s=s.replace('<span class="badge ok"><i class="bdot"></i>READY</span>','<span class="badge"><i class="bdot"></i>root INACTIVE</span>',1)
s=s.replace('<span class="status ">READY</span>','<span class="status ">ACTIVE</span>').replace('<span class="status warn">STALE</span>','<span class="status warn">INACTIVE</span>').replace('<span class="status warn">VERIFYING</span>','<span class="status warn">DELETED</span>')
root_id='22222222-2222-4222-8222-222222222222';version_id='33333333-3333-4333-8333-333333333333'
s=s.replace('<span class="badge teal"><i class="bdot"></i>stateVersion 184</span>','<span class="badge teal"><i class="bdot"></i>stateVersion 183</span>',1)
s=s.replace('<div class="statusrow">','<div class="statusrow" data-secret-id="'+root_id+'" data-record-state-version="183">',1)
s=s.replace('<b>KCML0009 Secret Broker</b>','<b>DEMO_TOTP_SEED</b>')
s=s.replace('<tr><td class="namecell"><b>DEMO_TOTP_SEED</b>','<tr data-selected-root="true" data-secret-id="'+root_id+'" data-record-state-version="183"><td class="namecell"><b>DEMO_TOTP_SEED</b>')
s=s.replace('<div class="cardhead"><b>Secret detail</b>','<div class="cardhead" data-secret-id="'+root_id+'" data-record-state-version="183" data-active-version-id="null"><b>Secret detail</b>')
s=s.replace('data-record-status="INACTIVE"','data-record-status="INACTIVE" data-secret-id="'+root_id+'" data-record-state-version="183" data-active-version-id="null"')
s=s.replace('<span class="right badge teal">vybraná v1 · CREATED</span>','<span class="right badge teal" data-version-id="'+version_id+'" data-version-lifecycle="CREATED">vybraná v1 · CREATED</span>')
s=s.replace('<label>Stable name<span class="req">*</span></label><div class="input">KCML production capability</div>','<label>Stable name<span class="req">*</span></label><div class="input">DEMO_TOTP_SEED</div>')
p.write_text(s);(OUT/'secrets.html').write_text(s)
manifest={'sourceDocumentSha256':consumed['00_SSOT/KajovoCMLNG_SSOT.md'],'copiedCanonicalInputDigests':consumed,'candidateHtmlPath':'03_UI_REFERENCE/pages/secrets.html','candidateHtmlSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'change':'readonly derived root status + distinct selected version lifecycle; no backend or sensitive value fixture','rendererScripts':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['scripts/render_reference.py','scripts/render_reference_package.py']}}
(OUT/'visual-inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('isolated canonical snapshot and Secret HTML candidate ready')
