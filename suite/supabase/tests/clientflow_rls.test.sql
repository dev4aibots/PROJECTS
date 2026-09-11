-- clientflow_rls.test.sql — adversarial authorization tests (CF-02)
-- Runs with pgTAP as the REAL request roles (SET ROLE anon / authenticated)
-- with identity injected exactly like PostgREST does (request.jwt.claim.sub).
-- Nothing here runs as postgres/service_role except the setup that pgTAP
-- itself needs; those roles bypass RLS and would prove nothing.
--
-- Fixtures come from seed.sql (alice/bob/carol/dave/erin/frank, WS-A/WS-B/WS-S).
-- Every test is inside one transaction and rolled back.

begin;
select plan(73);

-- ---------------------------------------------------------------------------
-- helpers
-- ---------------------------------------------------------------------------
create or replace function test_as(user_id uuid) returns void language plpgsql as $$
begin
  perform set_config('request.jwt.claim.sub', coalesce(user_id::text, ''), true);
  perform set_config('request.jwt.claim.role', case when user_id is null then 'anon' else 'authenticated' end, true);
  if user_id is null then set local role anon; else set local role authenticated; end if;
end $$;
-- Execute a DML statement as the CURRENT role and return affected rows.
-- Mirrors how the DAL detects conflicts/invisible rows: zero rows, not an error.
create or replace function test_affected(stmt text) returns bigint language plpgsql as $$
declare n bigint;
begin
  execute stmt;
  get diagnostics n = row_count;
  return n;
end $$;
create or replace function test_reset() returns void language plpgsql as $$
begin
  reset role;
  perform set_config('request.jwt.claim.sub', '', true);
  perform set_config('request.jwt.claim.role', '', true);
end $$;


-- Fixture ids as a function: psql does not interpolate :variables inside the
-- dollar-quoted statements pgTAP executes, so constants live in SQL.
create or replace function fx(key text) returns uuid language sql immutable as $$
  select case key
    when 'alice' then '00000000-0000-4000-8000-00000000000a'
    when 'bob' then '00000000-0000-4000-8000-00000000000b'
    when 'carol' then '00000000-0000-4000-8000-00000000000c'
    when 'dave' then '00000000-0000-4000-8000-00000000000d'
    when 'erin' then '00000000-0000-4000-8000-00000000000e'
    when 'frank' then '00000000-0000-4000-8000-00000000000f'
    when 'wsA' then '10000000-0000-4000-8000-00000000000a'
    when 'wsB' then '10000000-0000-4000-8000-00000000000b'
    when 'wsS' then '10000000-0000-4000-8000-00000000000f'
    when 'clA' then '20000000-0000-4000-8000-0000000000a1'
    when 'clB' then '20000000-0000-4000-8000-0000000000b1'
    when 'prA' then '30000000-0000-4000-8000-0000000000a1'
    when 'prB' then '30000000-0000-4000-8000-0000000000b1'
  end::uuid
$$;
grant execute on function fx(text), test_as(uuid), test_reset(), test_affected(text) to anon, authenticated;

-- ---------------------------------------------------------------------------
-- 1. Schema shape: RLS is on AND forced for every public table
-- ---------------------------------------------------------------------------
select is(
  (select count(*) from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relkind = 'r' and not (c.relrowsecurity and c.relforcerowsecurity)),
  0::bigint, 'every public table has RLS enabled and forced');
select has_table('public', 'platform_profiles',   'platform_profiles exists');
select has_table('public', 'platform_workspaces', 'platform_workspaces exists');
select has_table('public', 'platform_members',    'platform_members exists');
select has_table('public', 'cf_clients',          'cf_clients exists');
select has_table('public', 'cf_projects',         'cf_projects exists');
select fk_ok('public', 'cf_projects', array['workspace_id','client_id'], 'public', 'cf_clients', array['workspace_id','id'],
  'cf_projects -> cf_clients is a COMPOSITE (workspace_id, client_id) foreign key');
select col_is_unique('public', 'cf_clients', array['workspace_id','id'], 'cf_clients (workspace_id,id) unique so it can be a composite FK target');

