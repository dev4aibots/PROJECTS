# Plain-PostgreSQL harness (no Docker)

`supabase start` needs Docker. When Docker is unavailable (the 1 GB sandbox where CF-02 was implemented), the migration chain and the pgTAP authorization tests run against a plain **PostgreSQL 17** with a small shim that recreates the parts of Supabase the SQL depends on.

## What the shim provides (`auth_shim.sql`)
| Supabase piece | Shim | Difference that matters |
|---|---|---|
| Roles `anon`, `authenticated`, `service_role` | Created `NOLOGIN NOINHERIT`; `service_role` is `BYPASSRLS` | Identical semantics for `SET ROLE` testing |
| `auth.users` | Minimal table (id, email, aud, role, metadata, timestamps) | Real GoTrue table has more columns/triggers; only FK targets and seed rows are needed here |
| `auth.uid()`, `auth.role()`, `auth.jwt()` | Same definitions Supabase ships (read `request.jwt.claim.sub` / `request.jwt.claims`) | Tests inject identity with `set local request.jwt.claim.sub` exactly like PostgREST does |
| Default grants | Supabase grants request roles broad `public` access; the shim grants only `USAGE` | The platform migration revokes/locks defaults anyway, so both environments end deny-by-default |

The shim is **never** a migration and must never be applied to a hosted project.

## Commands
```bash
# one-time (Debian/Ubuntu)
sudo apt-get install -y postgresql postgresql-contrib postgresql-17-pgtap   # pg_prove ships with pgtap
sudo pg_ctlcluster 17 main start
sudo -u postgres psql -c "create role cf_dev login superuser password 'cf_dev';" \
                      -c "create database clientflow_test owner cf_dev;"

export DATABASE_URL=postgres://cf_dev:cf_dev@127.0.0.1/clientflow_test
suite/supabase/scripts/local-reset.sh                 # drop -> shim -> migrations -> seed
PGPASSWORD=cf_dev pg_prove -h 127.0.0.1 -U cf_dev -d clientflow_test suite/supabase/tests/*.test.sql
node suite/supabase/scripts/gen-types.mjs             # regenerate database.types.ts
node suite/supabase/scripts/gen-types.mjs --check     # drift check (exit 1)
```
The same commands are exposed from `suite/apps/clientflow` as `npm run db:reset`, `db:test`, `db:types`, `db:types:check`.

## What this harness does and does not prove
- **Proves:** the migration chain applies from empty; every table has RLS enabled and forced; grants, policies, triggers, composite FKs and functions behave as specified for real `anon`/`authenticated` roles with a JWT subject.
- **Does not prove:** GoTrue behaviour (sign-up, refresh, email), PostgREST request parsing, storage policies, or Supabase-specific extensions. Those are exercised by the app integration tests from CF-03 onward and, finally, by the hosted smoke tests at the FINAL gate.
- `local-reset.sh` refuses any `DATABASE_URL` containing `supabase.co`, `supabase.com` or `pooler`.

## With Docker available
Prefer the CLI: `supabase start && supabase db reset` applies the same `migrations/*.sql` and `seed.sql` (see `config.toml`). Run `supabase test db` for pgTAP. Diff `supabase gen types typescript --local` against `gen-types.mjs` output; the only intended differences are documented at the top of `scripts/gen-types.mjs` (extension objects excluded; Insert/Update follow column grants).
