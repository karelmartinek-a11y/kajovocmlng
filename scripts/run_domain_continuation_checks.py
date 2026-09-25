"""Record focused checks with exact per-command input hashes and current matrix."""
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from ssot_sources import ROOT,SSOT,resource_index,resources

def main():
    raw=SSOT.read_bytes();source=hashlib.sha256(raw).hexdigest()
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-897da64/generation-domain');out.mkdir(parents=True,exist_ok=True)
    commands=[(['scripts/verify_generation_domain_payloads.py','--baseline'],1),
              (['scripts/verify_generation_domain_payloads.py'],0),
              (['scripts/close_generation_domain_payloads.py','--check'],0),
              (['scripts/verify_portable_manifests.py'],0),
              (['scripts/verify_native_manifest_continuation.py'],0),
              (['scripts/verify_saga_handoffs.py'],0),
              (['scripts/verify_generation_operation_masks.py'],0),
              (['scripts/verify_route_guard_counters.py'],0),
              (['scripts/project_experience.py','--check'],0),
              (['scripts/investigate_missing_operation_masks.py'],0)]
    if '--focused' in sys.argv:
        commands=[(args,code) for args,code in commands if args[0] not in
                  (['scripts/verify_route_guard_counters.py'] if '--provider' in sys.argv else
                   ['scripts/verify_route_guard_counters.py','scripts/verify_generation_operation_masks.py'])]
    if '--provider' in sys.argv:
        commands=[(['scripts/verify_provider_outcome_mask.py','--baseline'],1),
                  (['scripts/verify_provider_outcome_mask.py'],0),
                  (['scripts/close_provider_outcome_mask.py','--check'],0)]+commands
    if '--read' in sys.argv:
        commands=[(['scripts/verify_read_boundary_completion.py','--baseline'],1),
                  (['scripts/verify_read_boundary_completion.py'],0),
                  (['scripts/close_mcp_list_operation_masks.py','--check'],0),
                  (['scripts/close_read_handoff_provenance.py','--check'],0),
                  (['scripts/report_read_boundary_evidence.py'],0)]+commands
    rs=resource_index(resources(raw.decode()))
    report={'baselineCommit':'897da64','sourceSha256':source,'scope':__doc__,
            'runnerSha256':hashlib.sha256((ROOT/'scripts/run_domain_continuation_checks.py').read_bytes()).hexdigest(),
            'requirementsSha256':hashlib.sha256((ROOT/'requirements-audit.txt').read_bytes()).hexdigest(),
            'pythonVersion':sys.version,
            'validationPackages':{name:importlib.metadata.version(name) for name in
                ['jsonschema','referencing','rfc3339-validator','rfc3986-validator','uri-template']},
            'resourceVersions':{p:r['sha256'] for p,r in rs.items()},
            'baselineCounts':{'unresolvedOperationReferences':250,'operationsWithUnresolvedReferences':125,'genericRoutes':505,'genericBoundaryDefinitions':1512},
            'commands':[],'allCommandsFinished':False,'packageStatus':'BLOCKED'}
    if '--read' in sys.argv:report['baselineCommit']='664d617'
    if '--events' in sys.argv:
        commands=[(['scripts/verify_generation_event_boundaries.py','--baseline'],1),
                  (['scripts/verify_generation_event_boundaries.py'],0),
                  (['scripts/close_generation_event_boundaries.py','--check'],0)]+commands
        report['baselineCommit']='2d2eea4'
        report['baselineCounts'].update(unresolvedOperationReferences=242,operationsWithUnresolvedReferences=121)
    for args,expected in commands:
        print('RUN '+' '.join(args),flush=True);started=time.monotonic()
        script_hash=hashlib.sha256((ROOT/args[0]).read_bytes()).hexdigest()
        input_commit=('664d617' if args[0]=='scripts/verify_read_boundary_completion.py' else '897da64') if '--baseline' in args else None
        if args[0]=='scripts/verify_generation_event_boundaries.py' and '--baseline' in args:input_commit='2d2eea4'
        input_hash=(hashlib.sha256(subprocess.check_output(['git','show',input_commit+':00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT)).hexdigest()
                    if input_commit else source)
        result=subprocess.run([sys.executable,*args],cwd=ROOT,text=True,capture_output=True,encoding='utf8',errors='replace',
            env={**os.environ,'PYTHONUTF8':'1','KCML_AUDIT_OUTPUT':out.relative_to(ROOT).as_posix()})
        report['commands'].append({'command':'python '+' '.join(args),'exitCode':result.returncode,'expectedExitCode':expected,
            'sourceSha256':input_hash,'currentPackageSha256':source,'inputCommit':input_commit,
            'scriptSha256':script_hash,
            'seconds':round(time.monotonic()-started,3),'stdout':result.stdout,'stderr':result.stderr})
        (out/'commands.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
        print('EXIT '+str(result.returncode),flush=True)
        if SSOT.read_bytes()!=raw:raise ValueError('Input changed during group tests')
        if hashlib.sha256((ROOT/args[0]).read_bytes()).hexdigest()!=script_hash:raise ValueError('Test script changed during execution')
    report['allCommandsFinished']=True
    matrix=json.loads((out/'current-operation-schema-matrix.json').read_text(encoding='utf8'))
    report['currentSummary']=matrix['summary'];report['delta']={k:matrix['summary'][k]-v for k,v in report['baselineCounts'].items()}
    report['referenceIntegrityChecks']={k:matrix['summary'][k]==0 for k in
        ['nestedReferenceFailures','conflictingSchemaIdentities','conflictingOperationReferences','unparsedResources']}
    (out/'commands.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({'sourceSha256':source,'delta':report['delta']}))
    return int(any(c['exitCode']!=c['expectedExitCode'] for c in report['commands']) or not all(report['referenceIntegrityChecks'].values()))

if __name__=='__main__':raise SystemExit(main())
