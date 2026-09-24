"""Generate provenance, preservation and anti-omission evidence without rewriting Phase 1."""
import copy
import hashlib
import json
import subprocess
from ssot_sources import ROOT, SSOT, resources, resource_index
from phase2_handoff_closure import verify_matrix

def main():
    entry=json.loads((ROOT/'audit/generated/phase2-entry.json').read_text(encoding='utf8'))
    preservation=[]
    for name,sha in entry['files'].items():
        if name=='00_SSOT/KajovoCMLNG_SSOT.md':continue
        actual=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        preservation.append({'path':name,'unchanged':actual==sha,'entrySha256':sha,'currentSha256':actual})
    matrix=json.loads((ROOT/'audit/phase2-handoff-matrix.json').read_text(encoding='utf8'))
    anti=[]
    for name,key in [('omit-edge','edges'),('omit-source-candidate','discoveredCandidates'),('omit-source','sources')]:
        bad=copy.deepcopy(matrix);bad[key].pop()
        try:verify_matrix(bad,matrix)
        except ValueError:anti.append({'case':name,'rejected':True})
        else:anti.append({'case':name,'rejected':False})
    phase1=json.loads((ROOT/'audit/phase1-operation-schema-matrix.json').read_text(encoding='utf8'))
    current=resource_index()
    head=resource_index(resources(subprocess.check_output(['git','show','HEAD:00_SSOT/KajovoCMLNG_SSOT.md']).decode()))
    visual='r16/contracts/r15-visual-operation-closure.json'
    old={o['operationId']:o for o in json.loads(head[visual]['raw'])['operations']}
    browser=[]
    for op in json.loads(current[visual]['raw'])['operations']:
        browser.append({'operationId':op['operationId'],'source':visual,
            'before':{k:v for k,v in old[op['operationId']].items() if k.endswith(('Definition','SchemaAuthority','SchemaRef'))},
            'after':{k:v for k,v in op.items() if k.endswith(('Definition','SchemaAuthority','SchemaRef'))}})
    missing=[{'operationId':o['operationId'],'source':o['source'],'boundary':b} for o in phase1['operations'] for b in o['boundaries'] if b['resolution']!='RESOLVED']
    event_ids={e['producer'] for e in matrix['edges'] if e['id'].startswith('event-applicability:')}
    phase1event_ids={o['operationId'] for o in phase1['operations'] if o['eventApplicability']=='UNSPECIFIED_NOT_ASSUMED_ABSENT'}
    oldtext=(ROOT/'.cache/phase2-entry/SSOT.md').read_text(encoding='utf8');oldrs=resource_index(resources(oldtext))
    changed=[{'path':p,'beforeSha256':oldrs[p]['sha256'],'afterSha256':r['sha256'],
        'occurrences':[{'family':x['family'],'line':x['line']} for x in resources() if x['path']==p]}
        for p,r in current.items() if r['raw']!=oldrs[p]['raw']]
    mapping=current['contracts/generation/artifact-schema-map.json']
    manifest=json.loads(current['contracts/execution/embedded-manifest.json']['raw'])
    manifest_entry=next(x for x in manifest['files'] if x['path']==mapping['path'])
    map_manifest_ok=(manifest_entry['rawDigest']=='sha256:'+mapping['sha256'] and manifest_entry['sizeBytes']==len(mapping['raw']))
    result={'head':entry['head'],'currentHead':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),
        'currentStatus':subprocess.check_output(['git','status','--short']).decode(),
        'ssotSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'preservation':preservation,
        'allPriorNonSsotDirtyFilesUnchanged':all(p['unchanged'] for p in preservation),
        'matrixAntiOmissionTests':anti,'phase1BrowserReferenceEvidence':browser,
        'phase1UnresolvedReferences':missing,'browserOperationIntersectionWithUnresolved':sorted({x['operationId'] for x in missing}&set(old)),
        'eventCoverage':{'phase1':len(phase1event_ids),'phase2':len(event_ids),'identicalOperationSet':event_ids==phase1event_ids},
        'phase2ChangedResources':changed,'changedMapManifestEntryValid':map_manifest_ok}
    (ROOT/'audit/generated/phase2-provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'preserved':result['allPriorNonSsotDirtyFilesUnchanged'],'events':result['eventCoverage'],
        'antiOmission':anti,'changedResources':[x['path'] for x in changed]}))
    return int(not result['allPriorNonSsotDirtyFilesUnchanged'] or event_ids!=phase1event_ids or not all(c['rejected'] for c in anti) or not map_manifest_ok)

if __name__=='__main__':raise SystemExit(main())
