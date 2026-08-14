# Five-project deployment-readiness master plan

Updated: 2026-08-14

## Definition of “ready”

A project is **deployment-ready** only when a fresh clone passes all local/CI gates and no source edit is required to launch. The owner should only need to:

1. create the documented cloud resources;
2. apply versioned migrations/seed commands;
3. add server-only environment variables;
4. deploy the documented frontend/backend roots;
5. run the supplied live smoke/evaluation; and
6. add resulting URLs/screenshots/video to the proof file.

“Code exists,” “environment variable is listed,” and “migration exists” do not prove runtime integration. A credential-gated integration must have a production adapter, factory selection, contract tests and a live-smoke command before it is called ready.

## Portfolio order

1. **DocuMind** — flagship; finish identity/cloud isolation and live RAG proof.
2. **ZeroTrust SQL** — implement actual restricted Postgres execution and harden policy.
3. **LLMShield** — add scoped auth, distributed limits and held-out adversarial evaluation.
4. **StateGraph Agent** — rebuild around real LangGraph/checkpoints/tools before promotion.
5. **DocuExtract** — replace filename fixture extraction with real Gemini bytes and persistence.

Work one project/milestone at a time. Shared CI/security conventions may be delivered once across all projects, but acceptance/proof remains project-specific.

## Universal phases

| Phase | Required result |
|---|---|
| U0 Truth | README/status exactly matches runtime; fake/dead integrations removed or labelled |
| U1 Contracts | Typed API/domain/error schemas, state diagrams and config matrix |
| U2 Security | verified identity, object ownership, exact CORS, secret hygiene, abuse limits |
| U3 Runtime | live adapters are selected by validated configuration and covered by contract/integration tests |
| U4 UX | responsive accessible UI; all empty/loading/error/refusal/retry states; no dead controls |
| U5 Evaluation | versioned held-out dataset, meaningful metrics, failure analysis, release thresholds |
| U6 Reliability | transient retry/fallback, idempotency, timeouts, concurrency and restart behavior |
| U7 Observability | correlation IDs, privacy-safe structured logs/traces, health/readiness and cost/latency |
| U8 Delivery | CI, migrations, preflight, post-deploy smoke, rollback and dated proof |

## Quality bar for portfolio claims

- No “production-ready” claim without a live deployment, CI, authentication/ownership, rate limits, monitoring and operations proof.
- Deterministic fixtures are regression tests, not model-quality evidence.
- Every metric names dataset version, case count, model/policy/config, git SHA and date.
- Zero critical/high audit findings. Medium residual risks are explicit.
- Three real screenshots and a 90–120 second demo per promoted flagship.
- READMEs lead with problem, differentiator, architecture, measured evidence, live links and limitations.

## Shared delivery checklist

- [ ] Python versions and dependencies pinned; package metadata and licenses clear.
- [ ] Frontend lockfile, strict TypeScript, lint, unit/component and browser E2E.
- [ ] GitHub Actions matrix with Python tests/evals and frontend typecheck/build/audit.
- [ ] Dependabot/Renovate or documented dependency update process.
- [ ] Secret scanning and no credentials in browser bundles/logs.
- [ ] `.env.example` contains every variable with safe comments; `preflight` validates combinations.
- [ ] Health is liveness only; readiness checks configured dependencies without leaking secrets.
- [ ] Migration ordering, least-privilege roles, RLS/ownership, seed and rollback notes.
- [ ] Exact origin allowlist; trusted proxy/host behavior; security headers.
- [ ] Timeouts, retries, idempotency, provider error taxonomy and stable error envelopes.
- [ ] Rate/size/token/concurrency/daily-cost limits appropriate to public free-tier demos.
- [ ] Post-deploy smoke accepts URLs/credentials through environment, never hard-coded values.
- [ ] `PROOF.md` records command, timestamp, git SHA, result and artifact URL.

## Source research used for the plans

Official documentation should be rechecked before deployment because provider limits/models change:

- Vercel FastAPI: https://vercel.com/docs/frameworks/backend/fastapi
- Vercel Python runtime/limits: https://vercel.com/docs/functions/runtimes/python
- Vercel function duration: https://vercel.com/docs/functions/configuring-functions/duration
- Gemini document processing: https://ai.google.dev/gemini-api/docs/document-processing
- Gemini structured output: https://ai.google.dev/gemini-api/docs/structured-output
- FastAPI security: https://fastapi.tiangolo.com/tutorial/security/
- FastAPI CORS/proxy guidance: https://fastapi.tiangolo.com/tutorial/cors/ and https://fastapi.tiangolo.com/advanced/behind-a-proxy/
- PostgreSQL client/statement controls: https://www.postgresql.org/docs/current/runtime-config-client.html

## Per-project plans

- `projects/documind-rag-mcp/DEPLOYMENT_READY_PLAN.md`
- `projects/stategraph-agent/DEPLOYMENT_READY_PLAN.md`
- `projects/zerotrust-sql/DEPLOYMENT_READY_PLAN.md`
- `projects/docuextract/DEPLOYMENT_READY_PLAN.md`
- `projects/llmshield/DEPLOYMENT_READY_PLAN.md`

The repository resume guide is `AGENT_RESUME_GUIDE.md`. Project `CHECKLIST.md`, `RESUME.md`, and `PROOF.md` remain the live state; plans describe the full route, not completed work.
