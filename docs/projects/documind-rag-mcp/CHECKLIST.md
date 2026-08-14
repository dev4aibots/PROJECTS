# DocuMind — Enterprise RAG + MCP — Live Checklist

Legend: `[ ]` ready · `[~]` in progress · `[x]` verified · `[!]` blocked · `[-]` out of scope

## Phase 0 — Plan and contracts

- [x] `P0-T1` Define folder structure, schema, API contracts, component boundaries, and test plan
- [x] `P0-T2` Record initial architecture decisions and environment contract

## Phase 1 — Persistence

- [x] `P1-T1` Add idempotent migrations and repository interfaces
- [x] `P1-T2` Verify validation, persistence, isolation, and idempotency behavior

## Phase 2 — Core domain logic

- [x] `P2-T1` Implement the smallest end-to-end domain outcome
- [x] `P2-T2` Implement and test refusal/security/failure boundaries

## Phase 3 — Services and providers

- [x] `P3-T1` Add service layer and typed provider abstraction
- [x] `P3-T2` Verify malformed output, retry, fallback, and both-providers-down behavior

## Phase 4 — Interfaces

- [x] `P4-T1` Implement FastAPI and mounted Streamable HTTP MCP contracts with structured errors
- [x] `P4-T2` Wire Next.js UI to API behavior with loading, empty, failure, grounded, and refusal states

## Phase 5 — Evaluation and observability

- [x] `P5-T1` Add versioned fixtures/corpus and deterministic metrics
- [x] `P5-T2` Add optional Langfuse tracing that cannot fail the primary path
- [x] `P5-T3` Save honest reproducible evaluation results

## Phase 6 — Delivery and audit

- [x] `P6-T1` Run full backend tests, frontend tests/typecheck, dependency audit, and production build
- [x] `P6-T2` Trace API/UI/MCP flows and remediate adversarial project audit findings
- [x] `P6-T3` Synchronize README, decisions, pipeline, MCP, limitations, demo, proof, and resume
- [!] `P6-T4` Deploy and smoke-test live environment
  - Blocker: owner-managed Supabase, Gemini/Groq, Langfuse, and Vercel credentials/projects are unavailable.
  - Resume: apply migrations 001–005, deploy backend/frontend as separate roots, configure exact origins, then smoke REST, UI, MCP, deletion, refusal, fallback, and traces.

## Completion summary

- Terminal status: `BLOCKED — external live deployment gate`
- Current item: `P6-T4`
- Critical/high local findings open: `0`
- Strongest proof: `../../../projects/documind-rag-mcp/AUDIT.md`, `PROOF.md`, 135 backend tests, full MCP smoke, production frontend build, and frozen 15-case evaluation.
