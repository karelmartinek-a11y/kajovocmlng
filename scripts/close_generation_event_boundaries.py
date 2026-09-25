"""Implement OWNER 12.44.1; no whole-route or DB integration closure claim."""
import argparse
import base64
import copy
import gzip
import hashlib
import json
from phase1_repair_contracts import canonical_digest, encoded
from ssot_sources import SSOT, resource_index, resources

PATH='contracts/payload-contracts.json'
GEN='contracts/generation/generation-contracts.schema.json'
CONTROL='scripts/ssot/ssot_control.py'
MANIFEST='contracts/execution/embedded-manifest.json'
READS={'route.0232','route.0237'}

HELPER='''def validate_generation_approved_event(doc,event:dict[str,Any],specification:dict[str,Any],*,persisted_event:dict[str,Any],commit_snapshot:dict[str,Any],committed:bool)->None:
    """12.44.1: trusted repository/outbox inputs, not client claims or DB proof."""
    doc.validate('SseEnvelope',event)
    require(event['type']=='generation.spec.approved','ARTIFACT_VALIDATION_FAILED','/type','Not approval event')
    payload=event['payload']
    require(isinstance(payload,dict) and set(payload)=={'specificationRevisionId','specificationDigest'},
            'ARTIFACT_VALIDATION_FAILED','/payload','Exact approval pointer/digest required')
    doc.validate('Uuid',payload['specificationRevisionId']);doc.validate('Digest',payload['specificationDigest'])
    require(committed is True,'ARTIFACT_VALIDATION_FAILED','/commit','Cannot publish before commit')
    require(event==persisted_event,'ARTIFACT_VALIDATION_FAILED','/event','Delivery must equal immutable persisted event')
    require(commit_snapshot.get('jobId')==event['objectId'] and commit_snapshot.get('eventSequence')==event['eventId']
            and commit_snapshot.get('state')=='ANALYZING'
            and commit_snapshot.get('specificationRevisionId')==payload['specificationRevisionId']
            and commit_snapshot.get('specificationDigest')==payload['specificationDigest'],
            'ARTIFACT_VALIDATION_FAILED','/commitSnapshot','Event and approval commit snapshot differ')
    doc.validate('GenerationSpecification',specification)
    require(specification['jobId']==event['objectId'] and semantic_digest(specification)==payload['specificationDigest'],
            'ARTIFACT_VALIDATION_FAILED','/specification','Approved immutable content differs')


def generation_event_delivery_action(doc,event:dict[str,Any],*,stream_job_id:str,last_sequence:str,previous_event_digest:str|None=None)->str:
    """49.5 consumer preflight after domain validation; no persistence claim.

    previous_event_digest is the trusted inbox digest for this exact event ID.
    Missing history cannot establish duplicate identity: request replay/snapshot.
    """
    doc.validate('SseEnvelope',event);doc.validate('Counter',last_sequence)
    doc.validate('Uuid',stream_job_id)
    require(event['objectId']==stream_job_id,'ARTIFACT_VALIDATION_FAILED','/objectId','Cursor/inbox belongs to another job stream')
    current=int(event['eventId']);last=int(last_sequence)
    if current<=last:
        if previous_event_digest is None:return 'REPLAY_REQUIRED'
        doc.validate('Digest',previous_event_digest)
        require(previous_event_digest==semantic_digest(event),'ARTIFACT_VALIDATION_FAILED','/eventId','Duplicate with different content')
        return 'DUPLICATE'
    return 'APPLY' if current==last+1 else 'REPLAY_REQUIRED'


'''

