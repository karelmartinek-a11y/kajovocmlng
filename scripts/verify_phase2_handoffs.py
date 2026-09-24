"""Test actual embedded artifact hydration, with in-memory byte I/O only.

These tests do not certify filesystem security, transitive registry references,
runtime execution, or the still-missing R11 compact-reference adapter.
"""
import argparse
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from ssot_sources import ROOT, SSOT, resource_index, resources
from phase2_repair_handoffs import ADDITIONS, GEN

UUID='00000000-0000-4000-8000-000000000001'
DIGEST='sha256:'+'0'*64

def witness(schema,defs):
    if '$ref' in schema:return witness(defs[schema['$ref'].split('/')[-1]],defs)
    if 'const' in schema:return schema['const']
    if 'enum' in schema:return schema['enum'][0]
    if 'allOf' in schema:
        result=witness(schema['allOf'][0],defs)
        for part in schema['allOf'][1:]:
            for k,v in part.get('properties',{}).items():result[k]=witness(v,defs)
        return result
    for key in ['anyOf','oneOf']:
        if key in schema:
            branch=next((v for v in schema[key] if v.get('type')=='null'),schema[key][0])
            return witness(branch,defs)
    typ=schema.get('type')
    if typ=='object':return {k:witness(schema['properties'][k],defs) for k in schema.get('required',[])}
    if typ=='array':return [witness(schema['items'],defs) for _ in range(schema.get('minItems',0))]
    if typ=='null':return None
    if typ=='boolean':return False
    if typ in ['integer','number']:return schema.get('minimum',0)
    if typ=='string':
        pattern=schema.get('pattern','')
        if 'sha256:' in pattern:return DIGEST
        if '{8}-' in pattern:return UUID
        if pattern.startswith('^\\d+'):return '12.2'
        if '[a-z0-9.+-]+/' in pattern:return 'application/json'
        if 'urn:' in pattern:return 'urn:kcml:test'
        if schema.get('format')=='date-time':return '2026-09-24T00:00:00Z'
        if 'JsonPointer' in str(schema) or pattern.startswith('^(?:/') or pattern.startswith('^(/'):return ''
        return 'sample'
    raise ValueError('No fixture construction for '+str(schema)[:200])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--entry',action='store_true');args=parser.parse_args()
    source=ROOT/'.cache/phase2-entry/SSOT.md' if args.entry else SSOT
    rs=resource_index(resources(source.read_text(encoding='utf8')))
    directory=Path(tempfile.mkdtemp(prefix='phase2-content-',dir=ROOT/'.cache'))
    modulepath=directory/'ssot_control.py';modulepath.write_bytes(rs['scripts/ssot/ssot_control.py']['raw'])
    spec=importlib.util.spec_from_file_location('phase2_embedded_control',modulepath)
    control=importlib.util.module_from_spec(spec);sys.modules[spec.name]=control;spec.loader.exec_module(control)
    doc=control.Document(source);defs=doc.schema['$defs'];checks=[];fixtures={}
    def run_case(name,fn,expected):
        try:fn();valid=True;error=None
        except Exception as exc:valid=False;error=type(exc).__name__+': '+str(exc)
        checks.append({'case':name,'expectedValid':expected,'actualValid':valid,'status':'PASS' if expected==valid else 'FAIL','error':error})
    def hydrate(kind,definition,value,mutation=None,bytes_override=None):
        raw=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode() if bytes_override is None else bytes_override
        ref={'artifactId':UUID,'kind':kind,'schema':{'schemaId':doc.schema['$id'],'definition':definition,'bundleDigest':doc.schema_digest},
            'mediaType':'application/json','path':'fixture.json','contentDigest':control.raw_digest(raw),
            'sizeBytes':len(raw),'producerNodeId':None,'provenanceDigest':DIGEST}
        if mutation:mutation(ref)
        # Only replace physical byte loading. All original parsing, trusted
        # inventory, kind, schema address/digest and native validation still run.
        control.read_regular_at=lambda root,path,limit:raw
        return control.ArtifactResolver(doc,directory,{UUID:ref}).get(ref)
    for kind,(definition,role) in ADDITIONS.items():
        sample=witness(defs[definition],defs)
        if definition=='IntegrationPlan':
            for i,step in enumerate(sample['steps']):step['stepId']=f'S{i+1:02d}'
        fixtures[kind]=sample
        run_case(kind+'/native-positive',lambda:doc.validate(definition,sample),True)
        envelope={'schemaVersion':'1.0','role':role,'proposal':sample,'questions':[],'blocker':None}
        run_case(kind+'/producer-positive',lambda:doc.validate(role+'Proposal',envelope),True)
        run_case(kind+'/hydrate-positive',lambda:hydrate(kind,definition,sample),True)
        run_case(kind+'/null',lambda:hydrate(kind,definition,None),False)
        run_case(kind+'/wrong-type',lambda:hydrate(kind,definition,42),False)
        bad=copy.deepcopy(sample);bad.pop(next(iter(bad)))
        run_case(kind+'/missing-required',lambda:hydrate(kind,definition,bad),False)
        bad=copy.deepcopy(sample);bad['NOT_A_DECLARED_FIELD']=True
        run_case(kind+'/unknown-field',lambda:hydrate(kind,definition,bad),False)
        run_case(kind+'/invalid-json',lambda:hydrate(kind,definition,sample,bytes_override=b'{broken'),False)
        run_case(kind+'/duplicate-json-key',lambda:hydrate(kind,definition,sample,bytes_override=b'{"x":1,"x":2}'),False)
        run_case(kind+'/stale-schema-digest',lambda:hydrate(kind,definition,sample,lambda r:r['schema'].update(bundleDigest=DIGEST)),False)
        run_case(kind+'/wrong-definition',lambda:hydrate(kind,definition,sample,lambda r:r['schema'].update(definition='SourceAnalysis' if definition!='SourceAnalysis' else 'RequirementProposal')),False)
    sample=fixtures['REQUIREMENT_PROPOSAL']
    bad=copy.deepcopy(sample);bad['requirements']=[]
    run_case('requirement/empty-requirements',lambda:hydrate('REQUIREMENT_PROPOSAL','RequirementProposal',bad),False)
    bad=copy.deepcopy(sample);bad['requirements'][0]['kind']='NOT_A_VARIANT'
    run_case('requirement/invalid-kind',lambda:hydrate('REQUIREMENT_PROPOSAL','RequirementProposal',bad),False)
    bad=copy.deepcopy(sample);bad['objective']['requirementIds']*=2
    run_case('requirement/duplicate-identity',lambda:hydrate('REQUIREMENT_PROPOSAL','RequirementProposal',bad),False)
    envelope={'schemaVersion':'1.0','role':'REQUIREMENTS_ANALYST','proposal':sample,'questions':[],'blocker':None}
    envelope['proposal']=None
    run_case('producer/null-without-question-or-blocker',lambda:doc.validate('REQUIREMENTS_ANALYSTProposal',envelope),False)
    # Reproduce the still-open transport mismatch, without pretending this is
    # an implemented or validated adapter. R11 accepts metadata without the
    # native address/path required for actual hydration.
    from jsonschema import Draft202012Validator, FormatChecker
    oschema=json.loads(rs['r11/contracts/orchestration.schema.json']['raw'])
    compact_schema=oschema['$defs']['CAPABILITY_RESOLVERInput']['properties']['inputs']['properties']['requirementProposal']
    compact={'artifactId':UUID,'kind':'REQUIREMENT_PROPOSAL','contentDigest':DIGEST,
        'schemaDigest':None,'mediaType':'application/json','sizeBytes':0,'provenanceDigest':DIGEST}
    run_case('open-adapter/compact-reference-valid',lambda:Draft202012Validator(compact_schema,format_checker=FormatChecker()).validate(compact),True)
    run_case('open-adapter/compact-is-not-native-ArtifactRef',lambda:doc.validate('ArtifactRef',compact),False)
    full={'artifactId':UUID,'kind':'REQUIREMENT_PROPOSAL','schema':{'schemaId':doc.schema['$id'],'definition':'RequirementProposal','bundleDigest':doc.schema_digest},
        'mediaType':'application/json','path':'fixture.json','contentDigest':DIGEST,'sizeBytes':0,'producerNodeId':None,'provenanceDigest':DIGEST}
    run_case('open-adapter/native-reference-valid',lambda:doc.validate('ArtifactRef',full),True)
    run_case('open-adapter/native-is-not-compact',lambda:Draft202012Validator(compact_schema,format_checker=FormatChecker()).validate(full),False)
    # Raw is not arbitrary JSON: the original resolver applies the metaschema
    # and local-reference closure to JSON_SCHEMA_BUNDLE.
    run_case('raw-schema/valid',lambda:hydrate('JSON_SCHEMA_BUNDLE','unused',{'$schema':'https://json-schema.org/draft/2020-12/schema','type':'string'}),True)
    run_case('raw-schema/invalid-type',lambda:hydrate('JSON_SCHEMA_BUNDLE','unused',{'type':'NOT_A_TYPE'}),False)
    run_case('raw-schema/missing-ref',lambda:hydrate('JSON_SCHEMA_BUNDLE','unused',{'$ref':'#/$defs/missing'}),False)
    result={'scope':__doc__,'checks':checks,'checked':len(checks),'failed':sum(c['status']=='FAIL' for c in checks),'fixtures':fixtures,
        'openCounterexamples':['R11 compact reference accepts schemaDigest=null and has no schema address/path; neither reference shape can be passed unchanged to the other validator. This is NOT a fixed adapter.']}
    suffix='before' if args.entry else 'after'
    (ROOT/f'audit/generated/phase2-content-tests-{suffix}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'checked':result['checked'],'failed':result['failed'],'failures':[c for c in checks if c['status']=='FAIL']}))
    return int(bool(result['failed']))

if __name__=='__main__':raise SystemExit(main())
