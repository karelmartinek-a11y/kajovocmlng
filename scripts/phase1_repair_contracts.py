"""Reproduce the narrow Phase 1 repairs in canonical embedded resources.

This does not close the remaining domain masks. --check is read-only.
"""
import argparse
import base64
import copy
import gzip
import hashlib
import json
import subprocess

from ssot_sources import ROOT, SSOT, resource_index, resources


def canonical_digest(value):
    return 'sha256:'+hashlib.sha256(json.dumps(value, ensure_ascii=False,
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def changes(rs):
    updates = {}
    path = 'r16/contracts/r15-visual-operation-closure.json'
    visual = json.loads(rs[path]['raw'])
    for op in visual['operations']:
        for role in ('request', 'response'):
            definition = op[role+'Definition']
            sources = op[role+'SchemaAuthority'].split(' + ')
            matches = [p for p in sources if definition in json.loads(rs[p]['raw']).get('$defs', {})]
            if len(matches) != 1:
                raise ValueError('Ambiguous definition: '+op['operationId']+'/'+definition)
            op[role+'SchemaRef'] = matches[0]+'#/$defs/'+definition
        op.pop('operationContractDigest')
        op['operationContractDigest'] = canonical_digest(op)
    updates[path] = visual

    path = 'contracts/payload-contracts.json'
    payloads = json.loads(rs[path]['raw'])
    for route in payloads['records']:
        if route['operationId'] not in ('secret.create', 'generation.job.create'):
            continue
        props = route['requestSchema']['properties']
        body = props['body']
        if 'oneOf' in body:
            branches = [x for x in body['oneOf'] if x.get('type') != 'null']
            if len(branches) != 1 or 'values' not in branches[0].get('properties', {}):
                raise ValueError('Unexpected create body')
            body = copy.deepcopy(branches[0])
            props['body'] = body
        # Both commands create a domain object from supplied content (8.3,
        # 12.2, 72 secret.create). This necessary condition is NOT a complete
        # domain mask, and the audit continues to mark these routes generic.
        body['properties']['values']['minItems'] = 1
        props['guards']['properties']['idempotencyKey']['type'] = 'string'
    # Preserve the existing digest recipe, verified against the untouched source.
    original = json.loads(rs[path]['raw'])
    old = original.pop('canonicalDigest')
    candidate = copy.deepcopy(payloads)
    candidate.pop('canonicalDigest')
    if old == canonical_digest(original):
        payloads['canonicalDigest'] = canonical_digest(candidate)
    elif old == canonical_digest(original['records']):
        payloads['canonicalDigest'] = canonical_digest(candidate['records'])
    elif old == canonical_digest({**original, 'canonicalDigest': None}):
        payloads['canonicalDigest'] = canonical_digest({**candidate, 'canonicalDigest': None})
    else:
        raise ValueError('Unknown payload canonicalDigest recipe; do not guess')
    updates[path] = payloads
    return updates


def encoded(value, original):
    # Retain each source's existing JSON whitespace convention.
    pretty = original.lstrip().startswith(b'{\n')
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
        indent=2 if pretty else None, separators=None if pretty else (',', ':'))+'\n').encode()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true')
    parser.add_argument('--verify-from-baseline', action='store_true'); args=parser.parse_args()
    text = SSOT.read_text(encoding='utf8')
    rs = resource_index(list(resources(text)))
    if args.verify_from_baseline:
        baseline=subprocess.check_output(['git','show','6180d9fe67dfaa5365190301dfd58cc8d9812f3d:00_SSOT/KajovoCMLNG_SSOT.md']).decode()
        before=resource_index(list(resources(baseline)))
        expected=changes(before)
        evidence=[]
        for path,value in expected.items():
            if rs[path]['raw'] != encoded(value,before[path]['raw']):
                raise ValueError('Non-reproducible resource:'+path)
            evidence.append({'resource':path,'beforeSha256':before[path]['sha256'],'afterSha256':rs[path]['sha256']})
        changed={p for p in rs if rs[p]['sha256']!=before[p]['sha256']}
        if changed != set(expected)|{'manifest.json'}:
            raise ValueError('Unexpected canonical changes:'+str(changed))
        manifest=json.loads(before['manifest.json']['raw'])
        raw=rs['contracts/payload-contracts.json']['raw']
        manifest['resources']['contracts/payload-contracts.json'].update(sizeBytes=len(raw),sha256='sha256:'+hashlib.sha256(raw).hexdigest())
        if rs['manifest.json']['raw']!=encoded(manifest,before['manifest.json']['raw']):
            raise ValueError('Non-reproducible embedded manifest')
        result={'reproducedFromCommit':'6180d9fe67dfaa5365190301dfd58cc8d9812f3d','resources':evidence,
                'onlyAdditionalChange':'R9 embedded manifest resource bytes/hash','status':'PASS'}
        (ROOT/'audit/generated/phase1-reproduction.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
        print(json.dumps(result));return 0
    values = changes(rs)
    changed = {p:encoded(v, rs[p]['raw']) for p,v in values.items() if json.loads(rs[p]['raw']) != v}
    if 'contracts/payload-contracts.json' in changed:
        manifest = json.loads(rs['manifest.json']['raw'])
        raw = changed['contracts/payload-contracts.json']
        manifest['resources']['contracts/payload-contracts.json'].update(sizeBytes=len(raw),sha256='sha256:'+hashlib.sha256(raw).hexdigest())
        changed['manifest.json'] = encoded(manifest,rs['manifest.json']['raw'])
    if args.check:
        print(json.dumps({'reproducible':not changed,'pending':list(changed)}))
        return int(bool(changed))
    for path in sorted(changed, key=lambda p:rs[p]['match'].start(), reverse=True):
        r=rs[path]; raw=changed[path]; encoding=r['declared'].get('encoding','plain')
        if encoding=='gzip+base64':
            data=base64.b64encode(gzip.compress(raw,compresslevel=6,mtime=0)).decode()
            body='\n'.join(data[i:i+120] for i in range(0,len(data),120))+'\n'
            language='text'
        else:
            body=raw.decode(); language='json'
        block=(f'<!-- {r["family"]} path="{path}" kind="{r["declared"]["kind"]}" bytes="{len(raw)}" '
               f'sha256="{hashlib.sha256(raw).hexdigest()}" encoding="{encoding}" -->\n'
               f'```{language}\n{body}```\n<!-- {r["family"]}-END -->')
        a,b=r['match'].span(); text=text[:a]+block+text[b:]
    if changed: SSOT.write_text(text,encoding='utf8',newline='\n')
    print(json.dumps({'changed':list(changed)}))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
