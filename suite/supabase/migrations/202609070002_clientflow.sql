-- 202609070002_clientflow.sql — ClientFlow clients + projects (CF-02)
-- Contract: suite/docs/projects/clientflow/ARCHITECTURE.md "Planned relational
-- model" and suite/docs/DATABASE.md "Integrity beyond tenant filtering".
-- Limits mirror suite/apps/clientflow/src/lib/projects.ts (Zod) exactly:
--   name 1..100, description <= 2000, status enum, due_date nullable date,
--   version positive integer.
-- Tasks/comments/files/requests/notifications arrive with their own gates
-- (CF-05..CF-07); no placeholder tables here.

-- ---------------------------------------------------------------------------
-- 1. Types (same literal set as projectStatuses in projects.ts)
-- ---------------------------------------------------------------------------
create type public.cf_project_status as enum ('planned', 'active', 'review', 'completed', 'archived');

-- ---------------------------------------------------------------------------
-- 2. Generic guards shared by cf_* tables
-- ---------------------------------------------------------------------------
-- workspace_id / created_by / id are immutable; a member of two workspaces
-- must never be able to "move" a row between tenants by UPDATE.
create or replace function public.cf_guard_tenant_columns()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.id <> old.id then
    raise exception 'id is immutable' using errcode = 'check_violation';
  end if;
  if new.workspace_id <> old.workspace_id then
    raise exception 'workspace_id is immutable' using errcode = 'check_violation';
  end if;
  if new.created_by <> old.created_by then
    raise exception 'created_by is immutable' using errcode = 'check_violation';
  end if;
  return new;
end;
$$;
revoke all on function public.cf_guard_tenant_columns() from public, anon, authenticated;

-- created_by is always the caller; clients cannot attribute rows to others.
create or replace function public.cf_set_created_by()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if auth.uid() is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  new.created_by := auth.uid();
  return new;
end;
$$;
revoke all on function public.cf_set_created_by() from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- 3. cf_clients
-- ---------------------------------------------------------------------------
create table public.cf_clients (
  id             uuid not null default gen_random_uuid(),
  workspace_id   uuid not null references public.platform_workspaces (id) on delete cascade,
  name           text not null
                 constraint cf_clients_name_len check (char_length(name) between 1 and 100),
  contact_name   text
                 constraint cf_clients_contact_name_len check (contact_name is null or char_length(contact_name) between 1 and 100),
  contact_email  text
                 constraint cf_clients_contact_email_len check (contact_email is null or char_length(contact_email) between 3 and 254),
  archived_at    timestamptz,
  created_by     uuid not null references auth.users (id) on delete restrict,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  primary key (id),
  -- Target for composite foreign keys from cf_projects (and later tables).
  constraint cf_clients_workspace_id_id_key unique (workspace_id, id)
);
create index cf_clients_workspace_name_idx on public.cf_clients (workspace_id, name);

create trigger cf_clients_updated_at
  before update on public.cf_clients
  for each row execute function public.platform_set_updated_at();
create trigger cf_clients_created_by
  before insert on public.cf_clients
  for each row execute function public.cf_set_created_by();
create trigger cf_clients_tenant_guard
  before update on public.cf_clients
  for each row execute function public.cf_guard_tenant_columns();

-- ---------------------------------------------------------------------------
-- 4. cf_projects
-- ---------------------------------------------------------------------------
create table public.cf_projects (
  id             uuid not null default gen_random_uuid(),
  workspace_id   uuid not null references public.platform_workspaces (id) on delete cascade,
  client_id      uuid not null,
  name           text not null
                 constraint cf_projects_name_len check (char_length(name) between 1 and 100),
  description    text not null default ''
                 constraint cf_projects_description_len check (char_length(description) <= 2000),
  status         public.cf_project_status not null default 'planned',
  due_date       date,
  version        integer not null default 1
                 constraint cf_projects_version_positive check (version > 0),
  created_by     uuid not null references auth.users (id) on delete restrict,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  primary key (id),
  constraint cf_projects_workspace_id_id_key unique (workspace_id, id),
  -- THE tenant-integrity constraint: a project may only reference a client in
  -- the SAME workspace. A plain FK on client_id would accept any client the
  -- caller can see, including one from another workspace they belong to.
  constraint cf_projects_client_same_workspace_fkey
    foreign key (workspace_id, client_id)
    references public.cf_clients (workspace_id, id)
    on delete restrict
);
create index cf_projects_workspace_status_due_idx on public.cf_projects (workspace_id, status, due_date);
create index cf_projects_workspace_client_idx     on public.cf_projects (workspace_id, client_id);

