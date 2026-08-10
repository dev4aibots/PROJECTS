# Repository Resume — start here every session

Updated: `2026-08-10 16:10 UTC`
Branch/commit: `genspark_ai_developer @ pending final DocuMind handoff commit`
Working tree: `expected clean after final handoff commit; verify with git status`

## Current state

- Active project: `stategraph-agent`
- Project folder: `projects/stategraph-agent`
- Current milestone: `Phase 0 — plan and contracts`
- Current checklist item: `P0-T1`
- Item state: `ready`

## Resume now

1. Read `../AGENTS.md` and `PROJECTS.md`.
2. Read `projects/stategraph-agent/BRIEF.md`, `CHECKLIST.md`, `RESUME.md`, and `PROOF.md`.
3. Run `cd /home/user/webapp && git status --short --branch`.
4. Read `../03-project-2-stategraph-agents.md` and the relevant shared constraints in `../01-master-context.md`.
5. Create a plan-only `../projects/stategraph-agent/PLAN.md`; do not write application code until Phase 0 contracts and gates are explicit.

## What changed last

- DocuMind's initial audit high findings were remediated: session-scoped MCP search, mounted Streamable HTTP MCP, citation FK `SET NULL`, and configurable frontend CORS.
- Added focused tests, a full all-tools MCP smoke script, and patched Vitest to 3.2.7 after a critical dev advisory.
- Added portfolio README, decisions, RAG pipeline, MCP, limitations, and demo documentation.
- Final local checks observed 135 backend tests passing, 3 frontend tests passing, typecheck/build passing, dependency audit clean, MCP smoke passing, and the frozen 15-case evaluation unchanged.
- DocuMind now has zero open critical/high local findings and is blocked only at owner-managed live integration/deployment.
- Activated StateGraph as the next independent core project.

## Important constraints and traps

- Keep exactly one project active.
- Do not count local deterministic DocuMind tests as Supabase, Gemini, Groq, Langfuse, Vercel, or live MCP proof.
- Do not modify DocuMind further unless evidence reveals a defect or credentials unblock `P6-T4`.
- StateGraph Phase 0 is plan-only and must preserve checkpoint, approval, resume-idempotency, and memory-isolation requirements.

## Blockers requiring action

- `documind-rag-mcp/P6-T4`: owner/cloud holder must provide and authorize Supabase, Gemini/Groq, Langfuse, and Vercel setup. Apply migrations 001–005 and run the documented live smoke before changing status.
- No blocker prevents StateGraph Phase 0 or local implementation.

## Last verification

| Command/procedure | Result | When |
|---|---|---|
| DocuMind backend pytest | 135 passed; one third-party warning | 2026-08-10 16:07 UTC |
| DocuMind frozen evaluation | all four deterministic metrics 100% on 15 authored cases | 2026-08-10 16:07 UTC |
| Frontend test/typecheck/build | 3 tests, typecheck, Next 16.3.0 webpack build passed | 2026-08-10 16:07 UTC |
| Full npm audit after Vitest patch | 0 vulnerabilities | 2026-08-10 16:09 UTC |
| MCP local protocol smoke | all four tools and cross-session denial verified | 2026-08-10 16:09 UTC |

## Handoff integrity check

- [x] `PROJECTS.md` names exactly one active project
- [x] active project `RESUME.md` names the same next task
- [x] DocuMind checklist/proof/audit match observed local and blocked external state
- [x] no deployment, provider, trace, screenshot, or public URL was fabricated
- [x] no secret or personal data appears in state docs
