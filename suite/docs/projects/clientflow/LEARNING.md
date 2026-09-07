# ClientFlow learning guide

## First understand the business
An agency workspace owns clients; a client commissions projects; projects contain tasks, comments and files. Workspace teammates have broad delivery access. Client users get only explicitly linked portal records. “Signed in” is not enough.

## CF-01 concepts — read alongside the real code
Files: `suite/apps/clientflow/src/lib/projects.ts` (domain), `src/components/demo-provider.tsx` (state), `src/components/project-form.tsx`, `src/components/project-workbench.tsx`, tests in `tests/projects.test.ts` and `tests/workbench.spec.ts`.
- Runtime project schema validates trimmed text, enumerated status and real calendar dates.
- A pure `filterProjects` function should combine name/client search with selected status without mutating the input array.
- `projectMetrics` derives numbers from the same dataset as the list; completed/archived projects aren't overdue.
- `DemoProvider` is UI state, not a database. It must say reload resets data; it cannot prove authentication or persistence.
- A shared form receives existing data or defaults. Submit parses unknown input before mutation; invalid fields remain editable; saved edit includes expected version.
- URL query params make views/filtering shareable. Local project mutations are not shareable until the backend milestone.

### What the tests actually prove (and what they do not)
- `projectInputSchema` (Zod) trims text, caps name/description, requires a UUID client and a real calendar date (`isCalendarDate` rejects 2026-02-30). Unit tests cover each rule.
- `saveProject(projects, clients, input, {id, expectedVersion})` is pure: it returns a new array or a typed failure (`validation | not_found | conflict | limit`). The conflict branch is the optimistic version guard. Because it is pure, the same contract can later be enforced in SQL (`WHERE version = $expected`) — the browser check alone is never authoritative.
- `DemoProvider.save` reads `latest.current` (a ref), not the rendered `projects` state, so two rapid saves cannot overwrite each other with stale data.
- `filterProjects`, `projectMetrics`, `dueSoon`, `isOverdue` all take `today` as an argument and the demo fixes it to `2026-09-07`. That is why the browser tests can assert "1 overdue project" deterministically.
- `ProjectWorkbench` reads `useSearchParams()`; unknown `status` values fall back to `all` and show "Unknown status ignored"; `page=999` clamps to the last page. Test: "unknown status and out-of-range page values degrade safely".
- Accessibility is tested, not assumed: axe (WCAG 2.1 A/AA) runs on five routes at two viewports. It found real contrast failures during the build; the fix is in commit `26dc086`. Interview point: automated a11y checks catch design-token drift that visual review misses.
- **Not proven:** persistence, multi-user isolation, authentication. A reload discards everything — one test asserts exactly that, so nobody can claim otherwise.

## CF-02 concepts — the database is the security boundary
Files: `suite/supabase/migrations/202609070001_platform.sql`, `202609070002_clientflow.sql`, `suite/supabase/tests/clientflow_rls.test.sql`, `suite/supabase/scripts/gen-types.mjs`, `suite/apps/clientflow/src/lib/database.types.ts`, `tests/database-types.test.ts`.

### One complete trace: "Carol tries to point an A project at a B client"
Carol is `member` of workspace A and `admin` of workspace B (seed.sql). She sends `UPDATE cf_projects SET client_id = <B client>, version = version + 1 WHERE id = <A project>` as role `authenticated` with `request.jwt.claim.sub = carol`.
1. **Grant check** — `authenticated` has `UPDATE (client_id, name, description, status, due_date, version)` on `cf_projects`; `workspace_id`/`created_by` are not in the list, so even trying to set them is a privilege error (42501) before any policy runs.
2. **USING policy** `cf_projects_update_staff` — `platform_is_staff(workspace_id, 'clientflow')` → `platform_has_role(...)` runs as SECURITY DEFINER with `search_path = ''`, reads `platform_members` for `auth.uid()` (never a caller-supplied id). Carol is staff of A → the row is visible for update.
3. **Triggers** — `cf_guard_tenant_columns` (workspace_id/created_by unchanged ✓), `cf_projects_bump_version` (version advanced by exactly one ✓), `platform_set_updated_at`.
4. **WITH CHECK** — the new row still has `workspace_id = A` and Carol is staff of A ✓.
5. **Composite FK** `cf_projects_client_same_workspace_fkey (workspace_id, client_id) → cf_clients(workspace_id, id)` — `(A, B-client)` has no match → **23503 foreign_key_violation**. The row never changes.
A plain `client_id → cf_clients(id)` FK would have accepted this because the B client exists and Carol can see it. pgTAP test: "carol: cannot re-point an A project at a B client via UPDATE".

