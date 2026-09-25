"""Verify exact native asset closure, with independent manifest mutations.

This is byte integrity, not semantic closure or whole-package readiness.
"""
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import types
from pathlib import Path

from ssot_sources import ROOT, SSOT, resource_index, resources


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',action='store_true')
    args=parser.parse_args()
    raw=(subprocess.check_output(['git','show','5b60c8a:00_SSOT/KajovoCMLNG_SSOT.md'])
         if args.baseline else SSOT.read_bytes())
    rs=resource_index(resources(raw.decode('utf8')))
    module=types.ModuleType('manifest_embedded_test')
    sys.modules[module.__name__]=module
    exec(compile(rs['scripts/ssot/ssot_control.py']['raw'],'SSOT:ssot_control.py','exec'),module.__dict__)
    with tempfile.TemporaryDirectory(prefix='kcml-manifest-') as directory:
        path=Path(directory)/'SSOT.md';path.write_bytes(raw)
        doc=module.Document(path)
    manifest_path='contracts/execution/embedded-manifest.json'
    original_load=doc.load
    manifest=original_load(manifest_path)
    expected={p for p,a in doc.assets.items() if a.authority=='NORMATIVE' and p!=manifest_path}
    listed={e['path'] for e in manifest['files']}
    mismatches=[]
    for entry in manifest['files']:
        asset=doc.assets.get(entry['path'])
        if asset is None or (module.raw_digest(asset.body),len(asset.body),asset.authority)!=(
                entry['rawDigest'],entry['sizeBytes'],entry['authority']):
            mismatches.append({'entry':entry,'actualSha256':None if asset is None else module.raw_digest(asset.body),
                               'actualSizeBytes':None if asset is None else len(asset.body)})
    cases=[]
    def check(name,value,expected):
        doc.load=lambda p: value if p==manifest_path else original_load(p)
        error=None
        try:doc.verify_manifest();actual=True
        except module.ContractFailure as exc:actual=False;error=str(exc)
        cases.append({'name':name,'expectedValid':expected,'actualValid':actual,
                      'passed':actual==expected,'error':error})
    check('exact_current_manifest',manifest,True)
    # Mutations start from the real current manifest. Baseline failure must not
    # be counted as a negative-test success: only run mutations once it is valid.
    if cases[0]['actualValid']:
        for name in ['missing_entry','duplicate_entry','wrong_digest','wrong_size','wrong_authority','unknown_asset']:
            value=copy.deepcopy(manifest)
            if name=='missing_entry':value['files'].pop()
            elif name=='duplicate_entry':value['files'].append(copy.deepcopy(value['files'][0]))
            elif name=='wrong_digest':value['files'][0]['rawDigest']='sha256:'+'0'*64
            elif name=='wrong_size':value['files'][0]['sizeBytes']+=1
            elif name=='wrong_authority':value['files'][0]['authority']='HISTORY'
            else:value['files'][0]['path']='missing-native-asset.json'
            check(name,value,False)
    report={'sourceSha256':hashlib.sha256(raw).hexdigest(),'baselineCommit':'5b60c8a' if args.baseline else None,
            'scope':__doc__,'nativeAssets':len(manifest['files']),'mismatches':mismatches,
            'missingAssets':sorted(expected-listed),'extraAssets':sorted(listed-expected),
            'checked':len(cases),'failed':sum(not c['passed'] for c in cases),'cases':cases,
            'nativeScriptSha256':rs['scripts/ssot/ssot_control.py']['sha256'],
            'nativeManifestSha256':rs[manifest_path]['sha256']}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-997e835/native-integrity')
    out.mkdir(parents=True,exist_ok=True)
    (out/('manifest-baseline.json' if args.baseline else 'manifest-current.json')).write_text(
        json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in ['sourceSha256','nativeAssets','checked','failed','mismatches']}))
    return int(bool(report['failed']))


if __name__=='__main__':raise SystemExit(main())
