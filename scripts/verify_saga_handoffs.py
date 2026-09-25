"""Exercise the embedded saga validator with real in-memory artifact bytes.

Only filesystem byte loading is replaced. Inventory identity, byte digests,
native schemas, typed evidence and predecessor content validation execute.
This is offline conformance, not proof of PostgreSQL/runtime execution.
"""
import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import types
from pathlib import Path

from ssot_sources import ROOT, SSOT, resource_index, resources
from verify_phase2_handoffs import witness


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    raw = subprocess.check_output(['git','show','997e835:00_SSOT/KajovoCMLNG_SSOT.md']) if args.baseline else SSOT.read_bytes()
    rs = resource_index(resources(raw.decode('utf8')))
    module = types.ModuleType('saga_embedded_test')
    sys.modules[module.__name__] = module
    exec(compile(rs['scripts/ssot/ssot_control.py']['raw'], 'SSOT:ssot_control.py','exec'),module.__dict__)
    with tempfile.TemporaryDirectory(prefix='kcml-saga-') as directory:
        snapshot = Path(directory)/'SSOT.md'
        snapshot.write_bytes(raw)
        doc = module.Document(snapshot)
    defs = copy.deepcopy(doc.schema['$defs'])
    for key,value in {'Counter':'0','PositiveCounter':'1','Timestamp':'2026-09-25T00:00:00.000Z',
                      'RelPath':'fixture.json','JsonPointer':'','NonemptyJsonPointer':'/fixture'}.items():
        defs[key] = {'const':value}
    ledger, blobs, checks = {}, {}, []
    serial = 0
    digest = 'sha256:'+'a'*64

    def artifact(kind, value):
        nonlocal serial
        serial += 1
        aid = f'00000000-0000-4000-8000-{serial:012d}'
        body = json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
        definition = doc.kind_to_schema.get(kind)
        ref = {'artifactId':aid,'kind':kind,'schema':None if definition is None else {
            'schemaId':doc.schema['$id'],'definition':definition,'bundleDigest':doc.schema_digest},
            'mediaType':'application/json','path':f'{serial}.json','contentDigest':module.raw_digest(body),
            'sizeBytes':len(body),'producerNodeId':None,'provenanceDigest':digest}
        ledger[aid] = copy.deepcopy(ref)
        blobs[ref['path']] = body
        return ref

    native = {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:saga-test-observation',
              'type':'object','properties':{'verified':{'const':True}},
              'required':['verified'],'additionalProperties':False}
    native_ref = artifact('JSON_SCHEMA_BUNDLE',native)

    def evidence(kind):
        value = witness(defs['EvidenceRecord'],defs)
        value['kind'] = kind
        value['observationSchema'] = {'schemaId':native['$id'],'dialect':native['$schema'],
            'rootPointer':'','bundle':native_ref,'nativeSchemaDigest':module.semantic_digest(native)}
        value['observations'] = {'verified':True}
        return artifact(kind,value)

    before = evidence('INTEGRATION_INVENTORY')
    after = evidence('INTEGRATION_INVENTORY')
    observation = evidence('INTEGRATION_INVENTORY')
    revision = artifact('CANDIDATE_REVISION_RECEIPT',witness(defs['CandidateRevisionReceipt'],defs))
    predecessor = witness(defs['IntegrationStepReceipt']['oneOf'][0],defs)
    predecessor.update(stepId='S02',result=revision,afterInventory=after,readBackEvidence=[observation])
    predecessor_ref = artifact('INTEGRATION_STEP_RECEIPT',predecessor)
    request = witness(defs['IntegrationStepInput'],defs)
    request.update(stepId='S03',beforeInventory=before,predecessorReceipts=[predecessor_ref])
    module.read_regular_at = lambda root,path,limit: blobs[path]

    def resolve(ref):
        return module.ArtifactResolver(doc,ROOT,ledger).get(ref)

    def run(name, fn, expected=True):
        try:
            value=fn(); actual=True; error=None
        except Exception as exc:
            value=None; actual=False; error=str(exc)
        checks.append({'case':name,'expectedValid':expected,'actualValid':actual,
                       'passed':expected==actual,'error':error,'returnValue':value})

    # Without a callable validator, negative cases do not count as rejected inputs.
    validator = getattr(module,'validate_integration_step_input',None)
    run('input-validator-exists',lambda: module.require(validator is not None,'MISSING_VALIDATOR','','No integration input validation'))
    if validator is not None:
        run('S02-content-to-S03-input',lambda:validator(doc,request,resolve))
        for name,mutate in [
            ('missing-predecessor',lambda x:x.update(predecessorReceipts=[])),
            ('duplicate-predecessor',lambda x:x.update(predecessorReceipts=x['predecessorReceipts']*2)),
            ('another-job',lambda x:x.update(jobId='00000000-0000-4000-8000-999999999999')),
            ('another-saga',lambda x:x.update(sagaId='00000000-0000-4000-8000-999999999999')),
            ('forward-predecessor',lambda x:x.update(stepId='S01')),
        ]:
            bad=copy.deepcopy(request);mutate(bad)
            run(name,lambda bad=bad:validator(doc,bad,resolve),False)
        bad=copy.deepcopy(predecessor)
        bad['result']=evidence('CANDIDATE_RELEASE_RECEIPT')
        wrong=copy.deepcopy(request);wrong['predecessorReceipts']=[artifact('INTEGRATION_STEP_RECEIPT',bad)]
        run('S02-wrong-result-kind',lambda:validator(doc,wrong,resolve),False)
        unconfirmed=witness(defs['IntegrationStepReceipt']['oneOf'][2],defs)
        unconfirmed.update(stepId='S02',effectOutcome='UNKNOWN',readBackEvidence=[observation],afterInventory=None)
        unconfirmed['problem']['retryDirective']='MANUAL_REVIEW'
        wrong=copy.deepcopy(request);wrong['predecessorReceipts']=[artifact('INTEGRATION_STEP_RECEIPT',unconfirmed)]
        run('unknown-predecessor-cannot-admit-S03',lambda:validator(doc,wrong,resolve),False)
        wrong=copy.deepcopy(request);wrong['predecessorReceipts'][0]['contentDigest']=digest
        run('untrusted-peer-reference',lambda:validator(doc,wrong,resolve),False)
        saved=blobs[predecessor_ref['path']];blobs[predecessor_ref['path']]=b'{}'
        run('corrupt-predecessor-bytes',lambda:validator(doc,request,resolve),False)
        blobs[predecessor_ref['path']]=saved

    pending=witness(defs['IntegrationStepReceipt']['oneOf'][2],defs)
    pending.update(stepId='S01',effectOutcome='UNKNOWN',readBackEvidence=[observation],afterInventory=None)
    pending['problem']['retryDirective']='MANUAL_REVIEW'
    run('unknown-recovery-remains-S01',lambda:module.verify_saga(doc,[pending],pending['jobId'],pending['sagaId'],resolve))
    saved=blobs[observation['path']];blobs[observation['path']]=b'{}'
    run('unknown-recovery-corrupt-readback',lambda:module.verify_saga(doc,[pending],pending['jobId'],pending['sagaId'],resolve),False)
    blobs[observation['path']]=saved
    report={'sourceSha256':hashlib.sha256(raw).hexdigest(),'baseline':args.baseline,'scope':__doc__,
            'scriptResourceSha256':rs['scripts/ssot/ssot_control.py']['sha256'],
            'checks':checks,'failed':sum(not c['passed'] for c in checks),'checked':len(checks),
            'handoff':{'producer':'S02/component.revision.publish','consumer':'S03/generation.candidate.publish',
                'sourceMask':'IntegrationStepReceipt','targetSlot':'IntegrationStepInput/predecessorReceipts',
                'transfer':'Trusted ArtifactRef -> exact bytes -> IntegrationStepReceipt',
                'verified':'Identity, native payload, predecessor membership, output kind, known outcome, readback bytes',
                'remaining':'Current DB guards, semantic postcondition evaluation, compensation record and actual external execution'},
            'fixtures':{'input':request,'predecessor':predecessor,'manualReview':pending}}
    out=ROOT/'audit/generated/continuation-997e835';out.mkdir(parents=True,exist_ok=True)
    (out/('saga-baseline.json' if args.baseline else 'saga-current.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in ('sourceSha256','baseline','checked','failed')}))
    for check in checks:
        if not check['passed']:print(json.dumps(check))
    return int(bool(report['failed']))


if __name__=='__main__':
    raise SystemExit(main())
