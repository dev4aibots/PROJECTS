BEGIN;

-- Queryable task projections previously omitted terminal output and update time.
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS result text;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS error text;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- Required by ON CONFLICT idempotent event writes.
CREATE UNIQUE INDEX IF NOT EXISTS agent_events_id_unique ON agent_events(id);
CREATE INDEX IF NOT EXISTS task_runs_task_id_idx ON task_runs(task_id);
CREATE INDEX IF NOT EXISTS tasks_user_created_idx ON tasks(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS approvals_run_requested_idx ON approvals(task_run_id, requested_at DESC);
CREATE INDEX IF NOT EXISTS memories_user_created_idx ON memories(user_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS memories_source_task_unique
  ON memories(source_task_id) WHERE source_task_id IS NOT NULL;

-- Seed only fictional demo identities. Production authentication must map a
-- verified identity claim to an application user before these APIs are public.
INSERT INTO demo_users(id, name) VALUES
  ('00000000-0000-0000-0000-000000000001', 'Avery'),
  ('00000000-0000-0000-0000-000000000002', 'Blake')
ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name;

COMMIT;
