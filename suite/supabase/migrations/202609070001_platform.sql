-- 202609070001_platform.sql — shared platform layer (CF-02)
-- Contract: suite/docs/DATABASE.md. Append-only once applied (ADR-006).
-- Everything here is namespaced platform_* and lives in public (ADR-001).
-- Request roles (anon/authenticated) get no table privileges except those
-- granted below, and every table has RLS with FORCE so even the owner role
-- is subject to policies when it is not BYPASSRLS.

-- ---------------------------------------------------------------------------
-- 0. Lock down default privileges. Supabase grants broad public-schema access
--    to request roles by default; we want deny-by-default so every access path
--    is an explicit, testable grant.
-- ---------------------------------------------------------------------------
revoke all on all tables    in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke all on all functions in schema public from anon, authenticated;
alter default privileges in schema public revoke all on tables    from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;
alter default privileges in schema public revoke all on functions from anon, authenticated;
alter default privileges in schema public revoke execute on functions from public;

-- ---------------------------------------------------------------------------
-- 1. Types
-- ---------------------------------------------------------------------------
create type public.platform_app as enum ('clientflow', 'supportdesk', 'invoicehub');
create type public.platform_role as enum ('owner', 'admin', 'member', 'client');

-- ---------------------------------------------------------------------------
-- 2. Shared trigger: maintain updated_at server-side; clients cannot forge it.
-- ---------------------------------------------------------------------------
create or replace function public.platform_set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;
revoke all on function public.platform_set_updated_at() from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- 3. Profiles: 1:1 with auth.users. A user may only read/update their own row.
--    Rows are created by platform_ensure_profile() (called by the app after
--    sign-in) or by a future auth trigger; never by arbitrary INSERT.
-- ---------------------------------------------------------------------------
create table public.platform_profiles (
  id            uuid primary key references auth.users (id) on delete cascade,
  display_name  text not null
                constraint platform_profiles_display_name_len
                check (char_length(display_name) between 1 and 80),
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create trigger platform_profiles_updated_at
  before update on public.platform_profiles
  for each row execute function public.platform_set_updated_at();

-- ---------------------------------------------------------------------------
-- 4. Workspaces: a tenant boundary scoped to exactly one app.
--    app and created_by are immutable after insert (trigger below).
-- ---------------------------------------------------------------------------
create table public.platform_workspaces (
  id          uuid primary key default gen_random_uuid(),
  app         public.platform_app not null,
  name        text not null
              constraint platform_workspaces_name_len
              check (char_length(name) between 1 and 80),
  created_by  uuid not null references auth.users (id) on delete restrict,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index platform_workspaces_created_by_idx on public.platform_workspaces (created_by);
create trigger platform_workspaces_updated_at
  before update on public.platform_workspaces
  for each row execute function public.platform_set_updated_at();

create or replace function public.platform_workspaces_guard_immutable()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.app <> old.app then
    raise exception 'platform_workspaces.app is immutable' using errcode = 'check_violation';
  end if;
  if new.created_by <> old.created_by then
    raise exception 'platform_workspaces.created_by is immutable' using errcode = 'check_violation';
  end if;
  if new.id <> old.id then
    raise exception 'platform_workspaces.id is immutable' using errcode = 'check_violation';
  end if;
  return new;
end;
$$;
revoke all on function public.platform_workspaces_guard_immutable() from public, anon, authenticated;
create trigger platform_workspaces_immutable
  before update on public.platform_workspaces
  for each row execute function public.platform_workspaces_guard_immutable();

-- ---------------------------------------------------------------------------
-- 5. Members: the ONLY source of truth for "who may touch this workspace".
--    role 'client' is legal only in ClientFlow (checked by trigger because
--    the app lives on the parent row).
-- ---------------------------------------------------------------------------
create table public.platform_members (
  workspace_id  uuid not null references public.platform_workspaces (id) on delete cascade,
  user_id       uuid not null references auth.users (id) on delete cascade,
  role          public.platform_role not null,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  primary key (workspace_id, user_id)
);
create index platform_members_user_idx on public.platform_members (user_id);
create trigger platform_members_updated_at
  before update on public.platform_members
  for each row execute function public.platform_set_updated_at();

create or replace function public.platform_members_guard()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  ws_app public.platform_app;
begin
  select app into ws_app from public.platform_workspaces where id = new.workspace_id;
  if new.role = 'client' and ws_app is distinct from 'clientflow' then
    raise exception 'role client is only valid in clientflow workspaces' using errcode = 'check_violation';
  end if;
  if tg_op = 'UPDATE' and (new.workspace_id <> old.workspace_id or new.user_id <> old.user_id) then
    raise exception 'platform_members identity columns are immutable' using errcode = 'check_violation';
  end if;
  return new;
end;
$$;
revoke all on function public.platform_members_guard() from public, anon, authenticated;
create trigger platform_members_guard
  before insert or update on public.platform_members
  for each row execute function public.platform_members_guard();

-- ---------------------------------------------------------------------------
-- 6. Authorization helper. SECURITY DEFINER so policies on other tables can
--    consult membership without recursing into platform_members RLS.
--    Hardening per DATABASE.md: fixed empty search_path, fully qualified
--    names, auth.uid() only (never a caller-supplied user id), STABLE,
--    execute revoked from public and granted to authenticated only.
--    Returns false for anonymous callers, unknown workspaces, wrong app,
--    non-members and members whose role is not in allowed_roles.
-- ---------------------------------------------------------------------------
create or replace function public.platform_has_role(
  target_workspace uuid,
  expected_app     public.platform_app,
  allowed_roles    public.platform_role[]
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select
    target_workspace is not null
    and auth.uid() is not null
    and exists (
      select 1
      from public.platform_members m
      join public.platform_workspaces w on w.id = m.workspace_id
      where m.workspace_id = target_workspace
        and m.user_id = auth.uid()
        and w.app = expected_app
        and m.role = any (allowed_roles)
    );
$$;
revoke all on function public.platform_has_role(uuid, public.platform_app, public.platform_role[]) from public, anon;
grant execute on function public.platform_has_role(uuid, public.platform_app, public.platform_role[]) to authenticated;

-- Any-role membership check. Used by the platform_members policy itself, which
-- would otherwise recurse (a policy on T that queries T re-enters T's RLS).
create or replace function public.platform_is_member(target_workspace uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select
    target_workspace is not null
    and auth.uid() is not null
    and exists (
      select 1 from public.platform_members m
      where m.workspace_id = target_workspace and m.user_id = auth.uid()
    );
$$;
revoke all on function public.platform_is_member(uuid) from public, anon;
grant execute on function public.platform_is_member(uuid) to authenticated;

-- Convenience: internal staff of a workspace (everything except portal clients).
create or replace function public.platform_is_staff(target_workspace uuid, expected_app public.platform_app)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select public.platform_has_role(target_workspace, expected_app, array['owner','admin','member']::public.platform_role[]);
$$;
revoke all on function public.platform_is_staff(uuid, public.platform_app) from public, anon;
grant execute on function public.platform_is_staff(uuid, public.platform_app) to authenticated;

-- ---------------------------------------------------------------------------
-- 7. Transactional workspace creation. Verifies the caller, bounds the number
--    of workspaces per user (quota abuse), and inserts workspace + owner
--    membership atomically. This is the only way a normal user gets a row
--    into platform_workspaces (no INSERT policy exists).
-- ---------------------------------------------------------------------------
create or replace function public.platform_create_workspace(
  target_app public.platform_app,
  ws_name    text
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  caller  uuid := auth.uid();
  new_id  uuid;
  owned   integer;
  trimmed text := btrim(coalesce(ws_name, ''));
begin
  if caller is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if char_length(trimmed) < 1 or char_length(trimmed) > 80 then
    raise exception 'workspace name must be 1-80 characters' using errcode = '22023';
  end if;

  -- Serialise per caller so concurrent calls cannot both pass the quota check.
  perform pg_advisory_xact_lock(hashtext('platform_create_workspace'), hashtext(caller::text));

  select count(*) into owned
  from public.platform_members
  where user_id = caller and role = 'owner';
  if owned >= 10 then
    raise exception 'workspace limit reached (10 owned workspaces)' using errcode = '54000';
  end if;

  insert into public.platform_workspaces (app, name, created_by)
  values (target_app, trimmed, caller)
  returning id into new_id;

  insert into public.platform_members (workspace_id, user_id, role)
  values (new_id, caller, 'owner');

  return new_id;
end;
$$;
revoke all on function public.platform_create_workspace(public.platform_app, text) from public, anon;
grant execute on function public.platform_create_workspace(public.platform_app, text) to authenticated;

-- Upsert the caller's own profile. Display name is validated by the CHECK.
create or replace function public.platform_ensure_profile(name text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  caller uuid := auth.uid();
begin
  if caller is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  insert into public.platform_profiles (id, display_name)
  values (caller, btrim(name))
  on conflict (id) do update set display_name = excluded.display_name;
end;
$$;
revoke all on function public.platform_ensure_profile(text) from public, anon;
grant execute on function public.platform_ensure_profile(text) to authenticated;

-- ---------------------------------------------------------------------------
-- 8. Row Level Security. FORCE so table owners are also bound.
-- ---------------------------------------------------------------------------
alter table public.platform_profiles   enable row level security;
alter table public.platform_profiles   force  row level security;
alter table public.platform_workspaces enable row level security;
alter table public.platform_workspaces force  row level security;
alter table public.platform_members    enable row level security;
alter table public.platform_members    force  row level security;

-- Profiles: self only. No INSERT/DELETE policy — rows come from the function.
create policy platform_profiles_select_self on public.platform_profiles
  for select to authenticated
  using (id = auth.uid());
create policy platform_profiles_update_self on public.platform_profiles
  for update to authenticated
  using (id = auth.uid())
  with check (id = auth.uid());

-- Workspaces: members (any role) can read; owner/admin can rename.
-- No INSERT policy (use platform_create_workspace); no DELETE policy yet
-- (reviewed deletion flow is a later gate).
create policy platform_workspaces_select_member on public.platform_workspaces
  for select to authenticated
  using (public.platform_is_member(id));
create policy platform_workspaces_update_admin on public.platform_workspaces
  for update to authenticated
  using  (public.platform_has_role(id, app, array['owner','admin']::public.platform_role[]))
  with check (public.platform_has_role(id, app, array['owner','admin']::public.platform_role[]));

-- Members: a member can see the roster of their own workspaces.
-- No direct INSERT/UPDATE/DELETE policies: role changes go through reviewed
-- functions in CF-06 (invitations, last-owner invariant). Until then the
-- only membership writer is platform_create_workspace.
create policy platform_members_select_same_workspace on public.platform_members
  for select to authenticated
  using (public.platform_is_member(workspace_id));

-- ---------------------------------------------------------------------------
-- 9. Grants. Column-level where it matters: authenticated may only change
--    display_name / name, never ids, timestamps, app or created_by.
-- ---------------------------------------------------------------------------
grant select                on public.platform_profiles   to authenticated;
grant update (display_name) on public.platform_profiles   to authenticated;
grant select                on public.platform_workspaces to authenticated;
grant update (name)         on public.platform_workspaces to authenticated;
grant select                on public.platform_members    to authenticated;
-- anon: nothing. service_role keeps default owner-equivalent access via BYPASSRLS.
