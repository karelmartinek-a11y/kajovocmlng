"""Parameterized fixtures for repaired bindings and still-open escape paths.

All values are synthetic. Positive envelope witnesses do not certify business
validity; unresolved domain rules are reported as FAIL, never as expected PASS.
"""
import copy
import argparse
import json
import subprocess
import sys
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from phase1_schema_closure import Inventory
from ssot_sources import ROOT, SSOT

UUID='00000000-0000-4000-8000-000000000001'
DIGEST='sha256:'+'0'*64


def example(schema, resolver):
    if '$id' in schema:
        resolver=resolver.in_subresource(Resource.from_contents(schema))
    if '$ref' in schema:
        r=resolver.lookup(schema['$ref']);return example(r.contents,r.resolver)
    if 'const' in schema:return schema['const']
    if 'enum' in schema:return schema['enum'][0]
    for key in ('oneOf','anyOf'):
        if key in schema:
            choices=sorted(schema[key],key=lambda s:s.get('type')=='null')
            return example(choices[0],resolver)
    typ=schema.get('type')
    if isinstance(typ,list):typ=next(t for t in typ if t!='null')
    if typ=='object':return {k:example(schema['properties'][k],resolver) for k in schema.get('required',[])}
    if typ=='array':return [example(schema['items'],resolver) for _ in range(schema.get('minItems',0))]
    if typ=='null':return None
    if typ=='boolean':return False
    if typ in ('number','integer'):return schema.get('minimum',0)
    if typ=='string':
        pattern=schema.get('pattern','')
        if schema.get('format')=='date-time':return '2026-09-23T12:00:00.000Z'
        if schema.get('format')=='uuid' or '{8}-' in pattern:return UUID
        if 'sha256:' in pattern:return DIGEST
        if '0|[1-9]' in pattern:return '0'
        if pattern.startswith('^[1-9]'):return '1'
        return 'sample' if schema.get('minLength',0)<=6 else 's'*schema['minLength']
    raise ValueError('No justified fixture generator for '+str(schema)[:250])


