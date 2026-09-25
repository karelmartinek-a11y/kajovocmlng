"""12.14: refusal/incomplete/provider failure cannot carry accepted structured success.

Update native schema and its two active embedded copies, never history/r2.
This does not bind the incomplete generation.model.execute operation masks.
"""
import argparse
import hashlib
import json
from ssot_sources import SSOT,resource_index,resources

GEN='contracts/generation/generation-contracts.schema.json'
PROJECTION='contracts/registry-schemas/project-registry.schema.json'
MANIFEST='contracts/execution/embedded-manifest.json'
RULE={'if':{'properties':{'localStatus':{'enum':['REFUSED','INCOMPLETE','FAILED']}}},
      'then':{'properties':{'acceptedOutput':{'type':'null'}}}}

def encode(value,original):
    pretty=original.lstrip().startswith(b'{\n')
    return (json.dumps(value,ensure_ascii=False,indent=2 if pretty else None,
                       separators=None if pretty else (',',':'))+'\n').encode()

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=SSOT.read_text(encoding='utf8');items=list(resources(text));rs=resource_index(items)
    updates={};definitions=[]
    for path in [GEN,PROJECTION]:
        value=json.loads(rs[path]['raw']);definition=value['$defs']['ProviderOutcome'];definitions.append(definition)
        rules=definition.setdefault('allOf',[])
        if RULE not in rules:rules.append(RULE)
        updates[path]=encode(value,rs[path]['raw'])
    if definitions[0]!=definitions[1]:raise ValueError('Native/projected ProviderOutcome conflict')
    manifest=json.loads(rs[MANIFEST]['raw'])
    for entry in manifest['files']:
        if entry['path'] in updates:
            raw=updates[entry['path']];entry.update(sizeBytes=len(raw),rawDigest='sha256:'+hashlib.sha256(raw).hexdigest())
    updates[MANIFEST]=encode(manifest,rs[MANIFEST]['raw'])
    updates={p:b for p,b in updates.items() if rs[p]['raw']!=b}
    if args.check:print(json.dumps({'pending':list(updates)}));return int(bool(updates))
    changed=[]
    for r in reversed(items):
        path=r['path']
        if path not in updates:continue
        if r['declared'].get('authority')=='AUDIT_ONLY' or path.startswith('history/'):raise ValueError('History is immutable')
        raw=updates[path];attrs=dict(r['declared'])
        if 'bytes' in attrs:attrs['bytes']=str(len(raw))
        if 'sha256' in attrs:attrs['sha256']=hashlib.sha256(raw).hexdigest()
        if attrs.get('encoding') not in (None,'plain'):raise ValueError('Unexpected encoding')
        head=f'<!-- {r["family"]} path="{path}" '+' '.join(f'{k}="{v}"' for k,v in attrs.items())+' -->'
        block=head+'\n```json\n'+raw.decode()+'```\n<!-- '+r['family']+'-END -->'
        a,b=r['match'].span();text=text[:a]+block+text[b:];changed.append(r['family']+':'+path)
    if updates:SSOT.write_text(text,encoding='utf8',newline='\n')
    print(json.dumps({'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'changed':changed}));return 0

if __name__=='__main__':raise SystemExit(main())
