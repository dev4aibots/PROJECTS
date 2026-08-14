# DocuMind — Enterprise RAG + MCP — Session Resume

Updated: `2026-08-10 16:10 UTC`
Project folder: `projects/documind-rag-mcp`
Branch/commit: `genspark_ai_developer @ pending final handoff commit`
Working tree: `remediation and portfolio updates pending final commit`

## Exact current position

- Milestone: `Phase 6 delivery`
- Checklist item: `P6-T4 — live deployment and smoke`
- State: `BLOCKED on owner-managed external services`
- Acceptance remaining: apply migrations to Supabase; configure live providers/Langfuse; deploy backend and frontend roots; smoke REST, UI, MCP, CORS, storage, refusal, fallback, deletion, and traces.

## Verified local outcome

- Shared service layer powers REST and four mounted Streamable HTTP MCP tools.
- Append-only migration 005 preserves self-contained citation history with a nullable source-chunk relation.
- Configurable deployed frontend CORS origin is covered by focused tests.
- Backend: 135 passed; full MCP smoke passed, including cross-session denial.
- Evaluation: 15 frozen cases; all four local deterministic metrics reported 100%, with methodology limits explicit.
- Frontend: 3 tests, typecheck, production build, and full dependency audit passed; Vitest advisory fixed at 3.2.7.
- Adversarial audit: zero open critical/high local findings; route/UI deviation remains an accepted medium limitation.
- README, decisions, RAG pipeline, MCP, limitations, audit, and demo script now match current behavior.

## Resume commands for deployment

```bash
cd /home/user/webapp/projects/documind-rag-mcp
git status --short --branch
cat docs/limitations.md
cat docs/mcp.md
cat AUDIT.md
```

Then obtain owner approval/credentials, apply `migrations/001` through `005`, deploy the backend root and `frontend/` root separately, set `FRONTEND_ORIGIN` and `NEXT_PUBLIC_API_BASE_URL`, and rerun live smoke checks. Never convert local deterministic proof into a live-provider claim.

## Last verification

| Command | Result |
|---|---|
| `cd backend && python -m pytest -q` | 135 passed, one third-party warning |
| `python evals/run.py` | 15 cases; retrieval 100%, offline faithfulness 100%, citations 100%, refusals 100% |
| `npm test` | 3 passed with Vitest 3.2.7 |
| `npm run typecheck` | passed |
| `npm run build` | Next.js 16.3.0 webpack production build passed |
| `npm audit` | 0 vulnerabilities after patching Vitest |
| `python scripts/test_mcp.py` | all four tools and cross-session denial passed |

## External blocker

- Required action owner: repository owner/cloud-account holder.
- Missing proof: Supabase schema/storage, live Gemini/Groq behavior, Langfuse trace, Vercel routes, browser CORS, public URL, and post-deploy MCP smoke.
- Safe local work for the accepted milestone is exhausted; the repository may proceed to the next independent project while this gate remains blocked.
