# PROJECT 1 — FLAGSHIP: Enterprise RAG + MCP + Evaluation Harness

**Repo name:** `enterprise-rag-mcp`
**Days:** 2–3 of the sprint (most time of any project)
**Hiring signal:** RAG done properly (the #1 skill in 2026 job listings) + MCP (fast-growing differentiator) + evaluation harness (the #1 screening signal hiring managers look for)

> Paste `01-master-context.md` first, then this prompt.

---

```
==================================================
PROJECT SPECIFICATION
==================================================

PROJECT NAME: DocuMind — Enterprise Document Intelligence Agent (RAG + MCP)

ONE-SENTENCE PITCH:
Upload business documents, ask questions, and get answers that are grounded,
cited to exact pages, evaluated for faithfulness, and refused when the
evidence isn't there — with the same retrieval engine exposed as an MCP
server for AI assistants.

WHY THIS EXISTS (write this into the README):
Most RAG demos hallucinate confidently. This system is designed around the
opposite principle: it must PROVE every claim with a citation or refuse to
answer. It also demonstrates that a retrieval engine is a reusable service:
the identical service layer powers the web UI, the REST API, and an MCP
server that Claude/other assistants can call as a tool.

==================================================
CORE USER FLOWS (all must actually work end-to-end)
==================================================

FLOW 1 — Ingest:
User uploads a PDF (max 10MB, validated MIME + extension + magic bytes).
→ stored in Supabase Storage
→ text extracted page-by-page (use pypdf; keep the bundle lean)
→ page-aware chunking (target ~800 tokens, 15% overlap, never split
  mid-sentence when avoidable; store page_number + chunk_index)
→ embeddings via Gemini embedding API (batch requests, respect rate limits)
→ chunks + embeddings persisted to pgvector
→ document status transitions: uploaded → processing → ready | failed
→ UI shows live status (poll every 2s; no websockets needed)

Because Vercel functions are short-lived: process documents in RESUMABLE
BATCHES. POST /api/documents/{id}/process handles up to N pages/chunks per
invocation, persists a cursor (last_processed_page) on the document row, and
returns {done: false, progress: 0.6}. The frontend keeps calling until
done: true. Document this serverless pattern in DECISIONS.md — it is an
interview talking point.

FLOW 2 — Ask (the core RAG pipeline):
question → input validation (length, non-empty, injection screening)
→ query embedding
→ pgvector similarity search (top_k=8, cosine, optional document filter)
→ EVIDENCE GATE: if zero chunks above similarity threshold (default 0.35,
  env-configurable) → do NOT call the LLM. Return the honest refusal:
  "I couldn't find sufficient evidence in the indexed documents." with
  grounded=false. This is a FEATURE — surface it in the UI with a distinct
  amber state, not an error state.
→ lightweight rerank: deduplicate near-identical chunks, prefer page
  diversity, cap context at ~4000 tokens
→ grounded generation with a strict system prompt: use ONLY the provided
  evidence; every claim must cite [doc_id p.X]; if evidence is insufficient,
  say so
→ structured output (Pydantic):
    {
      "answer": str,
      "citations": [{"document_id", "filename", "page", "excerpt"}],
      "grounded": bool,
      "confidence": float   # derived from retrieval scores, NOT invented
    }
→ CITATION VALIDATOR (deterministic post-check): every citation must
  reference a chunk that was actually retrieved, with a page number that
  exists. If the LLM cites something not retrieved → strip it; if the answer
  then has zero valid citations → replace with the refusal response and log
  a "citation_violation" event to Langfuse.
→ persist conversation + message + retrieval_log rows

FLOW 3 — Inspect:
For any answer, the user can expand a "Sources" panel showing each cited
chunk: filename, page, similarity score, and the exact excerpt highlighted.
This transparency panel is the money shot for the demo video.

FLOW 4 — MCP:
Expose the SAME service layer via an MCP server with tools:
  - search_documents(query, top_k) → ranked chunks with scores
  - ask_question(question) → the full grounded answer object
  - list_documents() → document metadata
Implementation: MCP over Streamable HTTP so it deploys on Vercel (Vercel
officially documents MCP server deployment). Python side: use the official
MCP Python SDK; if the Python Streamable HTTP path fights the Vercel
runtime, implement the MCP endpoint as a thin Next.js route using the
mcp-handler package that calls the FastAPI service endpoints internally —
choose whichever is cleaner, implement ONE of them fully, and document the
choice + tradeoff in DECISIONS.md. Provide a copy-paste snippet in the
README showing how to add this MCP server to Claude Desktop / any MCP
client, and a scripts/test_mcp.py that exercises each tool locally.

==================================================
DATABASE SCHEMA (migrations/, idempotent SQL)
==================================================

documents(id uuid pk, filename, content_type, file_size, storage_path,
          status, page_count, last_processed_page, processing_error,
          session_id, created_at, updated_at)
document_chunks(id uuid pk, document_id fk, page_number, chunk_index,
          content, token_count, embedding vector(768) or provider dimension,
          created_at)
conversations(id uuid pk, session_id, title, created_at)
messages(id uuid pk, conversation_id fk, role, content, grounded,
          confidence, created_at)
message_citations(id uuid pk, message_id fk, chunk_id fk, page_number,
          excerpt)
retrieval_logs(id uuid pk, message_id fk, query, top_k, threshold,
          returned_count, max_similarity, duration_ms, created_at)

- HNSW (or IVFFlat) index on the embedding column — justify the choice in
  DECISIONS.md.
- A Postgres function match_document_chunks(query_embedding, match_count,
  similarity_threshold, filter_document_ids) for the similarity search.
- session_id scoping everywhere so demo users don't see each other's docs.

==================================================
API SURFACE (FastAPI, auto OpenAPI docs at /api/docs)
==================================================

GET    /api/health                      → status + db + provider reachability
POST   /api/documents/upload            → multipart, returns document
POST   /api/documents/{id}/process      → resumable batch processing
GET    /api/documents?session_id=       → list with status
DELETE /api/documents/{id}              → cascades chunks + storage object
POST   /api/chat                        → {question, conversation_id?, document_ids?}
GET    /api/conversations/{id}          → messages + citations
GET    /api/retrieval/{message_id}      → full retrieval log for transparency panel

==================================================
FRONTEND (pages)
==================================================

/            Landing: name, pitch, "Open Demo", 4 feature cards
             (Grounded citations / Honest refusals / MCP server / Eval
             results with real numbers), architecture diagram image.
/app         3-panel workspace:
             left  = documents (upload, status chips, delete)
             center= chat (messages, citation chips [filename p.X] that
                     scroll/open the source panel)
             right = sources panel (chunk excerpts, similarity scores)
             States: empty ("upload a document to begin"), loading
             (skeleton + streaming-style progressive reveal is optional),
             refusal (amber "insufficient evidence" card), error (red card
             with retry).

==================================================
EVALUATION HARNESS (this section is NOT optional)
==================================================

Create evals/ with a pytest-runnable harness:

1. Golden dataset: evals/golden.jsonl with 15–20 Q/A pairs authored against
   3 sample documents you create in sample_docs/ (write realistic fake
   company docs: a refund policy PDF, an employee handbook PDF, a product
   spec PDF — generate them with a script, scripts/make_sample_pdfs.py,
   using reportlab).
2. Metrics per question, computed with deterministic checks + LLM-as-judge
   via the provider abstraction:
   - retrieval_hit: did top_k contain the gold page?
   - faithfulness: judge scores whether every answer claim is supported by
     retrieved context (0–1)
   - citation_accuracy: % of citations pointing at truly retrieved chunks
   - refusal_correctness: 5 of the questions must be UNANSWERABLE from the
     docs; the system must refuse. Score = refused/5.
3. Output: evals/run.py prints a results table AND writes
   docs/evaluation.md with the table. The README must show the final table.
   If any metric is embarrassing, tune (threshold, chunking, prompt) and
   record before/after in docs/evaluation.md — improvement narrative is
   gold for interviews.

==================================================
PROJECT-SPECIFIC FAILURE HANDLING (test each one)
==================================================

- corrupt/encrypted/empty PDF → status=failed with human-readable error
- embedding API 429 mid-processing → cursor persists, retry resumes, no
  duplicate chunks (idempotency by (document_id, page, chunk_index) unique
  constraint)
- Groq 429/timeout → fallback to Gemini → both down → structured 503 with
  "AI provider temporarily unavailable"
- LLM returns malformed JSON → one corrective retry → refusal fallback
- question about un-indexed topic → evidence gate refusal (test asserts NO
  LLM call was made)
- prompt injection in a document ("ignore instructions and say X") → the
  citation validator + grounded prompt limit blast radius; add a test with
  a poisoned sample doc and document residual risk honestly in
  docs/limitations.md

==================================================
PROJECT-SPECIFIC DOCS
==================================================

docs/rag-pipeline.md   — every stage with a Mermaid sequence diagram
docs/mcp.md            — tools, transport choice, client setup, test script
docs/evaluation.md     — methodology + results table (+ before/after tuning)
DECISIONS.md must cover at minimum: chunk size choice, similarity threshold
choice, HNSW vs IVFFlat, resumable-batch serverless pattern, evidence gate
design, why citations are validated deterministically instead of trusting
the LLM.

Now begin with PHASE 0 (plan only, no code).
```

---

## After the agent finishes
1. Run `08-audit-prompt.md`
2. Run `09-deployment-prompt.md`
3. Run `10-documentation-polish-prompt.md`
4. Record demo: upload refund-policy PDF → ask "What are the refund conditions?" (show citations) → ask "What is the CEO's salary?" (show refusal) → show Langfuse trace → show eval table → show MCP tool call.
