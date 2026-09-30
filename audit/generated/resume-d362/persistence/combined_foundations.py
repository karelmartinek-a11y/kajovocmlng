"""Dependency-ordered SQL for an isolated fresh PUBLIC-schema combined fixture."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def foundations():
 # These are deliberately auth *fixture* columns used by source-owned guards.
 # Full owner/session/API DDL/credential-verifier acceptance is a separate obligation.
 auth=HERE.joinpath('authentication-roots-proposed.sql').read_text()
 root=HERE.joinpath('generation-root-proposed.sql').read_text();events=ROOT.joinpath('audit/generated/resume-d362/events/generation-event-storage-proposed.sql').read_text();command,rest=events.split('CREATE TABLE domain_idempotency_record (',1)
 return auth+command+root.split('-- Immutable initial request')[0]+ROOT.joinpath('audit/generated/resume-5334/sql/generation-create-persistence-proposed.sql').read_text()+root[root.index('-- Immutable initial request'):]+ 'CREATE TABLE domain_idempotency_record ('+rest+HERE.joinpath('generation-contract-pin-proposed.sql').read_text()+HERE.joinpath('trusted-generation-context-proposed.sql').read_text()+HERE.joinpath('generation-context-role-bindings.sql').read_text()+HERE.joinpath('generation-root-context-bindings.sql').read_text()+ROOT.joinpath('audit/generated/resume-d362/events/generation-command-links-proposed.sql').read_text()+HERE.joinpath('generation-snapshot-pin-links.sql').read_text()
if __name__=='__main__':print(foundations())
