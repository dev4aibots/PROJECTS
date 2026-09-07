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

## Live project flow to learn at CF-04
Browser form → Zod → server action → verify user → validate client/workspace → user-scoped insert → RLS + composite FK → DTO → revalidation. Read the actual function at each step. If a future agent omits RLS from explanation, ask for direct API isolation tests.

## Interview prompts
**How does User A get blocked from Project B?** User JWT → membership check for project workspace/app → row policy; composite FK stops assigning foreign clients. UI filtering alone is not security.

**Why distinguish client-visible comments?** Internal notes may contain private pricing/team discussion. Visibility belongs in policy and DTO, not just a hidden tab.

**Why use a version column?** Two teammates load version 3; first saves version 4; second update expecting 3 fails with conflict, preventing silent overwrite.

**Why don't project status counts come from hardcoded cards?** They would become inconsistent after changes and misrepresent real workload; derive from authorized records and tested rules.

## Ownership exercises
1. Add an optional project reference (max 40 characters) through schema, form, DB migration, DTO and tests once live.
2. Add an overdue filter; define inclusive/exclusive date boundaries before coding.
3. Test a user belonging to two workspaces trying to attach one workspace's project to the other's client.
4. Show a conflict and recover without losing draft text.
5. Explain why a valid signed URL may still work until expiry after a role removal; choose short expiry and document risk.

## Present this project
Show one client/project workflow, a client portal denied internal record, and a direct API/RLS test. Explain one bug fix from actual history. Until CF-08, present only verified milestone behavior, not the planned whole CRM.
