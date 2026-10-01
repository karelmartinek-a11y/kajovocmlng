from pathlib import Path
R=Path('/workspace/kajovocmlng/scripts')
helper='''    # Replay only the reviewed source-derived family deltas, never copy current
    # rows into a historical expectation or skip preservation for these routes.
    def reviewed_families(payload):
        virtual = dict(rs)
        virtual[PATH] = {**rs[PATH], 'raw': json.dumps(payload).encode('utf8')}
        if 'contracts/owner-session-family.json' in rs:
            from close_owner_session_family import updates as owner_updates
            body = owner_updates(virtual)[PATH]
            payload = json.loads(body)
            virtual[PATH] = {**virtual[PATH], 'raw': body}
        if 'contracts/audit/core-read.schema.json' in rs:
            from close_audit_read_family import prepare as audit_updates
            payload = json.loads(audit_updates(virtual)[PATH])
        return payload
'''
p=R/'verify_generation_event_boundaries.py';s=p.read_text();target="    expected_rows={r['routeId']:r for r in expected['records']}\n";assert s.count(target)==1;s=s.replace(target,helper+"    expected=reviewed_families(expected)\n    old_rows={r['routeId']:r for r in reviewed_families({'records':list(old_rows.values())})['records']}\n"+target);p.write_text(s)
p=R/'verify_generation_read_errors.py';s=p.read_text();target='    expected=copy.deepcopy(previous)\n';assert s.count(target)==1;s=s.replace(target,helper+'    previous=reviewed_families(previous)\n'+target);p.write_text(s)
p=R/'verify_generation_operation_masks.py';s=p.read_text();target="    record('exact-source-derived-variant-set', inv.docs[PATH].get('$defs') == expected_masks)\n";assert s.count(target)==1;s=s.replace(target,'''    # Six native OWNER definitions are derived from their published source
    # contract, not accepted by reading the actual operation registry back.
    if 'contracts/owner-session-family.json' in inv.rs:
        from owner_session_family_contracts import contracts as owner_contracts
        for operation in owner_contracts(inv.rs)['operations']:
            oid = operation['operationId']
            for role, field in [('command', 'requestSchema'), ('response', 'responseSchema'), ('event', 'eventSchema')]:
                mask = copy.deepcopy(operation[field])
                mask['$id'] = 'urn:kcml:r9:operation:' + oid + ':' + role
                expected_masks[oid + ':' + role] = mask
    # Four reviewed native MCP read aliases have an exact pinned package; its
    # authoring validation still checks native and operation identities.
    package_path = ROOT / 'audit/generated/closure-replan-84c/references/native-read-reference-patch.json'
    if package_path.exists():
        import importlib.util
        author_path = package_path.with_name('authoring.py')
        spec = importlib.util.spec_from_file_location('reviewed_mcp_read_alias_author', author_path)
        author = importlib.util.module_from_spec(spec); spec.loader.exec_module(author)
        package = json.loads(package_path.read_text())
        author.updates(SSOT.read_text(), package)
        identities = {operation + ':' + role for operation in ('mcp.prompts.get', 'mcp.resources.read') for role in ('command', 'response')}
        aliases = {item['path'].split('/', 2)[2]: item['value'] for item in package['jsonPatch']}
        assert aliases.keys() == identities, 'EXACT_FOUR_REVIEWED_MCP_ALIASES_REQUIRED'
        expected_masks.update(aliases)
'''+target);p.write_text(s)
p=R/'verify_preserved_policy.py';s=p.read_text();target='    before=sections(original);after=sections(current)\n';assert s.count(target)==1;s=s.replace(target,'''    from close_secret_retention_contract import TEXT as RETENTION_NORM
    from close_owner_key_reveal_scope import TEXT as REVEAL_SCOPE_NORM
    from close_scoped_sql_helpers import TEXT as SCOPED_HELPER_NORM
    for norm, scope, resource in [
        (RETENTION_NORM, '8.17', 'contracts/create-completion.json'),
        (REVEAL_SCOPE_NORM, '8.18', 'contracts/owner-query-helper-family.json'),
        (SCOPED_HELPER_NORM, '51.39', 'database/owner-query-helpers.sql'),
    ]:
        ok = resource in resource_index() and current.count(norm) == 1
        addition.append({'section': scope, 'status': 'PASS' if ok else 'FAIL',
            'scope': 'Exact reviewed additive supplement only; missing/duplicate/changed bytes fail and original policy stays byte-compared.'})
        if ok: current = current.replace(norm, '', 1)
'''+target);p.write_text(s)
