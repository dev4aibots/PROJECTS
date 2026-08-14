BEGIN;

-- The API never runs projection queries as the database owner. This NOLOGIN
-- role is assumed per transaction after the bearer token has been verified.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'stategraph_api') THEN
    CREATE ROLE stategraph_api NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;
END $$;

DO $$
BEGIN
  EXECUTE format('GRANT stategraph_api TO %I', current_user);
END $$;

GRANT USAGE ON SCHEMA public TO stategraph_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON
  demo_users, tasks, task_runs, agent_events, approvals, memories
TO stategraph_api;
REVOKE ALL ON graph_checkpoints FROM stategraph_api;

ALTER TABLE demo_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

ALTER TABLE demo_users FORCE ROW LEVEL SECURITY;
ALTER TABLE tasks FORCE ROW LEVEL SECURITY;
ALTER TABLE task_runs FORCE ROW LEVEL SECURITY;
ALTER TABLE agent_events FORCE ROW LEVEL SECURITY;
ALTER TABLE approvals FORCE ROW LEVEL SECURITY;
ALTER TABLE memories FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS demo_users_owner ON demo_users;
CREATE POLICY demo_users_owner ON demo_users
  USING (id = nullif(current_setting('app.current_user_id', true), '')::uuid)
  WITH CHECK (id = nullif(current_setting('app.current_user_id', true), '')::uuid);

DROP POLICY IF EXISTS tasks_owner ON tasks;
CREATE POLICY tasks_owner ON tasks
  USING (user_id = nullif(current_setting('app.current_user_id', true), '')::uuid)
  WITH CHECK (user_id = nullif(current_setting('app.current_user_id', true), '')::uuid);

DROP POLICY IF EXISTS task_runs_owner ON task_runs;
CREATE POLICY task_runs_owner ON task_runs
  USING (EXISTS (
    SELECT 1 FROM tasks t
    WHERE t.id = task_runs.task_id
      AND t.user_id = nullif(current_setting('app.current_user_id', true), '')::uuid
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM tasks t
    WHERE t.id = task_runs.task_id
      AND t.user_id = nullif(current_setting('app.current_user_id', true), '')::uuid
  ));

DROP POLICY IF EXISTS agent_events_owner ON agent_events;
CREATE POLICY agent_events_owner ON agent_events
  USING (EXISTS (
    SELECT 1 FROM task_runs r JOIN tasks t ON t.id = r.task_id
    WHERE r.id = agent_events.task_run_id
      AND t.user_id = nullif(current_setting('app.current_user_id', true), '')::uuid
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM task_runs r JOIN tasks t ON t.id = r.task_id
    WHERE r.id = agent_events.task_run_id
      AND t.user_id = nullif(current_setting('app.current_user_id', true), '')::uuid
  ));

DROP POLICY IF EXISTS approvals_owner ON approvals;
CREATE POLICY approvals_owner ON approvals
  USING (EXISTS (
    SELECT 1 FROM task_runs r JOIN tasks t ON t.id = r.task_id
    WHERE r.id = approvals.task_run_id
      AND t.user_id = nullif(current_setting('app.current_user_id', true), '')::uuid
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM task_runs r JOIN tasks t ON t.id = r.task_id
    WHERE r.id = approvals.task_run_id
      AND t.user_id = nullif(current_setting('app.current_user_id', true), '')::uuid
  ));

DROP POLICY IF EXISTS memories_owner ON memories;
CREATE POLICY memories_owner ON memories
  USING (user_id = nullif(current_setting('app.current_user_id', true), '')::uuid)
  WITH CHECK (user_id = nullif(current_setting('app.current_user_id', true), '')::uuid);

COMMIT;
