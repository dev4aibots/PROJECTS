# DocuMind Adversarial Audit

Audit date: 2026-08-10
Scope: local implementation on `genspark_ai_developer`; external providers and deployment were intentionally not exercised without owner credentials.

## Findings and disposition

| Severity | Location | Finding | Remediation / disposition | Status |
|---|---|---|---|---|
| HIGH | `backend/app/mcp_server.py` | Required `search_documents` MCP tool was absent. | Added session-scoped `ChatService.search`, facade/tool registration, service tests, mount contract test, and full MCP smoke. | Fixed and verified |
| HIGH | `backend/app/main.py`, `api/index.py` | MCP was standalone and unreachable through the deployed ASGI entrypoint. | Mounted the official SDK Streamable HTTP app at `/mcp`, shared one container, and managed its session lifecycle in FastAPI lifespan. | Fixed locally; live Vercel smoke blocked |
| HIGH | migrations 001/004 | Citation history claimed to survive source deletion but the original chunk FK cascaded. | Added append-only migration 005 replacing the FK with `ON DELETE SET NULL`; migration remains unapplied to an external DB. | Fixed in schema; live migration blocked |
| HIGH | `backend/app/main.py` | Fixed localhost-only CORS blocked a separately deployed frontend. | Added validated `FRONTEND_ORIGIN`, retained local origins, and covered valid/invalid/duplicate cases. | Fixed and verified |
| MEDIUM | project root/docs | Portfolio README, decisions, pipeline, MCP, limitations, and demo docs were absent. | Added all required documents with truthful local proof and explicit external gates. | Fixed |
| MEDIUM | `frontend/app/page.tsx` | Workspace is at `/#workspace`, not `/app`, and sources are inline instead of a permanent third panel. | Core inspect flow works; deviation is visible in README/demo and retained as a bounded UI improvement. | Accepted for local milestone |
| MEDIUM | `vercel.json`, `frontend/` | Backend/frontend need separate Vercel roots; topology was undocumented. | Documented two-project setup, added `/mcp` rewrites, added frontend CORS setting. | Configured/documented; live smoke blocked |
| CRITICAL | `frontend/package.json` | Final full dependency audit found vulnerable Vitest `<3.2.6`. | Upgraded direct dev dependency to `3.2.7`; reran tests and full audit. | Fixed and verified |
| LOW | `evals/run.py` | Offline faithfulness is a deterministic support judge, not an independent live LLM judge. | Metric label and limitations are explicit; credentialed evaluation remains a deployment gate. | Accepted |

## Final local verification

| Check | Observed result |
|---|---|
| Backend | `python -m pytest -q` → **135 passed**, one third-party `pydantic_settings` warning |
| MCP protocol | `python scripts/test_mcp.py` → all four tools invoked; grounded answer and cross-session denial verified |
| Evaluation | Frozen 15 cases: retrieval hit 100% (10), offline faithfulness 100% (15), citation accuracy 100% (15), refusal correctness 100% (5) |
| Frontend tests | Vitest 3.2.7 → **3 passed** |
| TypeScript | `npm run typecheck` → passed |
| Production build | Next.js 16.3.0 webpack build → passed; static `/` and `/_not-found` generated |
| Dependency audit | `npm audit` after Vitest patch → **0 vulnerabilities** |
| Formatting/static checks | MCP script compiles; migration contains `ON DELETE SET NULL`; text diff check passed |

The backend warning originates from MCP/Pydantic settings introspection of the ASGI lifespan annotation; no test or startup failure was observed.

## Trace conclusions

- **Ingest:** validated PDF → stored repository object → bounded page extraction/chunking/embedding → idempotent upsert → cursor/progress/status is exercised by service and API tests.
- **Ask:** screening → embedding → scoped retrieval → shaping/evidence gate → provider → citation validator → durable messages/retrieval log is exercised end to end locally.
- **Inspect:** REST history/retrieval APIs and frontend source cards use persisted validated citation data.
- **MCP:** mounted `/mcp` lists and invokes `list_documents`, `search_documents`, `ask_question`, and `get_conversation` over the shared services.
- **Isolation:** document, conversation, search, API, and MCP checks deny a different session.

## Remaining external blocker

No live Supabase migration/storage operation, Gemini embedding, Groq/Gemini generation, Langfuse trace, Vercel route, CORS exchange, public UI, or post-deploy MCP call has been observed. Completion of the deployment gate requires owner-managed credentials/projects, applying migrations 001–005, then smoke-testing the two-project topology. These items are not claimed by local deterministic proof.

## Completion judgment

- Open critical/high local findings: **0**.
- Local implementation/documentation milestone: **verified**.
- Project terminal status: **BLOCKED at live deployment/smoke**, with safe local work exhausted for the accepted milestone.
