# ClientFlow file ledger

Paths relative to `suite/apps/clientflow/` unless prefixed `suite/`. Initially planned; update statuses after implementation and tests.

| File | Symbols / responsibility | Gate | State |
|---|---|---|---|
| package.json | scripts, exact dependency versions, Node engine | CF-01 | planned |
| package-lock.json | reproducible dependencies | CF-01 | planned |
| tsconfig.json | strict TypeScript and alias | CF-01 | planned |
| next-env.d.ts | Next-generated ambient types | CF-01 | planned |
| next.config.ts | app runtime configuration | CF-01 | planned |
| postcss.config.mjs | Tailwind 4 plugin | CF-01 | planned |
| eslint.config.mjs | Next TypeScript lint | CF-01 | planned |
| vitest.config.ts | domain test environment | CF-01 | planned |
| playwright.config.ts | browser projects/server | CF-01 | planned |
| .gitignore | env/build/test outputs excluded | CF-01 | planned |
| .env.example | explicit no credentials for UI milestone | CF-01 | planned |
| README.md | implemented commands and limitations | CF-01 | planned |
| src/app/layout.tsx | RootLayout, metadata, skip link | CF-01 | planned |
| src/app/globals.css | design tokens and responsive components | CF-01 | planned |
| src/app/page.tsx | explicit demo entry redirect | CF-01 | planned |
| src/app/not-found.tsx | missing-page recovery | CF-01 | planned |
| src/app/error.tsx | safe route error/retry | CF-01 | planned |
| src/app/demo/layout.tsx | demo provider + shell boundary | CF-01 | planned |
| src/app/demo/page.tsx | overview derived from sample records | CF-01 | planned |
| src/app/demo/projects/page.tsx | Suspense boundary for URL state | CF-01 | planned |
| src/app/demo/projects/new/page.tsx | create form | CF-01 | planned |
| src/app/demo/projects/[id]/page.tsx | detail/edit route | CF-01 | planned |
| src/app/demo/guide/page.tsx | implementation limits and flow | CF-01 | planned |
| src/components/app-shell.tsx | accessible sidebar and navigation | CF-01 | planned |
| src/components/demo-provider.tsx | sample state context, save/revise commands | CF-01 | planned |
| src/components/project-workbench.tsx | search/filter/table/board/pagination | CF-01 | planned |
| src/components/project-form.tsx | shared validated create/edit form | CF-01 | planned |
| src/components/project-detail.tsx | edit data lookup and not-found state | CF-01 | planned |
| src/components/overview.tsx | counts and deadline list | CF-01 | planned |
| src/components/status-badge.tsx | text + semantic status style | CF-01 | planned |
| src/lib/projects.ts | schema, types, filters, metrics, date handling, versioned updates | CF-01 | planned |
| src/lib/demo-data.ts | synthetic clients/projects, fixed reference date | CF-01 | planned |
| tests/projects.test.ts | validation/date/filter/metrics/conflict tests | CF-01 | planned |
| tests/demo.spec.ts | browser create/edit/filter/board/mobile/axe | CF-01 | planned |
| src/lib/supabase/server.ts | server-only cookie client | CF-03 | planned |
| src/lib/supabase/client.ts | browser auth client | CF-03 | planned |
| src/proxy.ts | auth refresh with cookie propagation | CF-03 | planned |
| src/app/auth/callback/route.ts | code exchange, safe redirect | CF-03 | planned |
| src/app/login/page.tsx | OAuth/email UX | CF-03 | planned |
| src/app/auth/recovery/page.tsx | password recovery | CF-03 | planned |
| src/lib/data/projects.ts | minimal user-scoped query DTOs | CF-04 | planned |
| src/lib/data/clients.ts | client queries and pagination | CF-04 | planned |
| src/app/app/[workspaceId]/projects/actions.ts | validated authorized mutations | CF-04 | planned |
| src/lib/database.types.ts | generated from migrations | CF-02 | planned |
| suite/supabase/config.toml | local Supabase services | CF-02 | planned |
| suite/supabase/migrations/202609070001_platform.sql | platform workspace/membership policies | CF-02 | planned |
| suite/supabase/migrations/202609070002_clientflow.sql | client/project integrity and RLS | CF-02 | planned |
| suite/supabase/tests/clientflow_rls.test.sql | real-role negative access tests | CF-02 | planned |
| suite/supabase/seed.sql | isolated synthetic local fixtures | CF-02 | planned |

## Expansion rule
Before CF-05/06/07, add exact task/comment/invite/portal/file paths and test contracts to this ledger. Do not pre-create empty files. PRD/ROADMAP freeze behavior; file structure can expand in a recorded plan. Every new path must appear here before task verification.
