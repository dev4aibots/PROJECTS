# LLMShield — Security and Observability Gateway — Verified Brief

Project ID: `llmshield`  
Folder: `projects/llmshield`  
Brief status: `owner-supplied specification, implementation not started`  
Last verified: `2026-08-10 13:24 UTC`

## One-sentence outcome

Protect LLM calls with independent request and response guards, privacy-aware logging, provider fallback, and traces that never break the data path.

## Goal sources

| Priority | Source | What it establishes | Confidence |
|---:|---|---|---|
| 1 | User request | Build resume-ready, resumable projects from the supplied archive | High |
| 2 | `06-project-5-llmshield.md` | Product behavior, interfaces, data model, failures, evaluation, and demo | High |
| 3 | `01-master-context.md` | Shared stack, architecture, testing, deployment, and truth standards | High |

## Intended users and problem

- Primary user: a recruiter-facing demo user or developer evaluating the API.
- Problem: protect llm calls with independent request and response guards, privacy-aware logging, provider fallback, and traces that never break the data path.
- Successful outcome: the primary flow and its most important refusal/security path are reproducible with saved proof.

## Primary acceptance scenarios

1. **Happy path:** The core user flow persists and returns the specified structured result through a real service path.
2. **Important failure:** Blocked prompts must skip llm calls, both providers down, empty/oversized output, malformed request, tracing outage produce the specified safe behavior without fabricated output or leaked internals.
3. **Recovery/resume:** Repeating an interrupted or retried operation is safe and does not duplicate durable side effects where the specification requires it.

## Scope now

- injection scoring, PII detection/redaction, Luhn validation, provider fallback, output guards, Langfuse traces, attack corpus.
- FastAPI backend, Next.js frontend, migrations, tests/evals, decision records, and verified setup documentation.

## Explicit non-goals

- Paid infrastructure, production authentication, unsupported cloud services, fabricated live metrics, or bonus-project scope.
- Features not named by this project's own specification.

## Constraints

- Use the stack and free-tier constraints in `01-master-context.md`.
- Do not claim external provider, Supabase, Langfuse, or deployment success without credentials and observed proof.
- Keep provider calls mockable so the local suite runs without secrets.
- Follow the project-specific scope discipline and failure behavior in `06-project-5-llmshield.md`.

## Definition of done

The specified API/UI flow, failure handling, tests, evaluation, docs, production build, and adversarial audit pass with proof. Deployment is complete only after a live URL is supplied and smoke-tested; otherwise it remains an explicit external blocker rather than a false claim.
