# PROJECT 4 — DocuExtract: Multimodal Extraction with Deterministic Verification

**Repo name:** `docuextract`
**Day:** 8 (ONE day — keep scope tight)
**Hiring signal:** Multimodal AI (Gemini vision), structured outputs (the #2 most-cited production skill), and the key differentiator: **the AI is not trusted — deterministic code verifies the math**. "Structured data extraction" appears in nearly every 2026 "projects that get you hired" list; the verification layer is what separates yours.

> Paste `01-master-context.md` first, then this prompt.

---

```
==================================================
PROJECT SPECIFICATION
==================================================

PROJECT NAME: DocuExtract — Verified Invoice Intelligence API

ONE-SENTENCE PITCH:
Upload an invoice (PDF/PNG/JPEG); Gemini extracts structured data, Pydantic
validates the shape, and a deterministic arithmetic engine independently
recomputes every total — any mismatch is flagged as VERIFICATION_FAILED
instead of silently trusted.

WHY THIS EXISTS (README):
Extraction demos stop at "the model returned JSON". Real document pipelines
(AP automation, expense systems) cannot book an invoice whose line items
don't sum to its total. This project draws the trust boundary explicitly:
AI proposes, deterministic code verifies, humans see exactly which fields
passed and which failed.

SCOPE DISCIPLINE: ONE document type (invoice). No OCR tuning, no multi-
document classification, no async workers. One day of build time.

==================================================
PIPELINE
==================================================

upload (PDF/PNG/JPEG, ≤8MB, validate MIME + extension + magic bytes)
→ Supabase Storage
→ POST /api/documents/{id}/process (single invocation is fine — one page-ish
  docs; enforce ≤5 pages for PDFs, reject larger with a clear message)
→ Gemini multimodal call: send the file bytes + a strict extraction prompt
  demanding JSON matching the schema; temperature 0
→ Pydantic validation (schema below); malformed → one corrective retry with
  the validation errors quoted back to the model → then FAILED_EXTRACTION
→ DETERMINISTIC VERIFICATION ENGINE (pure Python, zero AI, exhaustively
  unit-tested — this module is the heart of the repo):
    for each line item:  quantity × unit_price ≈ line_total
    sum(line_total)      ≈ subtotal
    subtotal + tax       ≈ total            (support tax as amount; if the
                                             doc gives a rate, compute it)
    date sanity: invoice_date parseable, not > today + 1 day
    currency: ISO-4217 code recognized
  All money math in Decimal (NEVER float). Tolerance configurable, default
  0.02 currency units, to absorb rounding. Result:
    {"status": "VERIFIED" | "VERIFICATION_FAILED",
     "checks": [{"name","field","expected","actual","passed","delta"}]}
  NEVER auto-correct values. Mismatches are surfaced, not fixed.
→ persist: documents, invoices, invoice_items, verification_results
  (normalized columns + raw_extraction jsonb for auditability)
→ UI renders extraction + a per-check verification report

==================================================
EXTRACTION SCHEMA (Pydantic v2)
==================================================

LineItem:  description, quantity (Decimal), unit_price (Decimal),
           line_total (Decimal)
Invoice:   invoice_number, vendor_name, invoice_date (date),
           currency (str, ISO-4217), subtotal, tax, total (Decimal),
           line_items (min_length=1),
           vendor_address (opt), customer_name (opt)

Field-level trust labels in the API response — each field is marked:
  "ai_extracted"            (came from the model)
  "verified"                (confirmed by deterministic checks)
  "unverified"              (no independent check possible, e.g. vendor name)
Do NOT invent confidence percentages the model never produced.

==================================================
SAMPLE DOCUMENTS + THE KILLER DEMO ARTIFACT
==================================================

scripts/make_samples.py (reportlab) generates:
  1. clean_invoice.pdf          — correct math → VERIFIED
  2. broken_total_invoice.pdf   — total inflated by 1000 → VERIFICATION_FAILED
  3. broken_lineitem_invoice.pdf— one line_total wrong → FAILED with the
                                  exact line identified
  4. receipt_photo.png          — an invoice rendered as an image → proves
                                  the multimodal path
Ship all four in sample_docs/ and add one-click "try a sample" buttons in
the UI. Sample #2 is the demo-video money shot: the system CATCHING a wrong
invoice is worth more than ten clean extractions.

==================================================
DATABASE SCHEMA
==================================================

documents(id, filename, content_type, file_size, storage_path, status
          [uploaded|processing|extracted|verified|verification_failed|
           failed_extraction], error, session_id, created_at)
invoices(id, document_id fk, invoice_number, vendor_name, invoice_date,
          currency, subtotal, tax, total, raw_extraction jsonb, created_at)
invoice_items(id, invoice_id fk, position, description, quantity,
          unit_price, line_total)
verification_results(id, invoice_id fk, status, checks jsonb, tolerance,
          created_at)
All money columns NUMERIC — assert in a test that nothing casts to float.

==================================================
API SURFACE
==================================================

POST   /api/documents/upload
POST   /api/documents/{id}/process
GET    /api/documents?session_id=
GET    /api/documents/{id}            full detail: invoice + items + verification
DELETE /api/documents/{id}
GET    /api/health

==================================================
FRONTEND
==================================================

/       Landing: pitch, pipeline diagram (Upload → Gemini → Pydantic →
        Deterministic verification → Verdict), "AI proposes, code verifies"
        as the visual theme.
/app    Single page:
        - dropzone + the 4 sample-document buttons
        - processing status
        - result: header fields with trust labels, line-items table,
          VERIFICATION REPORT card — green VERIFIED or red
          VERIFICATION_FAILED with each failed check showing
          expected vs actual vs delta
        - collapsible raw JSON viewer
        - history list of processed documents

==================================================
EVALUATION
==================================================

evals/: run all 4 sample docs end-to-end (live Gemini) 3 times each;
report per-field extraction accuracy against known ground truth (the
generator script KNOWS the true values — write them to
sample_docs/ground_truth.json) and verification-verdict correctness
(4/4 expected). Verification engine itself: exhaustive pure unit tests —
rounding at tolerance boundary (0.019 pass / 0.021 fail), zero-quantity,
negative price rejection, missing tax treated as 0 with an "assumed_zero"
note, huge Decimal values. Results table → docs/evaluation.md + README.

==================================================
FAILURE HANDLING (tests for each)
==================================================

- non-invoice image (add sample_docs/cat.png) → model returns
  unusable/malformed extraction → FAILED_EXTRACTION with friendly message,
  NOT a fabricated invoice — assert no invoice row was created
- corrupted PDF → clear error, status=failed
- Gemini 429/down → retry with backoff → structured 503 (Groq is NOT a
  fallback here — it has no vision; say so in DECISIONS.md)
- oversized/wrong-type upload → 400 before any storage write
- extraction returns duplicate invoice_number for the same session →
  store anyway but flag "possible_duplicate" in the response

==================================================
PROJECT-SPECIFIC DOCS
==================================================

docs/verification.md — every deterministic check, tolerance policy,
Decimal-not-float rationale, why auto-correction is forbidden.
DECISIONS.md must cover: single-doc-type scope choice, Decimal vs float,
tolerance value, trust-label design, why there's no vision fallback
provider.

Now begin with PHASE 0 (plan only, no code).
```

---

## Demo video beats
1. Upload clean invoice → extraction + green VERIFIED report
2. Upload broken_total invoice → red VERIFICATION_FAILED, expected 11,800 vs extracted 12,800, delta shown
3. Upload cat.png → graceful FAILED_EXTRACTION
4. Show the Decimal unit tests running (`pytest tests/test_verification.py -v`)
