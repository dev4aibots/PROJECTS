# DocuExtract — Verified Invoice Intelligence — Session Resume

Updated: `2026-08-14`
Project folder: `projects/docuextract`
State: `BLOCKED — owner integration/deployment only`

## Exact current position

All credential-free implementation gates are complete: verified local/live identity modes, owner-scoped memory/Postgres repositories, private memory/Supabase object-storage adapters, decoded upload validation and five-page policy, actual-byte Gemini structured extraction with one bounded correction attempt, Decimal verification, atomic processing claim, migrations/RLS, API/UI, preflight/live-smoke scripts, generated sample corpus, and local audit. Identity changes clear prior-owner UI state immediately, and private API responses are explicitly non-cacheable.

## Verification

```text
PYTHONPATH=backend:. .venv/bin/pytest -q backend/tests  → 43 passed, 1 credential-gated Postgres integration skipped
PYTHONPATH=backend:. .venv/bin/python evals/run.py       → 5/5 expected verdicts
CORS_ORIGINS=http://localhost:3000 ... scripts/preflight.py → passed
frontend npm run typecheck && npm run build              → passed
frontend npm audit --omit=dev --audit-level=high         → 0 production vulnerabilities
```

## Owner resume steps

1. Create disposable owner Supabase/Postgres/private Storage resources and apply `migrations/001_docuextract.sql` then `002_authenticated_persistence.sql`.
2. Configure the documented live modes, exact production CORS/API URLs, Gemini key/model, and optional Langfuse settings.
3. Run the credential-gated Postgres test and `scripts/live_smoke.py` with a real disposable invoice and Supabase access token.
4. Exercise one malformed-output correction, five-page acceptance/six-page refusal, cross-owner denial, provider outage, storage failure, and deployment restart.
5. Capture screenshots/traces and add only observed URLs/results to `PROOF.md`.

## Blocker

Gemini, Supabase/Postgres/private Storage, Langfuse, and deployment resources/credentials are owner-managed and unavailable. Local contract tests and deterministic fixtures do not prove live multimodal accuracy, RLS/storage behavior, provider latency/cost, or hosted reliability.

No secrets or live-service success are recorded in repository files.
