-- seed.sql — synthetic LOCAL fixtures for development and pgTAP tests (CF-02).
-- Deterministic UUIDs so tests can reference them. Never run against a hosted
-- project: these are fake users with no real credentials.
--
-- Cast: alice (owner of WS-A), bob (owner of WS-B), carol (member of A AND B —
-- the cross-tenant FK attacker), dave (former member of A, removed),
-- erin (portal client in A), frank (owner of a SupportDesk workspace — wrong app).

-- Deterministic ids ---------------------------------------------------------
-- users
--   alice 00000000-0000-4000-8000-00000000000a
--   bob   00000000-0000-4000-8000-00000000000b
--   carol 00000000-0000-4000-8000-00000000000c
--   dave  00000000-0000-4000-8000-00000000000d
--   erin  00000000-0000-4000-8000-00000000000e
--   frank 00000000-0000-4000-8000-00000000000f
-- workspaces
--   A (clientflow)  10000000-0000-4000-8000-00000000000a
--   B (clientflow)  10000000-0000-4000-8000-00000000000b
--   S (supportdesk) 10000000-0000-4000-8000-00000000000f
-- clients
--   A1 20000000-0000-4000-8000-0000000000a1
--   B1 20000000-0000-4000-8000-0000000000b1
-- projects
--   A-P1 30000000-0000-4000-8000-0000000000a1
--   B-P1 30000000-0000-4000-8000-0000000000b1

insert into auth.users (id, email, aud, role, raw_app_meta_data, raw_user_meta_data, email_confirmed_at)
values
  ('00000000-0000-4000-8000-00000000000a', 'alice@example.test', 'authenticated', 'authenticated', '{"provider":"email"}', '{}', now()),
  ('00000000-0000-4000-8000-00000000000b', 'bob@example.test',   'authenticated', 'authenticated', '{"provider":"email"}', '{}', now()),
  ('00000000-0000-4000-8000-00000000000c', 'carol@example.test', 'authenticated', 'authenticated', '{"provider":"email"}', '{}', now()),
  ('00000000-0000-4000-8000-00000000000d', 'dave@example.test',  'authenticated', 'authenticated', '{"provider":"email"}', '{}', now()),
  ('00000000-0000-4000-8000-00000000000e', 'erin@example.test',  'authenticated', 'authenticated', '{"provider":"email"}', '{}', now()),
  ('00000000-0000-4000-8000-00000000000f', 'frank@example.test', 'authenticated', 'authenticated', '{"provider":"email"}', '{}', now())
on conflict (id) do nothing;

-- Seed runs as a privileged role, so it writes directly. Application code must
-- go through platform_create_workspace(); the tests exercise that function.
insert into public.platform_profiles (id, display_name) values
  ('00000000-0000-4000-8000-00000000000a', 'Alice Owner'),
  ('00000000-0000-4000-8000-00000000000b', 'Bob Owner'),
  ('00000000-0000-4000-8000-00000000000c', 'Carol Two-Workspaces'),
  ('00000000-0000-4000-8000-00000000000d', 'Dave Removed'),
  ('00000000-0000-4000-8000-00000000000e', 'Erin Client'),
  ('00000000-0000-4000-8000-00000000000f', 'Frank Support')
on conflict (id) do nothing;

insert into public.platform_workspaces (id, app, name, created_by) values
  ('10000000-0000-4000-8000-00000000000a', 'clientflow',  'Studio A', '00000000-0000-4000-8000-00000000000a'),
  ('10000000-0000-4000-8000-00000000000b', 'clientflow',  'Studio B', '00000000-0000-4000-8000-00000000000b'),
  ('10000000-0000-4000-8000-00000000000f', 'supportdesk', 'Frank Support Desk', '00000000-0000-4000-8000-00000000000f')
on conflict (id) do nothing;

insert into public.platform_members (workspace_id, user_id, role) values
  ('10000000-0000-4000-8000-00000000000a', '00000000-0000-4000-8000-00000000000a', 'owner'),
  ('10000000-0000-4000-8000-00000000000a', '00000000-0000-4000-8000-00000000000c', 'member'),
  ('10000000-0000-4000-8000-00000000000a', '00000000-0000-4000-8000-00000000000e', 'client'),
  ('10000000-0000-4000-8000-00000000000b', '00000000-0000-4000-8000-00000000000b', 'owner'),
  ('10000000-0000-4000-8000-00000000000b', '00000000-0000-4000-8000-00000000000c', 'admin'),
  ('10000000-0000-4000-8000-00000000000f', '00000000-0000-4000-8000-00000000000f', 'owner')
on conflict do nothing;
-- dave was a member of A and has been removed: intentionally no row.

-- cf_* rows stamp created_by from auth.uid() by trigger, even for privileged
-- callers, so the seed impersonates the owner of each workspace (transaction-local).
set local request.jwt.claim.sub = '00000000-0000-4000-8000-00000000000a';
insert into public.cf_clients (id, workspace_id, name, contact_name, contact_email) values
  ('20000000-0000-4000-8000-0000000000a1', '10000000-0000-4000-8000-00000000000a', 'Northwind Bakery', 'Nina North', 'nina@northwind.test')
on conflict (id) do nothing;
insert into public.cf_projects (id, workspace_id, client_id, name, description, status, due_date) values
  ('30000000-0000-4000-8000-0000000000a1', '10000000-0000-4000-8000-00000000000a', '20000000-0000-4000-8000-0000000000a1', 'Spring menu launch site', 'Six-page marketing site.', 'active', '2026-09-30')
on conflict (id) do nothing;

set local request.jwt.claim.sub = '00000000-0000-4000-8000-00000000000b';
insert into public.cf_clients (id, workspace_id, name, contact_name, contact_email) values
  ('20000000-0000-4000-8000-0000000000b1', '10000000-0000-4000-8000-00000000000b', 'Bluefin Legal', 'Ben Blue', 'ben@bluefin.test')
on conflict (id) do nothing;
insert into public.cf_projects (id, workspace_id, client_id, name, description, status, due_date) values
  ('30000000-0000-4000-8000-0000000000b1', '10000000-0000-4000-8000-00000000000b', '20000000-0000-4000-8000-0000000000b1', 'Client intake portal', 'Secure intake forms.', 'planned', null)
on conflict (id) do nothing;
reset request.jwt.claim.sub;
