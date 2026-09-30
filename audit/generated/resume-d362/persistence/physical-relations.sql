-- SSOT-DECL-219.1: ordered cleanup step identity is independent from resource identity.
CREATE TABLE cleanup_step (
  cleanup_operation_id uuid NOT NULL REFERENCES cleanup_operation(id) ON DELETE CASCADE,
  step_sequence bigint NOT NULL CHECK (step_sequence >= 1),
  cleanup_resource_id uuid NOT NULL REFERENCES cleanup_resource(id) ON DELETE RESTRICT,
  step_kind text NOT NULL,
  state text NOT NULL,
  attempt_number bigint NOT NULL DEFAULT 0 CHECK (attempt_number >= 0),
  PRIMARY KEY (cleanup_operation_id, step_sequence)
);
CREATE INDEX ix_cleanup_step_resource ON cleanup_step(cleanup_resource_id, cleanup_operation_id, step_sequence);
-- Deliberately no UNIQUE(cleanup_resource_id): multiple ordered steps may share one resource.

-- SSOT-DECL-221.6: value derivation cardinality is fixed by immutable approved slot contract.
CREATE TABLE argument_slot_contract (
  operation_intent_id uuid NOT NULL,
  intent_revision_number bigint NOT NULL,
  destination_argument_path text NOT NULL,
  cardinality text NOT NULL CHECK (cardinality IN ('ONE','MANY')),
  slot_contract_digest bytea NOT NULL CHECK (octet_length(slot_contract_digest)=32),
  PRIMARY KEY (operation_intent_id,intent_revision_number,destination_argument_path),
  FOREIGN KEY (operation_intent_id,intent_revision_number) REFERENCES operation_intent(id,revision_number) ON DELETE RESTRICT
);
ALTER TABLE value_derivation ADD COLUMN intent_revision_number bigint NOT NULL;
ALTER TABLE value_derivation ADD COLUMN slot_contract_digest bytea NOT NULL CHECK (octet_length(slot_contract_digest)=32);
ALTER TABLE value_derivation ADD CONSTRAINT fk_value_derivation_slot_contract
  FOREIGN KEY (operation_intent_id,intent_revision_number,destination_argument_path)
  REFERENCES argument_slot_contract(operation_intent_id,intent_revision_number,destination_argument_path) ON DELETE RESTRICT;
CREATE UNIQUE INDEX uq_value_derivation_one_slot
  ON value_derivation(operation_intent_id,intent_revision_number,destination_argument_path)
  WHERE cardinality = 'ONE';
-- For MANY, row identity/digest remains unique while multiple rows for the same slot are allowed.