### Why each mechanism exists (read the SQL comments too)
- **RLS enabled AND forced** on every table (`test 1`): forced means even the table owner is bound unless it is BYPASSRLS, so a future "run this as the migration role" shortcut cannot leak data.
- **Deny-by-default grants** first, then explicit `GRANT ... (columns)`. Anonymous users have no grants at all — the first pgTAP tests prove `anon` fails at the privilege level, not merely with zero rows.
- **`auth.uid()` only**: helpers never take a `user_id` argument. A function that accepted one would be an authorization bypass for anyone who can call it.
- **`platform_is_member`** exists because a policy on `platform_members` that queries `platform_members` recurses. Discovered by a test failure, fixed with a SECURITY DEFINER helper.
- **`platform_create_workspace`** is the only way a normal user gets a row into `platform_workspaces` (no INSERT policy). It serialises per caller with `pg_advisory_xact_lock` so two concurrent calls cannot both pass the quota check.
- **Version trigger**: the DAL will send `WHERE version = $expected`. Zero affected rows = conflict (same contract as `saveProject`'s `conflict` result in CF-01). The trigger stops anyone from "resetting" a version downward or forgetting to increment.
- **Generated types follow grants**: `TablesInsert<'platform_workspaces'>` is `never`; `TablesInsert<'cf_projects'>` has no `created_by`. TypeScript now refuses to compile a write that Postgres would reject with 42501.

### What the tests prove (and what they do not)
- Proven: schema shape, grants, policies, triggers and the composite FK for anon, a no-subject token, owner/admin/member/client roles, a removed member, a two-workspace member and a wrong-app owner. The tests run as the real roles via `SET ROLE` + `request.jwt.claim.sub` — the mechanism PostgREST uses — not as `postgres`.
- Mutation-checked: weakening one WITH CHECK to `true` fails four assertions; changing the schema without regenerating types fails `db:types:check`.
- **Not proven:** GoTrue sign-in, cookie handling, PostgREST parsing, storage policies, hosted configuration. Those are CF-03/CF-07/FINAL.

## Live project flow to learn at CF-04
Browser form → Zod → server action → verify user → validate client/workspace → user-scoped insert → RLS + composite FK → DTO → revalidation. Read the actual function at each step. If a future agent omits RLS from explanation, ask for direct API isolation tests.

## Interview prompts
**How does User A get blocked from Project B?** User JWT → membership check for project workspace/app → row policy; composite FK stops assigning foreign clients. UI filtering alone is not security.

**Why distinguish client-visible comments?** Internal notes may contain private pricing/team discussion. Visibility belongs in policy and DTO, not just a hidden tab.

**Why use a version column?** Two teammates load version 3; first saves version 4; second update expecting 3 fails with conflict, preventing silent overwrite. In CF-02 `cf_projects_bump_version` additionally rejects any UPDATE whose version is not `old + 1`.

**Why is RLS alone insufficient for referential integrity?** RLS decides which rows you may see or write; it does not check that two columns in one row belong to the same tenant. A member of two workspaces passes both policies. The composite FK `(workspace_id, client_id)` is the constraint that fails. Show `test 5` in `clientflow_rls.test.sql`.

**Why SECURITY DEFINER with `search_path = ''`?** The helper must read `platform_members` without recursing into its RLS; with a definer function the caller could otherwise plant a same-named object earlier in the search path and hijack the lookup. Empty search path + fully qualified names + revoke from public closes that.

**Why don't project status counts come from hardcoded cards?** They would become inconsistent after changes and misrepresent real workload; derive from authorized records and tested rules.

## Ownership exercises
1. Add an optional project reference (max 40 characters) through schema, form, DB migration, DTO and tests once live.
2. Add an overdue filter; define inclusive/exclusive date boundaries before coding.
3. Test a user belonging to two workspaces trying to attach one workspace's project to the other's client. (Done in CF-02 — read the Carol tests, then write the same case for `cf_tasks` when CF-05 adds it.)
3b. Break a policy on purpose (`with check (true)`), run `npm run db:test`, and explain each failing assertion. Restore with `npm run db:reset`.
4. Show a conflict and recover without losing draft text.
5. Explain why a valid signed URL may still work until expiry after a role removal; choose short expiry and document risk.

## Present this project
Show one client/project workflow, a client portal denied internal record, and a direct API/RLS test. Explain one bug fix from actual history. Until CF-08, present only verified milestone behavior, not the planned whole CRM.
