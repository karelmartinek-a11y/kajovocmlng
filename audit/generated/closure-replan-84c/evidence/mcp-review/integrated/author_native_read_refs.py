"""Coordinator may import apply(text); standalone writes ONLY this owned directory."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resources,resource_index,SSOT
from author_resource_updates import rewrite
from operation_catalog import catalog
HERE=Path(__file__).parent

def updates(text, package=None):
    rs=resource_index(list(resources(text)));package=package if package is not None else json.loads((HERE/'native-read-reference-patch.json').read_text());target=package['targetResource']
    for path,expected in package['consumedResources'].items():
        if rs[path]['sha256']!=expected:raise ValueError('CONSUMED_RESOURCE_CHANGED:'+path)
    d=json.loads(rs[target]['raw'])
    native_hash=hashlib.sha256(json.dumps(d['$defs']['mcp.native.2026-07-28'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if native_hash!=package['selectedNativeDefinitionSha256']:raise ValueError('SELECTED_NATIVE_DEFINITION_CHANGED')
    ops=catalog(rs)
    for op,expected in package['selectedOperationSha256'].items():
        actual=hashlib.sha256(json.dumps({k:v for k,v in ops[op].items() if k!='sourceRef'},sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if actual!=expected:raise ValueError('SELECTED_OPERATION_CHANGED:'+op)
    for p in package['jsonPatch']:
        key=p['path'].split('/',2)[2]
        prior=package.get('previousPublishedDefinitions',{}).get(key)
        if prior is not None:
            actual_prior_hash=hashlib.sha256(json.dumps(prior,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if actual_prior_hash!=package.get('previousPublishedDefinitionSha256',{}).get(key):raise ValueError('PRIOR_PUBLICATION_DIGEST_MISMATCH:'+key)
        if key in d['$defs'] and d['$defs'][key]!=p['value'] and d['$defs'][key]!=package.get('previousPublishedDefinitions',{}).get(key):raise ValueError('ALIAS_IDENTITY_CONFLICT:'+key)
        d['$defs'][key]=p['value']
    return {target:(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()}

def apply(text):return rewrite(text,list(resources(text)),updates(text))
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=SSOT.read_text();u=updates(text)
    if args.check:
        rs=resource_index(list(resources(text)))
        d=json.loads(rs['contracts/operation-contracts.json']['raw']);package=json.loads((HERE/'native-read-reference-patch.json').read_text())
        differences=[]
        for item in package['jsonPatch']:
            key=item['path'].split('/',2)[2];actual=d['$defs'].get(key)
            if actual!=item['value']:differences.append({'path':item['path'],'reason':'MISSING' if key not in d['$defs'] else 'STALE_ALIAS_DEFINITION'})
        print(json.dumps({'status':'BLOCKED' if differences else 'PASS','publicationDifferences':differences}))
        sys.exit(1 if differences else 0)
    for path,raw in u.items():(HERE/'operation-contracts.patched.json').write_bytes(raw)
    print(json.dumps({'status':'AUTHORABLE','writesCanonical':False,'resources':{p:hashlib.sha256(r).hexdigest() for p,r in u.items()}}))
