# Handoff

Updated: 2026-09-07 (session 5). **CF-02 is verified.** Active task: **CF-03** (claimed; nothing implemented yet). CF-01 and CF-02 must not be rebuilt — read them to learn interfaces.

## Exact next action
Start CF-03 (authentication and workspace onboarding) per `docs/ARCHITECTURE.md` (shared auth), `docs/SECURITY_TESTING.md` (authorization matrix) and `docs/projects/clientflow/FILES.md` planned CF-03 rows:

1. **Restore the runtime first** (sandbox resets wipe it): `sudo apt-get install -y postgresql postgresql-contrib postgresql-17-pgtap`, start cluster, create `cf_dev`/`clientflow_test` (commands in `suite/supabase/local/README.md`), then `cd suite/apps/clientflow && npm ci`. Baseline: `DATABASE_URL=postgres://cf_dev:cf_dev@127.0.0.1/clientflow_test npm run db:reset && npm run db:test && npm run db:types:check && npm test` → expect reset complete, 73/73, no drift, 39/39.
2. Add `@supabase/supabase-js` + `@supabase/ssr` (exact pins) and write `src/lib/supabase/server.ts` (cookie client, server-only), `src/lib/supabase/client.ts` (browser), `src/proxy.ts` (session refresh + cookie propagation), `src/app/auth/callback/route.ts` (code exchange, **allow-listed relative redirect only**), `src/app/login/page.tsx`, `src/app/auth/recovery/page.tsx`, signout action. Type every client with `Database` from `src/lib/database.types.ts`.
3. Onboarding: after sign-in, call `platform_ensure_profile` then list `platform_workspaces` (RLS shows only memberships); if none, form → `platform_create_workspace('clientflow', name)` → redirect `/app/[workspaceId]`. Handle backend-failed state explicitly; **never fall back to demo data on a live failure**.
4. Tests: unit tests for redirect allow-list and cookie helpers; a Vitest integration test that talks to the local Postgres through PostgREST is not available without Docker — record that boundary honestly and cover the SQL side with a new `tests/onboarding.test.sql` (profile upsert idempotent; duplicate create under quota; anon cannot call). Playwright: unauthenticated `/app/*` redirects to `/login`; no cached authenticated HTML for a signed-out visitor.
5. Update `FILES.md` (CF-03 rows), STATUS evidence, CHANGELOG, LEARNING (real auth flow with file names), this HANDOFF. Commit, sync, push, update PR #3.

## CF-02 verification record (do not repeat unless a file changes)
| Check | Command (from `suite/apps/clientflow`, `DATABASE_URL` set) | Result |
|---|---|---|
| Fresh reset | `npm run db:reset` | shim + 2 migrations + seed applied from empty |
| Adversarial RLS | `npm run db:test` | 73/73 as `anon`/`authenticated` |
| Mutation checks | WITH CHECK→`true` / add enum value | 4 assertions fail / drift exit 1 |
| Types | `npm run db:types:check`, `db:types:selftest` | no drift; self-test passed |
| Domain + type contract | `npm test` | 39/39 |
| Lint / typecheck | `npm run lint`, `npm run typecheck` | clean |
| Continuity | `node suite/scripts/verify-state.mjs` | 30 docs OK |

Not run this session: `npm run build` and Playwright (unchanged UI; CF-01 record stands). `supabase start`/`config.toml` unexecuted — no Docker.

## Runtime notes
1 GB RAM sandbox. Build needs ~2 GB swap; Playwright `workers: 1`. Never import the `@phosphor-icons/react` barrel. Supabase CLI `gen types --db-url` also requires Docker — that is why `scripts/gen-types.mjs` exists (catalog introspection via psql; differences documented in its header).

## Current reality
- Only ClientFlow, SupportDesk AI and InvoiceHub are in scope. Legacy trees live on `archive/*` branches only; never restore them.
- ClientFlow `/demo` is a tested UI + domain foundation (browser memory). The database layer now exists and is adversarially tested locally, but **no app code talks to it yet** (that is CF-03/CF-04).
- No hosted credentials or deployments have been used.

## Git
Branch `genspark_ai_developer`; PR https://github.com/dev4aibots/PROJECTS/pull/3. Remote `main` is the wiped commit `e4bbba0`, recorded as an ancestor via an `ours` merge so pushes fast-forward.

## Boundaries
Supabase free-tier quotas and Vercel non-commercial terms are in RESEARCH. Local plain-Postgres proves SQL behaviour, not GoTrue/PostgREST/storage. Complete ClientFlow gates before scaffolding the next product.
