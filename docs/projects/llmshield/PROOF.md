# LLMShield — Proof Ledger

## Current proof summary

| Claim/criterion | Status | Strongest evidence | Limitation |
|---|---|---|---|
| Primary guarded flow | verified locally | 17 backend tests; clean and redacted API tests | deterministic provider is not live model proof |
| Security/failure behavior | verified locally | provider short-circuit, fallback, 503/502, truncation, telemetry outage tests | heuristic scope only |
| Evaluation | verified locally | frozen 40 cases; both guards P=1.00, R=1.00, FPR=0.00 | bounded fixture, not production traffic |
| Frontend delivery | verified locally | TypeScript and Next production build pass | no deployed URL |
| Persistence/trace adapters | implementation verified | migration, repository and fail-open sink tests | hosted Postgres/Langfuse unverified |
| Deploy/demo | blocked externally | `scripts/live_smoke.py` and demo plan ready | owner credentials/resources required |

## 2026-08-12 local completion verification

- Environment: Linux sandbox, Python 3.13 runtime for local proof, dependency pins target the documented application stack.
- `PYTHONPATH=backend pytest -q backend/tests` → `17 passed in 0.57s`.
- `python evals/run.py` → 40 unique cases; injection `15/0/0/25`, PII `10/0/0/30`.
- `npm run typecheck` → passed.
- `npm run build` → compiled, typechecked, and generated `/` plus `/app`.
- Repository audit also reran every other project's backend tests, evaluations, and frontend build successfully.

## Failure-path evidence

- Blocked requests do not invoke the provider.
- Groq-like primary failure selects fallback; both failures return structured `503` and log an error.
- Empty output returns controlled `502`; oversized output truncates with `truncated=true`; output PII is redacted.
- Langfuse sink failure logs a warning and the gateway still succeeds.
- Invalid request and log-limit fields return `422`.

## Deployment evidence

- Claimed URL: none.
- Post-deploy smoke: not run.
- Exact command after owner deploy: `python scripts/live_smoke.py https://<api-host>`.
- Unverified services: Groq, Gemini, Postgres/Supabase, Langfuse, Vercel/hosting.
