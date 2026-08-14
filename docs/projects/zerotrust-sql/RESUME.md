# ZeroTrust SQL — Secure Natural-Language Analytics — Session Resume

Updated: `2026-08-12`
Project folder: `projects/zerotrust-sql`
State: `BLOCKED — owner deployment only`

## Exact current position

All credential-free implementation gates are complete. The project includes schema-aware generation boundaries, SQLGlot AST validation, table/function allowlists, LIMIT rewriting, read-only deterministic execution, attack lab, audit records, API/UI, migration, golden evaluation, versioned security corpus, deployment smoke script, docs, and audit.

## Verification

```text
PYTHONPATH=backend pytest -q backend/tests  → 57 passed
PYTHONPATH=backend python evals/run.py       → 13/13 execution accuracy
security corpus                              → 25/25 safe allowed; 25/25 malicious blocked
frontend npm run typecheck                   → passed
frontend npm run build                       → passed
```

## Owner resume steps

1. Create hosted Postgres/Supabase and apply `migrations/001_zerotrust.sql` with the documented restricted execution role.
2. Configure live provider credentials and validate Groq-to-Gemini behavior without weakening AST enforcement.
3. Configure optional Langfuse and production CORS/API URLs.
4. Deploy backend/frontend and run `python scripts/live_smoke.py https://<api-host>`.
5. Prove the database role rejects direct writes/forbidden reads even if application validation is bypassed.
6. Capture one legitimate aggregate query, one blocked attack, audit evidence, and only observed deployment/trace URLs.

## Blocker

Hosted database/provider/tracing/deployment resources and credentials are owner-managed. The deterministic SQLite/provider suite proves local policy behavior, not hosted least-privilege or live-model availability.

No secrets or live-service success are recorded in repository files.
