BEGIN;

CREATE TABLE IF NOT EXISTS llmshield_rate_limits (
    bucket_key TEXT NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    request_count INTEGER NOT NULL CHECK (request_count > 0),
    expires_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (bucket_key, window_start)
);
CREATE INDEX IF NOT EXISTS llmshield_rate_limits_expires_at_idx
    ON llmshield_rate_limits (expires_at);

DO $$
BEGIN
    CREATE ROLE llmshield_log_writer NOLOGIN;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE ROLE llmshield_rate_limiter NOLOGIN;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

REVOKE ALL ON request_logs FROM PUBLIC, llmshield_rate_limiter;
REVOKE ALL ON llmshield_rate_limits FROM PUBLIC, llmshield_log_writer;
GRANT USAGE ON SCHEMA public TO llmshield_log_writer, llmshield_rate_limiter;
GRANT SELECT, INSERT ON request_logs TO llmshield_log_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON llmshield_rate_limits TO llmshield_rate_limiter;

-- Grant both NOLOGIN roles to the server login used by DATABASE_URL. The API
-- switches roles per transaction, so inference cannot silently gain table-owner
-- privileges. Expired limiter buckets can be removed by a scheduled owner job.

COMMIT;
