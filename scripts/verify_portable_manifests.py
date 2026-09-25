"""Current branch/source, inventory completeness, LF portability, stale PASS."""
import hashlib
import json
import os
import tempfile
from pathlib import Path
from package_integrity import generate,verify,MANIFEST,HASHES,JSON_HASHES
from ssot_sources import ROOT,SSOT

def main():
    checks=[]
    with tempfile.TemporaryDirectory(prefix='kcml-package-') as directory:
        root=Path(directory);(root/'00_SSOT').mkdir();(root/'audit').mkdir()
        (root/'00_SSOT/KajovoCMLNG_SSOT.md').write_bytes(b'# canonical\r\n')
        (root/'audit/final-audit.json').write_text('{"status":"PASS","sourceDocumentSha256":"old"}',encoding='utf8')
        (root/'payload.txt').write_bytes(b'value\r\n');(root/'binary.png').write_bytes(b'\x00\r\n\xff')
        def check(name,ok):checks.append({'case':name,'passed':ok})
        m=generate(root,'work/test');check('current-inventory',not verify(root,'work/test'))
        check('historical-PASS-does-not-certify',m['packageStatus']=='BLOCKED' and not m['historicalAuditStatusUsed'])
        check('paths-POSIX',all('\\' not in r['path'] for r in m['files']))
        check('wrong-current-branch-rejected',bool(verify(root,'main')))
        (root/'payload.txt').write_bytes(b'value\n');check('CRLF-LF-equivalence',not verify(root,'work/test'))
        (root/'payload.txt').write_bytes(b'changed\n');check('changed-content-rejected',bool(verify(root,'work/test')))
        generate(root,'work/test');(root/'00_SSOT/KajovoCMLNG_SSOT.md').write_bytes(b'new SSOT\n')
        check('new-SSOT-stale-manifest-rejected',bool(verify(root,'work/test')))
        generate(root,'work/test');(root/'added.txt').write_bytes(b'extra')
        check('unlisted-file-rejected',bool(verify(root,'work/test')))
        m=generate(root,'work/test');m['files'].append(m['files'][0])
        (root/MANIFEST).write_text(json.dumps(m),encoding='utf8');check('duplicate-row-rejected',bool(verify(root,'work/test')))
        generate(root,'work/test');(root/'binary.png').write_bytes(b'\x00\n\xff')
        check('binary-line-endings-not-normalized',bool(verify(root,'work/test')))
        generate(root,'work/test');text=(root/HASHES).read_text(encoding='utf8');(root/HASHES).write_text(text+text.splitlines()[0]+'\n',encoding='utf8')
        check('duplicate-hash-entry-rejected',bool(verify(root,'work/test')))
        generate(root,'work/test');(root/JSON_HASHES).write_text('{}',encoding='utf8')
        check('JSON-and-plain-must-agree',bool(verify(root,'work/test')))
        m=generate(root,'work/test');m['inventoryExclusions'].append('user-data')
        (root/MANIFEST).write_text(json.dumps(m),encoding='utf8')
        check('exclusion-policy-cannot-expand','inventory exclusion policy mismatch' in verify(root,'work/test'))
    report={'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'scope':__doc__,
            'checked':len(checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,
            'implementationHashes':{p:hashlib.sha256((ROOT/'scripts'/p).read_bytes()).hexdigest()
                                    for p in ['package_integrity.py','update_manifests.py','verify_package.py']}}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-897da64/generation-domain');out.mkdir(parents=True,exist_ok=True)
    (out/'portable-manifest-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(report));return int(bool(report['failed']))

if __name__=='__main__':raise SystemExit(main())
