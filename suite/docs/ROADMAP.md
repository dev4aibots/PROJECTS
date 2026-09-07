# Ordered execution roadmap

STATUS.json is authoritative for current state. Checkboxes below are acceptance templates, not completion claims. Each task may be split into subtasks in STATUS before starting; maintain one active task.

| ID | Deliverable and required evidence |
|---|---|
| DOCS | All linked specs, diagrams, schema contracts, learning guides, file ledgers and runbooks written. State/link validator passes. Architecture explicitly planned. |
| CF-01 | Independent Next app; real navigable project workbench in labeled credential-free demo; create/edit/status/filter/search; pure validation/metrics tests, build, responsive browser checks. No fake auth. |
| CF-02 | Platform and cf schema, composite FKs, role policies, SQL tests with actual roles including cross-tenant attempts; fresh migration reset and generated types. |
| CF-03 | Supabase SSR utilities/Proxy, OAuth callback, email auth/recovery UI where configured, signout, workspace onboarding. Validate redirects, session expiry, no shared cache. |
| CF-04 | User-scoped DAL + actions for clients/projects, pagination, duplicate-submit/conflict handling, reload persistence, direct API attacks denied. Replace live UI data path, keep demo isolated. |
| CF-05 | Tasks with due dates, assignments, version conflicts; comments with portal/internal visibility; audit events transactionally. Negative role and concurrent edit tests. |
| CF-06 | Expiring one-use invite links, owner/admin controls, last-owner invariant; client-project links and portal requests. Client cannot read internal data. |
| CF-07 | Private uploads/downloads, size/type policies, metadata cleanup, signed links, persisted in-app notifications, activity list. Unauthorized storage tests. |
| CF-08 | Full E2E and SQL suites, a11y/keyboard/mobile review, build/audit, schema type drift check, deployment dry run, learning/portfolio evidence; code-complete, not hosted-verified. |
| SD-01 | Independent SupportDesk app, brand/inbox; workspace auth reuse pattern, conversation/message schema, state machine and RLS. |
| SD-02 | Bounded TXT/MD/FAQ ingestion, normalization/chunk IDs/hash dedupe, Postgres full-text retrieval, publication boundary, tenant citations; malicious/empty/oversize tests. |
| SD-03 | Deterministic retrieval-only answer plus optional provider adapter, valid citations, refusal/no-answer, handoff, timeout/error handling, idempotency, conversation token design. |
| SD-04 | Public widget only after DB quotas/origin/size budget controls; explicit consent for lead capture; teammate replies, lead export, real derived analytics, retention/deletion. |
| SD-05 | Golden retrieval/evaluation dataset incl tenant leaks and injection, real-provider checks optional but recorded, all UI/RLS tests, operational runbook, evidence. |
| IH-01 | Exact integer money domain, per-line rounding rules, supported currency exponent map, schema/RLS, transition tests, safe-integer/overflow checks. |
| IH-02 | Customers, invoice drafts/items, validated totals and editing UX; server authoritative math, reload persistence and invalid-input cases. |
| IH-03 | Atomic issue/unique sequential number, immutable snapshot, partial/full payment with idempotency, void policy, real downloadable PDF; concurrent issue/payment tests. |
| IH-04 | Expenses, filtered totals per currency, server-computed reporting, CSV safe export, search/pagination, no misleading mixed-currency sum. |
| IH-05 | Finance edge cases/property tests, SQL/E2E/a11y, PDF review, complete learning docs and runbook; explicit non-tax-compliance boundary. |
| FINAL | Owner supplies env/configuration, applies migrations to chosen project, creates three Vercel roots; smoke auth + persistence + cross-user isolation + storage + provider/PDF. Record hosted evidence before release claims. |

## Per-feature mini-checklist
- [ ] Requirement and acceptance example identified.
- [ ] Named file/symbol plan and dependency/version impact recorded.
- [ ] Success, empty, loading, invalid, unauthorized, conflict and backend-failed cases implemented.
- [ ] Backend permission checks and DB constraints independently verified when applicable.
- [ ] Tests run with result and omissions recorded.
- [ ] Learning map updated with actual data flow and code references.
- [ ] FILES and STATUS updated, one next action in HANDOFF, commit and PR updated.

## Do not implement yet
Subscriptions, Stripe payments, mobile native apps, enterprise SSO, vector pipelines/agent swarms, cron-heavy automation, arbitrary crawling, OCR, bank reconciliation, real-time collaborative editors, microservices. Add only after the core release gates and a concrete requirement.
