"""Materialize SSOT-pinned MCP bytes and derive four public list RPC boundaries.

Authority: 10.3-10.4, 10.7, 10.11, 10.14, 10.16.1 and the existing
contracts/mcp-native-schema-artifact.json, not the latest upstream schema.
No HTTP route, lifecycle event or internal server receipt is substituted.
"""
import argparse
import base64
import copy
import gzip
import hashlib
import json
import subprocess

from phase1_repair_contracts import encoded
from ssot_sources import SSOT, resource_index, resources

PATH='contracts/operation-contracts.json'
ARTIFACT='contracts/mcp-native-schema-artifact.json'
NATIVE='contracts/mcp/native-2026-07-28.schema.json'
NATIVE_ID='urn:kcml:mcp-native:2026-07-28'
OPERATIONS={
    'mcp.prompts.list':('prompts/list','ListPrompts','prompts'),
    'mcp.tools.list':('tools/list','ListTools','tools'),
    'mcp.resources.list':('resources/list','ListResources','resources'),
    'mcp.resources.templates.list':('resources/templates/list','ListResourceTemplates','resourceTemplates'),
}


def verify_bytes(raw, pin):
    assert len(raw)==pin['sizeBytes'], 'Native byte length mismatch'
    assert 'sha256:'+hashlib.sha256(raw).hexdigest()==pin['contentSha256'], 'Native SHA256 mismatch'
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==pin['gitBlobSha1'], 'Native Git blob mismatch'


def definitions(native):
    projected=copy.deepcopy(native);projected['$id']=NATIVE_ID
    ref=lambda name:{'$ref':NATIVE_ID+'#/$defs/'+name}
    result={'mcp.native.2026-07-28':projected}
    for operation,(method,definition,_) in OPERATIONS.items():
        assert native['$defs'][definition+'Request']['properties']['method']['const']==method
        for role in ('command','response'):
            identity='urn:kcml:r9:operation:'+operation+':'+role
            if role=='command':
                mask={'allOf':[ref(definition+'Request'),
                    {'not':{'anyOf':[{'required':['result']},{'required':['error']}]},
                     'properties':{'params':{'required':['_meta'],
                        'properties':{'_meta':ref('RequestMetaObject')}}}}]}
            else:
                mask={'oneOf':[
                    {'allOf':[ref(definition+'ResultResponse'),
                        {'not':{'anyOf':[{'required':['error']},{'required':['method']}]},
                         'properties':{'result':{'required':['_meta'],
                            'properties':{'resultType':{'const':'complete'},'_meta':ref('ResultMetaObject')}}}}]},
                    {'allOf':[ref('JSONRPCErrorResponse'),
                        {'not':{'anyOf':[{'required':['result']},{'required':['method']}]},
                         'properties':{'error':{'properties':{'code':{'not':{
                             'type':'integer','minimum':-32099,'maximum':-32023}}}}}}]}
                ]}
            result[operation+':'+role]={'$schema':native['$schema'],'$id':identity,
                'description':'Public JSON-RPC '+role+'; SSOT 10.3/10.4/10.7/10.11/10.14/10.16.1. '
                    'Native definitions materialized from the exact SSOT-pinned artifact. '
                    'List methods cannot return MRTR or Tasks; HTTP admission and request-scoped '
                    'notifications remain distinct boundaries. Cross-message ID/cache/context checks are mandatory.',**mask}
    return result


def block(path,raw,family='KCML-R9-RESOURCE',kind='JSON'):
    b64=base64.b64encode(gzip.compress(raw,compresslevel=6,mtime=0)).decode()
    content='\n'.join(b64[i:i+120] for i in range(0,len(b64),120))+'\n'
    return (f'<!-- {family} path="{path}" kind="{kind}" bytes="{len(raw)}" '
            f'sha256="{hashlib.sha256(raw).hexdigest()}" encoding="gzip+base64" -->\n'
            f'```text\n{content}```\n<!-- {family}-END -->')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=SSOT.read_text(encoding='utf8');rs=resource_index(resources(text))
    pin=json.loads(rs[ARTIFACT]['raw'])
    if NATIVE in rs:raw=rs[NATIVE]['raw']
    elif args.check:print('Missing pinned native bytes');return 1
    else:
        blob=json.loads(subprocess.check_output(['gh','api',
            'repos/'+pin['upstreamRepository']+'/git/blobs/'+pin['gitBlobSha1']]))
        raw=base64.b64decode(blob['content'],validate=False)
    verify_bytes(raw,pin)
    doc=json.loads(rs[PATH]['raw']);wanted=definitions(json.loads(raw));doc.setdefault('$defs',{}).update(wanted)
    encoded_doc=encoded(doc,rs[PATH]['raw'])
    if args.check:
        pending=encoded_doc!=rs[PATH]['raw'];print(json.dumps({'pending':pending,'pinnedSha256':pin['contentSha256']}));return int(pending)
    updates={PATH:encoded_doc,NATIVE:raw}
    manifest=json.loads(rs['manifest.json']['raw'])
    for path,body in updates.items():
        manifest['resources'].setdefault(path,{}).update(sizeBytes=len(body),sha256='sha256:'+hashlib.sha256(body).hexdigest())
    updates['manifest.json']=encoded(manifest,rs['manifest.json']['raw'])
    for path in sorted((p for p in updates if p in rs),key=lambda p:rs[p]['match'].start(),reverse=True):
        if rs[path]['raw']==updates[path]:continue
        r=rs[path];assert r['declared']['encoding']=='gzip+base64'
        a,b=r['match'].span();text=text[:a]+block(path,updates[path],r['family'],r['declared']['kind'])+text[b:]
    if NATIVE not in rs:
        text+='\n\n<!-- Exact materialization of contracts/mcp-native-schema-artifact.json; no new product authority. -->\n'+block(NATIVE,raw)+'\n'
    SSOT.write_text(text,encoding='utf8',newline='\n')
    print(json.dumps({'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'operations':list(OPERATIONS),
        'nativeBytes':len(raw),'nativeSha256':pin['contentSha256']}));return 0


if __name__=='__main__':raise SystemExit(main())
