"""Regenerate current inventory without using historical audit statuses."""
import json
import subprocess
from package_integrity import generate
from ssot_sources import ROOT

if __name__=='__main__':
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()
    if not branch:raise SystemExit('Name the source branch before producing a publication manifest')
    result=generate(ROOT,branch)
    print(json.dumps({'files':len(result['files']),'sourceBranch':branch,
                      'sourceDocumentSha256':result['sourceDocumentSha256'],'packageStatus':result['packageStatus']}))
