# LLMShield — Security and Observability Gateway — Session Resume

Updated: `2026-08-12`
Project folder: `projects/llmshield`
State: `BLOCKED — owner deployment only`

## Exact current position

All credential-free implementation gates are complete. Typed contracts, layered guards, deterministic/live provider adapters, fallback, output checks, fail-open trace ingestion, memory/Postgres repositories, API, UI, migration, corpus, smoke script, docs, and audit exist and pass locally.

## Verification

```text
PYTHONPATH=backend pytest -q backend/tests  → 17 passed
python evals/run.py                         → 40/40 evaluated; no fixture FP/FN
frontend npm run typecheck                  → passed
frontend npm run build                      → passed
```

## Owner resume steps

1. Apply `migrations/001_llmshield.sql` to owner Postgres/Supabase and set `DATABASE_URL`.
2. Set `PROVIDER_MODE=live` plus Groq/Gemini key(s); optionally configure Langfuse.
3. Set production CORS/API URLs and deploy API/frontend.
4. Run `python scripts/live_smoke.py https://<api-host>`.
5. Force one fallback, inspect the matching Langfuse trace, and capture demo screenshots.
6. Add only observed URLs/results to this proof ledger.

No secrets or live-service success are recorded in repository files.
