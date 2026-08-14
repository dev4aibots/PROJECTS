# 60–90 Second Demo

1. Open `/app`; point out the defense-in-depth disclaimer and zeroed local stats.
2. Run **Normal question**; show input/output checks, provider, latency, trace ID, and answer.
3. Run **Injection attack**; show two pattern families, `BLOCK`, no answer, and provider `none`.
4. Run **PII input**; show email/card redactions and confirm the answer contains placeholders only.
5. Show request history with SHA-256 values—not prompt text—and the updated blocked/fallback/p95 stats.
6. In a configured deployment, open the trace ID in Langfuse and show input guards, LLM call/fallback, output guards, and final status.
7. Close with the limitation: lexical heuristics are transparent defense-in-depth, not a semantic jailbreak guarantee.

Capture plan: landing page, safe result, blocked result, redacted result, hash-only history, and one real Langfuse trace after owner configuration.
