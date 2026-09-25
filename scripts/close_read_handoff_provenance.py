"""Install source-derived read handoffs, preserving all previous native checks.

12.19/12.23: immutable generation reads must match their persisted pointer/digest.
10.3/10.4/10.7/10.10: exact RPC ID, known list outcome, cache/page semantics.
The server supplies trusted persisted metadata; no caller receipt is authority.
"""
import argparse
import hashlib
import json
from ssot_sources import SSOT,resource_index,resources
from close_provider_outcome_mask import encode,MANIFEST

CONTROL='scripts/ssot/ssot_control.py'
OLD_SIGNATURE='def validate_generation_read_handoff(doc:Document,operation_id:str,path_parameters:dict[str,Any],response:dict[str,Any])->bool:'
NEW_SIGNATURE='''def validate_generation_read_handoff(doc:Document,operation_id:str,path_parameters:dict[str,Any],response:dict[str,Any],*,
        persisted_job_id:str|None=None,persisted_document_id:str|None=None,persisted_document_digest:str|None=None)->bool:'''
OLD_END="""    return True

def validate_integration_step_input"""
NEW_END='''    # Trusted repository snapshot, not response metadata or caller-supplied digest.
    # A specification embeds jobId but not its immutable revision ID (12.19).
    doc.validate('Uuid',persisted_job_id);doc.validate('Uuid',persisted_document_id)
    doc.validate('Digest',persisted_document_digest)
    key='revisionId' if operation_id=='generation.spec.revision.read' else 'planId'
    require(path_parameters.get(key)==persisted_document_id and value['jobId']==persisted_job_id,
            'ARTIFACT_VALIDATION_FAILED','/persistedSnapshot','Persisted pointer belongs to another document/job')
    require(semantic_digest(value)==persisted_document_digest,'ARTIFACT_VALIDATION_FAILED',
            '/output','Read content differs from the immutable persisted digest')
    return True

def validate_mcp_list_handoff(request:dict[str,Any],response:dict[str,Any],*,previous_cache_scope:str|None=None)->tuple[bool,str|None]|None:
    """10.3/10.4/10.7/10.10; call after exact list request/response schema checks.

    None is a protocol failure, never a cacheable snapshot. An invalid cursor
    requires discarding the whole traversal before a fresh request without cursor.
    Return (nextCursor present, opaque cursor), preserving the valid empty string.
    No claim is made about transport authentication, persistence or freshness.
    """
    methods={'prompts/list':'prompts','tools/list':'tools','resources/list':'resources',
             'resources/templates/list':'resourceTemplates'}
    require(request.get('method') in methods,'ARTIFACT_VALIDATION_FAILED','/method','Not a list RPC')
    rid=request.get('id');sid=response.get('id')
    require(type(rid) in (str,int) and type(sid) is type(rid) and sid==rid,
            'ARTIFACT_VALIDATION_FAILED','/id','RPC ID must have the exact JSON type and value')
    require(('result' in response)!=('error' in response),'ARTIFACT_VALIDATION_FAILED','', 'Exactly one outcome required')
    if 'error' in response:return None
    result=response['result']
    require(result['resultType']=='complete','ARTIFACT_VALIDATION_FAILED','/result/resultType','List cannot return MRTR or Tasks')
    require(type(result['ttlMs']) is int and result['ttlMs']>=0,'ARTIFACT_VALIDATION_FAILED','/result/ttlMs','Invalid cache TTL')
    require(previous_cache_scope is None or previous_cache_scope==result['cacheScope'],
            'ARTIFACT_VALIDATION_FAILED','/result/cacheScope','Cross-page cacheScope mismatch')
    return ('nextCursor' in result,result.get('nextCursor'))

def validate_integration_step_input'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=SSOT.read_text(encoding='utf8');items=list(resources(text));rs=resource_index(items)
    source=rs[CONTROL]['raw'].decode()
    if OLD_SIGNATURE in source:
        assert source.count(OLD_SIGNATURE)==1 and source.count(OLD_END)==1
        source=source.replace(OLD_SIGNATURE,NEW_SIGNATURE).replace(OLD_END,NEW_END)
        source=source.replace('Revision digest/provenance still require the trusted persisted read snapshot.',
            'A successful handoff requires trusted persisted job, document ID and canonical digest.\n'
            '    These values must come from the immutable repository snapshot, never the caller.')
    assert NEW_SIGNATURE in source and NEW_END in source
    updates={CONTROL:source.encode()};manifest=json.loads(rs[MANIFEST]['raw'])
    for entry in manifest['files']:
        if entry['path']==CONTROL:entry.update(sizeBytes=len(updates[CONTROL]),rawDigest='sha256:'+hashlib.sha256(updates[CONTROL]).hexdigest())
    updates[MANIFEST]=encode(manifest,rs[MANIFEST]['raw'])
    updates={p:b for p,b in updates.items() if b!=rs[p]['raw']}
    if args.check:print(json.dumps({'pending':list(updates)}));return int(bool(updates))
    for r in reversed(items):
        if r['path'] not in updates:continue
        raw=updates[r['path']];attrs=dict(r['declared'])
        if 'bytes' in attrs:attrs['bytes']=str(len(raw))
        if 'sha256' in attrs:attrs['sha256']=hashlib.sha256(raw).hexdigest()
        assert attrs.get('encoding') in (None,'plain')
        head=f'<!-- {r["family"]} path="{r["path"]}" '+' '.join(f'{k}="{v}"' for k,v in attrs.items())+' -->'
        block=head+'\n```'+r['language']+'\n'+raw.decode()+'```\n<!-- '+r['family']+'-END -->'
        a,b=r['match'].span();text=text[:a]+block+text[b:]
    if updates:SSOT.write_text(text,encoding='utf8',newline='\n')
    print(json.dumps({'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'changed':list(updates)}));return 0


if __name__=='__main__':raise SystemExit(main())
