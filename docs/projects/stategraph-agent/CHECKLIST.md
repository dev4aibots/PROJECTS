# StateGraph — Multi-Agent Research Orchestrator — Live Checklist

Legend: `[ ]` ready · `[~]` in progress · `[x]` verified · `[!]` blocked · `[-]` out of scope

## Phase 0 — Plan and contracts

- [ ] `P0-T1` Define folder structure, schema, API contracts, component boundaries, and test plan
- [ ] `P0-T2` Record initial architecture decisions and environment contract

## Phase 1 — Persistence

- [ ] `P1-T1` Add idempotent migrations and repository interfaces
- [ ] `P1-T2` Verify validation, persistence, isolation, and idempotency behavior

## Phase 2 — Core domain logic

- [ ] `P2-T1` Implement the smallest end-to-end domain outcome
- [ ] `P2-T2` Implement and test the project-specific refusal/security/failure boundary

## Phase 3 — Services and providers

- [ ] `P3-T1` Add service layer and typed provider abstraction
- [ ] `P3-T2` Verify malformed output, retry, fallback, and both-providers-down behavior where applicable

## Phase 4 — Interfaces

- [ ] `P4-T1` Implement FastAPI contracts and structured errors
- [ ] `P4-T2` Wire Next.js UI to real API behavior with loading, empty, failure, and result states

## Phase 5 — Evaluation and observability

- [ ] `P5-T1` Add versioned fixtures/corpus and deterministic metrics
- [ ] `P5-T2` Add optional Langfuse tracing that cannot fail the primary path
- [ ] `P5-T3` Save honest reproducible evaluation results

## Phase 6 — Delivery and audit

- [ ] `P6-T1` Run full backend tests, frontend tests/typecheck, and production build
- [ ] `P6-T2` Trace API/UI flows and run adversarial project audit
- [ ] `P6-T3` Synchronize README, decisions, limitations, demo script, proof, and resume
- [!] `P6-T4` Deploy and smoke-test live environment
  - Blocker: requires owner-managed Supabase, provider, Langfuse, and Vercel credentials/settings.

## Completion summary

- Terminal status: `not terminal`
- Current item: `P0-T1 — plan and contracts`
- Critical/high findings open: `not audited`
- Strongest proof: project specification and populated resumable state only; implementation proof does not yet exist.
