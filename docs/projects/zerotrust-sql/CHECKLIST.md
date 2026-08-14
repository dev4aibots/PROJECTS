# ZeroTrust SQL — Secure Natural-Language Analytics — Live Checklist

Legend: `[ ]` ready · `[~]` in progress · `[x]` verified · `[!]` blocked · `[-]` out of scope

## Phase 0 — Plan and contracts

- [x] `P0-T1` Define folder structure, schema, API contracts, component boundaries, and test plan
- [x] `P0-T2` Record initial architecture decisions and environment contract

## Phase 1 — Persistence

- [x] `P1-T1` Add idempotent migration (schema, decoy table, `nl_query_ro` role, audit log)
- [x] `P1-T2` Verify seeded-sandbox determinism, read-only enforcement, and timeout behavior

## Phase 2 — Core domain logic

- [x] `P2-T1` Implement the seven-check AST validation pipeline with LIMIT rewriting
- [x] `P2-T2` Implement and test the security boundary: all 8 attack-lab prompts blocked with the failing check named

## Phase 3 — Services and providers

- [x] `P3-T1` Add typed generator abstraction (deterministic templates local; Groq→Gemini live)
- [x] `P3-T2` Verify generation-unavailable, database-down, and no-internal-leak failure paths

## Phase 4 — Interfaces

- [x] `P4-T1` Implement FastAPI contracts (`/api/query`, `/api/schema`, `/api/audit`) and structured errors
- [x] `P4-T2` Wire Next.js UI (attack lab, per-check verdicts, limit_injected badge) to the real API

## Phase 5 — Evaluation and observability

- [x] `P5-T1` 50-fixture corpus (25 safe / 25 malicious) as a versioned test gate
- [-] `P5-T2` Langfuse tracing deferred to owner-managed live configuration
- [x] `P5-T3` Golden-query eval saved and reproducible (`evals/run.py` → 13/13)

## Phase 6 — Delivery and audit

- [x] `P6-T1` Backend tests (57 passed), frontend typecheck, and Next production build verified
- [x] `P6-T2` API/UI flows traced; adversarial audit recorded in `projects/zerotrust-sql/AUDIT.md`
- [x] `P6-T3` README, decisions, limitations, demo script, proof, and resume synchronized
- [!] `P6-T4` Deploy and smoke-test live environment
  - Blocker: requires owner-managed Supabase, provider, Langfuse, and Vercel credentials/settings.

## Completion summary

- Terminal status: `BLOCKED — owner deployment only`
- Current item: `P6-T4 — owner-managed live deployment`
- Critical/high findings open: `0` (see `projects/zerotrust-sql/AUDIT.md`)
- Strongest proof: `PYTHONPATH=backend pytest -q backend/tests` → 57 passed; corpus 25/25 malicious blocked, 25/25 safe allowed; `evals/run.py` → 13/13; frontend `tsc --noEmit` and `next build --webpack` passed 2026-08-12.
