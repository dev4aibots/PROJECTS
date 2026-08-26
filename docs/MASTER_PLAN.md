# MASTER PLAN — Career Context + Full Specs (frozen source of truth)

## 1. Career context (why every decision matters)

- Owner: **fresher** targeting **AI Automation Engineer** roles: ₹6–12+ LPA (India) or $10k–$25k global remote retainers.
- Strategy: skip basic chatbots/document-Q&A. Ship automations that **generate revenue, eliminate hundreds of manual hours, or protect production databases** — the things enterprises actually pay for.
- Portfolio positioning per project = a one-line "extraordinary technical signal" a recruiter can repeat (e.g. "she built AST SQL guardrails that block prompt-injection from destroying prod").
- All 7 projects: deployable 24/7 on **Vercel at $0** (Serverless Functions, Cron, free DB tiers). Each is a standalone directory with its own `vercel.json`.
- Presentation: every project is a **web app** (not just an API) following the 5-element formula (sample-data trigger, execution stepper, structured output card, raw-JSON toggle, API-docs/telemetry links) so recruiters can try it in one click.
- **Demo mode is mandatory**: with no API keys set, every endpoint returns realistic deterministic results so the live Vercel URL never looks broken. With keys set (`GROQ_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY`, `SLACK_WEBHOOK_URL`, `DATABASE_URL`, …) real integrations activate.

## 2. Global engineering standards

- **Python projects**: FastAPI on Vercel Python runtime — single `api/index.py` entry, `requirements.txt`, Pydantic v2 schemas, `/docs` Swagger enabled, `/api/health` endpoint. Static dashboard in `public/index.html` (vanilla JS + Tailwind CDN — no build step, loads instantly).
- **Node projects**: Vercel Serverless Functions in `api/*.js` (plain JS, zero build), static dashboard in `public/index.html`.
- **Every project has**: `README.md` (problem, architecture diagram, quickstart, env vars, sample curl), `vercel.json`, sample data included in-repo, in-memory fallback stores when DB env vars are absent.
- **Interview-ready**: code is commented at the "why" level; each README has an "Interview talking points" section.

## 3. The 7 projects (frozen scope)

### P1 — FinAudit IDP: Intelligent Document Processing & Financial Audit API
- **Slug** `finaudit-idp` · dir `projects/01-finaudit-idp` · **Python/FastAPI**
- Problem ($15k–$40k/yr): enterprises manually parse millions of invoices; one parsing error = financial discrepancy.
- Flow: webhook receives invoice (PDF/image/JSON) → Gemini 1.5 Vision extracts vendor, line items, tax, totals into strict Pydantic schema → **arithmetic verification** (Σ line items + tax vs stated total, exact decimal math) → confidence scoring → if confidence <85% or math fails → **human review queue** + Slack alert; else auto-approve → persist to Supabase (or in-memory).
- Endpoints: `POST /api/documents` (ingest), `GET /api/documents`, `GET /api/documents/{id}`, `POST /api/documents/{id}/review` (approve/reject), `GET /api/stats`, `GET /api/health`, `GET /docs`.
- Signal: **mathematical verification + confidence-based human routing prevents hallucinated accounting errors**.

### P2 — LeadFlow: Autonomous B2B Lead Enrichment & AI Sales Qualification Engine
- **Slug** `leadflow-enrichment` · dir `projects/02-leadflow-enrichment` · **Node serverless**
- Problem: sales teams burn thousands of hours researching inbound leads.
- Flow: webform/webhook submits lead (name, email, company domain, budget) → extract domain → Tavily web search (company size, funding, news) → Groq Llama 3 grades lead **Tier A/B/C** against ICP + writes outreach angle → enriched dossier pushed to Slack + stored (Supabase/in-memory CRM).
- Endpoints: `POST /api/leads` (webhook), `GET /api/leads`, `GET /api/leads?id=`, `GET /api/health`.
- Signal: **webhook-driven autonomous web enrichment producing structured JSON dossiers straight into sales tools**.

### P3 — DuraSupport: Durable Multi-Agent Support Engine with Human Approval Gates
- **Slug** `durable-support` · dir `projects/03-durable-support` · **Node serverless**
- Problem: support bots hallucinate and lack safety gates; companies won't deploy them.
- Flow: ticket arrives → KB retrieval agent (vector-style similarity over seeded company KB) drafts response → classifier agent detects billing/refund topics → **durable pause**: workflow state persisted (KV/DB/in-memory) with status `AWAITING_APPROVAL`, Slack interactive message sent; workflow consumes ZERO compute while paused (serverless = state machine resumed by webhook, hours later, no timeout) → manager hits Approve/Edit/Reject → workflow resumes → reply "sent" to customer, full timeline recorded.
- Endpoints: `POST /api/tickets`, `GET /api/tickets`, `GET /api/tickets?id=`, `POST /api/approve` (approve/edit/reject callback), `GET /api/health`.
- Signal: **zero-infrastructure durable workflows — agent state persists across human approvals without server timeouts**.

