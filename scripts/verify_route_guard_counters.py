"""Check every effective R9 route guard against the numeric domain of 56.3.

This checks three named platform guards, not the remaining generic domain bodies.
"""
import argparse
import copy
import hashlib
import json
import os
import subprocess

from jsonschema import Draft202012Validator
from close_route_guard_counters import FIELDS, PATH
from ssot_sources import ROOT, SSOT, resource_index, resources


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',action='store_true');args=parser.parse_args()
    baseline=subprocess.check_output(['git','show','997e835:00_SSOT/KajovoCMLNG_SSOT.md'])
    raw=baseline if args.baseline else SSOT.read_bytes()
    rs=resource_index(resources(raw.decode('utf8')))
    routes=json.loads(rs[PATH]['raw'])['records']
    old=resource_index(resources(baseline.decode('utf8')))
    old_routes={r['routeId']:r for r in json.loads(old[PATH]['raw'])['records']}
    if not args.baseline:
        # 12.21 now requires non-null approval guards and a precise command.
        # Compare non-guard content against this explicit authored delta, not
        # against arbitrary current values. Other routes remain unchanged.
        from close_generation_domain_payloads import changed_payload
        from close_generation_event_boundaries import specialize,GEN
        from generation_http_contract import PATH as HTTP,specialize as specialize_http
        bundle=json.loads(old[GEN]['raw'])
        expected=specialize(changed_payload(old),bundle)
        # Historical resources predate HTTP; compose its explicit delta only
        # when checking the authored current HTTP contract.
        if HTTP in rs:expected=specialize_http(expected,bundle)
        from create_operation_contracts import PATH as CREATE_DESIGN, specialize as specialize_creates
        if CREATE_DESIGN in rs:expected=specialize_creates(expected)
        from secret_read_contracts import specialize as specialize_reads
        if 'contracts/secrets/metadata-read.schema.json'in rs:expected=specialize_reads(expected,rs)
        if 'contracts/owner-session-family.json' in rs:
            # Compose the reviewed family transform, not current arbitrary rows.
            # The explicit Counter prerequisite was independently authored before
            # this family and is native type authority, not a historical guess.
            from owner_session_family_contracts import contracts as owner_contracts
            family_input=copy.deepcopy(expected)
            counter=json.loads(rs['contracts/generation/generation-contracts.schema.json']['raw'])['$defs']['Counter']
            selected=next(r for r in family_input['records'] if r['operationId']=='owner.session.revoke')
            selected['requestSchema']['properties']['guards']['properties']['expectedStateVersion']=copy.deepcopy(counter)
            family_input.pop('canonicalDigest',None) # In-memory authored composition, not a canonical input claim.
            bound={**old,PATH:{**old[PATH],'raw':json.dumps(family_input).encode()}}
            from close_owner_session_family import updates as family_updates
            expected=json.loads(family_updates(bound)[PATH])
        if 'contracts/audit/core-read.schema.json' in rs:
            from close_audit_read_family import prepare as audit_updates
            # This is an explicit in-memory transformation of the historical
            # witness. Recompute its authored metadata before composing Audit.
            from phase1_repair_contracts import canonical_digest
            expected['canonicalDigest']=canonical_digest({**expected,'canonicalDigest':None})
            bound={**old,PATH:{**old[PATH],'raw':json.dumps(expected).encode()}}
            expected=json.loads(audit_updates(bound)[PATH])
        old_routes={r['routeId']:r for r in expected['records']}
    checks=[]
    values=[('0',True),('9223372036854775807',True),('9223372036854775808',False),
            ('18446744073709551616',False),('01',False),('-1',False),('',False),
            ('binding-1',False),(' 1',False),('1\n',False),(1,False),(False,False)]
    failures=0
    for route in routes:
        original=old_routes[route['routeId']]
        normalized=copy.deepcopy(route)
        if route['operationId']in ('secret.metadata.read','secret.value.read') and not args.baseline:
            guards=route['requestSchema']['properties']['guards']
            good=guards=={'type':'object','additionalProperties':False,'properties':{},'required':[]} and route==original
            cases=[{'value':{},'passed':good}]+[{'value':{f:'0'},'passed':not Draft202012Validator(guards).is_valid({f:'0'})}for f in FIELDS]
            failures+=sum(not c['passed']for c in cases)
            checks.append({'routeId':route['routeId'],'operationId':route['operationId'],'applicability':'NOT_APPLICABLE_CLOSED_OWNER_READ','authority':'SSOT8.16','cases':cases})
            continue
        for field in FIELDS:
            schema=route['requestSchema']['properties']['guards']['properties'][field]
            prior=original['requestSchema']['properties']['guards']['properties'][field]
            not_applicable=prior=={'type':'null'}
            nullable=not_applicable or isinstance(prior.get('type'),list) and 'null' in prior['type']
            v=Draft202012Validator(schema)
            cases=[]
            for value,expected in values+[(None,nullable)]:
                if not_applicable:expected=value is None
                actual=v.is_valid(value)
                cases.append({'value':value,'expectedValid':expected,'actualValid':actual,'passed':expected==actual})
            failures+=sum(not c['passed'] for c in cases)
            checks.append({'routeId':route['routeId'],'operationId':route['operationId'],
                           'schemaPointer':f'/requestSchema/properties/guards/properties/{field}',
                           'nullablePreserved':nullable,'applicability':'NOT_APPLICABLE' if not_applicable else 'COUNTER','cases':cases})
            normalized['requestSchema']['properties']['guards']['properties'][field]=prior
        if normalized!=original:
            raise ValueError('Unexpected change beyond guard domains: '+route['routeId'])
    if set(old_routes)!={r['routeId'] for r in routes}:raise ValueError('Route coverage drift')
    report={'sourceSha256':hashlib.sha256(raw).hexdigest(),'baseline':args.baseline,'scope':__doc__,
            'routes':len(routes),'guardDefinitions':len(checks),'checks':checks,
            'checked':sum(len(c['cases']) for c in checks),'failed':failures,
            'preserved':'Non-guard content and nullability match 997e835 plus explicit domain, event and (when authored) HTTP specialization for routes 0234/0232/0237; explicit source-reviewed OWNER_SESSION_RECORD_ADMIN transform; unrelated routes are unchanged.'}
    out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/continuation-7006785/design');out.mkdir(parents=True,exist_ok=True)
    (out/('baseline.json' if args.baseline else 'current.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in ('sourceSha256','baseline','routes','guardDefinitions','checked','failed')}))
    return int(bool(failures))


if __name__=='__main__':raise SystemExit(main())
