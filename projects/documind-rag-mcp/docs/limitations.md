# Limitations and Residual Risk

## Current milestone boundary

The local application, deterministic providers, generated corpus, tests, MCP protocol, evaluation harness, typecheck, and production frontend build are verifiable without secrets. Supabase, Gemini, Groq, Langfuse, Vercel, and a public URL are not configured or claimed.

## Retrieval and model quality

- The default similarity threshold is a starting point, not a corpus-independent optimum.
- Offline faithfulness is a deterministic support check, not an independent live LLM judge.
- Hash-based local embeddings prove pipeline behavior, not semantic quality of Gemini embeddings.
- `pypdf` does not OCR scanned or image-only documents and complex layouts may extract out of reading order.
- Token counts are estimates; provider tokenizers can differ.

## Prompt injection

Retrieved text is untrusted. Grounded prompting, question screening, session scoping, and deterministic citation validation prevent a document from directly changing authorization or inventing accepted source references. They do not prove that every cited statement is semantically safe or that a malicious passage cannot influence wording. Production hardening should add content provenance, stronger document-side injection detection, independent claim-level evaluation, and human review for consequential use.

## Privacy and security

- Session UUIDs isolate demo data but are not authentication. Production requires authenticated identities, authorization policies, row-level security, rate limits, and abuse controls.
- The backend currently trusts an `X-Session-ID` supplied by the caller.
- Uploaded document content is sent to configured embedding/chat providers in live mode; deployment needs retention, residency, consent, and deletion policies.
- CORS is not an authorization mechanism. `FRONTEND_ORIGIN` only controls browser access.
- Historical citation labels/excerpts survive source deletion by design, so a deletion policy must decide whether chat history should also be erased.

## Serverless and scale

- Resumable page batches fit short functions but the browser drives orchestration. A production system should use a durable queue, worker, leases, and dead-letter handling.
- In-memory mode loses all data on restart and is only for local verification.
- HNSW parameters have not been benchmarked against a production corpus.
- Free-tier services can pause, throttle, or exhaust quotas; the provider router returns a structured temporary-unavailable response but cannot remove the limit.
- Stateless MCP works for tools, but large results and long operations still face platform limits.

## Deployment

The two-project Vercel topology and rewrites are documented but not live-tested. A deployment must apply migrations in order, configure all origins and secrets, verify storage policies, and smoke-test REST, MCP, UI, deletion, refusal, fallback, and observability before it can be called complete.