-- security-definer helper hardening
select is((select prosecdef from pg_proc where proname = 'platform_has_role'), true, 'platform_has_role is SECURITY DEFINER');
select ok((select proconfig::text like '%search_path=%' from pg_proc where proname = 'platform_has_role'), 'platform_has_role pins search_path');
select ok(not has_function_privilege('anon', 'public.platform_has_role(uuid, public.platform_app, public.platform_role[])', 'execute'), 'anon cannot execute platform_has_role');
select ok(not has_function_privilege('anon', 'public.platform_create_workspace(public.platform_app, text)', 'execute'), 'anon cannot execute platform_create_workspace');
select ok(has_function_privilege('authenticated', 'public.platform_create_workspace(public.platform_app, text)', 'execute'), 'authenticated can execute platform_create_workspace');

-- ---------------------------------------------------------------------------
-- 2. Anonymous visitor: no grants, no rows, no functions
-- ---------------------------------------------------------------------------
select test_as(null);
select throws_like($$ select * from public.cf_projects $$, '%permission denied%', 'anon: SELECT cf_projects denied at grant level');
select throws_like($$ select * from public.cf_clients $$, '%permission denied%', 'anon: SELECT cf_clients denied');
select throws_like($$ select * from public.platform_workspaces $$, '%permission denied%', 'anon: SELECT platform_workspaces denied');
select throws_like($$ select * from public.platform_members $$, '%permission denied%', 'anon: SELECT platform_members denied');
select throws_like($$ select public.platform_create_workspace('clientflow', 'x') $$, '%permission denied%', 'anon: cannot call platform_create_workspace');
select throws_like($$ insert into public.cf_projects (workspace_id, client_id, name) values (fx('wsA'), fx('clA'), 'anon') $$, '%permission denied%', 'anon: INSERT cf_projects denied');
select test_reset();

-- ---------------------------------------------------------------------------
-- 3. Authenticated but without a subject claim (malformed token): treated as nobody
-- ---------------------------------------------------------------------------
set local role authenticated;
select set_config('request.jwt.claim.sub', '', true);
select is((select count(*) from public.cf_projects), 0::bigint, 'authenticated role with no sub sees zero projects');
select is((select count(*) from public.platform_workspaces), 0::bigint, 'authenticated role with no sub sees zero workspaces');
select throws_ok($$ select public.platform_create_workspace('clientflow', 'ghost') $$, '42501', 'authentication required', 'no sub: platform_create_workspace refuses');
select test_reset();

-- ---------------------------------------------------------------------------
-- 4. Alice (owner of A): sees only A
-- ---------------------------------------------------------------------------
select test_as(fx('alice'));
select results_eq($$ select id from public.platform_workspaces order by id $$, $$ values (fx('wsA')) $$, 'alice sees exactly workspace A');
select results_eq($$ select id from public.cf_projects $$, $$ values (fx('prA')) $$, 'alice sees exactly project A');
select results_eq($$ select id from public.cf_clients $$, $$ values (fx('clA')) $$, 'alice sees exactly client A');
select is((select count(*) from public.cf_projects where id = fx('prB')), 0::bigint, 'alice: forged project B id returns nothing (not an error, not a row)');
select is((select count(*) from public.platform_members where workspace_id = fx('wsB')), 0::bigint, 'alice: cannot enumerate workspace B roster');
select is((select count(*) from public.platform_profiles), 1::bigint, 'alice sees only her own profile');
select is(public.platform_has_role(fx('wsA'), 'clientflow', array['owner']::public.platform_role[]), true,  'helper: alice is owner of A');
select is(public.platform_has_role(fx('wsB'), 'clientflow', array['owner','admin','member']::public.platform_role[]), false, 'helper: alice has no role in B');
select is(public.platform_has_role(fx('wsA'), 'supportdesk', array['owner']::public.platform_role[]), false, 'helper: wrong app -> false even for the owner');
select is(public.platform_has_role(null, 'clientflow', array['owner']::public.platform_role[]), false, 'helper: null workspace -> false');
select is(public.platform_has_role(gen_random_uuid(), 'clientflow', array['owner']::public.platform_role[]), false, 'helper: unknown workspace -> false');

-- Alice cannot forge tenant on write
select throws_like($$ insert into public.cf_projects (workspace_id, client_id, name) values (fx('wsB'), fx('clB'), 'planted in B') $$,
  '%row-level security%', 'alice: INSERT stamped with workspace B rejected by WITH CHECK');