def run():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',action='store_true');args=parser.parse_args()
    source=subprocess.check_output(['git','show','6180d9fe67dfaa5365190301dfd58cc8d9812f3d:00_SSOT/KajovoCMLNG_SSOT.md']).decode() if args.baseline else SSOT.read_text(encoding='utf8')
    inv=Inventory(source)
    checks=[]; fixtures=[]
    def check(name, validator, value, valid, category='repaired-contract'):
        try:
            errors=list(validator.iter_errors(value))
            actual=not errors
            checks.append({'case':name,'category':category,'expectedValid':valid,'actualValid':actual,
                           'status':'PASS' if actual==valid else 'FAIL',
                           'validationErrors':[e.message[:250] for e in errors[:3]]})
        except Exception as exc:
            checks.append({'case':name,'category':category,'status':'ERROR','reason':str(exc)})
        fixtures.append({'case':name,'expectedValid':valid,'value':value})
    for op in inv.docs['r16/contracts/r15-visual-operation-closure.json']['operations']:
        for role in ('request','response'):
            ref=op.get(role+'SchemaRef')
            if ref is None:
                definition=op[role+'Definition']
                matches=[p for p in op[role+'SchemaAuthority'].split(' + ') if definition in inv.docs[p].get('$defs',{})]
                if len(matches)!=1:raise ValueError('Ambiguous fixture binding')
                ref=matches[0]+'#/$defs/'+definition
            v=inv.validator(ref)
            sample=example(v.schema,inv.registry.resolver())
            name=op['operationId']+'/'+role
            check(name+'/positive',v,sample,True)
            check(name+'/wrong-type',v,42,False)
            check(name+'/null',v,None,False)
            if isinstance(sample,dict):
                bad=copy.deepcopy(sample);bad['NOT_A_DECLARED_FIELD']=True;check(name+'/unknown-field',v,bad,False)
                if sample:
                    bad=copy.deepcopy(sample);bad.pop(next(iter(sample)));check(name+'/missing-required',v,bad,False)
            if op['operationId']=='browser.annotation.list' and role=='request':
                check(name+'/unknown-query',v,{'NOT_A_DECLARED_FILTER':'x'},False)
            if op['operationId']=='browser.annotation.create' and role=='request':
                bad=copy.deepcopy(sample);bad['sourceKind']='NOT_A_DECLARED_VARIANT';check(name+'/variant',v,bad,False)
    for i,route in enumerate(inv.docs['contracts/payload-contracts.json']['records']):
        if route['operationId'] not in ('secret.create','generation.job.create'):continue
        ref='contracts/payload-contracts.json#/records/'+str(i)+'/requestSchema'
        v=inv.validator(ref);sample=example(v.schema,inv.registry.resolver());name=route['operationId']
        if not sample['body']['values']:
            body=route['requestSchema']['properties']['body']
            if 'oneOf' in body:body=next(s for s in body['oneOf'] if s.get('type')!='null')
            sample['body']['values']=[example(body['properties']['values']['items'],inv.registry.resolver())]
        # This only witnesses the envelope invariants. The unbound slot below
        # is deliberately NOT labelled a valid domain example.
        check(name+'/envelope-witness',v,sample,True,'envelope-only')
        for mutation in ('empty-values','null-body','null-idempotency-key','missing-body','wrong-values-type'):
            bad=copy.deepcopy(sample)
            if mutation=='empty-values':bad['body']['values']=[]
            elif mutation=='null-body':bad['body']=None
            elif mutation=='null-idempotency-key':bad['guards']['idempotencyKey']=None
            elif mutation=='missing-body':bad.pop('body')
            else:bad['body']['values']='wrong'
            check(name+'/'+mutation,v,bad,False,'necessary-create-condition')
        bad=copy.deepcopy(sample);bad['query']=[{'name':'NOT_A_DECLARED_FILTER','value':'x'}]
        check(name+'/unknown-query',v,bad,False,'open-domain-gap')
        bad=copy.deepcopy(sample);bad['body']['values'][0]['canonicalJson']='{not JSON'
        check(name+'/malformed-canonicalJson',v,bad,False,'open-domain-gap')
        bad=copy.deepcopy(sample);bad['body']['values'][0]['slot']='NOT_A_DOMAIN_FIELD'
        check(name+'/unknown-domain-field',v,bad,False,'open-domain-gap')
        bad=copy.deepcopy(sample);bad['body']['values']*=2
        check(name+'/duplicate-domain-slot',v,bad,False,'open-domain-gap')
    fc=FormatChecker()
    for fmt,value in [('uuid','not-a-uuid'),('date-time','2026-99-99T00:00:00Z')]:
        if fmt not in fc.checkers:raise RuntimeError('Missing format dependency:'+fmt)
        check('format/'+fmt,Draft202012Validator({'type':'string','format':fmt},format_checker=fc),value,False,'validator')
    # Missing external references must raise, not fetch remote content or pass.
    try:
        Draft202012Validator({'$ref':'https://invalid.example/missing'},registry=Registry()).validate({})
    except Exception:
        checks.append({'case':'offline-missing-reference','category':'validator','status':'PASS'})
    else:
        checks.append({'case':'offline-missing-reference','category':'validator','status':'FAIL'})
    identity='urn:phase1:collision-test'
    inv.ids[identity]=[('one','',{'type':'string'}),('two','',{'type':'integer'})]
    for order in (False,True):
        if order:inv.ids[identity].reverse()
        try:inv.resolve(identity)
        except ValueError as exc:
            checks.append({'case':'conflicting-id-order-'+str(order),'category':'validator',
                           'status':'PASS' if 'CONFLICTING_ID' in str(exc) else 'FAIL'})
        else:checks.append({'case':'conflicting-id-order-'+str(order),'category':'validator','status':'FAIL'})
    for label,schema in [('unknown-dialect',{'$schema':'urn:unknown:dialect','type':'string'}),
                         ('unknown-format',{'$schema':'https://json-schema.org/draft/2020-12/schema','type':'string','format':'not-installed'})]:
        inv.docs['test:'+label]=schema
        try:inv.validator('test:'+label)
        except ValueError:
            checks.append({'case':label,'category':'validator','status':'PASS'})
        else:checks.append({'case':label,'category':'validator','status':'FAIL'})
    format_property=inv.validator('closure/contracts/operation-payloads.json#/records/9/requestSchema')
    sample=example(format_property.schema,inv.registry.resolver())
    check('format-property-is-not-schema-keyword',format_property,sample,True,'validator')
    dependency=subprocess.run([sys.executable,'-S',str(ROOT/'scripts/verify_phase1_contracts.py')],capture_output=True,text=True)
    checks.append({'case':'missing-jsonschema-dependency','category':'validator',
                   'status':'PASS' if dependency.returncode!=0 and "No module named 'jsonschema'" in dependency.stderr else 'FAIL',
                   'exitCode':dependency.returncode})
    report={'scope':'Schema fixtures and necessary create conditions, not domain closure or runtime evidence',
            'checks':checks,'failed':sum(c['status']!='PASS' for c in checks),'checked':len(checks)}
    suffix='-before' if args.baseline else ''
    (ROOT/('audit/generated/phase1-contract-tests'+suffix+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (ROOT/('audit/generated/phase1-fixtures'+suffix+'.json')).write_text(json.dumps(fixtures,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
    return int(bool(report['failed']))


if __name__=='__main__':sys.exit(run())
