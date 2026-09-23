"""Deterministic package manifests with explicit, non-circular hashing scope."""
import argparse
import hashlib
import json
import sys
from ssot_sources import ROOT

EXCLUDED_DIRS={'.git','.cache','__pycache__','node_modules'}
HASH_EXCEPTIONS={'FILE_MANIFEST_SHA256.json':'Cannot hash its own final bytes.',
 'audit/generated/integrity-receipt.json':'Post-hash receipt refers to the completed hash manifest; checked by recalculation, not hashed into itself.'}


def files():
    return {p.relative_to(ROOT).as_posix():p for p in ROOT.rglob('*') if p.is_file() and not any(part in EXCLUDED_DIRS for part in p.relative_to(ROOT).parts)}


def generate():
    paths=set(files())|{'PACKAGE_MANIFEST.json','FILE_MANIFEST_SHA256.json','audit/generated/integrity-receipt.json'}
    package={'format':'KCML-PACKAGE/1','canonicalRoot':'.','mainDocument':'00_SSOT/KajovoCMLNG_SSOT.md',
        'entryIndex':'README_CZ.md','audit':'audit/FINAL_AUDIT.md','excludedDirectories':sorted(EXCLUDED_DIRS),
        'hashExceptions':HASH_EXCEPTIONS,'files':sorted(paths),
        'authority':'Main SSOT and its explicitly designated sources; audit is evidence, generated projections have no independent authority.'}
    (ROOT/'PACKAGE_MANIFEST.json').write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest={'algorithm':'SHA256','bytePolicy':'Exact on-disk bytes; text LF enforced through .gitattributes; no newline normalization during hashing.',
        'excludedDirectories':sorted(EXCLUDED_DIRS),'exceptions':HASH_EXCEPTIONS,
        'files':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in sorted(files().items()) if name not in HASH_EXCEPTIONS}}
    (ROOT/'FILE_MANIFEST_SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return len(manifest['files'])


def verify(receipt=False):
    mpath=ROOT/'FILE_MANIFEST_SHA256.json';manifest=json.loads(mpath.read_text(encoding='utf-8'))
    current={n:p for n,p in files().items() if n not in HASH_EXCEPTIONS}; expected=manifest['files'];issues=[]
    if manifest['exceptions']!=HASH_EXCEPTIONS:issues.append('EXCEPTION_POLICY_MISMATCH')
    if manifest['excludedDirectories']!=sorted(EXCLUDED_DIRS):issues.append('EXCLUDED_DIRECTORY_POLICY_MISMATCH')
    for name in sorted(set(expected)-set(current)):issues.append('MISSING:'+name)
    for name in sorted(set(current)-set(expected)):issues.append('UNMANIFESTED:'+name)
    for name in sorted(set(current)&set(expected)):
        if hashlib.sha256(current[name].read_bytes()).hexdigest()!=expected[name]:issues.append('HASH_MISMATCH:'+name)
    package=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    if set(package['files'])!=set(files())|{'audit/generated/integrity-receipt.json'}:issues.append('PACKAGE_FILE_SET_MISMATCH')
    result={'status':'FAIL' if issues else 'PASS','manifestSha256':hashlib.sha256(mpath.read_bytes()).hexdigest(),'hashedFiles':len(expected),'issues':issues}
    if receipt:
        out=ROOT/'audit/generated/integrity-receipt.json';out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--generate',action='store_true');parser.add_argument('--receipt',action='store_true');args=parser.parse_args()
    if args.generate:print(json.dumps({'generatedHashes':generate()}))
    else:
        result=verify(args.receipt);print(json.dumps(result));sys.exit(result['status']!='PASS')
