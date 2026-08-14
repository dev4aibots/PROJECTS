# Engineering decisions

- Use supported LangGraph `StateGraph`, `interrupt()` and `Command(resume=...)`; do not emulate the graph with a loop.
- `thread_id == task_run_id` is generated server-side. LangGraph checkpoints are execution truth; task/run/event/approval/memory tables are queryable projections.
- Local mode is explicit and deterministic. Live mode requires PostgresSaver, Postgres projections, Tavily and at least one structured model provider.
- Approval is a durable audit row. Postgres claims a decision using `UPDATE ... WHERE status='pending' RETURNING`, so only one worker resumes a run.
- Research content is untrusted data: HTTPS sources only, bounded snippets, no source text in system instructions.
- Agent outputs are Pydantic validated. Writer citations must be a subset of URLs returned by Research.
- Groq is attempted before Gemini when both keys exist; each adapter retries transient failure once before router fallback.
- Provider/tool failure remains explicit and must not silently fall back to fixture output in live mode.
- Long-term memory will remain opt-in; no sensitive trait inference is permitted.
- Local tests prove contracts, not hosted durability, current facts, live model quality or production security.
