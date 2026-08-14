# DocuExtract deployment-ready implementation plan

**Outcome:** genuine multimodal invoice extraction where Gemini proposes fields and deterministic Decimal logic independently verifies them. Deployment requires only credentials, migrations and deploy actions.

**Current truth (2026-08-14):** upload checks, Pydantic models, Decimal verifier, UI and sample tests exist. The extractor currently keys hard-coded output from filenames; no Gemini call or runtime database adapter exists; ownership checks are incomplete. It must not be marketed as multimodal AI until P3 passes.

## Target architecture

Authenticated Next.js review console → FastAPI upload/process API → private object storage → Gemini document/image structured-output adapter → Pydantic normalization → independent Decimal verification → Postgres normalized invoice/line-item/check records → human review/export. Provider data is untrusted and never auto-corrects financial values.

## Phase gates

### P0 — extraction contract and dataset
- Freeze schemas for invoice, parties, dates, currency, tax/discount/shipping, line items, page/source evidence, confidence and verification checks.
- Define null vs zero rules, decimal precision/rounding, tolerance, duplicate fingerprint and status machine.
- Build a legally safe labelled dataset of generated and owner-provided invoices: scans, photos, rotations, blur, multi-page, missing fields, locale/currency variants and non-invoices.
- **Gate:** ground truth has field provenance and expected verification status; no filename controls output.

### P1 — secure upload and ownership
- Verify JWT principal; generate storage paths server-side; enforce owner on process/get/list/delete/export.
- Validate extension, MIME, magic bytes, decoded image/PDF integrity, page/dimension/pixel count, decompression risk and total size.
- Store in a private bucket with short-lived signed access; hash bytes for idempotency/duplicate detection.
- **Gate:** IDOR, spoofed MIME, polyglot/corrupt/encrypted/oversized/many-page inputs have tested safe outcomes.

### P2 — Gemini multimodal provider
- Use the supported Google Gen AI SDK and Gemini document processing with Pydantic/JSON schema structured output.
- Send actual bytes/file reference and extraction instructions, not filenames. Pin configurable model; set timeout and token limits.
- Parse strictly; perform one bounded schema-repair attempt that receives validation errors but no trusted expected values.
- Classify invalid document, permanent auth/config, transient 429/5xx/timeout and malformed-output failures.
- **Gate:** mocked HTTP/provider contract tests prove bytes are supplied, valid JSON parses, malformed output fails safely and retry policy is bounded.

### P3 — independent verification
- Normalize decimals/currency/dates without floats; preserve raw provider values alongside normalized values.
- Verify each `quantity × unit_price = line_total`, subtotal composition, tax/discount/shipping and grand total with explicit deltas/tolerance.
- Add anomaly checks for duplicate invoice, inconsistent currency, negative/huge values and unsupported arithmetic.
- Never silently fix; expose `verified`, `mismatch`, `not_verifiable`, `assumed_zero` per field/check.
- **Gate:** boundary/property tests include huge exponents, rounding, negatives, missing fields and adversarial strings.

### P4 — persistence and processing reliability
- Implement repository protocol plus Postgres/Supabase adapter for documents, invoices, items and checks; transactionally replace one extraction result.
- Use idempotency key and lease/version so retries/concurrent process calls cannot duplicate records.
- Keep local memory repo explicit; persist provider/model/schema version and error reason.
- **Gate:** Postgres integration tests prove ownership, rollback, retry and delete cascade.

### P5 — review-first UI/UX
- Add upload/drop/camera guidance, queue/progress/retry, original-document preview, extracted field table, line-item arithmetic, mismatch deltas, confidence/evidence, edit-as-human-correction and CSV/JSON export.
- Visually separate extracted, verified and human-corrected values; preserve correction audit.
- Cover responsive, keyboard, screen-reader and every status/error state.
- **Gate:** browser E2E covers clean invoice, mismatch, non-invoice, provider outage, duplicate and ownership denial; accessibility target >=95.

### P6 — evaluation and observability
- Report field-level exact/normalized precision-recall/F1, line-item matching, amount MAE, invoice verdict accuracy, non-invoice rejection, parse-failure rate, latency and estimated cost by document type.
- Split dataset by template/vendor so near-duplicates cannot leak across train/tuning/eval.
- Trace upload/extraction/validation/verification/persistence with values redacted by default.
- **Gate:** dated report includes dataset version, model, prompt/schema version, git SHA, failures and confidence intervals where possible.

### P7 — CI/deployment
- CI runs verifier/provider/repository tests, Postgres integration, eval, frontend build/E2E, dependency audit and secret scan.
- Add migrations/RLS/storage setup, environment preflight, Vercel function limits, exact CORS, health/readiness, post-deploy smoke and cleanup/retention policy.
- **Gate:** fresh cloud project can be configured without code edits; live smoke processes actual PDF/image bytes and persists normalized rows.

### P8 — owner launch proof
Configure Supabase DB/private storage, Gemini and optional Langfuse, deploy API/UI, run labelled live eval and ownership/outage smokes, then record URLs, model, migration, CI, screenshots and demo.

## Research basis

- Gemini document processing: https://ai.google.dev/gemini-api/docs/document-processing
- Gemini structured output/Pydantic: https://ai.google.dev/gemini-api/docs/structured-output
- Vercel Python limits: https://vercel.com/docs/functions/runtimes/python