### P4 — ZeroTrust-SQL: Zero-Trust Text-to-SQL Enterprise Data Analyst Agent
- **Slug** `zerotrust-sql` · dir `projects/04-zerotrust-sql` · **Python/FastAPI**
- Problem: execs need instant BI but letting an LLM run raw SQL on prod is a severe security risk.
- Flow: plain-English question → LLM (Groq) sees schema, writes SQL → **AST Safety Interceptor** (`sqlglot` parse): reject anything that is not a single SELECT — DROP/DELETE/UPDATE/INSERT/ALTER/TRUNCATE/PRAGMA/ATTACH, multi-statements, comments-based injection; enforce LIMIT cap; table allow-list → safe SELECT runs on read-only demo warehouse (bundled SQLite with realistic sales data; Neon/Supabase Postgres if `DATABASE_URL` set) → formatted table + chart-ready payload.
- Endpoints: `POST /api/query`, `GET /api/schema`, `GET /api/audit` (blocked-query log), `GET /api/health`, `/docs`.
- Signal: **AST SQL guardrails defeating prompt-injection before it touches the database**.

### P5 — SelfHeal Scraper: Autonomous Self-Healing Web Scraper & Price Monitor
- **Slug** `selfheal-scraper` · dir `projects/05-selfheal-scraper` · **Python/FastAPI + Vercel Cron**
- Problem: scrapers break whenever competitor sites change HTML/CSS.
- Flow: Vercel Cron triggers scrape of monitored products → fast path: stored CSS selectors via BeautifulSoup → **self-healing fallback**: selector returns None → send raw DOM snippet to Groq → LLM extracts price contextually AND proposes the new working selector → selector registry auto-updated and versioned → price history logged, price-drop alerts. Bundled mock e-commerce pages (v1 + "redesigned" v2 layout) prove the healing live.
- Endpoints: `POST /api/scrape` (run now), `GET /api/products`, `GET /api/selectors` (registry + heal history), `GET /api/cron` (cron target), `GET /api/health`, `/docs`. `vercel.json` includes `crons`.
- Signal: **LLM as adaptive fallback layer — the scraper repairs itself when traditional code fails**.

### P6 — ModGuard: Real-Time Trust & Safety Content Moderation Agent
- **Slug** `modguard-moderation` · dir `projects/06-modguard-moderation` · **Node serverless**
- Problem: platforms need instant moderation of millions of posts.
- Flow: content posted → **Tier 1 fast-path**: content-hash cache lookup (Upstash Redis if `KV_REST_API_URL` set, else in-memory LRU) → cache hit returns verdict <50ms → **Tier 2**: Gemini Flash (or deterministic rule engine in demo mode) evaluates against policy taxonomy (hate/harassment, spam, scam/phishing links, violence, PII) → verdict cached; flagged content → incident log + Slack alert.
- Endpoints: `POST /api/moderate`, `GET /api/incidents`, `GET /api/stats` (cache hit-rate, latency percentiles), `GET /api/health`.
- Signal: **high-throughput caching layered over multimodal AI — sub-second verdicts at a fraction of the LLM cost**.

### P7 — MCP Gateway: Enterprise Model Context Protocol Server & Tool Gateway
- **Slug** `mcp-gateway` · dir `projects/07-mcp-gateway` · **Node serverless**
- Problem: orgs adopting agents need a secure, standardized way to expose internal APIs/DBs to any agent framework.
- Flow: JSON-RPC 2.0 endpoint speaking **MCP** (`initialize`, `tools/list`, `tools/call`) over HTTP → exposes `get_customer_record`, `query_inventory`, `trigger_refund`, `search_knowledge_base` against a seeded demo company DB → **API-key auth** (demo keys with scopes) → **token-bucket rate limiting per key** → **telemetry**: every invocation traced (latency, args, result size) and inspectable via `GET /api/traces` — Langfuse export if keys provided. Works with Claude Desktop / Cursor as a remote MCP server.
- Endpoints: `POST /api/mcp` (JSON-RPC), `GET /api/traces`, `GET /api/keys` (demo key info), `GET /api/health`.
- Signal: **protocol-level integration infrastructure with auth, rate limits, and live observability — not hardcoded endpoints**.

## 4. Acceptance criteria (per project — copied into each BRIEF.md)

1. `npx vercel --prod` deploys with zero interactive config (valid `vercel.json`).
2. Local run works: Python → `uvicorn api.index:app`; Node → `npx vercel dev` or bundled `dev-server.js`.
3. All endpoints return correct JSON in demo mode (no env keys).
4. Dashboard implements all 5 formula elements and calls the live API.
5. README complete (problem, architecture, quickstart, env table, curls, interview talking points).
6. Automated smoke test passes (`tests/` or `npm test` / `pytest`).
7. Entry updated in CHECKPOINTS.md, FILE_MANIFEST.md, project RESUME.md.
