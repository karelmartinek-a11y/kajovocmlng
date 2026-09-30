"""Dependency-ordered SQL for an isolated fresh PUBLIC-schema combined fixture."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def foundations():
 # These are deliberately auth *fixture* columns used by source-owned guards.
 # Full owner/session/API DDL/credential-verifier acceptance is a separate obligation.
 auth='''CREATE TABLE owner_identity(id uuid PRIMARY KEY,singleton_key smallint NOT NULL DEFAULT 1 UNIQUE CHECK(singleton_key=1),session_epoch bigint NOT NULL);
CREATE TABLE owner_session(id uuid PRIMARY KEY,owner_identity_id uuid NOT NULL REFERENCES owner_identity(id),lookup_digest bytea NOT NULL,session_hash text NOT NULL,created_at timestamptz,last_seen_at timestamptz,expires_at timestamptz NOT NULL,revoked_at timestamptz,session_epoch bigint NOT NULL);
CREATE TABLE owner_api_credential(singleton_key smallint PRIMARY KEY DEFAULT 1 CHECK(singleton_key=1),credential_version bigint NOT NULL,fingerprint text NOT NULL);
CREATE TABLE platform_incarnation(singleton_key smallint PRIMARY KEY DEFAULT 1 CHECK(singleton_key=1),platform_incarnation_id uuid NOT NULL);
CREATE TABLE application_deployment_head(singleton_key smallint PRIMARY KEY DEFAULT 1 CHECK(singleton_key=1),platform_incarnation_id uuid NOT NULL,application_deployment_epoch bigint NOT NULL);
'''
 root=HERE.joinpath('generation-root-proposed.sql').read_text();events=ROOT.joinpath('audit/generated/resume-d362/events/generation-event-storage-proposed.sql').read_text();command,rest=events.split('CREATE TABLE domain_idempotency_record (',1)
 return auth+command+root.split('-- Immutable initial request')[0]+ROOT.joinpath('audit/generated/resume-5334/sql/generation-create-persistence-proposed.sql').read_text()+root[root.index('-- Immutable initial request'):]+ 'CREATE TABLE domain_idempotency_record ('+rest+HERE.joinpath('trusted-generation-context-proposed.sql').read_text()+HERE.joinpath('generation-context-role-bindings.sql').read_text()+HERE.joinpath('generation-root-context-bindings.sql').read_text()+ROOT.joinpath('audit/generated/resume-d362/events/generation-command-links-proposed.sql').read_text()
if __name__=='__main__':print(foundations())
