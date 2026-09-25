"""12.14 negative tests on actual native and active projection ProviderOutcome."""
import argparse
import copy
import hashlib
import json
import os
import subprocess
from jsonschema import Draft202012Validator,FormatChecker
from referencing import Registry,Resource
from close_provider_outcome_mask import GEN,PROJECTION
from ssot_sources import ROOT,SSOT,resources,resource_index
from verify_phase2_handoffs import witness

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',action='store_true');args=p.parse_args()
    raw=subprocess.check_output(['git','show','897da64:00_SSOT/KajovoCMLNG_SSOT.md']) if args.baseline else SSOT.read_bytes()
    rs=resource_index(resources(raw.decode()));checks=[]
    for path in [GEN,PROJECTION]:
        bundle=json.loads(rs[path]['raw']);defs=copy.deepcopy(bundle['$defs'])
        for k,v in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-25T00:00:00.000Z','RelPath':'fixture.json','JsonPointer':'','NonemptyJsonPointer':'/fixture'}.items():defs[k]={'const':v}
        shape=copy.deepcopy(defs['ProviderOutcome']);shape.pop('allOf',None)
        value=witness(shape,defs)
        registry=Registry().with_resource(bundle['$id'],Resource.from_contents(bundle))
        validator=Draft202012Validator({'$ref':bundle['$id']+'#/$defs/ProviderOutcome'},registry=registry,format_checker=FormatChecker())
        def check(name,sample,expected):
            actual=validator.is_valid(sample);checks.append({'resource':path,'case':name,'expected':expected,'actual':actual,'passed':actual==expected})
        accepted=witness(defs['ArtifactRef'],defs)
        for status in ['COMPLETED','REFUSED','INCOMPLETE','FAILED']:
            sample={**value,'localStatus':status,'acceptedOutput':accepted}
            check(status+'/accepted-output',sample,status=='COMPLETED')
            check(status+'/no-accepted-output',{**sample,'acceptedOutput':None},True)
        check('UNKNOWN-is-not-confirmed-provider-receipt',{**value,'localStatus':'UNKNOWN'},False)
        missing=copy.deepcopy(value);del missing['rawResponse'];check('missing-raw-response',missing,False)
        missing=copy.deepcopy(value);del missing['commit'];check('model-proposal-cannot-be-server-receipt',missing,False)
    report={'sourceSha256':hashlib.sha256(raw).hexdigest(),'baselineCommit':'897da64' if args.baseline else None,
            'scope':__doc__,'resourceVersions':{p:rs[p]['sha256'] for p in [GEN,PROJECTION]},
            'checked':len(checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,
            'notClosed':'Unknown-submit recovery, actual artifact hydration and generation.model.execute command/response remain separate.'}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-897da64/provider-outcome');out.mkdir(parents=True,exist_ok=True)
    (out/('provider-baseline.json' if args.baseline else 'provider-current.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:report[k] for k in ['sourceSha256','checked','failed']}))
    for c in checks:
        if not c['passed']:print(json.dumps(c))
    return int(bool(report['failed']))

if __name__=='__main__':raise SystemExit(main())
