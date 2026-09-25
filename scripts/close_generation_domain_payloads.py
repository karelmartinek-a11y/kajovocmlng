"""Technical schema derivation from SSOT 12.18-12.23 / 56.7-56.8.

Partial route closure only: no invented response/event for approval, no event
applicability inferred from HTTP method. Existing transport envelopes retained.
"""
import argparse
import base64
import gzip
import hashlib
import json

from phase1_repair_contracts import canonical_digest, encoded
from ssot_sources import SSOT, resource_index, resources

PATH='contracts/payload-contracts.json'
GEN='contracts/generation/generation-contracts.schema.json'
READS={'route.0232':'GenerationSpecification','route.0237':'GenerationPlan'}
APPROVAL_FIELDS={'currentTurnId':'Uuid','currentTurnStatus':None,
                 'specificationRevisionId':'Uuid','specificationDigest':'Digest',
                 'capabilitySnapshotId':'Uuid','capabilitySnapshotDigest':'Digest'}
READ_FAILURE_RULE={'if':{'properties':{'status':{'enum':['FAILED','CANCELLED']}}},
                   'then':{'properties':{'error':{'type':'object'}}}}


def changed_payload(rs):
    d=json.loads(rs[PATH]['raw']);bundle=json.loads(rs[GEN]['raw'])
    ref=lambda name:{'$ref':bundle['$id']+'#/$defs/'+name}
    for row in d['records']:
        if row['routeId']=='route.0234':
            assert row['operationId']=='generation.spec.approve'
            props=row['requestSchema']['properties']
            props['body']={'$schema':bundle['$schema'],
                '$id':'urn:kcml:r9:semantic:route.0234:body',
                'description':'12.21 approval command; technical field spelling per 12.18. '
                    'Caller supplies exact current snapshots, never server authority or receipt.',
                'type':'object','additionalProperties':False,
                'properties':{k:(ref(v) if v else {'const':'COMPLETED'}) for k,v in APPROVAL_FIELDS.items()},
                'required':list(APPROVAL_FIELDS)}
            props['guards']['properties']['expectedStateVersion']=json.loads(json.dumps(bundle['$defs']['Counter']))
            props['guards']['properties']['idempotencyKey']['type']='string'
        if row['routeId'] in READS:
            assert row['method']=='GET'
            definition=READS[row['routeId']]
            row['responseSchema']['properties']['output']={'oneOf':[{'type':'null'},
                {'$schema':bundle['$schema'],'$id':f'urn:kcml:r9:semantic:{row["routeId"]}:output',**ref(definition)}]}
            # Failure branch retains null output. A successful exact revision/plan
            # read delivers the actual domain document, not an empty slot bag.
            rule={'if':{'properties':{'status':{'const':'SUCCEEDED'}}},
                  'then':{'properties':{'output':ref(definition)}}}
            rules=row['responseSchema'].setdefault('allOf',[])
            if rule not in rules:rules.append(rule)
            # OWNER 12.44.1: an immutable read must return the requested
            # document or an explicit error, never FAILED with error=null.
            if READ_FAILURE_RULE not in rules:rules.append(READ_FAILURE_RULE)
    original=json.loads(rs[PATH]['raw'])
    assert original['canonicalDigest']==canonical_digest({**original,'canonicalDigest':None})
    d['canonicalDigest']=canonical_digest({**d,'canonicalDigest':None})
    return d


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=SSOT.read_text(encoding='utf8');rs=resource_index(resources(text))
    raw=encoded(changed_payload(rs),rs[PATH]['raw'])
    if args.check:
        pending=raw!=rs[PATH]['raw'];print(json.dumps({'pending':pending}));return int(pending)
    if raw==rs[PATH]['raw']:print('No changes');return 0
    manifest=json.loads(rs['manifest.json']['raw'])
    manifest['resources'][PATH].update(sizeBytes=len(raw),sha256='sha256:'+hashlib.sha256(raw).hexdigest())
    updates={PATH:raw,'manifest.json':encoded(manifest,rs['manifest.json']['raw'])}
    for path in sorted(updates,key=lambda p:rs[p]['match'].start(),reverse=True):
        r=rs[path];body=updates[path];encoding=r['declared']['encoding']
        if encoding=='gzip+base64':
            b64=base64.b64encode(gzip.compress(body,compresslevel=6,mtime=0)).decode()
            content='\n'.join(b64[i:i+120] for i in range(0,len(b64),120))+'\n';language='text'
        else:content=body.decode();language='json'
        block=(f'<!-- {r["family"]} path="{path}" kind="{r["declared"]["kind"]}" bytes="{len(body)}" '
               f'sha256="{hashlib.sha256(body).hexdigest()}" encoding="{encoding}" -->\n'
               f'```{language}\n{content}```\n<!-- {r["family"]}-END -->')
        a,b=r['match'].span();text=text[:a]+block+text[b:]
    SSOT.write_text(text,encoding='utf8',newline='\n')
    print(json.dumps({'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),
        'requestMasks':['route.0234'],'responseMasks':list(READS),'eventMasksClosed':[]}))
    return 0


if __name__=='__main__':raise SystemExit(main())
