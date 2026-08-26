# 🩹 SelfHeal Scraper — LLM-Adaptive Selector Repair for Price Monitoring

> **The problem:** every scraper in production is one CSS class rename away from silently returning nothing. Teams find out days later when the price feed flatlines.
>
> **The fix:** treat the selector as *mutable state with a repair loop*. On a miss, an LLM (or a deterministic heuristic in demo mode) re-locates the price in the changed DOM, derives a **new** selector, validates it against the live page, and version-bumps a selector registry — so the next run is back on the cheap CSS fast path.

## Pipeline

```
GET /api/cron (Vercel Cron, every 6h) or POST /api/scrape {product_id?, force_layout}
  → fetch page (bundled mock store: layout v1 · ?layout=v2 = simulated redesign · external URLs via httpx)
  → FAST PATH: stored CSS selector (BeautifulSoup) → price → done              [method: css]
  → SELF-HEAL on miss:
      trim DOM to the product's subtree
      GROQ_API_KEY → Llama 3 extracts price + proposes selector
      else        → heuristic healer: currency-regex DOM scan + selector derivation
                    (prefers data-* attrs like data-sku — the most redesign-stable anchors)
      validate: healed selector must re-yield the SAME price on the live DOM
      registry: {selector, version++, method: healed:…, healed_at} + heal audit entry
  → price history append · >5% drop → alert (SLACK_WEBHOOK_URL optional)
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/scrape` | Scrape one/all products, `force_layout: v1\|v2` |
| GET | `/api/cron` | Vercel Cron entrypoint (all products) |
| GET | `/api/products` | Products + price history + drop alerts |
| GET | `/api/selectors` | Selector registry + heal audit log |
| GET | `/api/mock/store?layout=v1\|v2` | The demo target site (v2 = redesigned) |
| GET | `/api/health` · `/docs` | Health · OpenAPI |

## Run locally

```bash
cd projects/05-selfheal-scraper
pip install -r requirements.txt uvicorn
python3 -m uvicorn api.index:app --port 8005
# open http://localhost:8005 — click "Run scrape (v1)" then "💥 Simulate site redesign"
python3 -m pytest tests/ -q   # 8 tests
```

## The demo story (what the acceptance tests prove)

1. **v1 scrape** → all selectors hit → `method: css`, registry stays at v1.
2. **v2 scrape (redesign)** → every selector misses → healer extracts the new prices, derives `article[data-sku='p1'] div.pcard__buy span.amount`-style selectors, validates them, bumps registry to v2, logs the heal.
3. **v2 scrape again** → healed selectors hit the fast path — **no re-heal**, no version bump. The loop converged.
4. Pulse 4K Monitor drops $429 → $399 (−7%) → price-drop alert fires.

## Design decisions

1. **Validate before trusting the heal.** A healed selector is only committed if it re-produces the exact extracted price on the same DOM. Hallucinated selectors never enter the registry.
2. **Prefer `data-*` anchors.** Class names are fashion; `data-sku` attributes survive redesigns. The selector deriver ranks them above classes.
3. **Tightest-scope extraction:** the healer only scans the DOM subtree that contains *exactly one* product name — preventing the classic bug of every product healing to the first card's price.
4. **The heuristic healer isn't a mock — it's the fallback tier.** LLM down / no key / rate-limited → the deterministic path still repairs selectors. The LLM makes it better, not possible.
5. **Registry as audit log:** every heal stores old selector, new selector, healer, validation result — the debugging trail scraping teams never have.
6. **State honesty:** in-memory per instance for the demo; the registry/history dicts are a documented 20-line swap for Postgres/KV.
