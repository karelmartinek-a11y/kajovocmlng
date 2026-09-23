#!/usr/bin/env python3
"""Executable R2 checks. Static/schema/reference-model evidence, not application acceptance."""
from __future__ import annotations
import argparse,ast,base64,copy,hashlib,json,os,random,re,subprocess,sys,tempfile,zlib
from pathlib import Path
import jsonschema
from ssot_control import *
import schema_projection as projection
import boundary_codecs as codec
import generation_guards as guards

RESULTS=[]
def test(name,fn):
    try:
        value=fn()
        if value is False:raise AssertionError('Predicate returned false')
        RESULTS.append({'id':name,'status':'PASS'})
    except Exception as e:RESULTS.append({'id':name,'status':'FAIL','detail':type(e).__name__+': '+str(e)[:1500]})
def rejects(fn):
    try:fn()
    except (ContractFailure,jsonschema.ValidationError,ValueError):return True
    return False

def main():
    ap=argparse.ArgumentParser();ap.add_argument('ssot',type=Path);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();doc=Document(args.ssot);D=doc.schema['$defs']
    test('document.manifest',doc.verify_manifest);test('catalog.cross_references',lambda:check_catalogs(doc))
    for name,definition in D.items():test('metaschema.'+name,lambda v=definition:jsonschema.Draft202012Validator.check_schema(v))
    # Positive and mutated instances for each of the 19 step inputs and outputs.
    special={'Uuid':'11111111-1111-4111-8111-111111111111','Digest':raw_digest(b'R2-TEST-ONLY'),'Id':'fixture','Counter':'0','Timestamp':'2026-09-21T00:00:00.000Z','RelPath':'components/fixture/index.ts','JsonPointer':'/fixture','ExactVersion':'24.1.0','NonemptyJsonPointer':'/fixture','PositiveCounter':'1','NativeToolName':'native tool'}
    def merge(a,b):
        result=copy.deepcopy(a)
        for k,v in b.items():
            if k=='properties':
                result.setdefault(k,{})
                for f,g in v.items():result[k][f]=merge(result[k].get(f,{}),g)
            elif k=='required':result[k]=sorted(set(result.get(k,[])+v))
            else:result[k]=copy.deepcopy(v)
        return result
    def resolve(s):
        if '$ref' in s:return merge(D[s['$ref'].split('/')[-1]],{k:v for k,v in s.items() if k!='$ref'})
        if 'allOf' in s:
            out={k:v for k,v in s.items() if k!='allOf'}
            for item in s['allOf']:out=merge(out,resolve(item))
            return out
        return s
    def sample(s,depth=0):
        if depth>80:raise ValueError('Fixture recursion')
        if 'const' in s:return copy.deepcopy(s['const'])
        if 'enum' in s:return s['enum'][0]
        if '$ref' in s:
            name=s['$ref'].split('/')[-1]
            if name in special:return special[name]
            return sample(resolve(s),depth+1)
        if 'allOf' in s:return sample(resolve(s),depth+1)
        if 'anyOf' in s:
            if any(x.get('type')=='null' for x in s['anyOf']):return None
            return sample(s['anyOf'][0],depth+1)
        if 'oneOf' in s:return sample(s['oneOf'][0],depth+1)
        t=s.get('type')
        if t=='object':return {k:sample(v,depth+1) for k,v in s.get('properties',{}).items() if k in s.get('required',[])}
        if t=='array':return [sample(s['items'],depth+1) for _ in range(s.get('minItems',0))]
        if t=='null':return None
        if t=='boolean':return True
        if t in {'integer','number'}:return s.get('minimum',0)
        if t=='string':
            if s.get('format')=='date-time':return special['Timestamp']
            for value in ['fixture','urn:kcml:fixture:1','application/json','sha512-Zml4dHVyZQ==','24.1.0','11.1.0','1.0.0','2026-07-28','t_fixture','KCML0001','kcml0001.kaja.hcasc.cz','ENV','a'*40,'eA==','']:
                if len(value)>=s.get('minLength',0) and len(value)<=s.get('maxLength',10**9) and (not s.get('pattern') or re.search(s['pattern'],value)):return value
        raise ValueError('Cannot build deterministic fixture: '+str(s)[:200])
    def valid(name,value):
        doc.validate(name,value);return True
    for item in doc.catalog:
        for side in ['Input','Output']:
            name=item['kind']+side
            try:
                value=sample({'$ref':'#/$defs/'+name})
                if side=='Output':value['checks'][0]['verdict']='PASS';value['checks'][0]['problems']=[]
            except Exception as e:
                test('instance.'+name,lambda e=e:(_ for _ in ()).throw(e));continue
            test('instance.'+name,lambda n=name,v=value:valid(n,v))
            extra=copy.deepcopy(value);extra['extraUndeclaredField']=True
            test('reject.extra.'+name,lambda n=name,v=extra:rejects(lambda:doc.validate(n,v)))
            for key in value:
                bad=copy.deepcopy(value);bad.pop(key)
                test('reject.missing.'+name+'.'+key,lambda n=name,v=bad:rejects(lambda:doc.validate(n,v)))
    raw_binding={'origin':'NODE_OUTPUT','producerNodeId':'fixture','outputSlot':'schemaBundle','expectedKind':'JSON_SCHEMA_BUNDLE','expectedSchema':None}
    test('raw_node_output.null_schema',lambda:valid('PlannedInput',raw_binding))
    bad_binding={**raw_binding,'expectedKind':'GENERATION_PLAN'}
    test('json_node_output.requires_schema',lambda:rejects(lambda:doc.validate('PlannedInput',bad_binding)))
    # Receipts from later saga steps must not bypass an absent predecessor.
    saga_sample=sample(D['IntegrationStepReceipt'])
    saga_sample['stepId']='S02'
    test('saga.reject_out_of_order_receipt',lambda:rejects(lambda:verify_saga(doc,[saga_sample],saga_sample['jobId'],saga_sample['sagaId'],lambda ref:ref)))
    failed=sample(D['IntegrationStepReceipt']['oneOf'][1])
    test('saga.failed_no_success_artifact',lambda:valid('IntegrationStepReceipt',failed))
    failed_with_result={**failed,'result':saga_sample['result']}
    test('saga.failed_reject_success_artifact',lambda:rejects(lambda:doc.validate('IntegrationStepReceipt',failed_with_result)))
    failed_unknown={**failed,'effectOutcome':'UNKNOWN'}
    test('saga.failed_reject_unknown_effect',lambda:rejects(lambda:doc.validate('IntegrationStepReceipt',failed_unknown)))
    manual=sample(D['IntegrationStepReceipt']['oneOf'][2]);manual['problem']['retryDirective']='MANUAL_REVIEW'
    test('saga.manual_review_schema',lambda:valid('IntegrationStepReceipt',manual))
    # Workspace proposal validates old bytes, slot ownership and allowed operations.
    pp=sample({'$ref':'#/$defs/PathPlan'});slot=sample({'$ref':'#/$defs/PathSlot'})
    slot.update(slotId='slot',repositoryPath='components/fixture/index.ts',ownerModule='components/fixture',allowedWriterNodeIds=['writer'],allowedOperations=['ADD','UPDATE','DELETE'],requirementIds=['req'],expectedSchema=None)
    pp['slots']=[slot]
    current=sample({'$ref':'#/$defs/WorkspaceRef'});files={slot['repositoryPath']:b'old'};current['treeDigest']=tree_digest(files)
    patch=sample({'$ref':'#/$defs/WorkspacePatchSet'});patch.update(jobId=pp['jobId'],nodeId='writer',base=current,pathPlanDigest=semantic_digest(pp))
    payload={'encoding':'BASE64','data':base64.b64encode(b'new').decode(),'sizeBytes':3,'contentDigest':raw_digest(b'new')}
    patch['changes']=[{'slotId':'slot','path':slot['repositoryPath'],'requirementIds':['req'],'reason':'TEST_ONLY','operation':'UPDATE','expectedOldDigest':raw_digest(b'old'),'content':payload}]
    test('patch.update_correct_bytes',lambda:apply_patch_model(doc,patch,pp,current,files,lambda ref:b'')=={slot['repositoryPath']:b'new'})
    bad=copy.deepcopy(patch);bad['changes'][0]['expectedOldDigest']=raw_digest(b'other')
    test('patch.old_digest_reject',lambda:rejects(lambda:apply_patch_model(doc,bad,pp,current,files,lambda ref:b'')))
    bad=copy.deepcopy(patch);bad['changes'][0]['path']='components/other/index.ts'
    test('patch.exact_path_reject',lambda:rejects(lambda:apply_patch_model(doc,bad,pp,current,files,lambda ref:b'')))
    bad=copy.deepcopy(patch);bad['nodeId']='other_writer'
    test('patch.writer_reject',lambda:rejects(lambda:apply_patch_model(doc,bad,pp,current,files,lambda ref:b'')))
    # A real minimal declared DAG, followed by a cycle and a coverage violation.
    plan=sample({'$ref':'#/$defs/GenerationPlan'});node=sample({'$ref':'#/$defs/PlanNode'});record=doc.catalog[0]
    plan.update(planId=pp['planId'],jobId=pp['jobId'],specificationDigest=pp['sourceSpecificationDigest'])
    plan['scopeLock']['approvedSpecificationDigest']=plan['specificationDigest'];plan['scopeLock']['approvedRequirementIds']=['req'];plan['scopeLock']['approvedTargetKeys']=pp['symbolicTargetKeys']
    node.update(nodeId='writer',kind=record['kind'],phase=record['phase'],operationId=record['canonicalOperationId'],dependencies=[],pathSlotIds=['slot'],requirementIds=['req'])
    node['outputSchema']={'schemaId':doc.schema['$id'],'definition':record['outputDefinition'],'bundleDigest':doc.schema_digest};node['inputBindings']=[];plan['rootArtifacts']=[]
    for index,(name,kind) in enumerate(record['inputSlots'].items(),1):
        ar=sample({'$ref':'#/$defs/ArtifactRef'});ar['artifactId']='00000000-0000-4000-8000-'+str(index).zfill(12);ar['kind']=kind
        ar['schema']={'schemaId':doc.schema['$id'],'definition':doc.kind_to_schema[kind],'bundleDigest':doc.schema_digest} if kind in doc.kind_to_schema else None
        plan['rootArtifacts'].append(ar);node['inputBindings'].append({'slot':name,'source':{'origin':'ROOT_ARTIFACT','artifact':ar}})
    plan['nodes']=[node];cov=sample({'$ref':'#/$defs/RequirementCoverage'});cov.update(requirementId='req',producerNodeIds=['writer'],verificationNodeIds=['writer']);plan['coverage']=[cov]
    test('plan.valid_declared_dag',lambda:validate_plan(doc,plan,pp)==['writer'])
    cycle=copy.deepcopy(plan);cycle['nodes'][0]['dependencies']=['writer']
    test('plan.reject_cycle',lambda:rejects(lambda:validate_plan(doc,cycle,pp)))
    missing=copy.deepcopy(plan);missing['coverage'][0]['requirementId']='other'
    test('plan.reject_scope_change',lambda:rejects(lambda:validate_plan(doc,missing,pp)))
    for good in ['0','1','9007199254740993','9223372036854775807']:test('counter.valid.'+good,lambda v=good:counter(v)>=0)
    for i,bad in enumerate(['01','-1','+1','1.0','1e2','9223372036854775808','1\n',1,True,None]):test('counter.reject.'+str(i),lambda v=bad:rejects(lambda:counter(v)))
    test('counter.exhaustion',lambda:rejects(lambda:next_counter('9223372036854775807')))
    for i,bad in enumerate([b'{"x":1,"x":2}',b'NaN',b'Infinity',b'{"x":9007199254740993}',b'"\\ud800"',b'\xef\xbb\xbf{}',b'\xff',b'['*129+b']'*129]):test('json.reject.'+str(i),lambda v=bad:rejects(lambda:strict_json(v)))
    test('jcs.utf16_and_numbers',lambda:jcs({'\u20ac':1,'a':1e-7,'z':-0.0})==b'{"a":1e-7,"z":0,"\xe2\x82\xac":1}')
    for i,bad in enumerate(['../etc/passwd','/etc/passwd','a//b','a/../b','C:/a','a\\b','a/%2e%2e','a/./b','a\n']):test('path.reject.'+str(i),lambda v=bad:rejects(lambda:safe_relpath(v)))
    test('path.case_collision',lambda:rejects(lambda:path_set(['a/A.ts','a/a.ts'])))
    test('path.prefix_collision',lambda:rejects(lambda:path_set(['a','a/b'])))
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);(root/'real').write_bytes(b'abc');(root/'link').symlink_to(root/'real')
        test('filesystem.safe_open',lambda:read_regular_at(root,'real')==b'abc')
        test('filesystem.symlink_rejected',lambda:rejects(lambda:read_regular_at(root,'link')))
        os.link(root/'real',root/'hard');test('filesystem.hardlink_rejected',lambda:rejects(lambda:read_regular_at(root,'hard')))
    # Lossless model codec over explicit and deterministic randomized JSON trees.
    rng=random.Random(21092026)
    def random_value(depth):
        if depth==0:return rng.choice([None,False,True,0,2.5,'','\u017e\u00e1ba','x\ny'])
        kind=rng.randrange(4)
        if kind==0:return random_value(0)
        if kind==1:return [random_value(depth-1) for _ in range(rng.randrange(4))]
        return {'k'+str(i):random_value(depth-1) for i in range(rng.randrange(4))}
    values=[{}, {'x':None},[],None,False,0,{'x':[{},None,{'y':False}]},9007199254740991]+[random_value(4) for _ in range(100)]
    for i,value in enumerate(values):test('projection.roundtrip.'+str(i),lambda v=value:strict_json(json.dumps(projection.decode(projection.encode(v)),ensure_ascii=True).encode())==v)
    test('projection.absence_distinct_from_null',lambda:projection.encode({})!=projection.encode({'x':None}))
    base=projection.encode({'x':1})
    for kind in ['duplicate_key','cycle','orphan','unused_scalar','null_number','missing_field']:
        bad=copy.deepcopy(base)
        if kind=='duplicate_key':bad['nodes'][0]['keys']=['x','x'];bad['nodes'][0]['children']=[1,1]
        elif kind=='cycle':bad['nodes'][0]['children']=[0]
        elif kind=='orphan':bad['nodes'].append({**bad['nodes'][1],'id':2})
        elif kind=='unused_scalar':bad['nodes'][0]['booleanValue']=True
        elif kind=='null_number':bad['nodes'][1]['numberValue']=None
        else:bad['nodes'][0].pop('keys')
        test('projection.reject.'+kind,lambda v=bad:rejects(lambda:projection.decode(v)))
    test('projection.structured_name',lambda:projection.structured_format('kcml_proposal')['strict'] is True)
    test('projection.non_ascii_name_reject',lambda:rejects(lambda:projection.structured_format('\u010d')))
    # Every declared reference-model edge is exercised; all undeclared state pairs are denied.
    models=doc.load('contracts/execution/model-catalog.json')
    for model in models:
        test('model.schema.'+model['modelId'],lambda m=model:valid('ExecutableModel',m))
        test('model.terminal.'+model['modelId'],lambda m=model:not(set(m['terminalStates']) & {e['from'] for e in m['edges']}))
        for j,edge in enumerate(model['edges']):
            state={'modelId':model['modelId'],'aggregateId':'fixture','state':edge['from'],'stateVersion':'1','fence':'1','incarnation':'fixture','cancellationVersion':'0','eventSequence':'1','terminalOutcomeDigest':None}
            evidence={'effectOutcome':'NOT_DISPATCHED','cleanupComplete':True,'dependenciesComplete':True,'preconditionsComplete':True,'cancelRequested':True,'rollbackRequested':True,'resumeState':edge['to'],'functionalContractChanged':'FUNCTIONAL_CHANGE' in edge['guardIds'],'scopeUnchanged':True}
            command={'modelId':model['modelId'],'aggregateId':'fixture','logicalOperationId':'fixture','idempotencyKey':'fixture','inputDigest':special['Digest'],'expectedState':edge['from'],'expectedStateVersion':'1','expectedFence':'1','expectedIncarnation':'fixture','expectedCancellationVersion':'0','toState':edge['to'],'evidence':evidence};command['inputDigest']=model_input_digest(command)
            def edgecheck(m=model,s=state,c=command):
                machine=ReferenceMachine(m,s);out=machine.transition(c);doc.validate('ModelObservation',out)
                require(out['after']['state']==c['toState'] and out['after']['stateVersion']=='2','STATE_VERSION_CONFLICT','','Wrong model transition')
                replay=machine.transition(c);require(replay['replayed'] and machine.state==out['after'],'IDEMPOTENCY_CONFLICT','','Replay changed state')
                return True
            test('model.edge_and_replay.'+model['modelId']+'.'+str(j),edgecheck)
            bad=copy.deepcopy(command);bad['expectedFence']='0'
            test('model.reject_stale_fence.'+model['modelId']+'.'+str(j),lambda m=model,s=state,c=bad:rejects(lambda:ReferenceMachine(m,s).transition(c)))
            bad=copy.deepcopy(command);bad['evidence']['preconditionsComplete']=False
            test('model.reject_guard.'+model['modelId']+'.'+str(j),lambda m=model,s=state,c=bad:rejects(lambda:ReferenceMachine(m,s).transition(c)))
        edgepairs={(e['from'],e['to']) for e in model['edges']}
        for f in model['states']:
            for to in model['states']:
                if (f,to) in edgepairs:continue
                state={'modelId':model['modelId'],'aggregateId':'fixture','state':f,'stateVersion':'1','fence':'1','incarnation':'fixture','cancellationVersion':'0','eventSequence':'1','terminalOutcomeDigest':None}
                c=copy.deepcopy(command);c['expectedState']=f;c['toState']=to;c['inputDigest']=model_input_digest(c)
                test('model.forbidden.'+model['modelId']+'.'+f+'.'+to,lambda m=model,s=state,c=c:rejects(lambda:ReferenceMachine(m,s).transition(c)))
    model=models[0];edge=model['edges'][0];s={'modelId':model['modelId'],'aggregateId':'fixture','state':edge['from'],'stateVersion':'1','fence':'1','incarnation':'fixture','cancellationVersion':'0','eventSequence':'1','terminalOutcomeDigest':None}
    c={'modelId':model['modelId'],'aggregateId':'fixture','logicalOperationId':'fixture','idempotencyKey':'fixture','inputDigest':special['Digest'],'expectedState':edge['from'],'expectedStateVersion':'1','expectedFence':'1','expectedIncarnation':'fixture','expectedCancellationVersion':'0','toState':edge['to'],'evidence':evidence};c['inputDigest']=model_input_digest(c)
    bad=copy.deepcopy(c);bad['toState']='UNDECLARED'
    test('model.forged_digest',lambda:rejects(lambda:ReferenceMachine(model,s).transition(bad)))
    for i,value in enumerate(['abc',' leading','trailing ','\u017elut\u00fd','x\ny','=?base64?YWJj?=','']):test('header.roundtrip.'+str(i),lambda v=value:codec.decode_header(codec.encode_header(v))==v)
    test('header.invalid_base64',lambda:rejects(lambda:codec.decode_header('=?base64?YQ=?=')))
    test('component.variable_width',lambda:codec.component_code('10000')=='KCML10000')
    test('component.zero_reject',lambda:rejects(lambda:codec.component_code('0')))
    frame=codec.encode_frame('REQUEST',1,jcs({'x':1}))
    test('ipc.roundtrip',lambda:codec.decode_frame(frame,1)==('REQUEST',jcs({'x':1})))
    test('ipc.sequence_reject',lambda:rejects(lambda:codec.decode_frame(frame,2)))
    test('ipc.truncated_reject',lambda:rejects(lambda:codec.decode_frame(frame[:-1],1)))
    test('ipc.chunk_size_reject',lambda:rejects(lambda:codec.encode_frame('STREAM_CHUNK',1,b'x'*65537)))
    for i,route in enumerate(doc.load('contracts/execution/route-catalog.json')):
        test('route.schema.'+str(i),lambda r=route:valid('RouteContract',r))
        params={x['parameter']:special[x['schemaDefinition']] for x in route['pathSegments'] if 'parameter' in x}
        test('route.render.'+str(i),lambda r=route,p=params:codec.render_route(r,p).startswith('/'))
    for i,recipe in doc.load('contracts/execution/mcp-native-recipes.json').items():test('native.recipe.'+i,lambda r=recipe:valid('McpNativeRecipe',r))
    test('sdk.design_schema',lambda:valid('SdkDesignProfile',doc.load('contracts/execution/sdk-design-profile.json')))
    inv={'businessOutcome':'SUCCEEDED','snapshotCurrent':True,**{k:[] for k in ['unknownEffects','pendingChildren','activeLeases','provisionalBindings','orphanRuntimes','unconfirmedPointers','pendingRequiredCleanup','uncommittedAudit','pendingAuthorityOutbox']}}
    test('closure.clean',lambda:closure(inv))
    for k in inv:
        if not isinstance(inv[k],list):continue
        dirty=copy.deepcopy(inv);dirty[k]=['unclosed']
        test('closure.reject.'+k,lambda v=dirty:rejects(lambda:closure(v)))
    facts={'terminalCommitted':False,'effectOutcome':'UNKNOWN','possibleDispatch':True,'outcomeReconciled':False,'compensationRequired':False,'cleanupComplete':False,'businessWorkTerminal':False,'cancelRequested':False,'currentAuthority':True,'checkpointCompatible':True,'retryAllowed':True}
    test('recovery.unknown_no_retry',lambda:recovery_action(facts)=='MANUAL_REVIEW')
    test('recovery.terminal_first',lambda:recovery_action({**facts,'terminalCommitted':True})=='REPLAY_TERMINAL')
    test('guard.owner_model_reject',lambda:rejects(lambda:guards.model_selection('a','b','a','RESPONSES','OPENAI')))
    test('guard.invalidation_transitive',lambda:guards.invalidated_gates({'input'},{'g1':{'input'},'g2':{'g1'},'g3':{'other'}})=={'g1','g2'})
    source=doc.load('audit/source-integrity.json');restored=zlib.decompress(base64.b64decode(source['zlibBase64'],validate=True))
    test('archive.byte_digest',lambda:len(restored)==source['sizeBytes'] and raw_digest(restored)==source['rawDigest'])
    original=restored.decode();scope=lambda v:v[v.index('## 4. '):v.index('## 5. ')]
    test('scope.byte_identical',lambda:scope(original)==scope(doc.text))
    # Every JSON fence is parsed strictly, independently from embedded asset extraction.
    for i,match in enumerate(re.finditer(r'^```json\n(.*?)^```\s*$',doc.text,re.M|re.S)):test('json_fence.'+str(i),lambda raw=match.group(1).encode():strict_json(raw))
    for p,asset in doc.assets.items():
        if p.endswith('.py'):test('python.syntax.'+p,lambda a=asset:ast.parse(a.body.decode()))
        if p.endswith('.mjs'):
            with tempfile.NamedTemporaryFile(suffix='.mjs') as temp:
                temp.write(asset.body);temp.flush();test('node.syntax.'+p,lambda p=temp.name:subprocess.run(['node','--check',p],capture_output=True).returncode==0)
    summary={'scope':'SCHEMA_STATIC_AND_EXECUTABLE_REFERENCE_TESTS','status':'PASS' if all(r['status']=='PASS' for r in RESULTS) else 'FAIL','tests':len(RESULTS),'passed':sum(r['status']=='PASS' for r in RESULTS),'failed':sum(r['status']=='FAIL' for r in RESULTS),'definitions':len(D),'localReferences':validate_local_refs(doc.schema),'nodeKinds':len(doc.catalog),'integrationSteps':len(doc.saga),'specialists':len(doc.load('contracts/execution/specialist-catalog.json')),'referenceModels':len(models),'declaredReferenceEdges':sum(len(m['edges']) for m in models),'routeOccurrences':len(doc.load('contracts/execution/route-catalog.json')),'normativeManifestDigest':raw_digest(doc.assets['contracts/execution/embedded-manifest.json'].body),'applicationRuntimeTested':False,'sdkPackagesTypechecked':False,'postgresStatementsExecuted':False,'productionAcceptanceTested':False,'architectureReadiness':'BLOCKED','results':RESULTS}
    args.report.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2));return 0 if summary['failed']==0 else 1
if __name__=='__main__':raise SystemExit(main())

