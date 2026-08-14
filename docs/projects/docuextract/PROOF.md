# DocuExtract — Verified Invoice Intelligence — Proof Ledger

## Current proof summary

| Claim/criterion | Status | Strongest evidence | Limitation |
|---|---|---|---|
| Upload and primary flow | verified locally | API tests cover accepted files, owner-scoped process/detail/list/delete, private response headers, and public byte filtering | live database/object storage remain credential-gated |
| Arithmetic trust boundary | verified locally | Decimal unit tests cover tolerance, line/subtotal/tax/total mismatches, huge values, and invalid currency | extraction values are deterministic fixtures |
| Failure behavior | verified locally | unsafe type/signature/size, non-invoice, provider-unavailable, duplicate, and missing-resource paths | live Gemini malformed/correction behavior unverified |
| Evaluation | verified locally | generated sample set returns 5/5 expected verdicts | bounded deterministic corpus, not model accuracy |
| Frontend delivery | verified locally | TypeScript check and Next production build pass | no deployed URL or screenshots |
| Deploy/live integration | blocked externally | migration, env template, Vercel config, and capture plan exist | owner credentials/resources required |

## 2026-08-14 verification

- Environment: Linux sandbox, Python 3.13 used for local proof.
- `PYTHONPATH=backend:. .venv/bin/pytest -q backend/tests --strict-markers --disable-warnings` → `43 passed, 1 credential-gated Postgres integration skipped in 1.09s`.
- `PYTHONPATH=backend:. .venv/bin/python evals/run.py` → clean PDF `VERIFIED`; two broken invoices `VERIFICATION_FAILED`; receipt image `VERIFIED`; non-invoice image `FAILED_EXTRACTION`; `verdict_accuracy: 5/5`.
- `CORS_ORIGINS=http://localhost:3000 PYTHONPATH=backend:. .venv/bin/python scripts/preflight.py` → passed.
- `.venv/bin/pip check` → no broken requirements.
- `npm run typecheck` and `npm run build` → passed; generated `/` plus `/app`.
- `npm audit --omit=dev --audit-level=high` → zero production vulnerabilities.
- Identity changes now synchronously clear prior-owner UI state; API responses set `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, and `Referrer-Policy: no-referrer`.
- `projects/docuextract/AUDIT.md` → no open critical/high credential-free finding.

## Failure-path evidence

- MIME, suffix, size, and magic bytes are validated before repository writes.
- Public responses remove uploaded bytes.
- Non-invoice extraction records `failed_extraction` and does not create invoice fields.
- Provider outage resets the document to retryable `uploaded` and returns controlled `503`; concurrent processing claims have one winner.
- Decimal mismatches remain visible with exact deltas; values are never silently corrected.
- Duplicate invoice numbers are warnings scoped to the same demo session.

## Deployment evidence

- Claimed URL: none.
- Post-deploy smoke: not run.
- Owner checks still required: live Gemini structured output/correction retry, five-page PDF behavior, Supabase storage/persistence, Langfuse, production CORS, deployment, and visual capture.
- Unverified services: Gemini, Supabase/Postgres/Storage, Langfuse, Vercel/hosting.
