# StateGraph Agent — proof ledger

## Current evidence

| Claim | Status | Evidence | Limitation |
|---|---|---|---|
| Real LangGraph topology | verified locally | `backend/app/graph.py`; API and checkpoint tests | Hosted process restart pending |
| Human interrupt/resume | verified locally | `interrupt()`, `Command(resume=...)`, approval/rejection tests | No hosted database contacted |
| Durable checkpoint factory | contract-verified | `GraphRuntime`; setup/lifecycle and reconstructed-graph tests | Shared-memory test is not process-A/process-B Postgres proof |
| Durable API projections | implemented/locally tested | `repository.py`, migrations 002–004, API suite | SQL paths need disposable-Postgres execution |
| Database authorization | source/contract verified | forced RLS policies; least-privilege role; transaction-local subject binding; session preamble tests | Real Supabase token/RLS execution pending |
| One approval winner | verified locally + integration harness | 8-thread local race; Postgres compare-and-set; credential-gated database race test | Harness skipped without disposable Postgres |
| Typed live agents/search | contract-verified | Groq/Gemini router, Tavily adapter, Pydantic outputs | No credentials/live quality evidence |
| Citation boundary | verified locally | source allowlist, malicious-citation test, `stategraph-heldout-v1` | Live supportedness/model-quality eval pending |
| Verified identity | contract-verified | JWKS verifier; signed RS256 issuer/audience/expiry/subject tests | No real Supabase token used |
| Owner isolation | verified locally | cross-user task/event/resume/approval/memory denial tests | Hosted RLS/database proof pending |
| Privacy-safe memory | verified locally | explicit `remember`; provenance; 90-day expiry; owner list/delete/export | No hosted retention job or export UX |
| Frontend delivery | verified locally | Supabase magic-link flow; typecheck/build; 4 Chromium E2E scenarios; production audit | No public URL or hosted identity proof |
| Deployment | unverified | none | owner cloud resources absent |

## 2026-08-14 verification

Backend:

```bash
APP_MODE=local AUTH_MODE=local PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests
```

Observed on the final local gate: `34 passed, 1 skipped in 1.54s`. Coverage includes graph completion, interrupt/rejection, duplicate and concurrent decisions, terminal cancellation, checkpointer lifecycle, reconstructed resume, typed agents/search, provider fallback, citation allowlisting, signed JWT validation, identity derivation, cross-user denial, opt-in memory export/expiry, request-correlation privacy, preflight validation, and RLS role/subject session binding. The skipped test is the explicitly credential-gated disposable-Postgres integration.

Frontend:

```bash
npm ci
npm run typecheck
npm run build
npm audit --omit=dev --audit-level=high
```

Observed: TypeScript and Next 16.3.0 webpack build passed; four Chromium E2E scenarios passed; production audit found zero vulnerabilities. The E2E suite covers approval/completion/reload/memory deletion, cancellation, rejection without Writer and 375px mobile overflow. The frontend uses explicit demo headers only without Supabase configuration; with public Supabase settings it sends the authenticated session bearer token.

Evaluation and delivery:

```bash
APP_MODE=local AUTH_MODE=local PYTHONPATH=backend .venv/bin/python evals/run.py
APP_MODE=local AUTH_MODE=local .venv/bin/python scripts/preflight.py
```

Observed: `stategraph-heldout-v1` routing accuracy `1.0` and citation-policy accuracy `1.0` met their `1.0` thresholds; local configuration preflight passed. `scripts/live_smoke.py` is present and help-parsed, but was not run against a hosted URL.

New implementation evidence:

- `backend/app/auth.py`: asymmetric JWKS verification with required issuer, audience, expiry, issue time, UUID subject and bearer challenge behavior.
- `backend/app/main.py`: identity-derived ownership; no public command accepts authoritative `user_id`.
- `backend/app/repository.py`: owner-filtered task/memory operations and atomic owner-filtered approval claims.
- `migrations/003_authenticated_ownership.sql`: opt-in task memory, memory expiry and owner-query indexes.
- `migrations/004_database_authorization.sql`: forced RLS policies for every projection table plus least-privilege `stategraph_api` grants.
- `backend/app/repository.py`: every live transaction assumes `stategraph_api` and binds the verified subject through `set_config(..., true)`.
- `backend/tests/test_auth.py`, `test_stategraph.py`, and `test_repository_rls.py`: signed-token failure cases, cross-tenant denial and database-session binding.
- `backend/tests/test_postgres_integration.py`: owner-gated process restart, two-owner isolation and concurrent decision proof.
- `frontend/app/page.tsx`: Supabase magic-link/session integration and explicit memory consent.

## Truth boundary and next proof

This does not prove hosted Postgres durability, real Supabase JWT/RLS behavior, live search/model quality, provider token/cost tracing or deployment. The project is credential-free source complete and blocked only on owner integration: run the prepared database suite against disposable pgvector Postgres, verify two real Supabase users, deploy, execute the authenticated smoke, and capture live telemetry/media.
