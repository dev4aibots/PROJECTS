# DocuMind — Enterprise RAG + MCP — Verified Brief

Project ID: `documind-rag-mcp`
Folder: `projects/documind-rag-mcp`
Brief status: `implemented and locally verified; owner deployment blocked`
Last verified: `2026-08-12`

## One-sentence outcome

Upload and incrementally index PDFs, then answer only from retrieved evidence with page citations; expose the same service through REST, UI, and MCP.

## Goal sources

| Priority | Source | What it establishes | Confidence |
|---:|---|---|---|
| 1 | User request | Build resume-ready, resumable projects from the supplied archive | High |
| 2 | `02-project-1-enterprise-rag-mcp.md` | Product behavior, interfaces, data model, failures, evaluation, and demo | High |
| 3 | `01-master-context.md` | Shared stack, architecture, testing, deployment, and truth standards | High |

## Intended users and problem

- Primary user: a recruiter-facing demo user or developer evaluating the API.
- Problem: upload and incrementally index pdfs, then answer only from retrieved evidence with page citations; expose the same service through rest, ui, and mcp.
- Successful outcome: the primary flow and its most important refusal/security path are reproducible with saved proof.

## Primary acceptance scenarios

1. **Happy path:** The core user flow persists and returns the specified structured result through a real service path.
2. **Important failure:** Corrupt pdfs, provider rate limits, malformed model output, unsupported questions, poisoned documents produce the specified safe behavior without fabricated output or leaked internals.
3. **Recovery/resume:** Repeating an interrupted or retried operation is safe and does not duplicate durable side effects where the specification requires it.

## Scope now

- RAG, resumable ingestion, pgvector retrieval, evidence gate, citation validation, MCP tools, evaluation harness.
- FastAPI backend, Next.js frontend, migrations, tests/evals, decision records, and verified setup documentation.

## Explicit non-goals

- Paid infrastructure, production authentication, unsupported cloud services, fabricated live metrics, or bonus-project scope.
- Features not named by this project's own specification.

## Constraints

- Use the stack and free-tier constraints in `01-master-context.md`.
- Do not claim external provider, Supabase, Langfuse, or deployment success without credentials and observed proof.
- Keep provider calls mockable so the local suite runs without secrets.
- Follow the project-specific scope discipline and failure behavior in `02-project-1-enterprise-rag-mcp.md`.

## Definition of done

The specified API/UI flow, failure handling, tests, evaluation, docs, production build, and adversarial audit pass with proof. Deployment is complete only after a live URL is supplied and smoke-tested; otherwise it remains an explicit external blocker rather than a false claim.
