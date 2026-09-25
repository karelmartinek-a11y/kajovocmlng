"""Portable current-tree inventory. Inventory alone cannot grant readiness."""
import hashlib
import json
from pathlib import PurePosixPath

EXCLUDED={'.git','.cache','__pycache__','node_modules'}
MANIFEST='PACKAGE_MANIFEST.json'
HASHES='FILE_MANIFEST_SHA256'
JSON_HASHES='FILE_MANIFEST_SHA256.json'
RECEIPT='audit/generated/integrity-receipt.json'
SELF_EXCLUDED={MANIFEST,HASHES,JSON_HASHES,RECEIPT}
SSOT_PATH='00_SSOT/KajovoCMLNG_SSOT.md'
REPRESENTATION='UTF8_TEXT_CRLF_TO_LF_ELSE_RAW/1'

def files(root):
    return sorted((p for p in root.rglob('*') if p.is_file() and not EXCLUDED.intersection(p.relative_to(root).parts)),key=lambda p:p.relative_to(root).as_posix())

def content(path):
    raw=path.read_bytes()
    if path.suffix.lower() in {'.png','.jpg','.zip'} or b'\0' in raw:return raw
    try:raw.decode('utf8')
    except UnicodeDecodeError:return raw
    return raw.replace(b'\r\n',b'\n')

def digest(path):return hashlib.sha256(content(path)).hexdigest()

def authority(name):
    if name==SSOT_PATH:return 'CANONICAL_SSOT'
    if name.startswith('audit/'):return 'AUDIT_EVIDENCE_INPUT_HASH_SCOPED'
    if name.startswith('01_UI_CONTRACT/'):return 'SSOT_PROJECTION_OR_SUPPORT'
    return 'SUPPORTING_OR_DERIVED'

def generate(root,branch):
    inventory=[]
    for p in files(root):
        name=p.relative_to(root).as_posix()
        if name in SELF_EXCLUDED:continue
        raw=content(p)
        inventory.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'authority':authority(name)})
    manifest={'format':'KCML-PACKAGE-MANIFEST/2','representation':REPRESENTATION,
        'representationRule':'UTF-8 non-NUL text normalizes CRLF to LF; .png/.jpg/.zip and other binary bytes remain raw. Paths are root-relative POSIX.',
        'sourceBranch':branch,'canonicalSSOT':SSOT_PATH,'sourceDocumentSha256':digest(root/SSOT_PATH),
        'packageStatus':'BLOCKED','statusScope':'INVENTORY_ONLY_NO_SEMANTIC_OR_FREEZE_CERTIFICATION',
        'freezePerformed':False,'historicalAuditStatusUsed':False,'inventoryExclusions':sorted(EXCLUDED),
        'selfReferencePolicy':'Package inventory excludes the package and both hash manifests plus the post-hash receipt; both hash lists hash PACKAGE_MANIFEST and the same content set, never each other. Git binds their bytes. Historical receipt is not an input.',
        'selfExcludedPaths':sorted(SELF_EXCLUDED),
        'files':inventory}
    (root/MANIFEST).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    values={p.relative_to(root).as_posix():digest(p) for p in files(root)
            if p.relative_to(root).as_posix() not in {HASHES,JSON_HASHES,RECEIPT}}
    rows=[h+'  '+name for name,h in values.items()]
    (root/HASHES).write_text('\n'.join(rows)+'\n',encoding='utf8',newline='\n')
    (root/JSON_HASHES).write_text(json.dumps({'algorithm':'SHA256','representation':REPRESENTATION,
        'excludedPaths':[HASHES,JSON_HASHES,RECEIPT],'files':values},indent=2)+'\n',encoding='utf8',newline='\n')
    return manifest

def verify(root,branch=None):
    problems=[]
    try:manifest=json.loads((root/MANIFEST).read_text(encoding='utf8'))
    except (OSError,ValueError) as e:return ['package manifest unreadable: '+str(e)]
    if manifest.get('format')!='KCML-PACKAGE-MANIFEST/2':return ['stale package format: regenerate current inventory']
    if manifest.get('representation')!=REPRESENTATION:problems.append('unknown byte representation')
    if branch and manifest.get('sourceBranch')!=branch:problems.append('source branch mismatch')
    if manifest.get('sourceDocumentSha256')!=digest(root/SSOT_PATH):problems.append('SSOT source hash mismatch')
    if manifest.get('packageStatus')!='BLOCKED' or manifest.get('freezePerformed') is not False or manifest.get('historicalAuditStatusUsed') is not False:problems.append('inventory must not certify readiness or trust historical status')
    actual={p.relative_to(root).as_posix():p for p in files(root)}
    if manifest.get('selfExcludedPaths')!=sorted(SELF_EXCLUDED):problems.append('self-reference exclusion policy mismatch')
    expected=set(actual)-SELF_EXCLUDED;seen=set()
    for row in manifest.get('files',[]):
        name=row['path'];pure=PurePosixPath(name)
        if '\\' in name or pure.is_absolute() or '..' in pure.parts or ':' in name:problems.append('noncanonical path: '+name)
        if name in seen:problems.append('duplicate package path: '+name)
        seen.add(name)
        if name not in actual:problems.append('missing package file: '+name);continue
        raw=content(actual[name])
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:problems.append('package content drift: '+name)
    if seen!=expected:problems.append('package inventory set mismatch')
    listed={}
    try:
        for line in (root/HASHES).read_text(encoding='utf8').splitlines():
            h,name=line.split('  ',1)
            if name in listed:problems.append('duplicate hash path: '+name)
            listed[name]=h
    except (OSError,ValueError) as e:return problems+['hash list unreadable: '+str(e)]
    omitted={HASHES,JSON_HASHES,RECEIPT}
    for name in sorted(set(listed)|(set(actual)-omitted)):
        if name in omitted or name not in actual or listed.get(name)!=digest(actual[name]):problems.append('file integrity: '+name)
    try:
        other=json.loads((root/JSON_HASHES).read_text(encoding='utf8'))
        if other.get('representation')!=REPRESENTATION or other.get('algorithm')!='SHA256' or other.get('excludedPaths')!=[HASHES,JSON_HASHES,RECEIPT] or other.get('files')!=listed:
            problems.append('JSON/plain hash manifest mismatch')
    except (OSError,ValueError) as e:problems.append('JSON hash manifest unreadable: '+str(e))
    return problems


if __name__=='__main__':
    import argparse
    import subprocess
    from ssot_sources import ROOT
    parser=argparse.ArgumentParser();parser.add_argument('--generate',action='store_true');parser.add_argument('--receipt',action='store_true');args=parser.parse_args()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()
    if args.generate:
        if not branch:raise SystemExit('Named source branch required for generation')
        generate(ROOT,branch)
    issues=verify(ROOT,branch or None)
    result={'scope':'CURRENT_PACKAGE_INTEGRITY_ONLY','status':'FAIL' if issues else 'INTEGRITY_MATCH',
            'sourceDocumentSha256':digest(ROOT/SSOT_PATH),'sourceBranch':branch,
            'manifestSha256':digest(ROOT/JSON_HASHES),'issues':issues,'packageStatus':'BLOCKED'}
    if args.receipt:
        (ROOT/RECEIPT).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result));raise SystemExit(bool(issues))
