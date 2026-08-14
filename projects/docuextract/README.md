# DocuExtract

Verified invoice intelligence: multimodal extraction proposes structured fields; Pydantic validates shape; pure Decimal arithmetic independently verifies every bookable amount.

## Local evidence

- 18 backend tests pass, including tolerance boundaries, huge Decimals, invalid currency, unsafe upload, non-invoice refusal, duplicates, and CRUD.
- Generated sample evaluation: 5/5 expected verdicts (clean PDF/image, two arithmetic failures, non-invoice).
- Next.js landing and verification console typecheck and build.
- No Gemini, Supabase, Langfuse, or deployment success is claimed.

## Quickstart

```bash
pip install -r requirements-dev.txt
python scripts/make_samples.py
PYTHONPATH=backend uvicorn app.main:app --port 8000
cd frontend && npm ci && npm run dev
```

Open `http://localhost:3000/app`; use sample buttons to see VERIFIED, exact mismatch deltas, and FAILED_EXTRACTION.

## Trust boundary

`validated upload → vision extraction → Pydantic schema → Decimal verification → normalized persistence → field trust labels`

Values are never auto-corrected. `0.019` is within the default `0.02` tolerance; `0.021` fails. Missing tax is treated as zero only with an `assumed_zero` note.

## Verify

```bash
PYTHONPATH=backend pytest -q backend/tests
PYTHONPATH=backend python evals/run.py
cd frontend && npm ci && npm run typecheck && npm run build
```

Hosted persistence and Gemini are owner gates. Apply `migrations/001_docuextract.sql`, configure `.env.example`, deploy, then repeat happy, broken-total, non-invoice, duplicate, and provider-outage smokes.
