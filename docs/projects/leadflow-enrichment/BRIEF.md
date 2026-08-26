# BRIEF — P2 LeadFlow Enrichment (frozen spec)

**Dir** `projects/02-leadflow-enrichment` · **Stack** Node serverless (zero deps) · **Signal:** webhook-driven autonomous web enrichment → structured Tier A/B/C dossiers into Slack/CRM.

## Architecture
```
POST /api/leads {name, email, company, domain?, budget?, message?}
  → derive domain from email/company
  → research: TAVILY_API_KEY → live web search (size, funding, news)
              else → deterministic demo research corpus (5 known domains + generator)
  → grade: GROQ_API_KEY → Llama 3.1 JSON grading against ICP
           else → deterministic scorer (budget, domain quality, employee count, funding recency)
  → output dossier: {tier: A|B|C, score 0-100, firmographics, news[], talking_points[], recommended_action}
  → push Slack (if configured) + store in CRM (in-memory seeded; Supabase if configured)
```

## Endpoints
`POST /api/leads` · `GET /api/leads` (list) · `GET /api/leads?id=` · `GET /api/health`.

## Dashboard
Webform + 3 sample-lead buttons (enterprise A-tier, mid B-tier, low C-tier) · stepper (Webhook received → Domain extracted → Web research → LLM grading → Dossier stored → Slack pushed) · dossier card (tier badge, score gauge, firmographics grid, news list, talking points) · CRM table of all leads · raw JSON toggle.

## Acceptance
node tests/smoke.test.js green (grading determinism, tier thresholds, endpoint contracts); demo works keyless.
