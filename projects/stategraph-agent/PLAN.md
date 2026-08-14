# Implementation plan and contracts

The canonical phase plan is `../../docs/projects/stategraph-agent/DEPLOYMENT_READY_PLAN.md`.

Current architecture uses FastAPI commands/queries, a compiled LangGraph graph, explicit local/live checkpointer runtime, projection repositories, typed agent/search services and a Next.js workspace. Local mode is deterministic but exercises the same state and output contracts. Live mode selects PostgresSaver, Postgres projections, Tavily and a Groq/Gemini provider router.

Completed source gates: real graph topology; interrupt/resume; rejection and duplicate-decision behavior; local/Postgres projection boundary; atomic approval claim; typed live search/provider adapters; HTTPS/content bounds; citation allowlisting.

Next implementation order:

1. Verified JWT identity and repository ownership filters.
2. Opt-in memory with provenance, TTL, export and deletion.
3. Disposable-Postgres restart/race integration harness.
4. Held-out routing/risk/citation evaluation and privacy-safe tracing.
5. Refresh-safe UX, browser E2E and deployment preflight/live smoke.

No local fixture result may be presented as hosted, current-fact or production evidence.
