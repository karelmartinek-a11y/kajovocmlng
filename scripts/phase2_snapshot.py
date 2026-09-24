"""Capture the dirty Phase 2 entry once; never substitute HEAD for that baseline."""
import hashlib
import json
import subprocess
from pathlib import Path
from ssot_sources import ROOT, SSOT, resources, resource_index

def main():
    target = ROOT / '.cache/phase2-entry'
    if target.exists():
        raise SystemExit('Entry snapshot already exists; refusing overwrite')
    target.mkdir(parents=True)
    diff = subprocess.check_output(['git', 'diff', '--binary'])
    (target / 'working.diff').write_bytes(diff)
    (target / 'SSOT.md').write_bytes(SSOT.read_bytes())
    paths = subprocess.check_output(['git', 'ls-files', '-m', '-o', '--exclude-standard', '-z']).decode().split('\0')
    files = {}
    for name in filter(None, paths):
        p = ROOT / name
        if p.is_file():
            raw = p.read_bytes()
            files[name] = hashlib.sha256(raw).hexdigest()
            out = target / 'files' / name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(raw)
    before = resource_index(resources(subprocess.check_output(['git','show','HEAD:00_SSOT/KajovoCMLNG_SSOT.md']).decode()))
    current = resource_index()
    changed = []
    for p, r in current.items():
        if p not in before or before[p]['raw'] != r['raw']:
            changed.append({'path':p, 'before':before.get(p,{}).get('sha256'), 'after':r['sha256']})
    evidence = {'head':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),
        'branch':subprocess.check_output(['git','branch','--show-current']).decode().strip(),
        'status':subprocess.check_output(['git','status','--short']).decode(),
        'diffSha256':hashlib.sha256(diff).hexdigest(), 'files':files, 'decodedResourceChanges':changed}
    (ROOT/'audit/generated/phase2-entry.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'snapshot':str(target),'resources':changed,'files':len(files)}))

if __name__ == '__main__':
    main()