select is(test_affected($$ update public.cf_projects set name = 'hijacked', version = version + 1 where id = fx('prB') $$), 0::bigint,
  'alice: UPDATE targeting project B affects 0 rows (row invisible under RLS)');
select throws_like($$ insert into public.cf_projects (workspace_id, client_id, name, created_by) values (fx('wsA'), fx('clA'), 'x', fx('bob')) $$,
  '%permission denied%', 'alice: cannot even name created_by in an INSERT (column grant)');
select lives_ok($$ insert into public.cf_projects (id, workspace_id, client_id, name) values ('30000000-0000-4000-8000-0000000000a2', fx('wsA'), fx('clA'), 'alice new project') $$,
  'alice: legitimate INSERT into A succeeds');
select is((select created_by from public.cf_projects where id = '30000000-0000-4000-8000-0000000000a2'), fx('alice'), 'created_by stamped from auth.uid(), not client input');
select is((select version from public.cf_projects where id = '30000000-0000-4000-8000-0000000000a2'), 1, 'new project starts at version 1');

-- Optimistic concurrency contract
select is(test_affected($$ update public.cf_projects set status = 'review', version = 2 where id = fx('prA') and version = 1 $$), 1::bigint,
  'alice: update with matching expected version affects 1 row');
select is(test_affected($$ update public.cf_projects set status = 'completed', version = 2 where id = fx('prA') and version = 1 $$), 0::bigint,
  'alice: stale expected version affects 0 rows (conflict for the DAL)');
select throws_ok($$ update public.cf_projects set status = 'completed' where id = fx('prA') $$, '40001', null,
  'alice: UPDATE that forgets to bump version is rejected by trigger');
select throws_ok($$ update public.cf_projects set version = 1 where id = fx('prA') $$, '40001', null,
  'alice: version cannot be moved backwards');
select throws_like($$ update public.cf_projects set workspace_id = fx('wsB'), version = 3 where id = fx('prA') $$, '%permission denied%',
  'alice: workspace_id is not an updatable column (grant)');
select throws_like($$ update public.cf_projects set created_by = fx('bob'), version = 3 where id = fx('prA') $$, '%permission denied%',
  'alice: created_by is not an updatable column (grant)');

-- Constraints mirror Zod
select throws_ok($$ insert into public.cf_projects (workspace_id, client_id, name) values (fx('wsA'), fx('clA'), '') $$, '23514', null, 'empty project name rejected');
select throws_ok($$ insert into public.cf_projects (workspace_id, client_id, name) values (fx('wsA'), fx('clA'), repeat('x', 101)) $$, '23514', null, '101-char project name rejected');
select throws_ok($$ insert into public.cf_projects (workspace_id, client_id, name, description) values (fx('wsA'), fx('clA'), 'ok', repeat('x', 2001)) $$, '23514', null, '2001-char description rejected');
select throws_ok($$ insert into public.cf_projects (workspace_id, client_id, name, status) values (fx('wsA'), fx('clA'), 'ok', 'bogus') $$, '22P02', null, 'unknown status rejected by enum');
select throws_ok($$ insert into public.cf_projects (workspace_id, client_id, name, version) values (fx('wsA'), fx('clA'), 'ok', 0) $$, '23514', null, 'version 0 rejected');

-- Owner manages clients; project delete allowed for owner
select lives_ok($$ insert into public.cf_clients (workspace_id, name) values (fx('wsA'), 'Second client A') $$, 'alice (owner): can create clients');
select lives_ok($$ delete from public.cf_projects where id = '30000000-0000-4000-8000-0000000000a2' $$, 'alice (owner): can delete own-workspace project');
select is((select count(*) from public.cf_projects where id = '30000000-0000-4000-8000-0000000000a2'), 0::bigint, 'deleted project is gone');
select test_reset();

