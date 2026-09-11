#!/usr/bin/env bash
# Fresh local database -> auth shim -> migration chain -> seed.
# Plain-PostgreSQL substitute for `supabase db reset` (see local/README.md).
# Usage: DATABASE_URL=postgres://user:pw@host/db suite/supabase/scripts/local-reset.sh
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${DATABASE_URL:?set DATABASE_URL to a throwaway local database}"
case "$DATABASE_URL" in
  *supabase.co*|*supabase.com*|*pooler*) echo "refusing to reset a hosted database" >&2; exit 2;;
esac
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q <<'SQL'
drop schema if exists public cascade;
create schema public;
drop schema if exists auth cascade;
create extension if not exists pgcrypto;
create extension if not exists pgtap;
SQL
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q -f "$here/local/auth_shim.sql"
for f in "$here"/migrations/*.sql; do
  echo "apply $(basename "$f")"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q -1 -f "$f"
done
if [ "${SKIP_SEED:-0}" != "1" ]; then
  echo "apply seed.sql"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q -1 -f "$here/seed.sql"
fi
echo "local reset complete"
