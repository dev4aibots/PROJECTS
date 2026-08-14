# Projects registry

Last verified: 2026-08-14

| Priority | Project | Status | Verified local progress | First remaining phase |
|---:|---|---|---|---|
| 1 | `documind-rag-mcp` | `QUEUED` | 135 tests; 15-case deterministic eval; REST/MCP; frontend tests/build | verified identity, tenant isolation and hosted RAG proof |
| 2 | `zerotrust-sql` | `BLOCKED — owner integration only` | 78 tests; 13/13 eval; scope-aware AST wall; scoped auth; durable audit/rate limits; 4 browser E2E | disposable Postgres/provider/deployment proof |
| 3 | `llmshield` | `ACTIVE` | 17 tests; 40-case bounded eval; guards/redaction/fallback/telemetry | scoped auth and distributed rate limits |
| 4 | `stategraph-agent` | `BLOCKED — owner integration only` | 34 tests + 1 gated integration; 4 browser E2E; held-out eval; preflight/smoke | disposable Postgres/Supabase proof, live providers/telemetry and deploy |
| 5 | `docuextract` | `BLOCKED — owner integration only` | 43 tests + 1 gated integration; 5/5 fixture verdicts; identity, owner-scoped Postgres/private storage, Gemini adapter | disposable Supabase/Gemini/deployment proof |

## Active project

`llmshield`. ZeroTrust SQL is now credential-free source complete and owner-integration blocked after scope-aware lineage, scoped bearer authentication, privacy-safe durable audit, distributed abuse limits, fail-closed live configuration, preflight/live smoke tooling, 78 tests, evaluation, build, and four Chromium E2E scenarios passed. Continue LLMShield with scoped authentication, distributed rate limits, and a stronger held-out adversarial evaluation before requesting live credentials.

## Latest shared verification

- Backend: DocuMind 135, StateGraph 34 passed + 1 credential-gated Postgres test skipped, ZeroTrust 78, DocuExtract 43 passed + 1 credential-gated Postgres test skipped, and LLMShield 17 tests passed.
- StateGraph passed its 18-case held-out routing/citation gate and four Chromium workflow/mobile scenarios; ZeroTrust passed four Chromium safe/blocked/bounded/mobile scenarios.
- Offline authored evaluations: DocuMind 15 cases, ZeroTrust 13/13, DocuExtract 5/5 and LLMShield 40 bounded cases passed.
- All five frontends passed available tests, TypeScript, production builds and `npm audit --omit=dev --audit-level=high` with zero production vulnerabilities.
- CI definition remains prepared at `docs/templates/portfolio-ci.yml`; owner workflow-write permission is required to activate it.
- Dev4AIbots remains removed and must not return.

## Truth boundary

None of the five is a verified public deployment. StateGraph signed-JWT, cross-user and RLS-session tests prove local contracts/source, not real Supabase JWT/RLS or hosted restart behavior. Local fixtures do not prove live model quality, hosted database isolation, latency, cost, traces, URLs, screenshots or uptime. “Deployment-ready” still means no source edit is needed after owner resources/credentials are added; see `IMPLEMENTATION_MASTER_PLAN.md`.
