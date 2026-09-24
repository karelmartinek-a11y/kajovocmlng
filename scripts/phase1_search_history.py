"""Search available local SSOT history and capsules; never promote old data."""
import base64
import hashlib
import json
import lzma
import re
import subprocess
from ssot_sources import ROOT, resources


def main():
    matrix=json.loads((ROOT/'audit/phase1-operation-schema-matrix.json').read_text(encoding='utf8'))
    wanted={b['reference'] for op in matrix['operations'] for b in op['boundaries'] if b['resolution']=='UNRESOLVED'}
    commits=subprocess.check_output(['git','rev-list','--all','--','00_SSOT/KajovoCMLNG_SSOT.md']).decode().splitlines()
    reports=[]
    for commit in commits:
        raw=subprocess.check_output(['git','show',commit+':00_SSOT/KajovoCMLNG_SSOT.md'])
        text=raw.decode();items=list(resources(text));sources=[('SSOT',text)]
        capsule_count=0
        for r in items:
            content=r['raw'].decode();sources.append((r['family']+':'+r['path'],content))
            if r['path'].endswith('.json') and 'KCML-UTF8-RESOURCE-MAP-XZ/1' in content:
                cap=json.loads(content)
                if cap.get('format')!='KCML-UTF8-RESOURCE-MAP-XZ/1':continue
                compressed=base64.b64decode(''.join(cap['dataSegments']),validate=True)
                decoded=lzma.decompress(compressed)
                if 'sha256:'+hashlib.sha256(decoded).hexdigest()!=cap['decodedSha256']:
                    raise ValueError('Historical capsule integrity failure:'+commit)
                for path,body in json.loads(decoded).items():
                    sources.append((r['path']+'::'+path,body));capsule_count+=1
        findings=[]
        for name,content in sources:
            ids=set(re.findall(r'urn:kcml:r9:operation:[A-Za-z0-9_.:-]+',content)) & wanted
            definitions=set(re.findall(r'"\$id"\s*:\s*"([^"]+)"',content)) & wanted
            if ids:findings.append({'source':name,'identitiesMentioned':sorted(ids),'identityDeclarations':sorted(definitions)})
        starts=set(re.findall(r'^<!-- (KCML-[\w-]+) path="([^"]+)"',text,re.M))
        parsed={(r['family'],r['path']) for r in items}
        reports.append({'commit':commit,'ssotSha256':hashlib.sha256(raw).hexdigest(),
                        'embeddedResources':len(items),'capsuleFiles':capsule_count,
                        'unparsedResourceHeaders':sorted(starts-parsed),'findings':findings})
        print(json.dumps({'commit':commit,'identityDeclarations':sum(len(f['identityDeclarations']) for f in findings),
                          'unparsedResourceHeaders':len(starts-parsed)}),flush=True)
    output={'scope':'Lexical search of exact missing identities in all locally available SSOT revisions, decoded resource bodies and XZ capsules. This does not prove absence of differently named semantic equivalents.',
            'historicalAuthority':'EVIDENCE_ONLY','missingIdentities':len(wanted),'revisions':reports}
    (ROOT/'audit/generated/phase1-history-search.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return 0


if __name__=='__main__':raise SystemExit(main())