-- ---------------------------------------------------------------------------
-- 5. Carol (member of A, admin of B): cross-tenant FK insertion must fail at the DB
-- ---------------------------------------------------------------------------
select test_as(fx('carol'));
select is((select count(*) from public.cf_projects), 2::bigint, 'carol sees both her workspaces'' projects');
select throws_ok($$ insert into public.cf_projects (workspace_id, client_id, name) values (fx('wsA'), fx('clB'), 'project in A pointing at client of B') $$,
  '23503', null, 'carol: composite FK rejects a B client on an A project even though she can read both');
select throws_ok($$ update public.cf_projects set client_id = fx('clB'), version = version + 1 where id = fx('prA') $$,
  '23503', null, 'carol: cannot re-point an A project at a B client via UPDATE');
select throws_like($$ insert into public.cf_clients (workspace_id, name) values (fx('wsA'), 'carol client') $$, '%row-level security%',
  'carol (member in A): cannot manage clients in A');
select lives_ok($$ insert into public.cf_clients (workspace_id, name) values (fx('wsB'), 'carol client in B') $$, 'carol (admin in B): can manage clients in B');
select is(test_affected($$ delete from public.cf_projects where id = fx('prA') $$), 0::bigint,
  'carol (member in A): DELETE of A project affects 0 rows (owner/admin only)');
select test_reset();

-- ---------------------------------------------------------------------------
-- 6. Dave (removed member): authenticated, but no membership -> nothing
-- ---------------------------------------------------------------------------
select test_as(fx('dave'));
select is((select count(*) from public.cf_projects), 0::bigint, 'dave (removed): sees zero projects');
select is((select count(*) from public.platform_workspaces), 0::bigint, 'dave (removed): sees zero workspaces');
select throws_like($$ insert into public.cf_projects (workspace_id, client_id, name) values (fx('wsA'), fx('clA'), 'dave sneaks back') $$, '%row-level security%',
  'dave (removed): INSERT into former workspace rejected');
select test_reset();

-- ---------------------------------------------------------------------------
-- 7. Erin (portal client in A): not staff -> no internal project access yet
-- ---------------------------------------------------------------------------
select test_as(fx('erin'));
select is((select count(*) from public.cf_projects), 0::bigint, 'erin (client role): sees zero internal projects');
select is((select count(*) from public.platform_workspaces), 1::bigint, 'erin (client role): still sees the workspace she belongs to');
select throws_like($$ insert into public.cf_projects (workspace_id, client_id, name) values (fx('wsA'), fx('clA'), 'client-created') $$, '%row-level security%',
  'erin (client role): cannot create projects');
select test_reset();

-- ---------------------------------------------------------------------------
-- 8. Frank (owner of a SupportDesk workspace): wrong app -> cf_* policies fail
-- ---------------------------------------------------------------------------
select test_as(fx('frank'));
select throws_like($$ insert into public.cf_clients (workspace_id, name) values (fx('wsS'), 'client in a supportdesk workspace') $$, '%row-level security%',
  'frank: owner of a supportdesk workspace cannot write cf_clients into it');
select test_reset();

-- ---------------------------------------------------------------------------
-- 9. Workspace creation function: atomic, bounded, self-owned
-- ---------------------------------------------------------------------------
select test_as(fx('dave'));
select lives_ok($$ select public.platform_create_workspace('clientflow', '  Dave''s Fresh Start  ') $$, 'dave can create his own new workspace');
select is((select count(*) from public.platform_workspaces where name = 'Dave''s Fresh Start'), 1::bigint, 'workspace name is trimmed and visible to creator');
select is((select role::text from public.platform_members where user_id = fx('dave')), 'owner', 'creator becomes owner atomically');
select throws_ok($$ select public.platform_create_workspace('clientflow', '') $$, '22023', null, 'empty workspace name rejected');
select throws_like($$ insert into public.platform_workspaces (app, name, created_by) values ('clientflow', 'direct', fx('dave')) $$, '%permission denied%',
  'direct INSERT into platform_workspaces is not granted; the function is the only path');
select throws_like($$ insert into public.platform_members (workspace_id, user_id, role) values (fx('wsA'), fx('dave'), 'owner') $$, '%permission denied%',
  'dave cannot grant himself membership by direct INSERT');
select throws_like($$ update public.platform_workspaces set app = 'supportdesk' where created_by = fx('dave') $$, '%permission denied%',
  'workspace app column is not updatable by request roles');
select test_reset();

select * from finish();
rollback;
