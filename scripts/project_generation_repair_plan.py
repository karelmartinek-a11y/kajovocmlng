"""Project current P00-P12 and additive browser/collaboration gates; no phase execution."""
import hashlib,json
from ssot_sources import ROOT,SSOT,resource_index

def main():
    rs=resource_index();base='r13/contracts/development-plan.json'
    plan=json.loads(rs[base]['raw']);phases={p['id']:p for p in plan['phases']}
    sources={base:rs[base]['sha256']}
    for path in sorted(rs):
        if path.endswith('/contracts/development-plan-delta.json'):
            delta=json.loads(rs[path]['raw']);sources[path]=rs[path]['sha256']
            for d in delta['phaseChanges']:
                p=phases[d['phase']]
                if 'replaceName' in d:p['name']=d['replaceName']
                for key in ['deliverables','exitGates']:p[key].extend(d.get('add'+key[0].upper()+key[1:],[]))
    outputs={
        'P00':['frozen-contract-pack/manifest.json','toolchain/locks/','audit/design-universe-results.json'],
        'P01':['packages/contract-compiler/','generated/schema-registry.json','tests/contracts/'],
        'P02':['database/migrations/','database/helpers/','evidence/postgresql-18.6/'],
        'P03':['packages/domain/','generated/kcip/','evidence/domain-lifecycle/'],
        'P04':['packages/openai-runtime/','generated/openai-schemas/','evidence/openai-projection/'],
        'P05':['packages/mcp-runtime/','generated/mcp-contracts/','evidence/mcp-wire/'],
        'P06':['packages/agent-runtime/','generated/agent-handoffs/','evidence/agent-resume/'],
        'P07':['packages/browser-runtime/','generated/kbpp/','evidence/browser-runtime/'],
        'P08':['packages/generation-factory/','evidence/generation-conformance/'],
        'P09':['apps/owner-ui/','packages/owner-api/','generated/ui-action-parity.json','evidence/ui-api-chat/'],
        'P10':['packages/monitoring-repair/','evidence/chaos/','evidence/audit-lineage/'],
        'P11':['deployment/systemd/','deployment/release-manifest.json','evidence/ci-deploy-preproduction/'],
        'P12':['evidence/production-shaped-acceptance/','evidence/activation-recovery/']}
    for phase,p in phases.items():p['plannedOutputLocations']=outputs[phase]
    result={'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'sourceResources':sources,
        'status':'PLANNED_NOT_EXECUTED','scope':'Derived continuation procedure. Output paths are planning conventions, not new normative product requirements.',
        'admission':'P00 requires current complete SSOT_CONTRACT_READY and separate freeze authorization. This repair task authorizes no freeze, application generation, release, deployment or production calls.',
        'progression':'No successor RUNNING before predecessor current PASSED with identical SSOT/Contract Pack/toolchain lineage (71.7).',
        'remainingProjectionReview':'R16 orchestration and R17 native toolchain/PGDG/browser requirements must be incorporated in implementation evidence; this projection does not certify their semantic closure.',
        'phases':list(phases.values())}
    out=ROOT/'audit/generated/repair-2026-09-30/generation-plan.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    lines=['# Postup generování P00–P12','',result['scope'],'',result['admission'],'',result['progression'],'',f"SSOT SHA-256: `{result['sourceDocumentSha256']}`.",'', 'Normativní deliverables a exit gates jsou převzaté z R13 a všech nalezených development-plan-delta resources. Plánované cesty jsou konkrétní umístění budoucích výstupů; aplikace nebyla generována.','']
    for p in result['phases']:
        lines += [f"## {p['id']} — {p['name']}",'', 'Závisí na: '+(', '.join(p['dependsOn']) or 'aktuální kompletní návrhové gate a samostatné oprávnění freeze')+'.','', 'Plánované výstupy: '+', '.join('`'+v+'`' for v in p['plannedOutputLocations'])+'.','', 'Deliverables:','']+['- '+v for v in p['deliverables']]+['','Exit criteria:','']+['- '+v for v in p['exitGates']]+['']
    lines += ['R17 / 73.2–73.7: P00 musí doložit exact native/PGDG package versions a integrity; P02 skutečný PostgreSQL 18.6 a extension smoke; P07 browser launch a pinned runtime tuple. Syntetické testy nenahrazují tyto runtime důkazy.','',result['remainingProjectionReview']]
    (ROOT/'audit/SSOT_GENERATION_P00_P12.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'phases':len(phases),'sourceResources':len(sources),'status':result['status']}))
if __name__=='__main__':main()
