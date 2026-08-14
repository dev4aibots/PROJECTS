# DocuExtract — Verified Invoice Intelligence — Live Checklist

Legend: `[ ]` ready · `[~]` in progress · `[x]` verified · `[!]` blocked · `[-]` out of scope

## Phase 0 — Plan and contracts
- [x] `P0-T1` Define folder structure, schema, API contracts, component boundaries, and test plan
- [x] `P0-T2` Record architecture decisions and environment contract

## Phase 1 — Persistence
- [x] `P1-T1` Add idempotent migration plus deterministic memory repository
- [x] `P1-T2` Verify private-byte filtering, session list isolation, duplicate warning, CRUD, and public responses

## Phase 2 — Core domain logic
- [x] `P2-T1` Implement typed invoice extraction and pure Decimal verification
- [x] `P2-T2` Verify tolerance boundaries, huge Decimal values, currencies, mismatches, and non-invoice refusal

## Phase 3 — Services and providers
- [x] `P3-T1` Add mockable deterministic extraction boundary for credential-free application verification
- [x] `P3-T2` Verify extraction failure and retryable provider-unavailable behavior
- [!] `P3-T3` Verify live Gemini structured extraction and one correction retry
  - Blocker: owner Gemini credentials and observed provider responses are required.

## Phase 4 — Interfaces
- [x] `P4-T1` Implement upload/process/list/detail/delete FastAPI routes and safe errors
- [x] `P4-T2` Wire Next.js UI to real API behavior with processing, error, verdict, checks, and result states; clear prior-owner state on identity changes

## Phase 5 — Evaluation and observability
- [x] `P5-T1` Add generated PDFs/images and deterministic ground truth
- [-] `P5-T2` Langfuse tracing is an owner-managed live integration gate, not claimed by local proof
- [x] `P5-T3` Save reproducible 5/5 deterministic verdict results

## Phase 6 — Delivery and audit
- [x] `P6-T1` Run 43 backend tests (plus one credential-gated Postgres skip), evaluation, frontend typecheck, production build, dependency checks, and configuration preflight
- [x] `P6-T2` Trace API/UI flows and complete local adversarial audit with no critical/high finding
- [x] `P6-T3` Synchronize README, decisions, verification docs, demo script, proof, and resume
- [!] `P6-T4` Configure hosted services, verify live integration, deploy, and smoke-test
  - Blocker: owner-managed Gemini, Supabase/storage, Langfuse, and deployment credentials/settings.
  - Live checks: correction retry, five-page PDF policy, storage/persistence, CORS, provider outage, and demo capture.

## Completion summary

- Terminal status: `BLOCKED — owner integration/deployment only`
- Local completion: credential-free implementation and verification gates passed
- Critical/high findings open: `0 local`; live integration remains unverified
- Strongest proof: 43 tests plus one credential-gated integration skip, 5/5 deterministic verdict evaluation, private-response controls, and successful production frontend build
