"""SSOT 56.3: preserve guard presence/nullability, fix their non-null domains."""
import argparse
import base64
import copy
import gzip
import hashlib
import json

from phase1_repair_contracts import canonical_digest, encoded
from ssot_sources import SSOT, resource_index, resources

FIELDS = ('expectedStateVersion', 'expectedBindingSetRevision', 'expectedActivationEpoch')
PATH = 'contracts/payload-contracts.json'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=SSOT.read_text(encoding='utf8');rs=resource_index(resources(text))
    payload=json.loads(rs[PATH]['raw'])
    counter=json.loads(rs['contracts/generation/generation-contracts.schema.json']['raw'])['$defs']['Counter']
    changes=[]
    for route in payload['records']:
        guards=route['requestSchema']['properties']['guards']['properties']
        for field in FIELDS:
            old=guards[field]
            nullable=isinstance(old.get('type'),list) and 'null' in old['type']
            new=copy.deepcopy(counter)
            if nullable:new['type']=['string','null']
            if old==new:continue
            legacy=({'type':['string','null'],'maxLength':256} if field=='expectedBindingSetRevision'
                    else {'type':['string','null'],'pattern':'^(0|[1-9][0-9]*)$'})
            if old!=legacy:raise ValueError('Unexpected guard constraint: '+route['routeId']+'/'+field)
            guards[field]=new
            changes.append({'routeId':route['routeId'],'operationId':route['operationId'],'field':field})
    if args.check:
        print(json.dumps({'pending':len(changes)}));return int(bool(changes))
    if changes:
        prior=json.loads(rs[PATH]['raw'])
        if prior['canonicalDigest']!=canonical_digest({**prior,'canonicalDigest':None}):
            raise ValueError('Unexpected digest recipe')
        payload['canonicalDigest']=canonical_digest({**payload,'canonicalDigest':None})
        raw=encoded(payload,rs[PATH]['raw']);manifest=json.loads(rs['manifest.json']['raw'])
        manifest['resources'][PATH].update(sizeBytes=len(raw),sha256='sha256:'+hashlib.sha256(raw).hexdigest())
        updates={PATH:raw,'manifest.json':encoded(manifest,rs['manifest.json']['raw'])}
        for path in sorted(updates,key=lambda p:rs[p]['match'].start(),reverse=True):
            r,data=rs[path],updates[path];encoding=r['declared']['encoding']
            if encoding=='gzip+base64':
                b64=base64.b64encode(gzip.compress(data,compresslevel=6,mtime=0)).decode()
                body='\n'.join(b64[i:i+120] for i in range(0,len(b64),120))+'\n';language='text'
            else:body=data.decode();language='json'
            block=(f'<!-- {r["family"]} path="{path}" kind="{r["declared"]["kind"]}" '
                   f'bytes="{len(data)}" sha256="{hashlib.sha256(data).hexdigest()}" encoding="{encoding}" -->\n'
                   f'```{language}\n{body}```\n<!-- {r["family"]}-END -->')
            a,b=r['match'].span();text=text[:a]+block+text[b:]
        SSOT.write_text(text,encoding='utf8',newline='\n')
    print(json.dumps({'changedFields':len(changes),'changedRoutes':len({c['routeId'] for c in changes}),
                      'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest()}))
    return 0


if __name__=='__main__':raise SystemExit(main())
