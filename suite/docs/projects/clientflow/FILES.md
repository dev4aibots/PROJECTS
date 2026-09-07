# ClientFlow file ledger

Paths relative to `suite/apps/clientflow/` unless prefixed `suite/`. CF-01 and CF-02 rows carry their verification evidence; later-gate rows are planned only.

| File | Symbols / responsibility | Gate | State |
|---|---|---|---|
| package.json | scripts (incl. `db:reset/test/types/types:check/types:selftest` from CF-02), exact dependency versions, Node engine | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| package-lock.json | reproducible dependencies | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| tsconfig.json | strict TypeScript and alias | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| next-env.d.ts | Next-generated ambient types | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| next.config.ts | app runtime configuration | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| postcss.config.mjs | Tailwind 4 plugin | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| eslint.config.mjs | Next TypeScript lint | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| vitest.config.ts | domain test environment | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| playwright.config.ts | browser projects/server | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| .gitignore | env/build/test outputs excluded | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| .env.example | explicit no credentials for UI milestone | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| README.md | implemented commands and limitations | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/app/layout.tsx | RootLayout, metadata, skip link | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/app/globals.css | design tokens and responsive components | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/app/page.tsx | explicit demo entry redirect | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/app/not-found.tsx | missing-page recovery | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/app/error.tsx | safe route error/retry | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/app/demo/layout.tsx | demo provider + shell boundary | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/app/demo/page.tsx | overview derived from sample records | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/app/demo/projects/page.tsx | Suspense boundary for URL state | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/app/demo/projects/new/page.tsx | create form | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/app/demo/projects/[id]/page.tsx | detail/edit route | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/app/demo/guide/page.tsx | implementation limits and flow | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/components/app-shell.tsx | accessible sidebar and navigation | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/components/demo-provider.tsx | sample state context, save/revise commands | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/components/project-workbench.tsx | search/filter/table/board/pagination | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/components/project-form.tsx | shared validated create/edit form | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/components/project-detail.tsx | edit data lookup and not-found state | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/components/overview.tsx | counts and deadline list | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/components/icons.ts | per-icon re-exports; barrel import exhausted 1 GB build | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/components/status-badge.tsx | text + semantic status style | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/lib/projects.ts | schema, types, filters, metrics, date handling, versioned updates | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/lib/demo-data.ts | synthetic clients/projects, fixed reference date | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| tests/projects.test.ts | validation/date/filter/metrics/conflict tests | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| tests/workbench.spec.ts | browser routing/filters/board mutation/create-edit/reload boundary/axe/skip link (was planned as demo.spec.ts) | CF-01 | verified 2026-09-07: lint, typecheck, 34 unit, build, 32 browser/axe |
| src/lib/supabase/server.ts | server-only cookie client | CF-03 | planned |
| src/lib/supabase/client.ts | browser auth client | CF-03 | planned |
| src/proxy.ts | auth refresh with cookie propagation | CF-03 | planned |
| src/app/auth/callback/route.ts | code exchange, safe redirect | CF-03 | planned |
| src/app/login/page.tsx | OAuth/email UX | CF-03 | planned |
| src/app/auth/recovery/page.tsx | password recovery | CF-03 | planned |
| src/lib/data/projects.ts | minimal user-scoped query DTOs | CF-04 | planned |
| src/lib/data/clients.ts | client queries and pagination | CF-04 | planned |
| src/app/app/[workspaceId]/projects/actions.ts | validated authorized mutations | CF-04 | planned |
| src/lib/database.types.ts | GENERATED `Database`, `Tables/TablesInsert/TablesUpdate/Enums/Functions`, `Constants`; Insert/Update follow column grants | CF-02 | verified 2026-09-07: local-reset from empty, pg_prove 73/73 as anon/authenticated, types no-drift, vitest 39 |
| suite/supabase/config.toml | local CLI config (Docker path): api/db/auth/storage ports, seed path, redirect allowlist | CF-02 | verified 2026-09-07: local-reset from empty, pg_prove 73/73 as anon/authenticated, types no-drift, vitest 39 (not executed: no Docker) |
| suite/supabase/migrations/202609070001_platform.sql | enums `platform_app/platform_role`; `platform_profiles/workspaces/members`; `platform_set_updated_at`, `*_guard_immutable`, `platform_members_guard`; security-definer `platform_has_role/is_member/is_staff`; `platform_create_workspace` (advisory lock, 10 quota), `platform_ensure_profile`; RLS enable+force; deny-by-default grants | CF-02 | verified 2026-09-07: local-reset from empty, pg_prove 73/73 as anon/authenticated, types no-drift, vitest 39 |
| suite/supabase/migrations/202609070002_clientflow.sql | enum `cf_project_status`; `cf_clients`, `cf_projects` with composite FK `cf_projects_client_same_workspace_fkey`; `cf_guard_tenant_columns`, `cf_set_created_by`, `cf_projects_bump_version`; policies `cf_clients_{select_staff,insert_admin,update_admin}`, `cf_projects_{select_staff,insert_staff,update_staff,delete_admin}`; column-level grants | CF-02 | verified 2026-09-07: local-reset from empty, pg_prove 73/73 as anon/authenticated, types no-drift, vitest 39 |
| suite/supabase/tests/clientflow_rls.test.sql | 73 pgTAP assertions via `SET ROLE` + `request.jwt.claim.sub`: RLS forced on all tables, anon/no-sub denied, cross-tenant read/insert/update/delete, composite FK vs two-workspace member, removed member, portal client, wrong app, stale version, column grants, workspace creation | CF-02 | verified 2026-09-07: local-reset from empty, pg_prove 73/73 as anon/authenticated, types no-drift, vitest 39; mutation check: WITH CHECK->true fails 4 |
| suite/supabase/seed.sql | deterministic fake users alice/bob/carol/dave/erin/frank, workspaces A/B/S, one client+project per CF workspace; never for hosted | CF-02 | verified 2026-09-07: local-reset from empty, pg_prove 73/73 as anon/authenticated, types no-drift, vitest 39 |
| suite/supabase/local/auth_shim.sql | plain-Postgres stand-in: roles anon/authenticated/service_role, minimal `auth.users`, `auth.uid/role/jwt`; NOT a migration | CF-02 | verified 2026-09-07: local-reset from empty, pg_prove 73/73 as anon/authenticated, types no-drift, vitest 39 |
| suite/supabase/local/README.md | harness differences vs Supabase; what it proves and does not | CF-02 | verified 2026-09-07: local-reset from empty, pg_prove 73/73 as anon/authenticated, types no-drift, vitest 39 |
| suite/supabase/scripts/local-reset.sh | drop public/auth -> shim -> migrations -> seed; refuses hosted URLs | CF-02 | verified 2026-09-07: local-reset from empty, pg_prove 73/73 as anon/authenticated, types no-drift, vitest 39 |
| suite/supabase/scripts/gen-types.mjs | `PG_TO_TS`, `tsType`, `buildModel`, `emit`; psql catalog introspection; `--check` drift (exit 1), `--self-test` fixture checks | CF-02 | verified 2026-09-07: local-reset from empty, pg_prove 73/73 as anon/authenticated, types no-drift, vitest 39; drift mutation check: added enum value -> exit 1 |
| tests/database-types.test.ts | enum parity with `projectStatuses`; grant-shaped Insert/Update; platform tables never-insertable | CF-02 | verified 2026-09-07: local-reset from empty, pg_prove 73/73 as anon/authenticated, types no-drift, vitest 39 |

## Expansion rule
Before CF-05/06/07, add exact task/comment/invite/portal/file paths and test contracts to this ledger. Do not pre-create empty files. PRD/ROADMAP freeze behavior; file structure can expand in a recorded plan. Every new path must appear here before task verification.
