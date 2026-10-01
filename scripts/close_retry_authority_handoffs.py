"""Author reviewed authority extensions without certifying complete operations."""
import hashlib
import json
import re
import argparse
from ssot_sources import ROOT, SSOT, resources, resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded

BASE = ROOT / 'audit/generated/resume-8cc'
SQL = {
    'database/generation-trusted-policy-publisher.sql': 'archive/generation-trusted-policy-publisher.sql',
    'database/canonical-key-invocation-receipts.sql': 'key/key-invocation-receipts.sql',
    'database/secret-owner-api-value-read.sql': 'broker/secret-owner-api-value-read.sql',
}
HELPERS = {
    'generation_own_kind_policy_v1.py': 'archive/generation_own_kind_policy_v1.py',
    'generation_policy_package.py': 'archive/generation_policy_package.py',
    'systemd_key_authority.py': 'key/systemd_key_authority.py',
    'secret_owner_value_read.py': 'broker/secret_owner_value_read.py',
}
GENERATION_NORM = '''### 12.56 Scoped trusted policy and key authority producers

`database/generation-trusted-policy-publisher.sql` materializes installer-owned immutable policy packages and same-transaction acceptance tickets under §§12.51–12.55,49.4,51.6–7,51.10,51.20. The deployment installer capability is distinct from the domain writer and archive builder; unsafe pre-existing role attributes reject installation. Only exact installed schema, policy, authority and implementation bytes can be published. Package masks, dependency closure and command/context/protected-snapshot identities must agree. An installed package requires its accepted binding at commit; a request-only archive is insufficient. Initial acceptance pins current credential/session authority before higher write locks; subsequent publication uses that same-transaction ticket without reacquiring lower locks. Tickets do not authorize a later transaction or replace retained outcome replay. The complete authentication/context/idempotency/FK lock plan remains a separate mandatory obligation; this module's bounded phase guard is not a global lock-order attestation.

`scripts/generation_policy_package.py` and `scripts/generation_own_kind_policy_v1.py` dispatch the exact archived UPDATE/RETRY/REPAIR discussion policy through statically loaded, digest-matched code and dependencies. They hydrate actual source bytes and frozen schema closure, preserve existing request rules, and grant no execution or activation authority. Unavailable policy, unknown implementation, missing required authority, malformed package or substituted identity produces a specific structured diagnostic. Archived Python is never evaluated; current policy/schema is not a fallback. CREATE/FOLLOW_UP policies, full ledger lifecycle, authenticated native child integration and trusted deployment installer provenance remain separately mandatory.

`database/canonical-key-invocation-receipts.sql` and `scripts/systemd_key_authority.py` bind immutable encrypted-source metadata to the existing key generation, exact service and observed invocation. The observer uses the exact root-owned system-bus socket, pins systemd's unique root/PID1 owner and exact active unit InvocationID/MainPID/start timestamp. The root installer hashes the root-owned0600 encrypted source without exposing its bytes; file metadata alone does not prove encryption. Actual read-only systemd materialization and fingerprint confirmation remain mandatory. Narrow safe installer/publisher capabilities cannot be granted to public/model/generated callers. Stored receipt rows and patched manager replies are not systemd attestations. Missing real manager/source remains ENVIRONMENT BLOCKED, transitively blocking genuine key/invocation/nonce and protected generation/Secret producer proofs. Retained key material uses the same encrypted systemd mechanism, never an environment-key fallback; actual rotation, desired/effective confirmation and historical materialization fixtures remain required before generation.

'''
SECRET_NORM = '''### 8.15 Scoped OWNER value read

`database/secret-owner-api-value-read.sql` and `scripts/secret_owner_value_read.py` materialize the required non-reserved OWNER API value read under §§7.2,8.5,25.6,51.6–7. Current credential SHARE and ordered OWNER/Secret roots remain held through exact immutable version selection, authenticated opening and immutable read evidence. Fresh constant-time token verification precedes disclosure of diagnostics or plaintext. The reserved KCML_OWNER_API_KEY reveal keeps its own OWNER-session contract (§51.20); a create context never grants read/reveal authority. CURRENT and explicit IMMUTABLE_VERSION selectors use the exact existing OWNER value-read transport in §8.16; unknown or duplicate query and implicit format guessing reject.

Hydration verifies exact same-root version, protected nonce/object/context/command authority, actual key fingerprint and actual declared crypto profile digest/bytes, exact typed AAD, ciphertext and original/canonical value digests before returning original bytes to the explicit OWNER read consumer. Imported profiles and legacy RAW versions retain their own representation; no format guessing or implicit conversion occurs. Source/invocation proof, complete usage/audit pipeline, session reveal, legacy restore authority, runtime broker and full browser/UI obligations remain separately required. Reference key injection and synthetic source records do not certify the actual systemd mechanism or the whole Secret operation.

'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--block', choices=('key', 'read', 'archive', 'all'), required=True)
    args = parser.parse_args()
    text = SSOT.read_text(); items = list(resources(text)); rs = resource_index(items)
    selected = lambda path: args.block == 'all' or path.split('/', 1)[0] == {'key': 'key', 'read': 'broker', 'archive': 'archive'}[args.block]
    updates = {name: (BASE / path).read_bytes() for name, path in SQL.items() if selected(path)}
    for name, path in HELPERS.items():
        if selected(path): (ROOT / 'scripts' / name).write_bytes((BASE / path).read_bytes())
    for name in ('contracts/generation/create-chain-handoffs.json', 'contracts/generation/producer-archive-handoffs.json'):
        doc = json.loads(rs[name]['raw'])
        order = doc['sqlInstallationOrder' if 'sqlInstallationOrder' in doc else 'generationInstallationOrder']
        for module in ('database/generation-trusted-policy-publisher.sql', 'database/canonical-key-invocation-receipts.sql'):
            if module in updates and module not in order: order.append(module)
        doc['scopedAuthorityNorm'] = 'SSOT12.56'
        updates[name] = encoded(doc, rs[name]['raw'])
    doc = {'contractId': 'SECRET_OWNER_VALUE_READ_HANDOFF_V1',
           'authority': ['SSOT7.2', 'SSOT8.5', 'SSOT8.15', 'SSOT25.6', 'SSOT51.6', 'SSOT51.20'],
           'installationDependencies': ['database/generation-create-foundations.sql', 'database/canonical-crypto-registry.sql', 'database/secret-profile-roots.sql', 'database/secret-owner-binding.sql', 'database/secret-command-chain.sql', 'database/secret-record-status.sql'],
           'sql': 'database/secret-owner-api-value-read.sql', 'consumer': 'scripts/secret_owner_value_read.py',
           'scope': 'Non-reserved OWNER API immutable value read; no create, runtime broker or OWNER-session credential reveal authority',
           'systemdFixtureStatus': 'BLOCKED_ENVIRONMENT', 'wholeOperationClosed': False,
           'IMPLEMENTATION_PRODUCTION_ACCEPTANCE': 'NOT_EVALUATED'}
    if 'database/secret-owner-api-value-read.sql' in updates:
        updates['contracts/secrets/owner-value-read-handoff.json'] = (json.dumps(doc, indent=2) + '\n').encode()
    manifest = json.loads(rs['manifest.json']['raw'])
    for name, raw in updates.items():
        manifest['resources'][name] = {'kind': 'SQL' if name.endswith('.sql') else 'JSON', 'sizeBytes': len(raw), 'sha256': 'sha256:' + hashlib.sha256(raw).hexdigest()}
    manifest['resourceCount'] = len(manifest['resources'])
    updates['manifest.json'] = encoded(manifest, rs['manifest.json']['raw'])
    text = rewrite(text, items, updates)
    for name in SQL:
        text = text.replace('KCML-R9-RESOURCE path="' + name + '" kind="JSON"', 'KCML-R9-RESOURCE path="' + name + '" kind="SQL"')
    paragraphs = GENERATION_NORM.strip().split('\n\n')
    generation_norm = paragraphs[0] + '\n\n'
    if 'database/generation-trusted-policy-publisher.sql' in rs or 'database/generation-trusted-policy-publisher.sql' in updates:
        generation_norm += '\n\n'.join(paragraphs[1:3]) + '\n\n'
    if 'database/canonical-key-invocation-receipts.sql' in rs or 'database/canonical-key-invocation-receipts.sql' in updates:
        generation_norm += paragraphs[3] + '\n\n'
    norms = [('12.56', generation_norm, '13.')]
    if 'database/secret-owner-api-value-read.sql' in rs or 'database/secret-owner-api-value-read.sql' in updates:
        norms.append(('8.15', SECRET_NORM, '9.'))
    for section, norm, next_section in norms:
        match = re.search(r'^### ' + re.escape(section) + r' .*?(?=^### |^## )', text, re.M | re.S)
        if match: text = text[:match.start()] + norm + text[match.end():]
        else:
            position = re.search(r'^## ' + re.escape(next_section), text, re.M)
            if not position: raise ValueError('Missing insertion boundary: ' + next_section)
            text = text[:position.start()] + norm + text[position.start():]
    SSOT.write_text(text, encoding='utf8', newline='\n')
    for name, raw in updates.items():
        if name == 'manifest.json': continue
        target = ROOT / '01_UI_CONTRACT' / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
    print(json.dumps({'resources': list(updates), 'wholeOperationsClosed': 0}))


if __name__ == '__main__': main()