def specialize(d,bundle):
    d=copy.deepcopy(d)
    ref=lambda name:{'$ref':bundle['$id']+'#/$defs/'+name}
    for row in d['records']:
        rid=row['routeId']
        if rid not in READS|{'route.0234'}:continue
        identity=f'urn:kcml:r9:route:{rid}:event'
        payload_id=f'urn:kcml:r9:semantic:{rid}:event-payload'
        if rid in READS:
            row['eventApplicability']='NOT_APPLICABLE'
            row['eventSchema']={'$schema':bundle['$schema'],'$id':identity,
                'description':'12.44.1 OWNER: no generation event for this read; audit remains separate.',
                'not':{},'$defs':{'inapplicablePayload':{'$id':payload_id,'not':{}}}}
        else:
            row['eventApplicability']='AGGREGATE_STREAM'
            event=copy.deepcopy(bundle['$defs']['SseEnvelope'])
            event.update({'$schema':bundle['$schema'],'$id':identity,
                'description':'12.21 / 12.44.1 / 26.15 / 49.5: persisted job aggregate approval, not command lifecycle.'})
            event['properties']={k:ref(t) for k,t in [('eventId','Counter'),('objectId','Uuid'),('emittedAt','Timestamp')]}
            event['properties']['type']={'const':'generation.spec.approved'}
            event['properties']['payload']={'$id':payload_id,'type':'object','additionalProperties':False,
                'properties':{'specificationRevisionId':ref('Uuid'),'specificationDigest':ref('Digest')},
                'required':['specificationRevisionId','specificationDigest']}
            row['eventSchema']=event
    d['canonicalDigest']=canonical_digest({**d,'canonicalDigest':None})
    return d

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=SSOT.read_text(encoding='utf8');items=list(resources(text));rs=resource_index(items)
    assert '#### 12.44.1 OWNER rozhodnutí 2026-09-25' in text
    d=json.loads(rs[PATH]['raw']);assert d['canonicalDigest']==canonical_digest({**d,'canonicalDigest':None})
    updates={PATH:encoded(specialize(d,json.loads(rs[GEN]['raw'])),rs[PATH]['raw'])}
    source=rs[CONTROL]['raw'].decode()
    previous=HELPER.replace('*,stream_job_id:str,last_sequence:', '*,last_sequence:').replace(
        "    doc.validate('Uuid',stream_job_id)\n    require(event['objectId']==stream_job_id,'ARTIFACT_VALIDATION_FAILED','/objectId','Cursor/inbox belongs to another job stream')\n",'')
    if previous in source:source=source.replace(previous,HELPER)
    if HELPER not in source:
        assert 'def validate_generation_approved_event(' not in source
        marker='def validate_generation_approval_handoff('
        assert source.count(marker)==1
        source=source.replace(marker,HELPER+marker)
    updates[CONTROL]=source.encode()
    m=json.loads(rs[MANIFEST]['raw'])
    for entry in m['files']:
        if entry['path']==CONTROL:entry.update(sizeBytes=len(updates[CONTROL]),rawDigest='sha256:'+hashlib.sha256(updates[CONTROL]).hexdigest())
    updates[MANIFEST]=encoded(m,rs[MANIFEST]['raw'])
    m=json.loads(rs['manifest.json']['raw'])
    m['resources'][PATH].update(sizeBytes=len(updates[PATH]),sha256='sha256:'+hashlib.sha256(updates[PATH]).hexdigest())
    updates['manifest.json']=encoded(m,rs['manifest.json']['raw'])
    updates={p:b for p,b in updates.items() if b!=rs[p]['raw']}
    if args.check:print(json.dumps({'pending':list(updates)}));return int(bool(updates))
    for r in reversed(items):
        if r['path'] not in updates:continue
        raw=updates[r['path']];attrs=dict(r['declared'])
        assert attrs.get('authority')!='AUDIT_ONLY'
        if 'bytes' in attrs:attrs['bytes']=str(len(raw))
        if 'sha256' in attrs:attrs['sha256']=hashlib.sha256(raw).hexdigest()
        if attrs.get('encoding')=='gzip+base64':
            b64=base64.b64encode(gzip.compress(raw,compresslevel=6,mtime=0)).decode()
            content='\n'.join(b64[i:i+120] for i in range(0,len(b64),120))+'\n'
        else:
            assert attrs.get('encoding') in (None,'plain');content=raw.decode()
        head=f'<!-- {r["family"]} path="{r["path"]}" '+' '.join(f'{k}="{v}"' for k,v in attrs.items())+' -->'
        block=head+'\n```'+r['language']+'\n'+content+'```\n<!-- '+r['family']+'-END -->'
        a,b=r['match'].span();text=text[:a]+block+text[b:]
    if updates:SSOT.write_text(text,encoding='utf8',newline='\n')
    print(json.dumps({'changed':list(updates),'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest()}));return 0

if __name__=='__main__':raise SystemExit(main())
