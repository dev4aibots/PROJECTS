CREATE TABLE IF NOT EXISTS request_logs (
    id UUID PRIMARY KEY,
    prompt_sha256 TEXT NOT NULL CHECK (length(prompt_sha256) = 64),
    security_status TEXT NOT NULL CHECK (security_status IN ('safe', 'warned', 'blocked', 'error')),
    blocked_by JSONB NOT NULL DEFAULT '[]'::jsonb,
    provider TEXT,
    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
    latency_ms INTEGER NOT NULL CHECK (latency_ms >= 0),
    token_usage INTEGER CHECK (token_usage IS NULL OR token_usage >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS request_logs_created_at_idx ON request_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS request_logs_security_status_idx ON request_logs (security_status);

ALTER TABLE request_logs ENABLE ROW LEVEL SECURITY;
-- The backend uses a server-only database role. Do not expose this table through a public client key.
