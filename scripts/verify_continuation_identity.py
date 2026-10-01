"""Validate current continuation identities without requiring a self commit hash."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SSOT = '00_SSOT/KajovoCMLNG_SSOT.md'


def verify(checkpoint, checklist, register, source_digest, committed_source):
    diagnostics = []
    def exact(path, actual, expected):
        if actual != expected:
            diagnostics.append({'code': 'CONTINUATION_IDENTITY_MISMATCH',
                                'pointer': path, 'actual': actual, 'expected': expected})
    for field in ('sourceDocumentSha256', 'currentSourceDocumentSha256'):
        exact('checkpoint#/' + field, checkpoint.get(field), source_digest)
    continuation = checkpoint.get('continuationInput', {})
    exact('checkpoint#/continuationInput/sourceSha256', continuation.get('sourceSha256'), source_digest)
    exact('checklist#/sourceSha256', checklist.get('sourceSha256'), source_digest)
    exact('register#/sourceDocumentSha256', register.get('sourceDocumentSha256'), source_digest)
    # Input and last committed blocks are historical identities, not the resulting commit.
    for head_field, digest_field in (
        ('verifiedInputHead', 'verifiedInputSSOTSha256'),
        ('lastVerifiedCommittedBlock', 'lastVerifiedCommittedBlockSSOTSha256'),
    ):
        head = continuation.get(head_field)
        try:
            digest = committed_source(head)
        except (ValueError, subprocess.CalledProcessError):
            diagnostics.append({'code': 'CONTINUATION_COMMIT_UNRESOLVED', 'pointer': head_field, 'actual': head})
            continue
        exact('checkpoint#/continuationInput/' + digest_field, continuation.get(digest_field), digest)
    return {'format': 'SSOT_CONTINUATION_IDENTITY_V1', 'sourceSha256': source_digest,
            'status': 'BLOCKED' if diagnostics else 'PASS', 'diagnostics': diagnostics,
            'scope': 'Continuation source and historical commit identities only; no semantic readiness certification.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    def committed_source(head):
        if not isinstance(head, str) or len(head) != 40 or any(c not in '0123456789abcdef' for c in head):
            raise ValueError('Full commit identity required')
        return hashlib.sha256(subprocess.check_output(['git', 'show', head + ':' + SSOT], cwd=ROOT)).hexdigest()
    try:
        report = verify(*(json.loads((ROOT / path).read_text()) for path in (
            'audit/SSOT_REPAIR_CHECKPOINT.json', 'audit/SSOT_CREATE_CLOSURE_CHECKLIST.json',
            'audit/SSOT_COMPLETION_REGISTER.json')),
            hashlib.sha256((ROOT / SSOT).read_bytes()).hexdigest(), committed_source)
    except (OSError, ValueError) as exc:
        report = {'status': 'BLOCKED', 'diagnostics': [{'code': 'CONTINUATION_INPUT_UNREADABLE', 'detail': str(exc)}]}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
