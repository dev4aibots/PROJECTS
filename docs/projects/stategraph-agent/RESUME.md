# StateGraph Agent — session resume

Updated: 2026-08-14
Branch: `genspark_ai_developer`

## Exact position

- Status: `BLOCKED — owner integration only`.
- P3 source includes LangGraph/PostgresSaver lifecycle plus local/Postgres projection repositories and atomic approval claim.
- P4 includes typed fixture/live services, Tavily HTTPS search, Groq/Gemini structured generation with retry/fallback, and citation allowlisting.
- P5 application layer now verifies Supabase JWT contracts, derives identity from claims, filters every exposed record path by owner, and makes memory explicitly opt-in with provenance, 90-day expiry, delete and export.
- Frontend supports local demo identities only when Supabase public settings are absent; configured deployments use magic-link sessions and bearer tokens.
- P5 database authorization now has migration 004 forced RLS, least-privilege `stategraph_api`, and transaction-local verified-subject binding.
- Credential-gated Postgres integration covers process-A/process-B resume, two-owner isolation and one-winner approval race.
- Last observed: 34 backend tests passed and 1 credential-gated Postgres test skipped; held-out routing/citation metrics were 1.0/1.0; four Chromium E2E scenarios, frontend typecheck/build and production audit passed.
- Refresh/reconnect, retry/cancel, evidence cards, memory delete/export, request correlation, preflight and authenticated live-smoke paths are implemented.
- Cancellation is terminal at both repository implementations: a stale pending approval cannot resume a canceled graph.
- No hosted database/provider/search integration or public deployment is claimed.

## Resume now

1. No credential-free source task remains; keep this project terminal while another project is active.
2. When owner resources are available, set `STATEGRAPH_TEST_DATABASE_URL` to disposable pgvector Postgres and run `backend/tests/test_postgres_integration.py`.
3. Apply migrations 001–004 and verify two real Supabase users/JWTs against forced RLS before exposing traffic.
4. Run `APP_MODE=live AUTH_MODE=live python scripts/preflight.py`, deploy, then execute `python scripts/live_smoke.py <base-url>` with a disposable owner token.
5. Capture live provider fallback, token/cost/latency trace, screenshots and demo evidence without storing credentials.

## Verification commands

```bash
cd /home/user/webapp/projects/stategraph-agent
APP_MODE=local AUTH_MODE=local PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests
cd frontend
npm ci
npm run typecheck
npm run build
npm audit --omit=dev --audit-level=high
```

## Required live configuration

- Backend: `APP_MODE=live`, `AUTH_MODE=live`, `DATABASE_URL`, `SUPABASE_JWT_ISSUER`, optional audience/JWKS override, provider/search keys and strict CORS origin.
- Frontend: API URL, `NEXT_PUBLIC_SUPABASE_URL`, and public anon key. Never place a service-role key in browser variables.
- Apply migrations 001–004 before readiness or traffic. Migration 004 grants a transaction-scoped API role; `DATABASE_URL` must belong to a login allowed to `SET ROLE stategraph_api`.

## Traps

- A skipped Postgres integration harness is not hosted proof; do not mark P3 live until migrations and process restart execute against disposable/hosted Postgres.
- RLS policy/source tests and signed-token unit tests are not real Supabase JWT/RLS proof.
- Local demo headers are accepted only in `AUTH_MODE=local`; never deploy that mode publicly.
- Memory creation defaults off. Do not reintroduce inferred or silent long-term memory.
- Provider/search content is untrusted; preserve HTTPS/content bounds and citation allowlisting.
- No credentials belong in source, tests, proof or resume files.
