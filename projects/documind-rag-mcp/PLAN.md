# DocuMind Phase 0 — Implementation Plan

Status: awaiting owner review before application code

## Acceptance boundary

The first build milestone will prove one vertical slice locally: a valid small PDF is page-extracted, chunked idempotently, embedded through a replaceable provider fixture, retrieved above a threshold, and answered with citations that pass deterministic validation. An unrelated question must return the specified grounded refusal without calling an LLM.

## Repository structure

```text
projects/documind-rag-mcp/
├── api/index.py                 # Vercel ASGI entrypoint
├── backend/
│   ├── app/main.py              # FastAPI composition only
│   ├── app/api/                 # thin health, document, chat, conversation routes
│   ├── app/core/                # settings, errors, logging, tracing adapters
│   ├── app/domain/              # Pydantic request/response and internal models
│   ├── app/providers/           # embeddings, Groq/Gemini, optional Langfuse
│   ├── app/repositories/        # document, conversation, retrieval protocols + Supabase implementations
│   ├── app/services/            # ingestion, retrieval, grounded answer, documents, MCP facade
│   └── tests/                   # unit, service/contract, and API tests
├── frontend/                    # Next.js App Router + TypeScript + Tailwind
│   ├── app/                     # landing and three-panel workspace
│   ├── components/              # upload, document list, chat, sources, states
│   └── tests/                   # Vitest component/client tests
├── migrations/                  # numbered idempotent Supabase SQL
├── evals/                       # golden JSONL, deterministic metrics, optional live judge
├── sample_docs/                 # generated fictional documents only
├── scripts/                     # sample PDF generation, MCP check, deployment smoke
├── docs/                        # architecture, DB, RAG, MCP, tests, evals, deployment, limitations
├── DECISIONS.md
├── README.md
├── .env.example
├── requirements.txt
└── vercel.json
```

## Data design

- `documents`: UUID, safe original filename, MIME, size, storage path, status enum, page count, persisted page cursor, sanitized error, session UUID, timestamps.
- `document_chunks`: UUID, document FK, page number, chunk index, content, token count, embedding, timestamp, unique `(document_id, page_number, chunk_index)`.
- `conversations`, `messages`, and `message_citations`: durable chat and validated citation records scoped through session ownership.
- `retrieval_logs`: query metadata, configured threshold/top-k, returned count, maximum similarity, and duration; no full document payload in tracing.
- HNSW cosine index is the initial pgvector choice because the demo corpus is read-heavy and incrementally inserted; exact parameters and the small-corpus tradeoff will be recorded before migration implementation.
- All repository reads and mutations include `session_id` ownership constraints. Database constraints, not UI filtering, protect isolation.

## API contracts

| Method and path | Request | Success | Important failures |
|---|---|---|---|
| `GET /api/health` | none | component status, no secrets | degraded status remains structured |
| `POST /api/documents/upload` | multipart PDF + session header/query | validated document metadata | 400 wrong/corrupt/oversized input; no storage write |
| `POST /api/documents/{id}/process` | session + optional batch size | cursor, progress, `done` | 404 isolation; retryable provider error preserves cursor |
| `GET /api/documents` | session | scoped documents | invalid session 422 |
| `DELETE /api/documents/{id}` | session | 204 after DB/storage cleanup | 404 isolation; safe partial-failure reporting |
| `POST /api/chat` | question, session, optional conversation/doc IDs | typed grounded answer | evidence refusal is 200; providers unavailable is 503 |
| `GET /api/conversations/{id}` | session | messages and citations | 404 on other session |
| `GET /api/retrieval/{message_id}` | session | retrieved chunks and scores | 404 on other session |
| MCP tools | typed tool args | same service DTOs | same service errors mapped to MCP errors |

All errors use `{"error":{"code":"...","message":"..."}}`; stack traces and provider bodies stay server-side.

## Core service boundaries

