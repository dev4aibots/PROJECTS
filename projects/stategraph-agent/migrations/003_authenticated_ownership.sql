BEGIN;

-- Task memory is opt-in. Identity is always derived from verified JWT claims.
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS remember boolean NOT NULL DEFAULT false;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS expires_at timestamptz;
UPDATE memories SET expires_at=created_at + interval '90 days' WHERE expires_at IS NULL;
ALTER TABLE memories ALTER COLUMN expires_at SET DEFAULT (now() + interval '90 days');
ALTER TABLE memories ALTER COLUMN expires_at SET NOT NULL;

-- Authenticated users are provisioned on first request; this table remains a
-- portfolio projection and does not replace auth.users as identity authority.
ALTER TABLE demo_users ADD COLUMN IF NOT EXISTS auth_subject uuid;
UPDATE demo_users SET auth_subject=id WHERE auth_subject IS NULL;
ALTER TABLE demo_users ALTER COLUMN auth_subject SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS demo_users_auth_subject_uidx
  ON demo_users(auth_subject);

-- These indexes support owner-filtered joins used by task, event and approval APIs.
CREATE INDEX IF NOT EXISTS tasks_user_id_id_idx ON tasks(user_id,id);
CREATE INDEX IF NOT EXISTS task_runs_task_id_id_idx ON task_runs(task_id,id);
CREATE INDEX IF NOT EXISTS approvals_task_run_id_id_idx ON approvals(task_run_id,id);
CREATE INDEX IF NOT EXISTS memories_user_id_id_idx ON memories(user_id,id);

COMMIT;
