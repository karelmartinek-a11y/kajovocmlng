import hashlib,json,os
from acceptance_gates import assess,DESIGN,PRODUCTION,inventory_scope
from ssot_sources import ROOT,SSOT

def main():
    source=hashlib.sha256(SSOT.read_bytes()).hexdigest();checks=[]
    d={'d':{'gate':DESIGN,'passed':True,'sourceSha256':source,'evidenceKind':'DESIGN_MODEL'}}
    p={'p':{'gate':PRODUCTION,'passed':True,'sourceSha256':source,'evidenceKind':'EXECUTED_IMPLEMENTATION'}}
    def check(name,actual,expected=True):checks.append({'case':name,'passed':actual==expected})
    a=assess(['d'],d,['p'],{},source)
    check('missing-live-system-does-not-block-design',a[DESIGN]['status']=='PASS')
    check('missing-live-system-cannot-pass-production',a[PRODUCTION]['status']=='BLOCKED')
    a=assess(['d'],{},['p'],p,source)
    check('production-success-does-not-fill-design-gap',a[DESIGN]['status']=='BLOCKED')
    check('current-real-production-evidence',a[PRODUCTION]['status']=='PASS')
    for label,bad in [('stale',{**d['d'],'sourceSha256':'old'}),('failed',{**d['d'],'passed':False}),
                      ('wronggate',{**d['d'],'gate':PRODUCTION})]:
        check(label,assess(['d'],{'d':bad},['p'],{},source)[DESIGN]['status']=='BLOCKED')
    check('omitted-design-record',assess(['d','missing'],d,['p'],{},source)[DESIGN]['status']=='BLOCKED')
    check('empty-universe',assess([],{},['p'],{},source)[DESIGN]['status']=='BLOCKED')
    check('duplicate-universe',assess(['d','d'],d,['p'],{},source)[DESIGN]['status']=='BLOCKED')
    check('unexpected-record',assess(['d'],{**d,'extra':d['d']},['p'],{},source)[DESIGN]['status']=='BLOCKED')
    check('model-not-runtime',assess(['d'],d,['p'],{'p':{**p['p'],'evidenceKind':'DESIGN_MODEL'}},source)[PRODUCTION]['status']=='BLOCKED')
    check('inventory-is-neither-readiness-gate',all(x['status']=='NOT_EVALUATED' for x in inventory_scope().values()))
    report={'sourceSha256':source,'evidenceGate':DESIGN,'checked':len(checks),
            'failed':sum(not x['passed'] for x in checks),'checks':checks}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-7006785/design');out.mkdir(parents=True,exist_ok=True)
    (out/'gate-separation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(report));return int(bool(report['failed']))

if __name__=='__main__':raise SystemExit(main())
