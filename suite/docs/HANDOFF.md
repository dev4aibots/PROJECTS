# Handoff

Updated: 2026-09-07 (session 4). Active task: **CF-02** (just claimed; nothing implemented yet). Previous task **CF-01 is verified** — do not rebuild it.

## Exact next action
Start CF-02 per `docs/DATABASE.md` and `docs/projects/clientflow/ARCHITECTURE.md` ("Planned relational model"):

1. **Establish a real local Postgres/Supabase runtime first.** `which docker supabase psql` all return nothing in the current sandbox. Options in order of preference: (a) Supabase CLI + Docker on a developer machine; (b) `apt-get install postgresql` in the sandbox and run the migration chain + role-based SQL tests against a plain local Postgres with `anon`/`authenticated` roles created manually; (c) if neither is available, set CF-02 to `blocked` in STATUS with that reason. **Do not write mocked RLS tests or fake a database.**
2. Create `suite/supabase/config.toml`, `suite/supabase/migrations/202609070001_platform.sql` (workspaces, members, role helper), `202609070002_clientflow.sql` (`cf_clients`, `cf_projects` with composite FK `(workspace_id, client_id)`, status CHECK, positive `version`, RLS policies with WITH CHECK), `suite/supabase/seed.sql` (synthetic users A/B, a two-workspace user, a removed member), and `suite/supabase/tests/clientflow_rls.test.sql` (cross-tenant SELECT/INSERT/UPDATE attempts as real roles must fail).
3. Generate `src/lib/database.types.ts` from the applied migration; add a drift check command.
4. Record every path in `docs/projects/clientflow/FILES.md`, evidence in `STATUS.json`, and a CHANGELOG entry. Update `docs/projects/clientflow/LEARNING.md` with the real policy names.

## CF-01 verification record (do not repeat unless a file changes)
| Check | Command (from `suite/apps/clientflow`) | Result |
|---|---|---|
| Lint | `npm run lint` | clean |
| Types | `npm run typecheck` | clean |
| Domain | `npm test` | 34/34 |
| Build | `NODE_OPTIONS=--max-old-space-size=700 npm run build` | 7 routes |
| Browser + axe | `npx playwright test --project=desktop` / `--project=mobile` | 16/16 each |
| Continuity | `node suite/scripts/verify-state.mjs` | 30 docs OK |

Sandbox constraints discovered: 1 GB RAM. The build needs ~2 GB swap (`sudo fallocate -l 2G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`). Playwright runs with `workers: 1`. Never import the `@phosphor-icons/react` barrel; use `src/components/icons.ts`.

## Current reality
- Only ClientFlow, SupportDesk AI and InvoiceHub are in scope. Legacy seven-project trees are recoverable from `archive/*` branches only (`archive/local-seven-projects-p5-2026-09-07` holds the most recent P1–P5 legacy work). Never restore them into the source tree.
- ClientFlow `/demo` is a tested UI + domain foundation. It stores nothing, authenticates nobody, and says so on every page.
- No hosted credentials or deployments have been used.

## Git
Branch `genspark_ai_developer`; PR https://github.com/dev4aibots/PROJECTS/pull/3. Remote `main` is the wiped commit `e4bbba0`, recorded as an ancestor via an `ours` merge so pushes fast-forward.

## Boundaries
Supabase free-tier quotas and Vercel non-commercial terms are documented in RESEARCH. Browser memory proves interaction only, not persistence/security. Complete ClientFlow gates before scaffolding the next product.
