# ZeroTrust SQL — Secure Natural-Language Analytics — Proof Ledger

## Current proof summary

| Claim/criterion | Status | Strongest evidence | Limitation |
|---|---|---|---|
| Product requirements understood | verified | `BRIEF.md` mapped to `04-project-3-zerotrust-sql.md` | — |
| Primary flow (question → draft → validate → execute → audit) | verified | `test_api.py` happy path + `evals/run.py` 13/13 | Deterministic local generator; no live LLM |
| All 8 attack-lab prompts blocked | verified | `test_api.py::test_attack_lab_blocked` (parametrized, names the failing check) | — |
| 50-fixture corpus gate | verified | `test_security_corpus.py`: 25/25 malicious blocked, 25/25 safe allowed | Corpus is versioned but finite |
| LIMIT rewrite honesty | verified | million-row request → 100 rows + `limit_injected: true` (test + eval) | — |
| Decoy table defense in depth | verified | allowlist reject in validator AND `PermissionError` at execution layer (tests) | Local layer is SQLite `query_only`, not a real Postgres role |
| Read-only sandbox, timeout, determinism | verified | `test_database.py` | 5 s timeout tested via progress handler |
| Failure paths hide internals | verified | `test_api.py`: 503 on generator/db outage, no host leak, still audited | Audit log is process-memory locally |
| Build/test quality | verified | 57 backend tests pass; `tsc --noEmit` and `next build --webpack` pass | — |
| Deploy/demo | blocked | None | Requires owner Supabase/provider/Vercel |

## Verification entries

### 2026-08-10 13:24 UTC — Repository bootstrap

- Requirements mapped from the specification; no application code existed.

### 2026-08-12 — Implementation milestone (commits f3f1133, 1ec619c, and this session)

- Environment: Linux sandbox, Python 3.13, sqlglot 30.16.0, pinned `requirements-dev.txt`.
- Procedure: `cd projects/zerotrust-sql && PYTHONPATH=backend python -m pytest -q backend/tests` → `57 passed`.
- Procedure: `PYTHONPATH=backend python evals/run.py` → `execution_accuracy: 13/13` (includes one honest refusal: churn prediction is unanswerable and returns 503, counted as PASS).
- Procedure: corpus spot-check script → `safe allowed 25/25, malicious blocked 25/25`.
- Procedure: `cd frontend && npm install && npm run typecheck && npm run build` → typecheck clean; Next 16.3.0 webpack production build succeeded (static `/` route).
- Proves: the validation pipeline, sandbox guarantees, attack lab, evals, and UI build are reproducible from a clean checkout with zero secrets.
- Does not prove: live Groq/Gemini generation quality, the hosted Postgres `nl_query_ro` role, Langfuse traces, or deployment.

## Failure-path evidence

- Unparseable / multi-statement / non-SELECT / unknown-table / unknown-column / disallowed-function SQL → 400 with the failing check named (verified by tests).
- Generator down → 503 "SQL generation is unavailable; the request was audited" (verified).
- Database down → 503 with no internal hostname leak; request still audited (verified).
- Empty or >500-char question → 422 structured error (verified).

## Deployment evidence

- Claimed URL: none.
- Post-deploy smoke: not run.
- Unverified services: Supabase, Groq, Gemini, Langfuse, Vercel — owner gate `P6-T4`.
