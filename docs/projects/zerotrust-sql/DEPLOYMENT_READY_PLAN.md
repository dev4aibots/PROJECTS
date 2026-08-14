# ZeroTrust SQL deployment-ready implementation plan

**Outcome:** a public attack-lab demo where a model may propose SQL but only deterministic policy and a database read-only role can authorize execution. Deployment requires only infrastructure, migrations and credentials.

**Current truth (2026-08-14):** strong SQLGlot policy/eval and read-only SQLite demo exist. `DATABASE_URL` and the Postgres migration are not connected to runtime execution. Authentication, durable audit, rate limits and alias-aware column provenance need completion.

## Target architecture

Next.js attack lab → authenticated/rate-limited FastAPI → provider router (proposal only) → SQLGlot parse/normalize → statement/table/function/column/lineage/complexity policy → LIMIT rewrite → transaction-scoped Postgres executor using `nl_query_ro` → shaped rows → append-only audit/Langfuse metadata. The executor refuses startup if a live role is over-privileged.

## Phase gates

### P0 — security invariants
- Write explicit attacker capabilities, protected assets, allowlisted schema and non-goals.
- Freeze policy reason codes and same-shape allowed/blocked API responses.
- Define query budgets: one SELECT, max joins/subqueries/AST nodes, 100 rows, 5 s statement timeout, output byte cap.
- **Gate:** each invariant maps to validator, DB control and test.

### P1 — validator correctness
- Resolve every column through table/CTE/alias lineage; reject unknown, ambiguous and cross-table-invalid columns.
- Reject locking, `SELECT INTO`, data-modifying CTEs, system catalogs, comments/hints where unsafe, unapproved set operations and expensive constructs.
- Allowlist functions by normalized dialect and reject schema-qualified bypasses.
- Rewrite LIMIT in the AST and re-parse final SQL; cap offset and result bytes.
- Add property/metamorphic fuzz tests and encoded/case/quoted/schema-qualified bypass corpus.
- **Gate:** zero malicious fixture execution; safe corpus maintains documented acceptance; every rejection has stable reason.

### P2 — real Postgres executor
- Implement a database protocol plus `PostgresDatabase` selected only when `DATABASE_URL` is present.
- Use psycopg pool appropriate for serverless; open read-only transactions; set local `statement_timeout`, `lock_timeout`, `idle_in_transaction_session_timeout`, search path and row security.
- At startup/preflight verify `current_user`, transaction read-only, grants, prohibited table denial and inability to write/create/call dangerous functions.
- Keep SQLite deterministic mode explicit and behavior-compatible.
- **Gate:** integration tests run against disposable Postgres and prove writes/decoy/system catalogs fail even if validator is bypassed.

### P3 — generation and failure policy
- Provide schema-only context; never expose sample PII, credentials, audit records or DB errors.
- Require typed `{sql, explanation}` output, one correction for syntax only, transient retry/fallback, and honest unsupported-question refusal.
- Never ask the model to decide safety. Cache only proposal output with schema/policy/model version in key.
- **Gate:** malformed output, 401, 429, timeout and dual outage are deterministic and audited.

### P4 — access, abuse and audit
- Add API-key/JWT auth for query and audit endpoints; public demo uses a low daily quota and no unrestricted audit detail.
- Add distributed per-principal/IP rate limits and request/body limits.
- Persist append-only audit metadata: prompt hash, model, generated/final SQL hash/text policy, checks, result count, duration, principal, correlation ID. Redact sensitive literals.
- **Gate:** logs/stats are protected; quota cannot be bypassed by process restart; audit failures fail closed/open per documented policy.

### P5 — portfolio UI
- Build schema explorer, question composer, generated-vs-executed SQL diff, policy checklist, results table/chart, attack presets and searchable audit timeline.
- Show local/live and role verification clearly. Add accessible keyboard/table behavior, responsive layout and all error/empty/rate-limit states.
- Add E2E tests for safe query, blocked mutation, LIMIT rewrite, provider outage and unauthorized audit.
- **Gate:** no control uses mock data outside explicit deterministic mode; accessibility target >=95.

### P6 — evaluation and observability
- Expand golden natural-language cases and 100+ attack variants; report allow precision/recall separately, refusal rate, reason distribution, execution correctness, latency and cost.
- Trace generation, parse, each policy family, DB execution and shaping without recording raw sensitive prompts by default.
- Add live Postgres regression suite and query-plan review for approved examples.
- **Gate:** versioned dated report includes model/schema/policy/git SHA and false-positive analysis.

### P7 — CI/deploy hardening
- CI runs Python tests, Postgres service integration, fuzz budget, eval, frontend typecheck/build, dependency audit and secret scan.
- Add migration/preflight/seed/live-smoke scripts, exact CORS/trusted hosts, sanitized health/readiness and rollback notes.
- **Gate:** fresh hosted DB can be created from migrations; smoke verifies role restrictions before app accepts traffic.

### P8 — owner launch proof
Create Supabase/Postgres, apply schema and grants, set the restricted connection string and provider/rate-limit/Langfuse credentials, deploy API/UI, then run attack corpus against hosted Postgres and record CI, URL, role preflight, screenshots and demo.

## Research basis

- PostgreSQL transaction read-only and statement timeout documentation: https://www.postgresql.org/docs/current/runtime-config-client.html and https://www.postgresql.org/docs/current/runtime-config-client.html#RUNTIME-CONFIG-CLIENT-STATEMENT
- FastAPI security: https://fastapi.tiangolo.com/tutorial/security/
- Vercel FastAPI deployment: https://vercel.com/docs/frameworks/backend/fastapi
