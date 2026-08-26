# BRIEF — P1 FinAudit IDP (frozen spec; do not change without a Decision entry in RESUME.md)

**Dir** `projects/01-finaudit-idp` · **Stack** Python 3.9+ / FastAPI / Pydantic v2 · **Career signal:** mathematical Σ-verification + confidence-based human review routing prevents hallucinated accounting errors.

## Architecture
```
POST /api/documents (invoice JSON | base64 image | sample_id)
  → extractor: GEMINI_API_KEY set → Gemini 1.5 Flash Vision structured extraction
               else → deterministic demo extractor (bundled sample invoices)
  → Pydantic schema: Invoice{vendor, invoice_number, date, currency, line_items[{desc, qty, unit_price, amount}], tax, stated_total}
  → VERIFY: Decimal math — sum(items)+tax vs stated_total (tolerance 0.01); qty*unit_price vs amount per line
  → confidence score (extractor-reported; demo mode derives from data completeness)
  → route: verified && confidence>=0.85 → AUTO_APPROVED
           else → NEEDS_REVIEW (review queue + Slack alert if SLACK_WEBHOOK_URL)
  → persist (Supabase if configured, else in-memory seeded store)
```

## Endpoints
`POST /api/documents` · `GET /api/documents?status=` · `GET /api/documents/{id}` · `POST /api/documents/{id}/review` {action: approve|reject, note} · `GET /api/stats` · `GET /api/health` · Swagger at `/docs`.

## Dashboard (public/index.html)
Upload zone + 2 sample buttons (clean invoice → auto-approve; mismatch invoice → review queue) · execution stepper (Received → Extracted → Schema validated → Arithmetic verified → Routed) · invoice table + PASS/FAIL verification badge + confidence bar · review queue with Approve/Reject · raw JSON toggle · header links to /docs.

## Acceptance
pytest green (verification math incl. mismatch case, routing thresholds, review endpoint); demo mode fully functional without keys; vercel.json valid.
