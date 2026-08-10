# DocuMind Engineering Decisions

These records describe the implemented local milestone. Live infrastructure choices remain unverified until deployment.

## 1. Shared service layer for REST and MCP

- **Context:** The retrieval engine must serve a browser, API clients, and MCP clients without divergent rules.
- **Options considered:** duplicate MCP logic; MCP calling REST; both protocols calling the same Python services.
- **Choice:** FastAPI routes and `MCPFacade` call the same `DocumentService` and `ChatService` instances.
- **Why:** Validation, session isolation, evidence gating, and citation checks have one implementation.
- **Tradeoff accepted:** The Python deployment bundle includes the MCP SDK and both protocols share one process lifecycle.

## 2. Streamable HTTP MCP mounted in FastAPI

- **Context:** Vercel needs an HTTP-compatible MCP transport.
- **Options considered:** standalone stdio/SSE service; Next.js `mcp-handler`; Python SDK Streamable HTTP.
- **Choice:** Mount the official Python SDK's stateless Streamable HTTP ASGI app at `/mcp`.
- **Why:** It keeps one language and one service graph; local protocol tests prove REST and MCP coexist.
- **Tradeoff accepted:** Vercel runtime behavior still requires a live smoke test, and long-lived state cannot live in process memory.

## 3. Resumable page batches for serverless ingestion

- **Context:** A PDF may outlive a short serverless invocation.
- **Options considered:** process synchronously; queue worker; bounded page batches with a persisted cursor.
- **Choice:** `/api/documents/{id}/process` advances `last_processed_page` only after a batch is durable; the client repeats until `done=true`.
- **Why:** Retries resume instead of restarting and the unique chunk key prevents duplicates.
- **Tradeoff accepted:** The client orchestrates several requests; production scale would favor a queue.

## 4. Approximate 800-token chunks with 15% overlap

- **Context:** Retrieval needs enough context without swallowing whole pages.
- **Options considered:** fixed characters; full pages; token-estimated sentence-aware chunks.
- **Choice:** Sentence-aware chunks target roughly 800 tokens with 15% overlap and preserve page numbers.
- **Why:** It balances semantic completeness, retrieval precision, and citation granularity.
- **Tradeoff accepted:** Token estimation is not the provider's exact tokenizer and scanned PDFs still need OCR.

## 5. Configurable 0.35 evidence threshold

- **Context:** Calling the LLM on weak matches creates confident unsupported answers.
- **Options considered:** always generate; fixed threshold; environment-configurable threshold.
- **Choice:** Gate generation at `SIMILARITY_THRESHOLD` (default `0.35` for live embeddings; deterministic local fixtures use a documented lower threshold).
- **Why:** No-hit questions refuse before any chat-provider call.
- **Tradeoff accepted:** The default is a starting value, not a universally optimized score; each corpus needs evaluation.

## 6. Deterministic citation validation

- **Context:** A model can invent document IDs, pages, or excerpts.
- **Options considered:** trust model JSON; regex citations; validate every citation against retrieved chunks.
- **Choice:** Strip citations not present in retrieved evidence and replace citation-free answers with the standard refusal.
- **Why:** Authorization and grounding cannot depend on model obedience.
- **Tradeoff accepted:** A partly useful answer can be refused if its citations cannot be validated.

## 7. HNSW cosine index

- **Context:** The corpus is incrementally inserted and queried more often than rebuilt.
- **Options considered:** exact scan; IVFFlat; HNSW.
- **Choice:** HNSW with cosine distance in migration 002.
- **Why:** HNSW gives strong read latency without a training step and fits incremental inserts.
- **Tradeoff accepted:** It costs more memory and build time; exact search may be simpler for a tiny demo corpus.

## 8. Optional live adapters with deterministic local defaults

- **Context:** Tests and reviews must run without secrets or rate-limited providers.
- **Options considered:** require cloud accounts; broad mocks; protocol-compatible memory repositories and deterministic providers.
- **Choice:** Live Supabase/Gemini/Groq/Langfuse adapters activate only when configured; local mode exercises real domain and service behavior.
- **Why:** The complete local verification is reproducible and failure paths are controllable.
- **Tradeoff accepted:** Local green tests do not prove cloud schema, provider quality, quotas, or deployment health.

## 9. Self-contained citations survive source deletion

- **Context:** Chat history should remain intelligible after a user deletes an indexed document.
- **Options considered:** cascade-delete citations; forbid deletion; snapshot citation display fields and null the chunk relation.
- **Choice:** Persist document label/page/excerpt and use `ON DELETE SET NULL` for `chunk_id`.
- **Why:** Deletion removes source content while preserving an auditable historical answer.
- **Tradeoff accepted:** The displayed excerpt is historical and can no longer be revalidated against a deleted source.
