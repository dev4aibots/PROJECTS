# 🎯 LeadFlow — Autonomous B2B Lead Enrichment & AI Sales Qualification Engine

> **The problem:** sales teams burn thousands of hours manually researching inbound leads before every call. Slow research = slow response = lost deals (leads contacted within 1 hour convert 7× better). LeadFlow turns a raw webhook into a graded, research-backed dossier in seconds.

## What it does

```
POST /api/leads {name, email, company, domain?, budget?, message?}
  → derive domain      (email domain unless free-mail → company-slug inference)
  → web research       (Tavily live search if TAVILY_API_KEY, else deterministic corpus)
  → grade against ICP  (Groq Llama 3.1 JSON grading if GROQ_API_KEY, else deterministic scorer)
  → dossier            {tier A|B|C, score 0-100, firmographics, news, talking_points, action}
  → push Slack (if SLACK_WEBHOOK_URL) + store in CRM (in-memory; Supabase if DATABASE_URL)
```

**Demo mode is first-class:** with zero API keys, research comes from a seeded corpus (Stripe, Notion, Flexport, Ramp, Acme) plus a stable hash-based generator for any other domain, and grading uses a deterministic scorer whose weights mirror the LLM's ICP prompt. The live URL never looks broken.

## ICP & grading

> B2B SaaS / fintech / logistics, 50–5000 employees, recent funding or active hiring, budget ≥ $10k.

| Signal | Max points |
|---|---|
| Budget (≥$50k / ≥$10k / ≥$1k) | 30 / 20 / 8 |
| Domain quality (real corporate domain vs inferred) | 15 / 7 |
| Employee count in 50–5000 ICP band | 25 |
| Funding recency (≤18mo / ≤36mo / older) | 20 / 12 / 5 |
| Intent language ("pilot", "ASAP", "evaluating"…) | 10 |

**Tier A ≥ 70 · Tier B ≥ 40 · Tier C < 40**

## Quickstart

```bash
node dev-server.js            # http://localhost:3002
node tests/smoke.test.js      # zero-dep smoke suite
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/leads` | Ingest lead webhook → full enrichment pipeline → 201 dossier |
| GET | `/api/leads` | CRM list (id, name, company, tier, score, action) |
| GET | `/api/leads?id=lead_0001` | One full dossier |
| GET | `/api/health` | Mode + integration flags + ICP |

### Sample curls

```bash
curl -s localhost:3002/api/health

curl -s -X POST localhost:3002/api/leads \
  -H 'content-type: application/json' \
  -d '{"name":"Dana Whitfield","email":"dana.whitfield@stripe.com","budget":120000,"message":"Need a pilot ASAP this quarter"}'

curl -s localhost:3002/api/leads
```

## Environment variables (all optional — demo mode without them)

| Var | Activates |
|---|---|
| `TAVILY_API_KEY` | Live web research (Tavily search API) |
| `GROQ_API_KEY` | LLM grading (Llama 3.1 8B, JSON mode) |
| `SLACK_WEBHOOK_URL` | Tier-alert pushes to a Slack channel |
| `DATABASE_URL` | Supabase/Postgres persistence (else in-memory seeded) |

## Deploy

`npx vercel --prod` — zero build step, `api/*.js` become serverless functions, `public/index.html` is the dashboard, `vercel.json` is `{}` (defaults suffice).

## Architecture decisions (interview talking points)

1. **Why webhook-driven?** Fits any form provider (Tally/Typeform/custom) — the engine is the integration point, not the form.
2. **Why deterministic fallback grading?** Testability + zero-key demos. The scorer's weights mirror the ICP prompt, so demo and live tiers agree in spirit; tests assert exact determinism.
3. **Free-mail filtering** — `bob@gmail.com` never pollutes firmographic lookups; domain inference falls back to the company name slug and is *penalized* in the domain-quality score, honestly reflecting lower data confidence.
4. **Tier thresholds are product decisions** (A ≥ 70, B ≥ 40) — documented, tested, and tunable per customer.
5. **Failure modes:** Tavily/Groq API errors fall through silently to demo paths — the pipeline never 500s because a third party is down.
