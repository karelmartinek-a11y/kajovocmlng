"""Reproduce narrowly evidenced artifact mappings, not a runtime implementation.

Authority: specialist-output-map, R11 call-sites/instructions/input slots and
orchestration edges; R12 model-artifact-handoff requires native payload validation.
The R11 reference adapter remains unresolved, independently of these mappings.
"""
import argparse
import hashlib
import json
import re
from ssot_sources import ROOT, SSOT, resources, resource_index

MAP='contracts/generation/artifact-schema-map.json'
GEN='contracts/generation/generation-contracts.schema.json'
ADDITIONS={
    'REQUIREMENT_PROPOSAL':('RequirementProposal','REQUIREMENTS_ANALYST'),
    'SOURCE_ANALYSIS':('SourceAnalysis','SOURCE_RESEARCHER'),
    'CAPABILITY_DECISION':('CapabilityDecision','CAPABILITY_RESOLVER'),
    'CONTRACT_ARCHITECTURE':('ContractArchitecture','CONTRACT_ARCHITECT'),
    'GENERATION_PLAN':('GenerationPlan','IMPLEMENTATION_PLANNER'),
    'INTEGRATION_PLAN':('IntegrationPlan','INTEGRATION_ARCHITECT'),
}

def repair(text):
    items=list(resources(text)); rs=resource_index(items)
    load=lambda p:json.loads(rs[p]['raw'])
    mapping=load(MAP); generation=load(GEN)
    outputs=load('contracts/generation/specialist-output-map.json')
    calls=load('r11/contracts/specialist-call-sites.json')['records']
    for kind,(definition,role) in ADDITIONS.items():
        assert outputs[role]==definition
        call=next(x for x in calls if x['role']==role)
        assert call['proposalDefinition']==definition
        envelope=generation['$defs'][call['outputEnvelopeDefinition']]
        assert {'$ref':'#/$defs/'+definition} in envelope['properties']['proposal']['anyOf']
        assert definition in generation['$defs']
        if kind in mapping and mapping[kind]!=definition:raise ValueError('Conflicting mapping: '+kind)
        mapping[kind]=definition
    encode=lambda d:(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
    updates={MAP:encode(mapping)}
    p='contracts/execution/embedded-manifest.json'; manifest=load(p)
    matches=[x for x in manifest['files'] if x['path']==MAP]
    assert len(matches)==1
    matches[0].update(sizeBytes=len(updates[MAP]),rawDigest='sha256:'+hashlib.sha256(updates[MAP]).hexdigest())
    updates[p]=encode(manifest)
    updates={p:raw for p,raw in updates.items() if raw!=rs[p]['raw']}
    # Both identical normative copies must remain identical. Historical manifests
    # and preserved snapshot receipts are not rewritten to claim a new history.
    for r in reversed(items):
        if r['path'] not in updates:continue
        raw=updates[r['path']]; m=r['match']; block=m.group(0)
        head=block.split('\n',1)[0]
        if 'bytes="' in head:head=re.sub(r'bytes="\d+"',f'bytes="{len(raw)}"',head)
        if 'sha256="' in head:head=re.sub(r'sha256="[0-9a-f]+"',f'sha256="{hashlib.sha256(raw).hexdigest()}"',head)
        assert r['declared'].get('encoding','plain')=='plain'
        block=head+'\n'+r['fence']+r['language']+'\n'+raw.decode()+r['fence']+'\n<!-- '+r['family']+'-END -->'
        text=text[:m.start()]+block+text[m.end():]
    return text,sorted(updates)

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--reproduce',action='store_true');a=p.parse_args()
    text=SSOT.read_text(encoding='utf8')
    if a.reproduce:
        expected,changed=repair((ROOT/'.cache/phase2-entry/SSOT.md').read_text(encoding='utf8'))
        ok=expected==text
        print(json.dumps({'exactReproduction':ok,'resources':changed}));return int(not ok)
    updated,changed=repair(text)
    if not a.check and changed:SSOT.write_text(updated,encoding='utf8',newline='\n')
    print(json.dumps({'pending' if a.check else 'changed':changed}))
    return int(a.check and bool(changed))

if __name__=='__main__':raise SystemExit(main())
