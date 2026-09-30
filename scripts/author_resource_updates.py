"""Deterministic embedded-resource rewrites; history is never a write target."""
import base64,gzip,hashlib

def block(resource, raw):
    attrs=dict(resource['declared']);family=resource['family'];path=resource['path']
    if path.startswith('history/') or attrs.get('authority')=='AUDIT_ONLY':raise ValueError('Historical resource is immutable')
    if 'bytes' in attrs:attrs['bytes']=str(len(raw))
    if 'sha256' in attrs:attrs['sha256']=hashlib.sha256(raw).hexdigest()
    if attrs.get('encoding')=='gzip+base64':
        data=base64.b64encode(gzip.compress(raw,compresslevel=6,mtime=0)).decode()
        content='\n'.join(data[i:i+120] for i in range(0,len(data),120))+'\n'
    else:
        assert attrs.get('encoding') in (None,'plain');content=raw.decode()
    header=f'<!-- {family} path="{path}" '+' '.join(f'{k}="{v}"' for k,v in attrs.items())+' -->'
    return header+'\n```'+resource['language']+'\n'+content+'```\n<!-- '+family+'-END -->'

def rewrite(text, items, updates):
    found=set()
    for r in reversed(items):
        if r['path'] not in updates:continue
        found.add(r['path']);a,b=r['match'].span()
        text=text[:a]+block(r,updates[r['path']])+text[b:]
    for path in sorted(set(updates)-found):
        text+='\n\n'+block({'path':path,'family':'KCML-R9-RESOURCE','language':'text',
            'declared':{'kind':'JSON','bytes':'0','sha256':'','encoding':'gzip+base64'}},updates[path])+'\n'
    return text
