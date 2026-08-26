# AI Automation Engineering Portfolio — 7 Enterprise-Grade Projects

> **Owner career goal:** Land a high-paying AI Automation Engineer role (₹6–12+ LPA India / $10k–$25k global remote retainers) **as a fresher** by demonstrating senior-level, revenue-impacting automation skills — not toy chatbots.
>
> **Every project deploys to Vercel at $0 cost** (Serverless Functions, Cron Jobs, free-tier databases) and ships with a live interactive dashboard, demo mode (works with zero API keys), Swagger/OpenAPI docs (Python projects), and raw-JSON inspection toggles.

## 🤖 FOR AI AGENTS: READ [`AGENTS.md`](AGENTS.md) FIRST

This repository uses a **resumable, checkpoint-driven build system**. Any AI agent (Claude, GPT, Cursor, Gemini — anyone) can pick up exactly where the last agent stopped, without re-reading finished files. Start at `AGENTS.md` → `docs/CHECKPOINTS.md` → the project's `RESUME.md`.

## The 7 Projects

| # | Project | Business Domain | Stack (all $0 on Vercel) | "Extraordinary" Signal |
|---|---------|-----------------|--------------------------|------------------------|
| 1 | [FinAudit IDP](projects/01-finaudit-idp/) — Intelligent Document Processing & Financial Audit API | Finance / Insurance | FastAPI · Gemini Vision · Pydantic · Supabase | Mathematical Σ-verification + confidence-based human review routing |
| 2 | [LeadFlow](projects/02-leadflow-enrichment/) — Autonomous B2B Lead Enrichment & AI Sales Qualification | Sales / GTM | Vercel Node Functions · Groq Llama 3 · Tavily · Slack | Webhook-driven web enrichment → Tier A/B/C dossiers pushed to CRM/Slack |
| 3 | [DuraSupport](projects/03-durable-support/) — Durable Multi-Agent Support Engine with Human Approval Gates | Customer Ops | Vercel Functions · durable state machine · pgvector-style KB · Slack | Pause/resume workflows across human approvals with zero server timeouts |
| 4 | [ZeroTrust-SQL](projects/04-zerotrust-sql/) — Zero-Trust Text-to-SQL Data Analyst Agent | Data Analytics | FastAPI · Groq · sqlglot AST · read-only Postgres/SQLite | AST SQL guardrail blocking DROP/DELETE/UPDATE & prompt-injection |
| 5 | [SelfHeal Scraper](projects/05-selfheal-scraper/) — Autonomous Self-Healing Web Scraper & Price Monitor | Data / E-Commerce | FastAPI · Vercel Cron · CSS selectors · Groq fallback | LLM-adaptive fallback that repairs selectors when site layouts change |
| 6 | [ModGuard](projects/06-modguard-moderation/) — Real-Time Trust & Safety Content Moderation Agent | Platform Ops / Security | Vercel Functions · KV/Redis cache · Gemini Flash · Supabase | <50ms cached fast-path layered over multimodal AI analysis |
| 7 | [MCP Gateway](projects/07-mcp-gateway/) — Enterprise Model Context Protocol Server & Tool Gateway | MLOps / AI Infra | MCP JSON-RPC · Node Serverless · auth keys · rate limiting · telemetry | Protocol-level tool host with live observability tracing |

## How each project is presented as a web app

Every project ships the **5-element "extraordinary app formula"**:
1. **Interactive input trigger** with "Click to Try Sample Data" buttons
2. **Live execution stepper** — step-by-step progress cards, not a spinner
3. **Structured visual output card** — status tags, metric cards, data tables
4. **"View Raw JSON" toggle** for technical reviewers
5. **API docs / telemetry links** — FastAPI `/docs` Swagger + trace logs

## Deploy any project to Vercel (1 minute)

```bash
cd projects/<project-dir>
npx vercel --prod          # zero config — vercel.json included
# then add env vars in the Vercel dashboard (all optional — demo mode works without keys)
```

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for env vars, cron setup, and database provisioning.

## Repository map

```
├── AGENTS.md                 ← AI-agent entry point (resume protocol)
├── docs/
│   ├── MASTER_PLAN.md        ← career context + full specs for all 7 projects
│   ├── CHECKPOINTS.md        ← global real-time checkpoint board
│   ├── FILE_MANIFEST.md      ← file-by-file completion registry (skip finished files!)
│   ├── AGENT_PROTOCOL.md     ← how agents work, commit, and hand off
│   ├── DEPLOYMENT.md         ← Vercel deployment runbook
│   └── projects/<slug>/      ← BRIEF.md · RESUME.md · FILES.md per project
└── projects/                 ← 7 deployable apps (each self-contained)
```
