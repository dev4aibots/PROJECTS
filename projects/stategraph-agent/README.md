# StateGraph — Human-governed LangGraph workflow

A four-stage research workflow built with LangGraph `StateGraph`. It checkpoints state, conditionally pauses at `interrupt()` for risky requests, and continues through `Command(resume=...)` after one atomic human decision.

## Current truth

- Real LangGraph nodes/edges, typed state, interrupt/resume and local/Postgres checkpointer lifecycle are implemented.
- Queryable task/run/event/approval/memory projections have local and Postgres repositories; approval claims use database compare-and-set.
- Local fixture agents and live Tavily + Groq/Gemini adapters share typed contracts. Live search bounds untrusted snippets and accepts HTTPS URLs only; Writer citations must match gathered sources.
- Supabase JWT verification, owner-scoped API paths, opt-in expiring memory and forced projection-table RLS are implemented and locally contract-tested.
- Hosted Postgres recovery/RLS, live provider quality, Langfuse and public deployment are not verified. Do not expose the API until migration 004 and real two-user isolation have been exercised.

## Graph

`START → Research → Analyst → Reviewer → [interrupt if risky] → Writer → END`

A rejected interrupt routes to `END`; Writer never runs. `thread_id == task_run_id` is generated server-side.

## Run and verify

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
APP_MODE=local PYTHONPATH=backend uvicorn app.main:app --reload
APP_MODE=local PYTHONPATH=backend pytest -q backend/tests
cd frontend && npm ci && npm run typecheck && npm run build
```

## Live configuration boundary

Set `APP_MODE=live`, `AUTH_MODE=live`, `DATABASE_URL`, Supabase JWT issuer settings, `TAVILY_API_KEY`, and at least one of `GROQ_API_KEY` or `GEMINI_API_KEY`. Apply migrations 001–004. Live startup initializes `PostgresSaver` and the projection pool; each projection transaction assumes `stategraph_api` and binds the verified token subject for RLS. This path is implemented but has not been exercised against owner cloud resources.

Verified local boundaries include rejection without Writer, duplicate-decision no-op, one concurrent decision winner, reconstructed-graph resume, citation allowlisting, insecure-search URL rejection, signed JWT contracts, cross-user denial, explicit memory consent and RLS session binding. Demo headers are accepted only in local mode and are not production authentication. Set `STATEGRAPH_TEST_DATABASE_URL` only to disposable pgvector Postgres to run the skipped restart/isolation/race integration proof.

See `PLAN.md`, `DECISIONS.md`, `docs/state-machine.md`, `AUDIT.md`, `DEMO_SCRIPT.md`, and `../../docs/projects/stategraph-agent/DEPLOYMENT_READY_PLAN.md`.
