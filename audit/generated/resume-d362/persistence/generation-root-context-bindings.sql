-- Apply after exact root and trusted context resources exist; no external stubs.
ALTER TABLE generation_job ADD CONSTRAINT generation_job_context_owner_channel
 FOREIGN KEY(initiating_execution_context_id,owner_id,initiating_access_channel)
 REFERENCES generation_create_trusted_context(id,owner_id,initiating_access_channel)
 ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
