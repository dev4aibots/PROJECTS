# StateGraph Agent — deployment-readiness checklist

Legend: `[ ]` ready · `[~]` partial · `[x]` locally verified · `[!]` owner/cloud blocked

## P0–P2 — contracts, API and real LangGraph

- [x] Typed task, event, approval and memory contracts exist.
- [x] Real LangGraph `StateGraph` has Research → Analyst → Reviewer → Writer topology.
- [x] Reviewer uses `interrupt()` and approval uses `Command(resume=...)`.
- [x] Rejection cannot execute Writer; duplicate decisions are no-ops.
- [x] Local deterministic API and Next.js UI build successfully.

## P3 — durable checkpoints and projections

- [x] `GraphRuntime` selects memory only in `APP_MODE=local`.
- [x] Live mode requires `DATABASE_URL`, opens `PostgresSaver`, runs `setup()`, and reports readiness.
- [x] Task/event/approval/memory repository protocols have local and Postgres implementations.
- [x] Projection migration adds required fields, indexes and fictional demo identities.
- [x] Approval claim uses one atomic `UPDATE ... WHERE status='pending' RETURNING`; local concurrency test proves one winner.
- [x] Reconstructed-graph test resumes from a shared checkpointer.
- [~] Credential-gated process-A/process-B recovery, projection isolation and approval-race harness exists; execution still requires `STATEGRAPH_TEST_DATABASE_URL` pointing to disposable pgvector Postgres.

## P4 — real agents, tools and evidence

- [x] Typed Gemini/Groq JSON adapters have timeouts, bounded retry and provider fallback.
- [x] Deterministic search fixture and Tavily live adapter share one protocol.
- [x] Search accepts HTTPS sources only and bounds untrusted snippets.
- [x] Analyst/Reviewer/Writer outputs are Pydantic validated; Writer citations must belong to gathered sources.
- [x] Local tests reject citation injection and insecure search URLs.
- [x] Local provider fallback, bounded all-provider failure, dependency-outage checkpoint retry, and held-out routing/citation policy evaluation pass; live quality remains owner-gated.

## P5 — authenticated ownership and memory privacy

- [x] Verify asymmetric Supabase JWTs server-side with JWKS, issuer, audience, expiry and UUID subject checks; derive ownership only from claims.
- [x] Enforce owner-scoped tasks, events, approvals and memories; checkpoint resume is reachable only after an owned task/approval lookup.
- [x] Make long-term memory opt-in with task provenance, 90-day TTL, owner delete and JSON export.
- [x] Add local cross-user API denial and signed-JWT claim tests.
- [x] Migration 004 enables/forces owner RLS on every projection table and grants only the `stategraph_api` role; each repository transaction assumes that role and binds verified subject through transaction-local configuration.
- [x] Unit tests prove the role/subject session preamble; local API tests prove cross-user denial.
- [!] Real Supabase JWT + RLS execution remains an owner-credential proof gate.

## P6 — production UX

- [x] Create/timeline/approval/result UI includes local demo identity and Supabase magic-link session flow.
- [x] Refresh/reconnect, retry/cancel, source cards, memory manager and JSON export are wired to owner-scoped APIs.
- [x] Empty, loading, error, interrupted, completed, rejected and mobile states have explicit UI coverage.
- [x] Four Chromium E2E scenarios cover create → interrupt → approve/reject/cancel → refresh → completion, memory management and mobile overflow.

## P7–P8 — evaluation, delivery and owner launch

- [~] CI workflow is prepared in `docs/templates/portfolio-ci.yml`; owner must activate it with workflow-write permission.
- [x] Versioned held-out routing/risk/citation evaluation has explicit release thresholds; restart and memory safety are covered by backend and browser integration tests.
- [~] Privacy-safe request correlation, bounded timeline latency, deployment preflight and authenticated live smoke exist; live provider token/cost traces require owner credentials.
- [!] Hosted database/provider/search/Langfuse/Vercel proof, screenshots and video require owner resources.

## Current status

`BLOCKED — owner integration only`. All credential-free source, evaluation, UI, E2E, preflight and smoke-script gates are locally complete. The disposable-Postgres restart/isolation/race harness, real Supabase RLS verification, live provider/search telemetry and public deployment require owner resources; none is claimed as verified.
