import json,sys,copy
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resources,resource_index,SSOT
from author_resource_updates import rewrite
from author_native_read_refs import apply
HERE=Path(__file__).parent;text=SSOT.read_text();candidate=apply(text);checks=[]
def check(name,value):
 checks.append({'id':name,'status':'PASS' if value else 'FAIL'})
 if not value:raise AssertionError(name)
def modified(text,mutator):
 rs=resource_index(list(resources(text)));d=json.loads(rs['contracts/operation-contracts.json']['raw']);mutator(d)
 return rewrite(text,list(resources(text)),{'contracts/operation-contracts.json':(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()})
check('publication_idempotent',apply(candidate)==candidate)
# Unrelated owner-session authoring must not invalidate exact MCP consumption.
unrelated=modified(text,lambda d:d['$defs'].update({'fixture.unrelated':{'type':'null'}}));check('unrelated_definition_preserved','fixture.unrelated' in json.loads(resource_index(list(resources(apply(unrelated))))['contracts/operation-contracts.json']['raw'])['$defs'])
for name,mutator,expected in [
 ('native_changed',lambda d:d['$defs']['mcp.native.2026-07-28']['$defs']['ReadResourceRequest']['properties'].update({'fixture':{'type':'boolean'}}),'SELECTED_NATIVE_DEFINITION_CHANGED'),
 ('selected_operation_changed',lambda d:next(x for x in d['records'] if x['operationId']=='mcp.prompts.get').update({'aggregateRoot':'incorrect'}),'SELECTED_OPERATION_CHANGED:mcp.prompts.get'),
 ('conflicting_alias',lambda d:d['$defs'].update({'mcp.prompts.get:command':{'$id':'incorrect','type':'null'}}),'ALIAS_IDENTITY_CONFLICT:mcp.prompts.get:command')]:
 try:apply(modified(text,mutator))
 except ValueError as e:check(name,str(e)==expected)
 else:check(name,False)
(HERE/'authoring-proof.json').write_text(json.dumps({'status':'PASS','checks':checks,'passed':len(checks),'failed':0,'scope':'Publication idempotence, selected consumption guards, unrelated changes preservation'},indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(checks)}))
