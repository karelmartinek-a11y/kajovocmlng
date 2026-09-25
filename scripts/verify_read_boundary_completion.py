"""Current-mask and producer/consumer regressions; not DB/SSE integration proof."""
import argparse
import copy
import hashlib
import inspect
import importlib.metadata
import json
import os
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
from referencing import Registry,Resource
from ssot_sources import ROOT,SSOT,resources,resource_index
from close_mcp_list_operation_masks import OPERATIONS,PATH,NATIVE,NATIVE_ID,ARTIFACT,verify_bytes
from verify_phase2_handoffs import witness


def main():
    script_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    p=argparse.ArgumentParser();p.add_argument('--baseline',action='store_true');args=p.parse_args()
    raw=subprocess.check_output(['git','show','664d617:00_SSOT/KajovoCMLNG_SSOT.md']) if args.baseline else SSOT.read_bytes()
    rs=resource_index(resources(raw.decode()));checks=[]
    def check(name,actual,expected=True):checks.append({'case':name,'actual':actual,'expected':expected,'passed':actual==expected})
    module=types.ModuleType('read_boundary_test');sys.modules[module.__name__]=module
    exec(compile(rs['scripts/ssot/ssot_control.py']['raw'],'SSOT:ssot_control.py','exec'),module.__dict__)
    with tempfile.TemporaryDirectory(prefix='kcml-read-') as directory:
        path=Path(directory)/'SSOT.md';path.write_bytes(raw);doc=module.Document(path)
    defs=copy.deepcopy(doc.schema['$defs'])
    for key,value in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-25T00:00:00.000Z','RelPath':'fixture.json','JsonPointer':'','NonemptyJsonPointer':'/fixture'}.items():defs[key]={'const':value}
    fn=module.validate_generation_read_handoff
    for definition,operation,key in [('GenerationSpecification','generation.spec.revision.read','revisionId'),('GenerationPlan','generation.plan.read','planId')]:
        value=witness(defs[definition],defs)
        identity=value.get('planId','00000000-0000-4000-8000-000000000042')
        params={'id':value['jobId'],key:identity};response={'status':'SUCCEEDED','output':value}
        snapshot={'persisted_job_id':value['jobId'],'persisted_document_id':identity,'persisted_document_digest':module.semantic_digest(value)}
        supports='persisted_document_digest' in inspect.signature(fn).parameters
        def accepted(response,snapshot=snapshot,params=params,omit=False):
            try:return fn(doc,operation,params,response,**(snapshot if supports and not omit else {}))
            except module.ContractFailure:return False
        check(operation+'/persisted-consumer-present',supports)
        check(operation+'/persisted-document',accepted(response))
        check(operation+'/missing-trusted-snapshot',accepted(response,omit=True),False)
        for field in snapshot:
            altered={**snapshot,field:'sha256:'+'f'*64 if field.endswith('digest') else '00000000-0000-4000-8000-000000000099'}
            check(operation+'/wrong-persisted/'+field,accepted(response,altered),False)
        changed=copy.deepcopy(value)
        if definition=='GenerationSpecification':changed['objective']['statement']='Different immutable revision content'
        else:changed['specificationDigest']='sha256:'+'e'*64
        doc.validate(definition,changed)
        check(operation+'/valid-shape-wrong-content',accepted({'status':'SUCCEEDED','output':changed}),False)
        # A different document requires a different immutable revision/plan ID.
        # Recovery must never be illustrated as overwriting the old ID's bytes.
        recovered_id='00000000-0000-4000-8000-000000000077'
        if definition=='GenerationPlan':changed['planId']=recovered_id
        check(operation+'/recovery-read-distinct-immutable-document',accepted({'status':'SUCCEEDED','output':changed},
            {**snapshot,'persisted_document_id':recovered_id,'persisted_document_digest':module.semantic_digest(changed)},
            {**params,key:recovered_id}))
        for status in ['FAILED','CANCELLED','ACCEPTED']:
            check(operation+'/'+status+'-no-document',accepted({'status':status,'output':None},{}),False)
    operation_doc=json.loads(rs[PATH]['raw']);schemas=operation_doc.get('$defs',{})
    registry=Registry().with_resources((s['$id'],Resource.from_contents(s)) for s in schemas.values() if '$id' in s)
    check('pinned-native-bytes-present',NATIVE in rs)
    if NATIVE in rs:
        pin=json.loads(rs[ARTIFACT]['raw']);verify_bytes(rs[NATIVE]['raw'],pin)
        native=json.loads(rs[NATIVE]['raw']);projection=copy.deepcopy(schemas['mcp.native.2026-07-28']);projection.pop('$id')
        check('native-projection-exact-definitions',projection==native)
        for mutation in [rs[NATIVE]['raw']+b' ',rs[NATIVE]['raw'][:-1]]:
            try:verify_bytes(mutation,pin);valid=True
            except AssertionError:valid=False
            check('native-byte-drift-rejected',valid,False)
    handoff=getattr(module,'validate_mcp_list_handoff',None)
    check('mcp-handoff-present',handoff is not None)
    check('uri-format-checker-required','uri' in FormatChecker.checkers)
    check('uri-template-format-checker-required','uri-template' in FormatChecker.checkers)
    descriptors={
        'mcp.prompts.list':('Prompt',{'name':'fixture.prompt','arguments':[{'name':'range','required':True}]},
            {'arguments':[{'name':'range','required':'yes'}]}),
        'mcp.tools.list':('Tool',{'name':'fixture.tool','inputSchema':{'type':'object','properties':{'query':{'type':'string'}},'required':['query'],'additionalProperties':False}},
            {'inputSchema':{'type':'string'}}),
        'mcp.resources.list':('Resource',{'name':'fixture.resource','uri':'fixture://report','mimeType':'text/plain','size':5},
            {'size':'5'}),
        'mcp.resources.templates.list':('ResourceTemplate',{'name':'fixture.template','uriTemplate':'fixture://reports/{id}','mimeType':'text/plain'},
            {'uriTemplate':'fixture://reports/{id'}),
    }
    for operation,(method,_,field) in OPERATIONS.items():
        command=schemas.get(operation+':command');result=schemas.get(operation+':response')
        check(operation+'/command-mask-present',command is not None)
        check(operation+'/response-mask-present',result is not None)
        if command is None or result is None:continue
        rv=Draft202012Validator(command,registry=registry,format_checker=FormatChecker())
        sv=Draft202012Validator(result,registry=registry,format_checker=FormatChecker())
        req={'id':1,'jsonrpc':'2.0','method':method,'params':{'_meta':{
            'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientCapabilities':{}}}}
        success={'jsonrpc':'2.0','id':1,'result':{'resultType':'complete',field:[],'ttlMs':0,'cacheScope':'private','_meta':{}}}
        check(operation+'/exact-request',rv.is_valid(req));check(operation+'/exact-response',sv.is_valid(success))
        descriptor,item,bad_patch=descriptors[operation]
        def with_item(value):return {**success,'result':{**success['result'],field:[value]}}
        check(operation+'/concrete-domain-item',sv.is_valid(with_item(item)))
        for missing in native['$defs'][descriptor]['required']:
            bad=copy.deepcopy(item);del bad[missing]
            check(operation+'/item-missing/'+missing,sv.is_valid(with_item(bad)),False)
        check(operation+'/wrong-domain-item-field',sv.is_valid(with_item({**item,**bad_patch})),False)
        for uri,valid in [('https://example.invalid/icon.png',True),('not a URI',False)]:
            icon={'name':'fixture','version':'1','icons':[{'src':uri}]}
            bad=copy.deepcopy(req);bad['params']['_meta']['io.modelcontextprotocol/clientInfo']=icon
            check(operation+'/request-icon-uri/'+str(valid),rv.is_valid(bad),valid)
            bad=copy.deepcopy(success);bad['result']['_meta']['io.modelcontextprotocol/serverInfo']=icon
            check(operation+'/response-icon-uri/'+str(valid),sv.is_valid(bad),valid)
        for name,patch in [('null-id',{'id':None}),('bool-id',{'id':True}),('wrong-method',{'method':'tools/call'}),('response-as-request',{'result':{}})]:
            check(operation+'/'+name,rv.is_valid({**req,**patch}),False)
        for params in [{},{'_meta':{}},{'_meta':req['params']['_meta'],'cursor':None},{'values':[]}]:
            check(operation+'/bad-request-params',rv.is_valid({**req,'params':params}),False)
        check(operation+'/empty-cursor-is-valid',rv.is_valid({**req,'params':{**req['params'],'cursor':''}}))
        for name,patch in [('MRTR',{'resultType':'input_required'}),('Task',{'resultType':'task'}),('unknown-result',{'resultType':'unknown'}),
                           ('negative-ttl',{'ttlMs':-1}),('wrong-cache-scope',{'cacheScope':'any'}),('wrong-list-type',{field:{}}),('null-item',{field:[None]})]:
            check(operation+'/'+name,sv.is_valid({**success,'result':{**success['result'],**patch}}),False)
        for missing in [field,'ttlMs','cacheScope','resultType','_meta']:
            bad=copy.deepcopy(success);del bad['result'][missing]
            check(operation+'/missing/'+missing,sv.is_valid(bad),False)
        check(operation+'/generic-slot-output',sv.is_valid({**success,'result':{'schemaId':operation,'values':[]}}),False)
        error={'jsonrpc':'2.0','id':1,'error':{'code':-32602,'message':'Invalid cursor','data':{'stableCode':'MCP_CURSOR_INVALID'}}}
        check(operation+'/protocol-error',sv.is_valid(error))
        check(operation+'/ambiguous-outcome',sv.is_valid({**success,'error':error['error']}),False)
        check(operation+'/reserved-unknown-code',sv.is_valid({**error,'error':{'code':-32025,'message':'invented'}}),False)
        # Shape validation precedes the cross-message predicate in real consumers.
        def consume(response,request=req,scope=None):
            if not rv.is_valid(request) or not sv.is_valid(response):return 'REJECTED'
            try:return handoff(request,response,previous_cache_scope=scope)
            except module.ContractFailure:return 'REJECTED'
        if handoff:
            check(operation+'/producer-to-consumer',consume(success),(False,None))
            check(operation+'/string-vs-integer-id',consume({**success,'id':'1'}),'REJECTED')
            check(operation+'/float-id-is-not-integer-json',consume({**success,'id':1.0}),'REJECTED')
            check(operation+'/wrong-id',consume({**success,'id':2}),'REJECTED')
            cursor_request={**req,'params':{**req['params'],'cursor':'expired-cursor'}}
            check(operation+'/protocol-error-not-snapshot',consume(error,cursor_request),None)
            check(operation+'/next-empty-cursor',consume({**success,'result':{**success['result'],'nextCursor':''}}),(True,''))
            check(operation+'/cross-page-scope',consume(success,scope='public'),'REJECTED')
            # After cursor invalidation, discard traversal; fresh first-page request.
            fresh={**req,'id':2};fresh_result={**success,'id':2}
            check(operation+'/fresh-first-page-after-error',consume(fresh_result,fresh),(False,None))
    report={'sourceSha256':hashlib.sha256(raw).hexdigest(),'baselineCommit':'664d617' if args.baseline else None,
        'command':'python scripts/verify_read_boundary_completion.py'+(' --baseline' if args.baseline else ''),
        'scriptSha256':script_hash,'exitCode':int(any(not c['passed'] for c in checks)),
        'validationPackages':{name:importlib.metadata.version(name) for name in ['jsonschema','referencing','rfc3986-validator','uri-template']},
        'resourceVersions':{p:rs[p]['sha256'] for p in [PATH,ARTIFACT,NATIVE,'contracts/generation/generation-contracts.schema.json','scripts/ssot/ssot_control.py'] if p in rs},
        'scope':__doc__,'checked':len(checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,
        'remaining':'DB provenance, actual snapshot persistence, transport/header/SSE integration and generation events are not proven by these fixtures.'}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-664d617/read-boundaries');out.mkdir(parents=True,exist_ok=True)
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=script_hash:raise ValueError('Test script changed during execution')
    (out/('read-baseline.json' if args.baseline else 'read-current.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:report[k] for k in ['sourceSha256','checked','failed']}))
    for c in checks:
        if not c['passed']:print(json.dumps(c))
    return int(bool(report['failed']))


if __name__=='__main__':raise SystemExit(main())
