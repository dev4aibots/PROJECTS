# Career Prompt Pack — Requirements Analysis

Analyzed: `2026-08-10 13:24 UTC`  
Source: user-supplied `career-prompt-pack.zip` (26 Markdown files, 2,718 lines after extraction)

## Interpretation

The archive is a build specification and operating system, not finished applications. It defines five independent, portfolio-grade AI engineering products plus two bonus projects. The controlling rules require one active project at a time, evidence before claims, explicit failure behavior, evaluation artifacts, and cold-start handoffs in `docs/projects/<id>/`.

## Cross-project requirements extracted line by line

- **Fixed target stack:** Next.js App Router, TypeScript, Tailwind, Python 3.12, FastAPI, Pydantic v2, Supabase/Postgres, Groq + Gemini provider abstraction, Langfuse, pytest, Vitest, and Vercel.
- **Architecture:** route handlers remain thin; service and repository layers own behavior; all interfaces reuse the same domain services.
- **Reliability:** validate hostile input, correct malformed structured output once, retry transient provider errors once, fall back where modality permits, and return structured safe errors.
- **Serverless correctness:** no durable process memory, no writes outside `/tmp`, and long operations must persist cursors/checkpoints and resume idempotently.
- **Portfolio proof:** each app needs real tests, a meaningful failure-path demo, an evaluation/security corpus, reproducible results, architecture and decision records, honest limitations, and deployment proof only after live smoke tests.
- **Truth boundary:** mocked provider tests prove application behavior only; they do not prove live provider, database, tracing, or deployment availability.

## Project portfolio map

| Priority | Product | Distinct hiring signal | Required proof |
|---:|---|---|---|
| 1 | DocuMind | grounded RAG + MCP + evals | retrieval hit, faithfulness, citation accuracy, correct refusal |
| 2 | StateGraph | durable agents + approval + memory | routing, schema compliance, interrupt recovery, memory isolation |
| 3 | ZeroTrust SQL | LLM security + SQL AST enforcement | 8 attack classes, 50 SQL fixtures, legitimate-query accuracy |
| 4 | DocuExtract | multimodal structured output + deterministic trust | Decimal boundary tests, extraction accuracy, verdict correctness |
| 5 | LLMShield | reusable guardrails + observability | injection/PII confusion matrices and dependency-failure tests |

## Dependency and sequencing analysis

The applications can run independently. Shared ideas (provider adapters, error envelopes, tracing) are patterns, not a shared runtime dependency. DocuMind is active first because the supplied pack explicitly marks it flagship and because its provider/reliability patterns can inform—but must not be blindly imported into—the later products. Bonus EvalBoard and Portfolio Hub remain out of active scope until all five core products are audited and deployed as required by `07-bonus-projects.md`.

## Delivery reality

No application code was present in the archive. Therefore none of the five projects can truthfully be marked complete. The repository has now been converted into a resumable build queue with verified briefs, live checklists, proof ledgers, and exact resume pointers. Implementation starts with DocuMind Phase 0 and proceeds phase-by-phase; deployment and live-provider checks will require owner credentials and provider accounts later.
