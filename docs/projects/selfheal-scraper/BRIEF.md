# BRIEF — P5 SelfHeal Scraper (frozen spec)

**Dir** `projects/05-selfheal-scraper` · **Stack** Python/FastAPI + BeautifulSoup + Vercel Cron · **Signal:** LLM-adaptive fallback repairs broken CSS selectors when site layouts change.

## Architecture
```
GET /api/cron (Vercel Cron, every 6h) or POST /api/scrape {product_id?, force_layout?}
  for each monitored product:
    → fetch page HTML (bundled mock store: layout v1; ?layout=v2 simulates a site redesign;
      real external URLs supported via httpx when product.url is external)
    → FAST PATH: stored CSS selector via BeautifulSoup → price found → done (method: "css")
    → SELF-HEAL: selector miss → trim DOM snippet → GROQ_API_KEY ? Llama 3 extracts price + proposes new selector
                 : deterministic heuristic healer (currency-regex DOM scan + candidate selector derivation)
    → validate healed selector against DOM → update selector registry {selector, version++, healed_at, method}
    → append price history; drop >5% → alert (Slack if configured)
```

## Endpoints
`POST /api/scrape` · `GET /api/products` (w/ price history) · `GET /api/selectors` (registry + heal audit) · `GET /api/cron` · `GET /api/mock/store?layout=v1|v2` (the demo target site) · `GET /api/health` · `/docs`.

## Dashboard
Product cards w/ current price + sparkline · "Run scrape (layout v1)" and "💥 Simulate site redesign (v2)" buttons · stepper (Cron triggered → CSS fast path → MISS detected → LLM healing → Selector updated → Price logged) · selector registry table showing version bumps + heal history · raw JSON toggle.

## Acceptance
pytest: v1 scrape uses css fast path; v2 breaks selector and heal succeeds (price extracted, registry version bumped, new selector works on next run); cron endpoint scrapes all products.
