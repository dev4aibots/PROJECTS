# LLMShield deployment-ready implementation plan

**Outcome:** a secure, measurable LLM gateway demo with protected management data, abuse controls, resilient providers and honest guardrail evaluation. Deployment requires only credentials, migrations and deploy actions.

**Current truth (2026-08-14):** provider fallback, heuristic guards, PII redaction, hash-only logs, Postgres/Langfuse adapters, UI, tests and bounded corpus exist. Gateway/logs/stats are unauthenticated, rate limiting is absent, injection rules are small, and the perfect authored-corpus score is not general security evidence.

## Target architecture

Client → edge/distributed rate limit → FastAPI API-key/JWT authentication → canonical input limits → versioned injection/PII/content guards → provider router with retry/circuit breaker/fallback → output guards → privacy-minimized append-only Postgres log + Langfuse spans → protected operator dashboard. Secrets are hashed and scoped; raw prompts are off by default.

## Phase gates

### P0 — threat model and policy contract
- Define protected assets, attacker capabilities, trust boundaries, retention, fail-open/closed decision for each guard/telemetry component and stable reason codes.
- Separate demo heuristic detection from enforceable controls; document bypass risk prominently.
- Version policy/config and include version in every response/log/eval.
- **Gate:** abuse cases map to preventative, detective and residual controls.

### P1 — authentication and authorization
- Support hashed API keys with prefix, scopes (`gateway:invoke`, `logs:read`, `stats:read`, `admin`), status, expiry and rotation; optionally verify Supabase JWTs for dashboard users.
- Use constant-time comparison and never store full keys. Protect logs/stats; attacks/health expose only safe metadata.
- Add owner/project ID to all logs and filters.
- **Gate:** missing/wrong/expired/revoked/under-scoped credentials fail; cross-project logs cannot be read.

### P2 — distributed abuse controls
- Add per-key and per-IP token-bucket rate limit using Redis/Upstash in live mode and deterministic memory implementation in tests.
- Enforce request bytes, prompt chars, output tokens, concurrency, daily quota and timeout; return standard 429 with retry metadata.
- Add replay/idempotency handling for client retries and bounded queue/backpressure.
- **Gate:** limits survive process restart in live integration and cannot be bypassed by forged forwarded headers.

### P3 — stronger guard pipeline
- Normalize Unicode and common obfuscation safely; preserve original hash. Expand versioned rules across instruction override, role spoofing, prompt extraction, data exfiltration, encoded payload and tool abuse.
- Combine deterministic patterns with optional classifier behind a conservative policy; expose reason/evidence without revealing secret rules.
- Keep PII detectors typed; add configurable regional identifiers and false-positive allowlists. Scan output independently.
- Treat a strong single critical family as block; calibrate weighted scoring on held-out data rather than arbitrary “two families”.
- **Gate:** paraphrased/encoded/multilingual/long-context and clean hard-negative suites meet published thresholds; bypasses remain documented.

### P4 — provider reliability and cost controls
- Classify transient vs permanent provider errors; bounded exponential backoff with jitter, circuit breaker and health state before fallback.
- Validate model IDs, timeout, max tokens and response shape. Never retry authentication/safety/schema failures blindly.
- Record token/cost estimates and enforce per-project budget. Stream only after output-policy strategy is explicit.
- **Gate:** 401, 429, 5xx, timeout, empty, oversized and dual outage each have tested stable behavior.

### P5 — persistence, tracing and privacy
- Make Postgres logging pooled/serverless-safe and append-only; add migrations for projects, API keys, quotas and policy versions.
- Default retention and deletion job; raw prompt/output storage disabled. Redact trace input/output and hash identifiers.
- Add correlation IDs and spans for auth, limits, each guard, provider attempts, output guard and persistence; tracing stays fail-open.
- **Gate:** secret scan and log inspection show no full key, raw PII or provider secret; retention can be demonstrated.

### P6 — portfolio dashboard
- Build API-key setup/rotation (show once), guarded playground, check timeline, redaction preview, provider/fallback status, policy version, filters, latency/cost charts and privacy-safe log details.
- Add responsive, accessible and complete unauthorized/rate-limit/outage/empty states.
- Browser E2E covers safe, blocked, redacted, fallback, 429 and scoped log access.
- **Gate:** every dashboard metric derives from API data; accessibility target >=95.

### P7 — serious evaluation
- Create versioned train/calibration/held-out sets with clean hard negatives, paraphrases, encodings, multilingual attacks, indirect injection and PII variants.
- Report per-class precision/recall/F1, ROC/PR where scored, false-positive examples, bypass rate, provider latency/cost and bootstrap confidence intervals.
- Add deterministic CI regression thresholds; run optional live classifier/provider suite separately.
- **Gate:** README never generalizes authored-fixture perfection; saved artifact includes policy/model/dataset/git versions.

### P8 — CI/deploy/launch proof
- CI: tests/eval/Postgres/Redis integration/frontend/build/E2E/dependency audit/secret scan.
- Add env preflight, migration/seed/rollback, exact CORS/trusted proxy configuration, readiness, load test and post-deploy smoke.
- Owner configures Postgres, Redis, providers, Langfuse and Vercel; then records scoped-auth denial, 429, fallback, trace, eval, p95/cost, URLs, screenshots and video.

## Research basis

- FastAPI security schemes: https://fastapi.tiangolo.com/reference/security/
- FastAPI proxy headers: https://fastapi.tiangolo.com/advanced/behind-a-proxy/
- Vercel Fluid compute: https://vercel.com/docs/fluid-compute
