# 🧾 FinAudit IDP — Intelligent Document Processing & Financial Audit API

> **The $15k–$40k/yr problem:** enterprises manually parse millions of invoices, claims, and receipts. A single mis-parsed line item creates a real financial discrepancy. Standard "AI extraction" tools hallucinate numbers — and nobody notices until the audit.

**The extraordinary signal:** this pipeline never trusts the extractor. Every document passes **exact-Decimal mathematical verification** (per-line `qty × unit_price == amount`, grand total `Σ items + tax == stated_total`) and **confidence-based human routing** — anything below 85% confidence or failing arithmetic lands in a human review queue with a Slack alert.

## Architecture

```
POST /api/documents  (invoice JSON | base64 PDF/image | sample_id)
   │
   ├─ EXTRACT   GEMINI_API_KEY set → Gemini 1.5 Flash Vision (structured JSON mode)
   │            else → deterministic demo extractor (bundled samples)
   ├─ VALIDATE  strict Pydantic v2 schema (Decimal fields — no float drift)
   ├─ VERIFY    exact Decimal math: every line item + grand total (tolerance $0.01)
   ├─ ROUTE     verified && confidence ≥ 0.85 → AUTO_APPROVED
   │            else → NEEDS_REVIEW  →  review queue + Slack alert
   └─ PERSIST   Supabase (if configured) | in-memory store
```

## Quickstart (local)

```bash
pip install -r requirements.txt uvicorn
uvicorn api.index:app --reload --port 8001
# open http://localhost:8001        → dashboard
# open http://localhost:8001/docs   → Swagger
python -m pytest tests/ -q          → 8 tests
```

## Deploy to Vercel ($0)

```bash
npx vercel --prod
```

| Env var (all optional) | Enables |
|---|---|
| `GEMINI_API_KEY` | real Gemini 1.5 Vision extraction of uploaded PDFs/images |
| `SLACK_WEBHOOK_URL` | Slack alert when a document routes to human review |
| `SUPABASE_URL` + `SUPABASE_KEY` | persistent document storage |

Without keys the API runs in **demo mode** — deterministic extraction, fully functional dashboard.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/documents` | Ingest → extract → verify → route |
| GET | `/api/documents?status=NEEDS_REVIEW` | List / filter documents |
| GET | `/api/documents/{id}` | Full document + verification report |
| POST | `/api/documents/{id}/review` | Human approve / reject |
| GET | `/api/stats` | Auto-approval rate, Σ pass rate, queue depth |
| GET | `/api/health` | Mode + integration status |
| GET | `/docs` | Swagger UI |

### Sample curls

```bash
# clean invoice → AUTO_APPROVED
curl -sX POST $URL/api/documents -H 'Content-Type: application/json' -d '{"sample_id":"clean"}'

# corrupted invoice (digit-swap in line 3 + transposed total) → NEEDS_REVIEW
curl -sX POST $URL/api/documents -H 'Content-Type: application/json' -d '{"sample_id":"mismatch"}'

# human approval
curl -sX POST $URL/api/documents/<id>/review -H 'Content-Type: application/json' -d '{"action":"approve"}'
```

Sample invoices in [`samples/`](samples/) — `invoice_mismatch.json` contains two realistic accounting errors (a digit swap and a transposed total) that the verifier catches.

## Interview talking points

1. **Why Decimal, not float?** `0.1 + 0.2 != 0.3` in floats — financial verification demands exact decimal arithmetic (there's a test proving it).
2. **Why verify at all?** LLMs hallucinate plausible numbers. Programmatic recomputation is the only guarantee; the LLM is untrusted input.
3. **Why human-in-the-loop?** Enterprises won't accept a black box in the payment path. Confidence thresholds + review queues turn a demo into a deployable system.
4. **Failure modes covered:** low-confidence extraction, line-level math errors, total-level errors, double-review prevention (409), Slack notification failure doesn't break ingestion.
