"""Check original Secrets-related normative sections against the starting commit."""
import hashlib
import json
import re
import subprocess
import sys
from ssot_sources import ROOT, SSOT

BASE='0ea5bf6b90ae4246956d1d76387ab540dc842f79'


def sections(text):
    headers=list(re.finditer(r'^(#{1,4}) (.+)$',text,re.M))
    result={}
    for index,header in enumerate(headers):
        if not re.search(r'secret|credential|plaintext|hesl',header[2],re.I):
            continue
        following=next((h for h in headers[index+1:] if len(h[1])<=len(header[1])),None)
        value=text[header.start():following.start() if following else len(text)].strip()
        result[header[2]]=hashlib.sha256(value.encode('utf-8')).hexdigest()
    return result


if __name__=='__main__':
    original=subprocess.run(['git','show',BASE+':00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8').replace('\r\n','\n')
    before=sections(original);after=sections(SSOT.read_text(encoding='utf-8'))
    checks=[{'section':key,'originalSha256':value,'currentSha256':after.get(key),
             'status':'PASS' if after.get(key)==value else 'FAIL'} for key,value in before.items()]
    report={'baseCommit':BASE,'scope':'Secret/credential/password headings and their full subordinate content, compared without publishing content. LF normalization and surrounding whitespace excluded.', 'checks':checks}
    (ROOT/'audit/generated/preserved-policy.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'sections':len(checks),'failures':sum(c['status']=='FAIL' for c in checks)}))
    sys.exit(any(c['status']=='FAIL' for c in checks))
