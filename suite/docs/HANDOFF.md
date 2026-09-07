# Handoff

Updated: 2026-09-07. Active task: **DOCS** (verification before CF-01).

## Exact next action
Run `node suite/scripts/verify-state.mjs` and `node --test suite/scripts/verify-state.test.mjs`. If both pass, mark DOCS verified and claim CF-01. Implement the bounded project workbench per its PRD and file ledger.

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
