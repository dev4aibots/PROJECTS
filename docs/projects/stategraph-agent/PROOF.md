# StateGraph — Multi-Agent Research Orchestrator — Proof Ledger

## Current proof summary

| Claim/criterion | Status | Strongest evidence | Limitation |
|---|---|---|---|
| Product requirements understood | verified | `BRIEF.md` mapped to `03-project-2-stategraph-agents.md` | — |
| Primary flow (create → four agents → completion) | verified | `test_safe_run_and_events` (4 agent events recorded) | Deterministic local mode; no live LLM |
| Approval interrupt + idempotent decision | verified | `test_interrupt_approval_and_idempotency` | In-memory checkpoint; Postgres adapter is migration-only |
| Rejection never runs Writer | verified | `test_rejection_never_runs_writer` | — |
| Memory isolation + owner-only prune | verified | `test_memory_isolation_and_owner_prune` | Demo identities are not authentication |
| Resume no-op/404 semantics | verified | `test_missing_and_completed_resume` | — |
| Validation and unknown user | verified | `test_validation_and_unknown_user` | — |
| Build/test quality | verified | 6 backend tests pass; `tsc --noEmit` and `next build --webpack` pass | — |
| Deploy/demo | blocked | None | Requires owner Supabase/provider/Langfuse/Vercel |

## Verification entries

### 2026-08-10 13:24 UTC — Repository bootstrap

- Environment: Linux sandbox; git branch `genspark_ai_developer`.
- Procedure: inspected every supplied Markdown file and mapped requirements.
- Observed result: build specification exists; no application code at that time.

### 2026-08-10 17:32 UTC — Implementation milestone (commits eb8f9e3, 59963be, d061aa8)

- Implemented the resumable four-agent service (`backend/app/main.py`), six-scenario test suite, Next.js UI, migrations, and delivery docs.

### 2026-08-12 — Re-verification in fresh sandbox

- Environment: Linux sandbox, Python 3.x, pinned `requirements-dev.txt` installed.
- Procedure: `cd projects/stategraph-agent/backend && python -m pytest -q` → `6 passed in 0.64s`.
- Procedure: `cd projects/stategraph-agent/frontend && npm install && npm run typecheck && npm run build` → typecheck clean; Next 16.3.0 webpack production build succeeded (static `/` route).
- Proves: local orchestration, approval, rejection, idempotency, isolation, and validation behavior are reproducible from a clean checkout.
- Does not prove: live provider quality, hosted Postgres checkpointing, Langfuse traces, or deployment.

## Failure-path evidence

- Duplicate approval decision → `noop` (verified by test).
- Reject → task `rejected`, Writer never emits an event (verified by test).
- Resume of missing task → 404; resume of completed task → `noop` (verified by test).
- Short input / unknown user → 422 / 404 structured errors (verified by test).

## Deployment evidence

- Claimed URL: none.
- Post-deploy smoke: not run.
- Unverified services: Supabase, Groq, Gemini, Langfuse, Vercel — owner gate `P6-T4`.
