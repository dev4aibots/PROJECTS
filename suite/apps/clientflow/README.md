# ClientFlow

Agency client and project workspace. This directory is an independent Next.js 16 / React 19 application and is the Vercel root for the ClientFlow product.

## What is implemented (CF-01)

An explicit, credential-free **demo workbench** under `/demo`:

- Validated project creation and editing (Zod schema: trimmed text limits, real calendar dates, enumerated status, existing non-archived client).
- Optimistic version guard: a stale edit is rejected with a conflict message instead of silently overwriting newer work.
- URL-driven search, status tabs, overdue ("attention") filter, list/board views and pagination. Unknown query values degrade to safe defaults.
- Board view changes status inline; every metric, tab count and deadline rail derives from the same in-memory dataset.
- Responsive native forms with labelled fields, described errors, focus management, unsaved-change warning and skip link.
- Fixed reference day `2026-09-07` so overdue/due-soon logic is deterministic in tests and screenshots.

## What is implemented (CF-02)

The **database layer** for the platform and ClientFlow, tested adversarially but not yet used by any app route:

- `suite/supabase/migrations/202609070001_platform.sql` — workspaces, members, profiles, role helpers, `platform_create_workspace`; RLS enabled and forced; deny-by-default grants.
- `suite/supabase/migrations/202609070002_clientflow.sql` — `cf_clients`, `cf_projects` with a composite foreign key `(workspace_id, client_id)`, Zod-mirrored CHECKs, version trigger, column-level grants, WITH CHECK policies.
- `suite/supabase/tests/clientflow_rls.test.sql` — 73 pgTAP assertions as real `anon`/`authenticated` roles (cross-tenant, removed member, portal client, wrong app, stale version, forged workspace...).
- `src/lib/database.types.ts` — generated from the applied schema; `npm run db:types:check` fails on drift. `tests/database-types.test.ts` keeps the SQL enum and the Zod `projectStatuses` identical.

## What is *not* implemented yet

No sign-in, no app code that reads or writes the database, no tasks/comments/files/portal. Sample data lives in browser memory for the current tab and is reset by a reload. The UI never pretends a live backend succeeded. Later gates (CF-02 onward) add Supabase schema, auth and persistence; see `../../docs/ROADMAP.md`.

## Commands

```bash
npm ci                 # exact pinned dependencies (Node 22)
npm run dev            # http://localhost:3000 -> redirects to /demo/projects
npm run lint           # eslint
npm run typecheck      # tsc --noEmit (generates Next route types first)
npm test               # Vitest domain tests (tests/projects.test.ts)
npm run build          # production build (Turbopack, single worker)
npm run start          # serve the production build on :3000
npx playwright install chromium
npm run test:e2e       # Playwright + axe, desktop and iPhone 13 (tests/workbench.spec.ts)

# Database (CF-02). Needs a throwaway LOCAL Postgres 17 with pgTAP; see ../../supabase/local/README.md
export DATABASE_URL=postgres://cf_dev:cf_dev@127.0.0.1/clientflow_test
npm run db:reset           # drop -> auth shim -> migrations -> seed
npm run db:test            # pg_prove: 73 adversarial RLS assertions as real roles
npm run db:types           # regenerate src/lib/database.types.ts
npm run db:types:check     # exit 1 if the file no longer matches the applied schema
npm run db:types:selftest  # generator unit checks, no database needed
```

`playwright.config.ts` starts `npm run start` automatically when nothing is listening on 3000; run `npm run build` first.

## Verification evidence (2026-09-07)

| Check | Result |
|---|---|
| `npm run lint` | clean |
| `npm run typecheck` | clean |
| `npm test` | 34 passed |
| `npm run build` | 7 routes, compiled with Turbopack |
| `npx playwright test --project=desktop` | 16 passed (incl. axe WCAG 2.1 AA on 5 routes) |
| `npx playwright test --project=mobile` | 16 passed |
| `npm run db:reset` (CF-02) | applied from empty schema |
| `npm run db:test` (CF-02) | 73 passed as `anon`/`authenticated` |
| `npm run db:types:check` (CF-02) | no drift |
| `npm test` after CF-02 | 39 passed (34 domain + 5 type contract) |

## Small-container notes

- Icons are imported per file through `src/components/icons.ts`. Importing the `@phosphor-icons/react` barrel pulled 1,500+ icons into the module graph and exhausted a 1 GB build container.
- `next.config.ts` sets `experimental.cpus: 1` and disables browser source maps. Building in ~1 GB RAM also needs swap (~2 GB) — the compile phase peaks near 1.1 GB.
- Playwright runs with one worker for the same reason.

## Environment

`.env.example` deliberately lists no variables. Nothing in this milestone reads configuration or secrets.
