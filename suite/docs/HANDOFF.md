# Handoff

Updated: 2026-09-07. Active task: **CF-01**.

## Exact next action
Implement the CF-01 paths in `suite/docs/projects/clientflow/FILES.md`. Acceptance: immutable validated sample project creation/editing, optimistic version guard, date-safe metrics, URL filters/table/board/pagination, responsive native forms, honest memory-only boundary. Run lint, typecheck, domain tests, build, browser flows and axe before verification.

## Feature plan
- No additional product scope. Existing file ledger is the implementation plan.
- Dependencies: pinned Next 16 / React 19, TypeScript strict, Zod, Tailwind 4, Phosphor icons, Vitest, Playwright and axe. Node 22.
- Pure domain first, then shared in-memory provider, form and workbench routes. No remote API or auth simulation.
- Invalid/stale/missing records return explicit errors; draft text is retained. Date-only comparisons use a fixed synthetic reference day, not host timezone.
- New project creation disabled during submission; mutation reads latest ref so repeated/stale updates do not overwrite prior changes.


## Current reality
- Only ClientFlow, SupportDesk AI and InvoiceHub are in scope. All seven legacy apps, their hub, root docs and Vercel config were removed at the owner's explicit request.
- GitHub checkpoint `7dff9c0` and the uploaded archive agree: specifications exist; no new application yet.
- Local previous tracked code is preserved on `archive/local-before-three-projects-2026-09-07`; untracked DuraSupport was moved to `.git/pre-scope-durable-support`. Recovery only, not part of the portable deliverable.
- Node 22/npm 10 available. Docker executable absent: local Supabase verification will need a suitable runtime at CF-02; do not substitute mocked RLS.
- No hosted credentials or deployment used.

## Git
Branch `genspark_ai_developer`, PR https://github.com/dev4aibots/PROJECTS/pull/2.

## Boundaries
Supabase free-tier quotas and Vercel non-commercial terms are documented in RESEARCH. Browser memory proves interaction only, not persistence/security. Complete ClientFlow before scaffolding the next product.
