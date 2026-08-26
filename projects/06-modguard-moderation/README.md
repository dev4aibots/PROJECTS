# 🛡️ ModGuard — Layered AI Content Moderation with a <50ms Cached Fast Path

> **The problem:** running every user post through an LLM moderation call costs real money and adds 500–2000ms of latency — yet most platforms see the *same* content repeatedly (reposts, spam blasts, copy-paste scams). Paying the LLM tax twice for identical bytes is waste.
>
> **The signal:** a sha256 verdict cache in front of the AI layer turns repeat content into a **<5ms** lookup, slashing both latency and per-token cost — while flagged content still lands in an incident log with Slack alerts.

**Stack:** Node serverless (zero dependencies) · Upstash KV (optional) · Gemini Flash (optional) · Vercel

---

## Architecture

```
POST /api/moderate {content, content_type, user_id?}
   │
   ├─ TIER 1 — sha256(content) → verdict cache
   │    Upstash REST if KV_REST_API_URL set, else in-memory LRU(500)
   │    HIT → return cached verdict, cached:true, ~<5ms  ✔ done
   │
   ├─ TIER 2 — analysis
   │    GEMINI_API_KEY set → Gemini Flash policy evaluation
   │    else → deterministic rule engine:
   │           · category lexicons (spam/scam/harassment/hate/violence/self_harm/sexual)
   │           · scam-link heuristics (URL shorteners, "send crypto", urgency+money)
   │           · PII regexes (email, phone, credit card, SSN)
   │
   ├─ verdict {allowed, categories[{name,score,flagged}], severity, action}
   │    action: allow (<0.5) · flag (≥0.5) · block (≥0.8)
   │
   ├─ verdict cached under the hash
   └─ flag/block → incident log (+ Slack webhook alert if configured)
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/moderate` | Moderate content → layered verdict with steps + latency |
| GET | `/api/incidents` | Flagged/blocked log, `?action=flag\|block&limit=N` |
| GET | `/api/stats` | Totals, cache hit rate, p50 latency cached vs uncached |
| GET | `/api/health` | Mode, cache backend, thresholds |

## Run locally

```bash
npm run dev        # dev server on :3006 (Vercel routing emulation)
npm test           # zero-dep smoke suite
```

**Demo mode is the default** — with no keys set, the deterministic rule engine and in-memory LRU keep the live URL fully functional. Env vars activate real integrations:

| Var | Activates |
|---|---|
| `GEMINI_API_KEY` | Gemini Flash policy evaluation (rule engine remains the fallback) |
| `KV_REST_API_URL` + `KV_REST_API_TOKEN` | Upstash verdict cache (shared across instances) |
| `SLACK_WEBHOOK_URL` | Incident alerts to Slack |

## Dashboard (5-element formula)

1. **Sample triggers** — clean post · spam · scam link · harassment · PII leak, one click each.
2. **"Send twice" demo** — sends identical content twice and prints both latencies side-by-side, proving the cache fast path (`cached:true`, typically 10–100× faster).
3. **Pipeline stepper** — Received → Hash → Cache check → AI analysis → Verdict cached → Incident logged.
4. **Verdict card** — action badge, per-category score bars, evidence chips, latency, hash.
5. **Stats row + incident table + raw JSON toggle** — hit rate, p50 cached vs uncached, live incident log.

## Design notes (interview talking points)

1. **Cache the verdict, not the content:** sha256 keys mean zero PII stored in the cache layer; identical bytes → identical verdict is a safe invariant for deterministic policies.
2. **The rule engine isn't a mock — it's the fallback tier.** LLM down / no key / rate-limited → deterministic lexicon + heuristic scoring still returns the same verdict shape. Graceful degradation is the feature.
3. **Thresholds as policy, not code:** `FLAG_AT`/`BLOCK_AT` are single constants — a policy team can tune them without touching the pipeline.
4. **Scam detection is compositional:** a URL shortener alone is suspicious (0.55); shortener + urgency or money language escalates to 0.9. Layered signals beat single keywords.
5. **Stats prove the claim:** `/api/stats` reports p50 latency cached vs uncached from real measurements — the <50ms fast-path claim is verifiable on the live URL, not marketing.
6. **State honesty:** stats/incidents are in-memory per serverless instance for the demo; Upstash KV is the documented one-env-var swap for shared state.
