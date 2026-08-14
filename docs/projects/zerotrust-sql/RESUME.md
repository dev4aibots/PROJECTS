# ZeroTrust SQL — Secure Natural-Language Analytics — Session Resume

Updated: `2026-08-14`
Project folder: `projects/zerotrust-sql`
State: `BLOCKED — owner deployment only`

## Exact current position

All credential-free implementation gates are complete. The project includes schema-aware generation boundaries, scope-aware SQLGlot lineage validation, table/function allowlists, LIMIT rewriting, read-only deterministic execution, scoped bearer auth, privacy-safe durable audit, distributed rate limits, request correlation, attack lab, four browser E2E scenarios, ordered migrations, preflight/live smoke, golden evaluation, versioned security corpus, docs, and audit.

## Verification

```text
PYTHONPATH=backend pytest -q backend/tests  → 78 passed
PYTHONPATH=backend python evals/run.py       → 13/13 execution accuracy
security corpus                              → 25/25 safe allowed; 25/25 malicious blocked
frontend npm run typecheck/build             → passed
frontend npm audit --omit=dev                 → 0 vulnerabilities
frontend npm run test:e2e                     → 4 Chromium scenarios passed
```

## Owner resume steps

1. Create hosted Postgres/Supabase, apply migrations `001` through `004`, and grant the server login membership in `nl_query_ro`, `nl_audit_writer`, and `nl_rate_limiter`.
2. Configure live provider credentials and validate Groq-to-Gemini behavior without weakening AST enforcement.
3. Configure optional Langfuse and production CORS/API URLs.
4. Run `python scripts/preflight.py`, deploy backend/frontend, and run the authenticated `python scripts/live_smoke.py https://<api-host>`.
5. Prove the database role rejects direct writes/forbidden reads even if application validation is bypassed.
6. Capture one legitimate aggregate query, one blocked attack, audit evidence, and only observed deployment/trace URLs.

## Blocker

Hosted database/provider/tracing/deployment resources and credentials are owner-managed. The deterministic SQLite/provider suite proves local policy behavior, not hosted least-privilege or live-model availability.

No secrets or live-service success are recorded in repository files.
