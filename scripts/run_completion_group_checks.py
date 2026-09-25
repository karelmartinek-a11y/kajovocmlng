"""Record actual child exit codes and exact inputs for the current repaired groups.

This suite is deliberately scoped; it is not the complete package readiness gate.
Historical generated reports from the entry tree are not overwritten.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

from ssot_sources import ROOT, SSOT, resource_index, resources


def main():
    before = SSOT.read_bytes()
    source_hash = hashlib.sha256(before).hexdigest()
    baseline = subprocess.check_output(['git','show','e025079:00_SSOT/KajovoCMLNG_SSOT.md'])
    old_rs = resource_index(resources(baseline.decode('utf8')))
    rs = resource_index(resources(before.decode('utf8')))
    changed = [{'path':p, 'beforeSha256':old_rs[p]['sha256'], 'afterSha256':r['sha256']}
               for p,r in rs.items() if p not in old_rs or old_rs[p]['sha256'] != r['sha256']]
    expected_changed = {'manifest.json','contracts/operation-contracts.json','contracts/payload-contracts.json'}
    if {r['path'] for r in changed} != expected_changed or set(old_rs) != set(rs):
        raise ValueError('Unexpected changed canonical resources')
    integrity = [p for p,r in rs.items() if r['declared'].get('sha256') and
                 r['sha256'] != r['declared']['sha256']]
    manifest = json.loads(rs['manifest.json']['raw'])
    for p,meta in manifest['resources'].items():
        if meta['sha256'] != 'sha256:'+rs[p]['sha256'] or meta['sizeBytes'] != len(rs[p]['raw']):
            integrity.append('manifest:'+p)
    if integrity:
        raise ValueError('Integrity errors:'+str(integrity))
    commands = [
        (['scripts/verify_control_counter_masks.py','--baseline'], 1),
        (['scripts/close_generation_operation_masks.py','--check'], 0),
        (['scripts/verify_transitive_mask_detection.py'], 0),
        (['scripts/verify_control_counter_masks.py'], 0),
        (['scripts/verify_component_protocol_examples.py'], 0),
        (['scripts/verify_generation_operation_masks.py'], 0),
        (['scripts/project_experience.py','--check'], 0),
        (['scripts/investigate_missing_operation_masks.py'], 0),
    ]
    results = []
    out = ROOT/'audit/generated/completion-group-checks.json'
    def save():
        report = {'scope':__doc__, 'sourceSha256':source_hash,
                  'baselineSha256':hashlib.sha256(baseline).hexdigest(),
                  'changedResources':changed,'resourceDigestFailures':integrity,
                  'commands':results, 'allCommandsFinished':len(results)==len(commands),
                  'packageStatus':'BLOCKED',
                  'remaining':'126 operation pairs still require investigation; generic route masks '
                              'and runtime handoff closure remain open.'}
        out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for args, expected in commands:
        started = time.monotonic()
        print('RUN '+' '.join(args),flush=True)
        result = subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,
                                text=True,encoding='utf8',errors='replace',
                                env={**os.environ,'PYTHONUTF8':'1'})
        record = {'command':'python '+' '.join(args),'exitCode':result.returncode,
                  'expectedExitCode':expected,'stdout':result.stdout,'stderr':result.stderr,
                  'durationSeconds':round(time.monotonic()-started,3),
                  'currentSsotSha256':source_hash,
                  'testInputSha256':hashlib.sha256(baseline).hexdigest() if '--baseline' in args else source_hash,
                  'scriptSha256':hashlib.sha256((ROOT/args[0]).read_bytes()).hexdigest()}
        results.append(record)
        save()
        print('EXIT '+str(result.returncode)+' '+args[0],flush=True)
        if SSOT.read_bytes()!=before:
            raise ValueError('SSOT changed during tests')
    return int(any(r['exitCode']!=r['expectedExitCode'] for r in results))


if __name__=='__main__':
    raise SystemExit(main())
