# BRIEF — P6 ModGuard (frozen spec)

**Dir** `projects/06-modguard-moderation` · **Stack** Node serverless (zero deps) + Upstash KV optional · **Signal:** <50ms cached fast-path layered over AI moderation slashes latency and LLM cost.

## Architecture
```
POST /api/moderate {content, content_type: "text"|"image_url", user_id?}
  → TIER 1: sha256(content) → cache lookup (Upstash REST if KV_REST_API_URL else in-memory LRU 500)
            hit → return cached verdict, cached:true, ~<5ms
  → TIER 2: GEMINI_API_KEY → Gemini Flash policy evaluation
            else → deterministic rule engine: category lexicons + scam-link heuristics
                   (url shorteners, "send crypto", urgency+money patterns), PII regexes (email/phone/card)
  → verdict {allowed, categories[{name, score, flagged}], severity, action: allow|flag|block}
  → cache verdict · flagged → incident log + Slack alert
GET /api/stats → total, cache_hit_rate, avg latency cached vs uncached, category counts
```

## Endpoints
`POST /api/moderate` · `GET /api/incidents` · `GET /api/stats` · `GET /api/health`.

## Dashboard
Content input + sample buttons (clean post · spam · scam link · harassment · PII leak) · "send twice" demo proving cache hit latency drop · stepper (Received → Hash → Cache check → AI analysis → Verdict cached → Incident logged) · verdict card w/ per-category score bars + action badge · stats row (hit rate, p50 latencies) · incident table · raw JSON toggle.

## Acceptance
smoke test: clean allows, scam blocks, second identical call returns cached:true, incidents recorded, stats math correct.
