# FILE_MANIFEST.md — File-by-File Completion Registry

> **Purpose:** agents must NOT re-read or rewrite files marked ✅. This registry saves tokens across sessions.
> Statuses: ⬜ todo · 🔨 wip (note what remains) · ✅ done+verified

**Last update:** 2026-08-26 · session #1

## Repo root & docs

| File | Status |
|---|---|
| `README.md` | ✅ |
| `AGENTS.md` | ✅ |
| `.gitignore` | ✅ |
| `docs/MASTER_PLAN.md` | ✅ |
| `docs/AGENT_PROTOCOL.md` | ✅ |
| `docs/CHECKPOINTS.md` | ✅ (living doc — update, don't rewrite) |
| `docs/FILE_MANIFEST.md` | ✅ (living doc) |
| `docs/DEPLOYMENT.md` | ✅ |

## P1 FinAudit IDP — `projects/01-finaudit-idp/`

| File | Status |
|---|---|
| `docs/projects/finaudit-idp/BRIEF.md` | ✅ |
| `docs/projects/finaudit-idp/RESUME.md` | ✅ |
| `api/index.py` (FastAPI app: ingest, extract, verify, review queue, stats) | ✅ |
| `requirements.txt` | ✅ |
| `vercel.json` | ✅ |
| `public/index.html` (dashboard) | ✅ |
| `samples/invoice_clean.json` + `samples/invoice_mismatch.json` | ✅ |
| `tests/test_api.py` | ✅ |
| `README.md` | ✅ |

## P2 LeadFlow — `projects/02-leadflow-enrichment/`

| File | Status |
|---|---|
| `docs/projects/leadflow-enrichment/BRIEF.md` | ✅ |
| `docs/projects/leadflow-enrichment/RESUME.md` | ✅ |
| `api/_lib.js` (store, enrichment engine, grading, slack) | ✅ |
| `api/leads.js` | ✅ |
| `api/health.js` | ✅ |
| `public/index.html` | ✅ |
| `vercel.json` | ✅ |
| `tests/smoke.test.js` | ✅ |
| `README.md` | ✅ |

## P3 DuraSupport — `projects/03-durable-support/`

| File | Status |
|---|---|
| `docs/projects/durable-support/BRIEF.md` | ✅ |
| `docs/projects/durable-support/RESUME.md` | ✅ |
| `api/_lib.js` (KB + vector-ish retrieval, workflow state machine, store) | ✅ |
| `api/tickets.js` | ✅ |
| `api/approve.js` | ✅ |
| `api/health.js` | ✅ |
| `public/index.html` | ✅ |
| `vercel.json` | ✅ |
| `tests/smoke.test.js` | ✅ |
| `README.md` | ✅ |

## P4 ZeroTrust-SQL — `projects/04-zerotrust-sql/`

| File | Status |
|---|---|
| `docs/projects/zerotrust-sql/BRIEF.md` | ✅ |
| `docs/projects/zerotrust-sql/RESUME.md` | ✅ |
| `api/index.py` (FastAPI: query, schema, audit; guard + nl2sql + warehouse inline) | ✅ |
| `requirements.txt` | ✅ |
| `vercel.json` | ✅ |
| `public/index.html` | ✅ |
| `tests/test_guard.py` | ✅ |
| `README.md` | ✅ |

## P5 SelfHeal Scraper — `projects/05-selfheal-scraper/`

| File | Status |
|---|---|
| `docs/projects/selfheal-scraper/BRIEF.md` | ✅ |
| `docs/projects/selfheal-scraper/RESUME.md` | ✅ |
| `api/index.py` (FastAPI: scrape, products, selectors, cron; mock pages v1/v2 inline) | ✅ |
| `requirements.txt` | ✅ |
| `vercel.json` (with crons) | ✅ |
| `public/index.html` | ✅ |
| `tests/test_scraper.py` | ✅ |
| `README.md` | ✅ |

## P6 ModGuard — `projects/06-modguard-moderation/`

| File | Status |
|---|---|
| `docs/projects/modguard-moderation/BRIEF.md` | ✅ |
| `docs/projects/modguard-moderation/RESUME.md` | ✅ |
| `api/_lib.js` (cache, rule engine, gemini client, incident store) | ✅ |
| `api/moderate.js` | ✅ |
| `api/incidents.js` | ✅ |
| `api/stats.js` | ✅ |
| `api/health.js` | ✅ |
| `public/index.html` | ✅ |
| `vercel.json` | ✅ |
| `tests/smoke.test.js` | ✅ |
| `README.md` | ✅ |

## P7 MCP Gateway — `projects/07-mcp-gateway/`

| File | Status |
|---|---|
| `docs/projects/mcp-gateway/BRIEF.md` | ✅ |
| `docs/projects/mcp-gateway/RESUME.md` | ✅ |
| `api/_lib.js` (auth keys, rate limiter, tool registry, demo DB, tracer) | ✅ |
| `api/mcp.js` (JSON-RPC 2.0 MCP endpoint) | ✅ |
| `api/traces.js` | ✅ |
| `api/keys.js` | ✅ |
| `api/health.js` | ✅ |
| `public/index.html` | ✅ |
| `vercel.json` | ✅ |
| `tests/smoke.test.js` | ✅ |
| `README.md` | ✅ |
