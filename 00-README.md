# AI Engineering Career Prompt Pack (2026)

**Goal:** Turn zero professional experience into a proof-of-work portfolio that wins 6–12 LPA+ remote AI Engineer / Agentic AI Engineer roles.

**How this pack was built:** Researched current (2026) AI engineering job listings, hiring-manager screening criteria, GenAI interview debriefs (80+ interviews field guide), and verified free-tier limits of every service used (Vercel, Supabase, Groq, Gemini, Langfuse).

---

## The research findings these prompts are built on

1. **Evaluation is the #1 hiring signal.** Hiring managers explicitly look for eval suites (RAGAS / DeepEval / LLM-as-judge). "23% hallucination rate → 4% after tuning" in a README is worth more than any UI. Every project here has a mandatory evaluation section.
2. **Failure handling is the #2 signal.** "What happens when retrieval returns nothing?" / "What happens on a 429?" — every prompt forces graceful failure paths and an explicit "insufficient evidence" behavior.
3. **GitHub is scanned in ~90 seconds.** README quality, architecture diagram, DECISIONS.md, tests, live URL. Every project mandates these.
4. **The 5 skills in current job listings:** RAG, LangGraph agents + tool calling, MCP, structured outputs (Pydantic), guardrails + observability (Langfuse). The 5 core projects map 1:1 to these.
5. **Connected projects signal systems thinking.** The eval harness tests the RAG project. LLMShield can gate any of them. The prompts cross-reference intentionally.

## Verified free-tier constraints (baked into every prompt)

| Service | Verified limit (2026) |
|---|---|
| Vercel Python Functions | FastAPI officially supported, bundle up to 500MB, Fluid compute, MCP via Streamable HTTP officially documented |
| Supabase Free | 500MB Postgres, 1GB storage, pgvector included, projects pause after ~1 week inactivity |
| Groq Free | ~30 req/min, ~14,400 req/day, ~6K tokens/min per model (varies by model) |
| Gemini Free | Gemini Flash-class: ~10 req/min, ~1,500 req/day; free embeddings API |
| Langfuse Cloud Free | ~50k observations/month |

**Consequence:** every app must implement provider fallback, honest 429 handling, and response caching. The prompts enforce this.

---

## Files in this pack

| File | What it is | When to use |
|---|---|---|
| `01-master-context.md` | Shared context block prepended to EVERY project prompt | Always, first message |
| `02-project-1-enterprise-rag-mcp.md` | FLAGSHIP: Multimodal RAG + MCP + Eval harness | Days 2–3 |
| `03-project-2-stategraph-agents.md` | Multi-agent LangGraph + memory + human-in-the-loop | Days 4–5 |
| `04-project-3-zerotrust-sql.md` | Secure text-to-SQL with AST validation | Days 6–7 |
| `05-project-4-docuextract.md` | Multimodal invoice extraction + deterministic verification | Day 8 |
| `06-project-5-llmshield.md` | LLM security gateway + observability | Day 9 |
| `07-bonus-projects.md` | 2 optional small projects (eval dashboard, job-hunt agent) | Only if time remains |
| `08-audit-prompt.md` | Hostile QA review prompt — run after EVERY project | After each project |
| `09-deployment-prompt.md` | Vercel deployment-readiness prompt | Before each deploy |
| `10-documentation-polish-prompt.md` | Portfolio-grade docs + demo script prompt | Day 10 |
| `11-interview-answers.md` | The questions you MUST be able to answer per project | Study while building |

## The exact workflow per project

```
1. Paste 01-master-context.md + the project prompt      → agent plans (NO code)
2. Approve/adjust the plan                              → agent builds Phase by Phase
3. After agent claims "done" → paste 08-audit-prompt.md → agent finds & fixes its own lies
4. Paste 09-deployment-prompt.md                        → deploy to Vercel, verify live
5. Paste 10-documentation-polish-prompt.md              → README, diagrams, DEMO_SCRIPT
6. YOU: record 90–120s demo video, take screenshots
7. YOU: read 11-interview-answers.md for that project until you can answer everything
```

## Rules for you (the human)

- One project at a time. Never give the agent two projects at once.
- Never accept "it works" — make the agent SHOW test output and a live URL.
- Never skip the audit prompt. Coding agents fake things; the audit prompt catches it.
- Keep demo data tiny (3–10 PDFs, seeded SQL). Free tiers are enough.
- You must be able to explain every architecture decision. If you can't, ask the agent "explain why we did X as if interviewing me" before moving on.
