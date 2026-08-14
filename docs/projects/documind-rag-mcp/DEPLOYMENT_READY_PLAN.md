# DocuMind deployment-ready implementation plan

**Outcome:** after phases P0–P8 pass, the owner only creates cloud projects, enters credentials, applies migrations, deploys the two Vercel roots, and records live proof. Code must not require edits during deployment.

**Current truth (2026-08-14):** strongest local project; deterministic RAG, REST, MCP, Supabase adapters, provider adapters, migrations, tests, build, and offline eval exist. It is not yet a verified hosted application. Caller-provided session UUIDs are demo isolation—not authentication. OCR and durable background ingestion are intentionally absent.

## Target architecture

Browser (Next.js) and MCP clients call one FastAPI service. FastAPI authenticates browser users or validates a deployment demo token, enforces quotas, then invokes shared document/chat services. Supabase Postgres + pgvector stores metadata/chunks/messages; private Storage holds documents. Gemini embeddings and Groq/Gemini generation sit behind typed adapters. Langfuse receives privacy-minimized traces. Vercel runs frontend and API as separate projects. Ingestion remains resumable and bounded per request so it is serverless-safe.

## Phase gates

### P0 — truth, contracts, and deploy topology
- Freeze REST/MCP request and response contracts with OpenAPI snapshots and MCP smoke tests.
- Document local, preview, and production environment matrices; fail startup on contradictory live configuration.
- Decide and record public-demo access policy: Supabase JWT for browser ownership, plus separately scoped MCP bearer tokens. Do not treat UUIDs as authorization.
- Define budgets: upload 10 MB, PDF page cap, context/token cap, request timeout, provider retry budget, and per-user daily quota.
- **Gate:** architecture, threat model, data-flow diagram, env validation tests, and no undocumented variable.

### P1 — identity and tenant isolation
- Add a `Principal` dependency that verifies Supabase JWTs using JWKS; retain explicit `AUTH_MODE=local` fixtures only for tests/local demo.
- Derive ownership from the verified subject, never from a client-supplied owner ID. Keep correlation/session IDs non-authoritative.
- Add RLS policies for documents, chunks, conversations, messages, and citations; service-role paths must re-check owner filters.
- Add cross-user tests for every REST and MCP resource operation.
- **Gate:** anonymous production writes fail; forged/expired tokens fail; cross-user IDs return non-enumerating 404; all isolation tests pass.

### P2 — reliable ingestion and retrieval
- Validate PDF bytes, encryption, page count, extracted-text density, filenames, and storage keys.
- Preserve idempotency keys and cursor progression; add lease/version fields to prevent concurrent duplicate processing.
- Add optional OCR adapter behind a feature flag; return `ocr_required` when disabled instead of fake success.
- Verify pgvector dimension, cosine function, HNSW index, session/user predicate, and query plan against hosted Supabase.
- Add retrieval diagnostics (top scores, threshold, dedup decisions) without leaking full documents.
- **Gate:** retry after each injected failure produces no duplicates; concurrent workers cannot corrupt cursors; empty/scanned/encrypted files have explicit outcomes.

### P3 — grounded generation and provider resilience
- Pin model names through environment variables and expose them in sanitized health metadata.
- Validate structured output with Pydantic, perform one bounded repair, then refuse safely.
- Use exponential backoff only for transient 429/5xx/timeouts; never retry invalid credentials or malformed requests.
- Enforce citation membership and sentence-level support; unsupported output becomes the standard refusal.
- Cache embeddings by content hash and safe answers by user/document-set/question fingerprint.
- **Gate:** primary outage exercises fallback; dual outage returns stable 503; invalid citations never reach users; cache cannot cross owners.

### P4 — portfolio-grade UI/UX
- Add authenticated landing/workspace states, keyboard-accessible upload, progress/retry, document management, chat history, citation drawer, copy/export, and clear local/live mode banner.
- Design mobile, tablet, desktop, empty, loading, partial, error, refusal, rate-limit, and offline states.
- Meet WCAG 2.2 AA basics: semantic controls, focus order, contrast, labels, reduced motion, and screen-reader status updates.
- Add component and browser E2E tests for upload → process → grounded answer and refusal.
- **Gate:** Lighthouse accessibility target >=95 on production build; no dead control; all network failures offer an action.

### P5 — evaluation and observability
- Expand to a versioned 40+ case dataset: supported, unsupported, conflicting, multi-page, injection, malformed and isolation cases.
- Record retrieval recall@k/MRR, citation precision, groundedness, refusal precision/recall, latency, provider errors, and estimated cost with confidence intervals where meaningful.
- Add Langfuse spans for upload, extraction, chunking, embedding, retrieval, evidence gate, generation, citation validation, and MCP calls; redact document text by default.
- Define release thresholds and CI regression gate using deterministic providers; run live eval manually after model changes.
- **Gate:** saved dated result artifact includes git SHA, dataset version, model IDs, configuration and limitations.

### P6 — deployment automation
- Add per-project GitHub Actions for Python tests, eval, frontend tests/typecheck/build, dependency audit, secret scan, and migration lint.
- Validate Vercel entrypoint, route size/duration, CORS exact origins, trusted hosts, HTTPS/proxy behavior, and separate frontend/backend project roots.
- Provide idempotent migration order, rollback notes, seed command, preflight script, post-deploy smoke, and health/readiness endpoints.
- **Gate:** fresh clone passes CI; preview deploy passes smoke with no local files or secret leakage.

### P7 — security and load audit
- Threat-test prompt injection in questions and documents, MIME spoofing, decompression/page bombs, IDOR, token replay, quota bypass, log leakage, SSRF assumptions, and provider payload retention.
- Load-test representative upload/process/chat/MCP traffic; publish p50/p95 and bounded free-tier capacity, not invented scale claims.
- **Gate:** zero critical/high findings; accepted residual risks documented with controls.

### P8 — owner-only launch proof
1. Create Supabase project, private bucket, and apply migrations in order.
2. Configure Vercel API/frontend projects and server-only secrets.
3. Configure providers and optional Langfuse.
4. Run hosted isolation, provider fallback, RAG eval, MCP, and post-deploy smoke.
5. Record URLs, timestamp, git SHA, screenshots, trace IDs (sanitized), and 90–120 second video.

## Required release evidence

CI URL, deployed frontend/API/MCP URLs, migration version, live health output, cross-user denial, grounded answer, refusal, fallback event, live eval artifact, accessibility report, load summary, three screenshots, demo video, license/contact, and honest limitations.

## Research basis

- Vercel FastAPI and Python runtime: https://vercel.com/docs/frameworks/backend/fastapi
- Vercel function limits/duration: https://vercel.com/docs/functions/limitations
- Gemini structured output: https://ai.google.dev/gemini-api/docs/structured-output
- FastAPI security/CORS: https://fastapi.tiangolo.com/tutorial/security/ and https://fastapi.tiangolo.com/tutorial/cors/
