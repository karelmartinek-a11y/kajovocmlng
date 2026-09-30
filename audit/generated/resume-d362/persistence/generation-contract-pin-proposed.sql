-- Deployment-owned immutable pin from actual consumed authoritative resource bytes.
-- Fresh create resolves by locked deployment epoch, never caller-selected schema.
CREATE TABLE generation_create_contract_pin (
 id uuid PRIMARY KEY,
 application_deployment_epoch bigint NOT NULL UNIQUE CHECK(application_deployment_epoch>=0),
 operation_id text NOT NULL CHECK(operation_id='generation.job.create'),
 operation_contract_revision text NOT NULL CHECK(length(operation_contract_revision)>0),
 operation_record_bytes bytea NOT NULL,
 route_record_bytes bytea NOT NULL,
 domain_schema_bytes bytea NOT NULL,
 contract_revision_bytes bytea NOT NULL,
 operation_resource_digest bytea NOT NULL CHECK(octet_length(operation_resource_digest)=32),
 route_resource_digest bytea NOT NULL CHECK(octet_length(route_resource_digest)=32),
 schema_resource_digest bytea NOT NULL CHECK(octet_length(schema_resource_digest)=32),
 contract_digest bytea NOT NULL CHECK(contract_digest=sha256(contract_revision_bytes)),
 UNIQUE(application_deployment_epoch,contract_digest),
 domain_schema_digest bytea NOT NULL CHECK(domain_schema_digest=sha256(domain_schema_bytes)),
 CHECK(convert_from(operation_record_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(route_record_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(domain_schema_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(contract_revision_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS),
 CHECK(convert_from(operation_record_bytes,'UTF8')::jsonb->>'operationId' IS NOT DISTINCT FROM operation_id),
 CHECK(convert_from(operation_record_bytes,'UTF8')::jsonb->>'operationRevision' IS NOT DISTINCT FROM operation_contract_revision),
 CHECK(convert_from(route_record_bytes,'UTF8')::jsonb->>'operationId' IS NOT DISTINCT FROM operation_id),
 CHECK(convert_from(route_record_bytes,'UTF8')::jsonb#>'{requestSchema,properties,body}' IS NOT DISTINCT FROM convert_from(domain_schema_bytes,'UTF8')::jsonb),
 CHECK(convert_from(route_record_bytes,'UTF8')::jsonb->>'routeId' IS NOT NULL),
 CHECK(convert_from(contract_revision_bytes,'UTF8')::jsonb->'operationRecord' IS NOT DISTINCT FROM convert_from(operation_record_bytes,'UTF8')::jsonb),
 CHECK(convert_from(contract_revision_bytes,'UTF8')::jsonb->'routeRecord' IS NOT DISTINCT FROM convert_from(route_record_bytes,'UTF8')::jsonb),
 CHECK(convert_from(contract_revision_bytes,'UTF8')::jsonb->'domainSchema' IS NOT DISTINCT FROM convert_from(domain_schema_bytes,'UTF8')::jsonb)
);
CREATE TRIGGER generation_create_contract_pin_immutable BEFORE UPDATE
 ON generation_create_contract_pin FOR EACH ROW
 EXECUTE FUNCTION kcml_reject_generation_create_snapshot_update_v1();
-- INSERT belongs only to deployment migrator, never auth/domain/model clients.
