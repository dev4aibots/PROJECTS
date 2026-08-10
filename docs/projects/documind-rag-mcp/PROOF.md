# DocuMind — Enterprise RAG + MCP — Proof Ledger

## Current proof summary

| Claim/criterion | Status | Strongest evidence | Limitation |
|---|---|---|---|
| Requirements and architecture | verified | `PLAN.md`, `DECISIONS.md`, `README.md` | Live topology unverified |
| Persistence/domain/services | verified locally | 135-test backend suite and migrations 001–005 | Supabase migrations not applied externally |
| REST and MCP primary flow | verified locally | API tests, MCP mount tests, `scripts/test_mcp.py` | No public serverless smoke |
| Failure/security behavior | verified locally | PDF, provider, screening, citation, isolation, refusal tests | Demo sessions are not production authentication |
| Evaluation | verified offline | `evals/golden.jsonl`, `evals/run.py`, `docs/evaluation.md` | Deterministic providers/support judge only |
| Frontend quality | verified locally | Vitest, typecheck, Next production build, dependency audit | `/app`/permanent third-panel spec deviation accepted |
| Deploy/demo | blocked | Two-project setup and demo script documented | No credentials, trace, URL, or screenshots |

## 2026-08-10 16:10 UTC — Final local remediation verification

- **Environment:** Linux sandbox; Python 3.13 runtime; Node/npm lockfile install; no provider or cloud credentials.
- **Backend command:** `cd projects/documind-rag-mcp/backend && python -m pytest -q`.
- **Observed:** 135 passed in 2.88s; one `pydantic_settings` warning caused no startup/test failure.
- **MCP procedure:** ran Uvicorn locally and `python scripts/test_mcp.py`.
- **Observed:** tool discovery returned `ask_question`, `get_conversation`, `list_documents`, and `search_documents`; all invoked successfully; grounded answer true; cross-session history call returned an MCP error.
- **Evaluation command:** `python evals/run.py`.
- **Observed:** 15 frozen fictional cases; retrieval hit 100% on 10 answerable cases, offline faithfulness 100% on 15, citation accuracy 100% on 15, refusal correctness 100% on 5 unanswerable cases.
- **Frontend procedure:** `npm ci`, `npm test`, `npm run typecheck`, `npm run build`, `npm audit`.
- **Observed:** 3 Vitest tests passed; typecheck passed; production build compiled and generated static routes; initial audit exposed critical Vitest advisory GHSA-5xrq-8626-4rwp; patched to 3.2.7; rerun full audit found 0 vulnerabilities.
- **Static checks:** MCP script compiled; migration 005 contains `ON DELETE SET NULL`; text diff check passed.

## Failure-path evidence

| Boundary | Evidence |
|---|---|
| Corrupt/encrypted/empty/spoofed PDF | PDF unit and document/API tests |
| Embedding failure and resumable idempotency | document service tests |
| No evidence means no model call | chat service and API tests |
| Prompt injection | screening and search tests |
| Invalid model citations/malformed output | citation and chat service tests |
| Rate limit, timeout, fallback, both down | resilient provider tests |
| Session isolation | repository, API, MCP facade, search, and MCP smoke tests |
| MCP routing and protocol errors | `test_mcp_mount.py` and `scripts/test_mcp.py` |
| Unsafe dependency version | audit discovery, Vitest 3.2.7 lockfile, clean rerun |

## Audit conclusion

`../../../projects/documind-rag-mcp/AUDIT.md` records every initial high/medium/low finding and its disposition. No critical/high local finding remains open. One UI route/layout deviation is accepted and the offline-judge limitation is explicit.

## Deployment evidence

- Claimed live URL: none.
- Supabase/provider/Langfuse/Vercel proof: none.
- Post-deploy REST/UI/MCP smoke: not run.
- Terminal state: blocked specifically at owner-managed live integration and deployment, not represented as complete.
