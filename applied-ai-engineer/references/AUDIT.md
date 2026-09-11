# Reference audit — 2026-09-11

## Method and limits

Source: [rohitg00/ai-engineering-from-scratch](https://github.com/rohitg00/ai-engineering-from-scratch), pinned commit `d18b8fe5a913c46011a3b06cb6ebd6a924414fd3`. Observed **523 English lesson files in 20 phases**. The complete machine-readable inventory includes exact paths, source hashes, classification and reason. All titles/paths were inventoried; selected directly relevant lesson content, headings and implementation structure were inspected. **This is not a line-by-line review or execution audit of all 523 lessons.** Preliminary rows are explicitly labeled. No upstream labs were run; no universal dependency compatibility claim is made.

The user's prior progress is a supplied summary, not accessible historical conversations. Therefore no independent skill ratings are invented. See ../curriculum/ROLE_AND_GAPS.md.

## Phase classification overview

| Phase | Folder | Lessons | Personalized classifications |
|---|---|---:|---|
| 00 | 00-setup-and-tooling | 12 | Must understand practically: 9; Can skip for now: 3 |
| 01 | 01-math-foundations | 22 | Learn only conceptually: 13; Can skip for now: 9 |
| 02 | 02-ml-fundamentals | 18 | Must understand practically: 6; Learn only conceptually: 12 |
| 03 | 03-deep-learning-core | 13 | Learn only conceptually: 13 |
| 04 | 04-computer-vision | 28 | Useful later: 28 |
| 05 | 05-nlp-foundations-to-advanced | 29 | Learn only conceptually: 24; Must understand practically: 5 |
| 06 | 06-speech-and-audio | 17 | Useful later: 17 |
| 07 | 07-transformers-deep-dive | 16 | Learn only conceptually: 16 |
| 08 | 08-generative-ai | 15 | Not relevant to my target role: 15 |
| 09 | 09-reinforcement-learning | 12 | Not relevant to my target role: 12 |
| 10 | 10-llms-from-scratch | 24 | Not relevant to my target role: 24 |
| 11 | 11-llm-engineering | 17 | Must learn deeply: 12; Must understand practically: 4; Useful later: 1 |
| 12 | 12-multimodal-ai | 25 | Useful later: 25 |
| 13 | 13-tools-and-protocols | 31 | Must learn deeply: 24; Useful later: 7 |
| 14 | 14-agent-engineering | 54 | Must learn deeply: 34; Useful later: 14; Must understand practically: 6 |
| 15 | 15-autonomous-systems | 22 | Useful later: 22 |
| 16 | 16-multi-agent-and-swarms | 25 | Useful later: 25 |
| 17 | 17-infrastructure-and-production | 28 | Useful later: 16; Must learn deeply: 12 |
| 18 | 18-ethics-safety-alignment | 30 | Learn only conceptually: 18; Must understand practically: 12 |
| 19 | 19-capstone-projects | 85 | Must understand practically: 37; Useful later: 48 |

Exact lesson-by-lesson classifications and reasons are in lesson_catalog.json. 'Not relevant' means outside the **current API-first target**, not useless in general. Review a preliminary entry substantively before depending on it.

## The best material for this system

- Phase 14 lessons 31–42: agent workbench, minimal harness, instructions, durable state, scope, runtime feedback, verification, review, handoff and capstone. Particularly [38 verification gates](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/14-agent-engineering/38-verification-gates/docs/en.md), [39 reviewer](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/14-agent-engineering/39-reviewer-agent/docs/en.md), [40 handoff](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/14-agent-engineering/40-multi-session-handoff/docs/en.md).
- Phase 14 lessons 43–54: task framing, evidence-based planning, isolated delegation, feedback, outcomes and risk. [43](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/14-agent-engineering/43-frame-the-task-before-code/docs/en.md), [49](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/14-agent-engineering/49-map-assumptions-and-risk/docs/en.md), [54](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/14-agent-engineering/54-build-the-feedback-ratchet/docs/en.md). These help operational judgment more directly than advanced model derivations.
- Phase 11: structured outputs, context, embeddings, RAG, function calling, evaluation and cost. Treat examples as learning material until exercised against your contracts.
- Phase 13: tool schema, auth, permissions, cancellation, versioning. [26 skills are not sandboxes](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/13-tools-and-protocols/26-skill-permissions-sandboxes-and-trust/docs/en.md), [18 MCP auth](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/13-tools-and-protocols/18-mcp-auth-production/docs/en.md), [31 conformance](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/13-tools-and-protocols/31-mcp-conformance-versioning-and-operations/docs/en.md).
- Phase 17 lessons 13–16, 19–25, 27: app observability, routing, canaries, load tests, SRE, secrets and FinOps. Add real deployment drills; theory/simulators do not establish operability.

## Findings requiring correction, not blind reuse

1. [Phase 11/06 RAG](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/11-llm-engineering/06-rag/docs/en.md), opening and 'Why RAG Beats Fine-Tuning': an LLM does **not** know everything before its cutoff. RAG does not guarantee truth, privacy or superiority in every factual task. Retrieved documents can leave your infrastructure through provider requests/logs. Price ranges, embedding rankings, chunk sizes and latency claims are workload-dependent, not universal defaults. Set baselines and measure.
2. [Phase 11/13 production app](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/11-llm-engineering/13-production-app/docs/en.md), 'Error Handling: The Three Layers': raw malformed output is not an acceptable fallback for a typed contract; skipping grounding is not acceptable when authoritative evidence is required. Return a typed error, bounded repair, abstention or escalation based on requirements. Do not route sensitive data to an unapproved fallback provider.
3. Same lesson labels itself production-ready while its `code/production_app.py` uses simulated responses. This is useful scaffolding, not proof of real-provider behavior, tenant isolation or surviving 10,000 users. MCP/semantic caching are not mandatory for every serious application. Native browser EventSource does not send POST bodies/custom bearer headers; choose a streaming client/auth pattern compatible with the actual API.
4. Same lesson's prerequisite line points to lessons 01–15 while it is lesson 13. Its RAG lesson lists Phase 10 as a prerequisite. For your target, practical API/embedding understanding is enough; building an LLM from scratch is not a required gate.
5. [Phase 17/23 SRE](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/17-infrastructure-and-production/23-sre-for-ai/docs/en.md) explicitly includes a toy incident triage simulator. Model agreement is not proof of a root cause; require logs, a discriminating experiment and an independently verified fix. Forecasts and impressive percentages need original evidence before use in architecture decisions.
6. [Phase 19/08 production RAG chatbot](https://github.com/rohitg00/ai-engineering-from-scratch/blob/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3/phases/19-capstone-projects/08-production-rag-chatbot/docs/en.md) is a starting exercise. The inspected lesson does not establish multi-tenant database/RLS, deletion propagation, backups or restore behavior. Add those project-specific gates rather than inferring them from 'production' in the title.

## Overlap to consolidate

- Structured output: Phase 11/03 and Phase 13/04; one typed endpoint with adversarial cases proves both.
- Function calling: Phase 11/09, Phase 13/01–05, Phase 14/06; one authorized idempotent integration, not three toy tools.
- MCP: Phase 11/14 overview vs Phase 13 detailed route; use the latter with protocol version pinned.
- RAG: Phase 5 embedding/chunking lessons, Phase 11/04–07, Phase 19/64–69; use one evaluated corpus lifecycle.
- Observability: Phase 13/20, Phase 14/23–24, Phase 17/13; one trace spanning API, worker, retrieval and tool.
- Frameworks: Phase 11/16–17 and Phase 14/13–18; evaluate one library against direct orchestration, don't memorize every SDK.

## Missing depth for your role

Not claims that a word never occurs upstream: these are **end-to-end competency gaps not established by the sampled artifacts**. Add Python service review; FastAPI contract/auth tests; SQL constraints, migrations, RLS with non-owner roles and connection-pool context; transactional outbox/inbox, DLQ/reconciliation; tenant-safe Redis/object/vector storage; OAuth/webhook lifecycle; booking races and time zones; usage/billing reconciliation; CI, reverse proxy/HTTPS, restore/rollback drills; data residency and deletion; customer acceptance and technical communication. The local phases/playbooks explicitly cover these.

## Outdated versus merely unnecessary

No blanket 'outdated repository' verdict: this snapshot contains current 2026 MCP lessons. We did not test all dependency versions. Rapidly changing model names, SDK examples, prices, quotas, benchmark claims and protocol versions require date/version verification. The official 2026-07-28 MCP profile was inspected; older 2025-06-18 authorization guidance differs on client registration. Treat old DCR recommendations as version-specific, not universal. See SOURCES.md.

## Next exact recommendation

Phase 0 baseline assessment, then Phase 2 secure API + Phase 3 tenant state vertical slice; targeted Phase 1 remediation only if code-reading/debugging fails. Security, evaluation and operability are included from day one, not postponed until the numbered later phases. Do not start with calculus, training a transformer, or a swarm.
