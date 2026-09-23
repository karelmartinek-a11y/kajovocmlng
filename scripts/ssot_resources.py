"""Read every embedded SSOT resource without executing it or trusting its claims."""
from pathlib import Path
import re, json, hashlib, gzip, base64, lzma
ROOT=Path(__file__).resolve().parents[1]
SSOT=ROOT/'00_SSOT/KajovoCMLNG_SSOT.md'
PAT=re.compile(r'^<!-- (KCML-(?:R\d+|UI|CLOSURE)-RESOURCE|KCML-EMBEDDED) path="([^"]+)"([^\n]*) -->\n(`{3,})[^\n]*\n(.*?)\n\4\n<!-- [^\n]*END[^\n]*-->',re.M|re.S)
def resources(text=None):
    text=SSOT.read_text() if text is None else text
    for m in PAT.finditer(text):
        family,path,attrs,fence,body=m.groups()
        a=dict(re.findall(r'(\w+)="([^"]*)"',attrs))
        if a.get('encoding')=='gzip+base64': raw=gzip.decompress(base64.b64decode(body))
        elif a.get('encoding')=='plain' or family=='KCML-EMBEDDED': raw=(body+'\n').encode()
        else:
            raw=body.encode()
            variants=[raw,raw.rstrip(b'\n')+b'\n',raw.rstrip(b'\n'),raw+b'\n']
            raw=next((v for v in variants if hashlib.sha256(v).hexdigest()==a.get('sha256')),raw.rstrip(b'\n')+b'\n')
        yield dict(family=family,path=path,attrs=a,raw=raw,span=m.span(),sha256=hashlib.sha256(raw).hexdigest())
def get(family,path):
    found=[r for r in resources() if r['family']==family and r['path']==path]
    if len(found)!=1: raise ValueError((family,path,len(found)))
    return found[0]['raw']
def load(family,path):return json.loads(get(family,path))
def capsule():
    c=load('KCML-R5-RESOURCE','contracts/materialized-records.capsule.json')
    data=base64.b64decode(''.join(c['dataSegments']),validate=True)
    assert 'sha256:'+hashlib.sha256(data).hexdigest()==c['compressedSha256']
    raw=lzma.decompress(data)
    assert len(raw)==c['decodedBytes'] and 'sha256:'+hashlib.sha256(raw).hexdigest()==c['decodedSha256']
    return json.loads(raw)
def sync_ui():
    text=SSOT.read_text()
    for r in reversed(list(resources(text))):
        if r['family'] not in ('KCML-UI-RESOURCE','KCML-CLOSURE-RESOURCE'):continue
        p=ROOT/'01_UI_CONTRACT'/r['path'];raw=p.read_bytes()
        if not raw.endswith(b'\n'):raw+=b'\n';p.write_bytes(raw)
        family=r['family'];kind=r['attrs']['kind'];body=raw.decode().rstrip('\n')
        replacement=f'<!-- {family} path="{r["path"]}" kind="{kind}" bytes="{len(raw)}" sha256="{hashlib.sha256(raw).hexdigest()}" encoding="plain" -->\n```'+('python' if kind=='PYTHON' else 'json')+'\n'+body+'\n```\n<!-- '+family+'-END -->'
        a,b=r['span'];text=text[:a]+replacement+text[b:]
    SSOT.write_text(text)
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--sync-ui',action='store_true');a=parser.parse_args()
    if a.sync_ui:sync_ui()
    else:print(json.dumps([dict(family=r['family'],path=r['path'],bytes=len(r['raw']),sha256=r['sha256'],integrity=not r['attrs'].get('sha256') or r['sha256']==r['attrs']['sha256']) for r in resources()],indent=2))
