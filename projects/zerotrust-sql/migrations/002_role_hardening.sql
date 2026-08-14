BEGIN;

-- The query executor may only assume this role for read-only analytics.
REVOKE INSERT ON query_audit_logs FROM nl_query_ro;
ALTER ROLE nl_query_ro SET default_transaction_read_only = on;
ALTER ROLE nl_query_ro SET statement_timeout = '5s';
ALTER ROLE nl_query_ro SET lock_timeout = '1s';
ALTER ROLE nl_query_ro SET idle_in_transaction_session_timeout = '5s';

-- Create a separate no-login capability role for a future audit repository.
-- Grant it to the server login independently from nl_query_ro.
DO $$
BEGIN
  CREATE ROLE nl_audit_writer NOLOGIN;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM nl_audit_writer;
GRANT USAGE ON SCHEMA public TO nl_audit_writer;
GRANT INSERT ON query_audit_logs TO nl_audit_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nl_audit_writer;

COMMIT;
