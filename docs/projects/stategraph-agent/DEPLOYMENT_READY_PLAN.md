# StateGraph Agent deployment-ready implementation plan

**Outcome:** replace the current hand-written deterministic workflow with a genuine, durable LangGraph application. After P0–P8, cloud setup is credentials/migrations/deploy only.

**Current truth (2026-08-14):** P2 uses real LangGraph. P3 has PostgresSaver, durable projections, atomic approval claim and a credential-gated restart/race harness, pending execution against disposable Postgres. P4 has typed Tavily/Groq/Gemini adapters and local contract tests, pending live quality/outage evaluation. P5 verifies JWT contracts, derives owner identity, implements opt-in expiring memory, and enforces forced RLS through a least-privilege transaction role; real Supabase JWT/RLS proof remains owner-gated. Browser E2E, observability and hosted evidence remain incomplete.

## Target architecture

Authenticated Next.js workspace → FastAPI command/query API → compiled LangGraph `StateGraph` → typed Research/Analyst/Reviewer/Writer nodes → real search/retrieval tool with citations → interrupt-based human approval → Postgres checkpointer/store → provider router → privacy-safe Langfuse traces. `thread_id` is generated server-side and bound to verified user ownership.

## Phase gates

### P0 — contract and risk model
- Freeze typed task state, node input/output, event, approval, memory, citation and error schemas.
- Define state transitions, interrupt semantics, idempotency keys, ownership rules, maximum loops/tool calls/tokens, timeout and cancellation.
- Choose tool: Tavily/Brave/Google Search adapter behind a protocol, plus deterministic fixture tool for tests.
- **Gate:** state diagram and transition table cover success, refusal, approval, rejection, retry, cancellation, provider/tool outage and restart.

### P1 — modular foundation
- Split the monolithic API into config, auth, domain models, repositories, providers, tools, graph, services and routes.
- Add strict settings validation and local/live modes. Local mode remains deterministic but exercises the same interfaces.
- Add request IDs, stable error envelopes and structured logging.
- **Gate:** unit tests import no global mutable app store; config mistakes fail fast with actionable messages.

### P2 — real LangGraph workflow
- Add supported `langgraph` and `langgraph-checkpoint-postgres` versions.
- Build `StateGraph[AgentState]` with explicit edges and conditional Reviewer routing.
- Use `interrupt()` for human decisions and `Command(resume=...)` to continue.
- Make each node return typed deltas; prevent unbounded recursion and duplicate writes.
- **Gate:** graph topology test proves Writer cannot run before approval when required; duplicate resume is a no-op.

### P3 — durable checkpoints and restart recovery
- Use PostgresSaver in live mode and a supported local checkpointer in tests.
- Store task/approval projection tables transactionally with checkpoint metadata; generate thread IDs server-side.
- Add restart integration test: process A pauses, process B resumes from the same database.
- Add optimistic versioning/idempotency for concurrent approval calls.
- **Gate:** completed/rejected tasks survive restart; only one decision wins; checkpointer schema setup is documented and automated.

### P4 — real agents, tools and evidence
- Implement Groq/Gemini structured-output adapters with bounded transient retries and fallback.
- Research node must use at least one real search tool in live mode and return source URL/title/date/snippet.
- Analyst compares claims and uncertainty; Reviewer applies deterministic risk policy plus typed model review; Writer can cite only gathered sources.
- Treat tool content as untrusted; isolate it from system instructions and validate URLs/size/type.
- **Gate:** live output is non-templated, citations resolve, unsupported claims are removed/refused, and tool/provider outages yield resumable errors.

### P5 — authentication, memory and privacy (source-complete; hosted proof pending)
- Verify Supabase JWTs; derive user ID from token; enforce owner filters on tasks, events, approvals, checkpoints and memories.
- Store only user-approved long-term memories with provenance, TTL and delete/export controls. Never infer sensitive traits.
- Add RLS and cross-tenant tests for every endpoint. Protect approval actions with ownership and CSRF-safe bearer semantics.
- **Gate:** forged user IDs cannot select another user; memory is opt-in, attributable and deletable.

### P6 — UI/UX and operator visibility
- Build accessible task composer, live timeline, node state, source cards, approval panel with risk explanation, resume/retry/cancel, memory manager and result export.
- Support refresh/reconnect by polling or SSE without relying on in-process state.
- Add mobile and all empty/loading/error/interrupted/completed/rejected states.
- **Gate:** browser E2E covers create → interrupt → approve/reject → restart → completed; every visible control reaches a real API.

### P7 — evaluation, CI and deployment
- Version datasets for routing accuracy, risk-policy recall, approval correctness, citation validity, answer support, tool success, restart recovery and memory isolation.
- Track latency/cost per node and whole run; add Langfuse parent trace and node/tool spans without raw sensitive prompts by default.
- CI: unit/integration/eval/frontend/build/security/migration checks. Vercel topology must account for request duration; use resumable commands, never one long request.
- **Gate:** deterministic release thresholds pass; hosted smoke demonstrates true process restart and Postgres checkpoints.

### P8 — owner launch proof
Configure Postgres/Supabase, provider/search/Langfuse credentials and Vercel roots; apply migrations/checkpointer setup; run hosted restart, approval race, isolation, outage and eval smokes; capture URLs, trace, screenshots and video.

## Minimum portfolio evidence

A graph visualization, real cited research run, risk interrupt, rejection path, restart/resume proof, concurrent decision proof, cross-user denial, eval report, CI, p95/cost summary, live URL and demo video. Do not use “multi-agent LangGraph” publicly before P4.

## Research basis

- LangGraph persistence concepts: https://langchain-ai.github.io/langgraph/concepts/persistence/
- LangGraph human-in-the-loop: https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/
- FastAPI API-key/JWT security primitives: https://fastapi.tiangolo.com/reference/security/
- Vercel function duration: https://vercel.com/docs/functions/configuring-functions/duration