1. `DocumentService` validates metadata, creates storage/database records, lists scoped documents, and coordinates deletion.
2. `IngestionService` reads a bounded page batch, chunks sentence-aware text, embeds in batches, upserts by the unique chunk key, and advances the cursor only after durable success.
3. `RetrievalService` embeds the question, calls the pgvector function, deduplicates overlap, favors page diversity, and caps context.
4. `AnswerService` applies input screening and the evidence gate, calls the fallback LLM router only when evidence exists, validates structured output, validates every citation against retrieved chunk IDs/pages, and persists only the final safe response.
5. `LLMRouter` retries one transient primary failure with bounded backoff, then uses the secondary provider. Corrective structured-output retry is separate from transport retry.
6. `MCPFacade` calls the same document/retrieval/answer services; it owns no duplicate business logic.

## Frontend component plan

- Landing: concise pitch, four evidence-oriented capability cards, real architecture diagram, and Open Demo link. Evaluation values remain visibly “not run” until generated.
- Workspace shell: generated session UUID in local storage; document rail, chat, and source inspector.
- Upload flow: preflight feedback, progress/status polling, resumable process loop, retry, and deletion confirmation.
- Chat flow: empty state, pending state, cited grounded response, amber insufficient-evidence response, safe red dependency error.
- Source inspector: exact retrieved excerpt, filename, page, and similarity; citation selection focuses the matching source.

## Test and evaluation plan

### Pure unit tests

- PDF signature/extension/MIME/size validation.
- Sentence-aware chunk boundaries, overlap, token budget, empty pages.
- Page cursor advancement and idempotent chunk keys.
- Retrieval deduplication, page diversity, threshold, context cap, confidence derivation.
- Citation acceptance, hallucinated chunk/page stripping, and zero-valid-citation refusal.

### Service and API tests

- Happy-path ingest/process/ask using in-memory protocol fakes and recorded provider fixtures.
- No-evidence question asserts zero LLM calls.
- Corrupt/encrypted/empty PDF becomes a sanitized failed status.
- Embedding 429 preserves the previous cursor and retry creates no duplicate chunks.
- Primary retry/fallback and both-providers-down structured 503.
- Malformed model JSON corrects once, then refuses safely.
- Cross-session document/conversation access is not found.
- Poisoned document cannot override the grounded system contract; residual risk remains documented.

### Evaluation

- Generate three fictional PDFs and 15–20 versioned cases, including exactly five unanswerable questions.
- Deterministic metrics: retrieval hit, citation accuracy, refusal correctness.
- Faithfulness judge is optional/live and clearly separated from offline mocked tests.
- `evals/run.py` writes a dated, configuration-stamped `docs/evaluation.md`; no result enters README until actually run.

## Implementation phases and gates

1. **Persistence:** migrations, repository protocols/implementation, settings, and validation tests.
2. **Domain:** PDF extraction, chunking, retrieval shaping, evidence gate, citation validator, and unit tests.
3. **Services/providers:** typed provider adapters, retry/fallback, tracing adapter, and service tests.
4. **FastAPI/MCP:** contracts, error mapping, API tests, and local MCP script.
5. **Frontend:** real API client and all required states; Vitest and production build.
6. **Evaluation/observability:** corpus, metrics, saved honest results, optional live tracing verification.
7. **Audit/deployment:** adversarial audit, clean builds, fresh migration check, Vercel readiness, then owner credential/deploy actions and live smoke.

Each phase updates `docs/projects/documind-rag-mcp/{CHECKLIST,RESUME,PROOF}.md` and receives a focused test result before the next begins.

## Decisions requiring confirmation

No product-scope decision blocks implementation. The initial choices are: Python MCP Streamable HTTP unless Vercel compatibility fails in a reproducible test; HNSW cosine retrieval; 800-token target with 15% overlap; threshold `0.35` as configuration, not a claimed optimum; and local protocol fakes for secret-free tests. Any change will be documented with evidence rather than silently substituted.

## External actions deferred

Supabase project creation, Groq/Gemini/Langfuse keys, Vercel project settings, real provider evaluation, and live deployment are intentionally deferred. They will not be represented as complete until verified against owner-managed accounts.
