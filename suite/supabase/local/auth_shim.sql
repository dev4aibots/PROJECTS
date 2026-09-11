-- Local-Postgres stand-in for the parts of Supabase that migrations depend on.
-- NOT a migration. Never apply to a Supabase project (it already has these).
-- Purpose: run the migration chain and the pgTAP role tests on a plain
-- PostgreSQL 17 when Docker/Supabase CLI are unavailable (sandbox case).
-- Differences from Supabase are listed in suite/supabase/local/README.md.

create schema if not exists auth;
create extension if not exists pgcrypto;

-- Roles mirror Supabase: request roles are NOLOGIN and switched into with SET ROLE.
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin noinherit; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin noinherit; end if;
  if not exists (select 1 from pg_roles where rolname = 'service_role') then create role service_role nologin noinherit bypassrls; end if;
end $$;

grant usage on schema public to anon, authenticated, service_role;
grant usage on schema auth to anon, authenticated, service_role;

-- Minimal subset of auth.users columns that seeds and FKs touch.
create table if not exists auth.users (
  id uuid primary key,
  instance_id uuid,
  aud text,
  role text,
  email text unique,
  encrypted_password text,
  email_confirmed_at timestamptz,
  raw_app_meta_data jsonb,
  raw_user_meta_data jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Same definitions Supabase ships: identity comes from the JWT claims GUC.
create or replace function auth.uid() returns uuid
language sql stable as $$
  select coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$$;

create or replace function auth.role() returns text
language sql stable as $$
  select coalesce(
    nullif(current_setting('request.jwt.claim.role', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role')
  )::text
$$;

create or replace function auth.jwt() returns jsonb
language sql stable as $$
  select coalesce(
    nullif(current_setting('request.jwt.claim', true), ''),
    nullif(current_setting('request.jwt.claims', true), '')
  )::jsonb
$$;

grant execute on function auth.uid(), auth.role(), auth.jwt() to anon, authenticated, service_role;
-- Supabase does not expose auth.users to request roles; keep it that way here.
revoke all on auth.users from anon, authenticated;