create trigger cf_projects_updated_at
  before update on public.cf_projects
  for each row execute function public.platform_set_updated_at();
create trigger cf_projects_created_by
  before insert on public.cf_projects
  for each row execute function public.cf_set_created_by();
create trigger cf_projects_tenant_guard
  before update on public.cf_projects
  for each row execute function public.cf_guard_tenant_columns();

-- Optimistic concurrency: every UPDATE must increment version by exactly 1
-- relative to the row it read. The DAL sends "WHERE version = $expected" and
-- treats zero affected rows as a conflict; this trigger makes it impossible to
-- forget the increment or to "reset" a version downward.
create or replace function public.cf_projects_bump_version()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.version <> old.version + 1 then
    raise exception 'version must advance by exactly one (expected %, got %)', old.version + 1, new.version
      using errcode = 'serialization_failure';
  end if;
  return new;
end;
$$;
revoke all on function public.cf_projects_bump_version() from public, anon, authenticated;
create trigger cf_projects_version
  before update on public.cf_projects
  for each row execute function public.cf_projects_bump_version();

-- ---------------------------------------------------------------------------
-- 5. RLS. Deny by default; staff of the *row's* workspace, app = clientflow.
--    WITH CHECK on INSERT/UPDATE is what stops a member of workspace A from
--    inserting a row stamped with workspace B — SELECT-only policies would not.
-- ---------------------------------------------------------------------------
alter table public.cf_clients  enable row level security;
alter table public.cf_clients  force  row level security;
alter table public.cf_projects enable row level security;
alter table public.cf_projects force  row level security;

-- Clients: read = any staff; write = owner/admin ("Manage clients" in the role matrix).
create policy cf_clients_select_staff on public.cf_clients
  for select to authenticated
  using (public.platform_is_staff(workspace_id, 'clientflow'));
create policy cf_clients_insert_admin on public.cf_clients
  for insert to authenticated
  with check (public.platform_has_role(workspace_id, 'clientflow', array['owner','admin']::public.platform_role[]));
create policy cf_clients_update_admin on public.cf_clients
  for update to authenticated
  using      (public.platform_has_role(workspace_id, 'clientflow', array['owner','admin']::public.platform_role[]))
  with check (public.platform_has_role(workspace_id, 'clientflow', array['owner','admin']::public.platform_role[]));
-- No DELETE policy: clients are archived (archived_at), never hard-deleted while
-- projects reference them (FK is ON DELETE RESTRICT as a second line).

-- Projects: read/create/update = any staff. Portal (role client) read arrives
-- in CF-06 via cf_client_users; until then clients see nothing.
create policy cf_projects_select_staff on public.cf_projects
  for select to authenticated
  using (public.platform_is_staff(workspace_id, 'clientflow'));
create policy cf_projects_insert_staff on public.cf_projects
  for insert to authenticated
  with check (public.platform_is_staff(workspace_id, 'clientflow'));
create policy cf_projects_update_staff on public.cf_projects
  for update to authenticated
  using      (public.platform_is_staff(workspace_id, 'clientflow'))
  with check (public.platform_is_staff(workspace_id, 'clientflow'));
create policy cf_projects_delete_admin on public.cf_projects
  for delete to authenticated
  using (public.platform_has_role(workspace_id, 'clientflow', array['owner','admin']::public.platform_role[]));

-- ---------------------------------------------------------------------------
-- 6. Grants. Column lists exclude server-managed columns so a request cannot
--    even attempt to set created_by/created_at/updated_at.
-- ---------------------------------------------------------------------------
grant select on public.cf_clients to authenticated;
grant insert (id, workspace_id, name, contact_name, contact_email, archived_at) on public.cf_clients to authenticated;
grant update (name, contact_name, contact_email, archived_at)                    on public.cf_clients to authenticated;

grant select on public.cf_projects to authenticated;
grant insert (id, workspace_id, client_id, name, description, status, due_date, version) on public.cf_projects to authenticated;
grant update (client_id, name, description, status, due_date, version)                    on public.cf_projects to authenticated;
grant delete on public.cf_projects to authenticated;
-- anon: nothing on cf_* tables.
