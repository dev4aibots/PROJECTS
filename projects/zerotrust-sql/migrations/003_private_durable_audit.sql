BEGIN;

-- Store privacy-safe metadata by default. Raw question/SQL columns remain
-- nullable and are populated only when AUDIT_STORE_RAW_TEXT=true.
ALTER TABLE query_audit_logs ALTER COLUMN question DROP NOT NULL;
ALTER TABLE query_audit_logs ADD COLUMN IF NOT EXISTS prompt_hash text;
ALTER TABLE query_audit_logs ADD COLUMN IF NOT EXISTS generated_sql_hash text;
ALTER TABLE query_audit_logs ADD COLUMN IF NOT EXISTS final_sql_hash text;
ALTER TABLE query_audit_logs ADD COLUMN IF NOT EXISTS principal_id text;
ALTER TABLE query_audit_logs ADD COLUMN IF NOT EXISTS request_id text;

CREATE INDEX IF NOT EXISTS query_audit_logs_created_at_idx
  ON query_audit_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS query_audit_logs_principal_created_idx
  ON query_audit_logs (principal_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS query_audit_logs_request_id_idx
  ON query_audit_logs (request_id)
  WHERE request_id IS NOT NULL;

-- The execution role can never read or write audit records. The separate
-- capability role may insert and read metadata for authenticated audit APIs.
REVOKE ALL ON query_audit_logs FROM nl_query_ro;
REVOKE ALL ON query_audit_logs FROM nl_audit_writer;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM nl_audit_writer;
GRANT INSERT, SELECT ON query_audit_logs TO nl_audit_writer;
GRANT USAGE, SELECT ON SEQUENCE query_audit_logs_id_seq TO nl_audit_writer;

COMMIT;
