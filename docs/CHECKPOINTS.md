# CHECKPOINTS.md — Global Real-Time Status Board

> Updated by every agent after every checkpoint. This is the single source of "where are we".
> Statuses: ⬜ TODO · 🔨 WIP · ✅ DONE · 🧊 BLOCKED

**Last update:** 2026-08-26 · agent session #1 (repo reboot: old 5-project portfolio deleted, new 7-project spec adopted)

## Global board

| # | Project | Dir | Docs | Backend | Dashboard | Tests | Deploy-ready | Status |
|---|---------|-----|------|---------|-----------|-------|--------------|--------|
| 0 | Repo docs system (AGENTS, MASTER_PLAN, protocol, manifests, deployment) | `docs/` | ✅ | — | — | — | — | ✅ DONE |
| 1 | FinAudit IDP | `projects/01-finaudit-idp` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ DONE |
| 2 | LeadFlow Enrichment | `projects/02-leadflow-enrichment` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ DONE |
| 3 | DuraSupport | `projects/03-durable-support` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ DONE |
| 4 | ZeroTrust-SQL | `projects/04-zerotrust-sql` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ DONE |
| 5 | SelfHeal Scraper | `projects/05-selfheal-scraper` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ DONE |
| 6 | ModGuard Moderation | `projects/06-modguard-moderation` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ DONE |
| 7 | MCP Gateway | `projects/07-mcp-gateway` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ DONE |

## Active project
**ALL DONE** — P1–P7 complete and verified. Portfolio finished.

## Session log (append-only, newest first)
- **2026-08-26 · session #7**: P7 MCP Gateway built — JSON-RPC 2.0 MCP server (2024-11-05), 4 JSON-Schema tools, API-key auth with scopes (-32001/-32003), per-key token bucket (-32029/429), live traces + Langfuse export hook, interactive playground dashboard with burst demo, 16-group smoke suite green. ALL 7 PROJECTS COMPLETE.
- **2026-08-26 · session #6**: P6 ModGuard built — sha256 verdict cache (LRU/Upstash), rule-engine + Gemini tiers, incident log, Slack alerts, stats with p50 cached vs uncached, dashboard with send-twice cache proof, smoke tests green.
- **2026-08-26 · session #5 (cont.)**: P5 SelfHeal Scraper built — CSS fast path, heuristic/LLM heal with validated selector derivation (data-sku anchors), registry versioning, drop alerts, cron, dashboard, 8 tests green.
- **2026-08-26 · session #5**: P4 ZeroTrust-SQL rebuilt after sandbox reset — sqlglot AST interceptor (16 tests green), NL→SQL, read-only warehouse, audit log, dashboard with injection demo, uvicorn smoke verified.
- **2026-08-26 · session #4**: P3 DuraSupport built — durable pause/resume state machine, approval gates, 409 idempotency guard, dashboard, smoke tests green.
- **2026-08-26 · session #3**: P2 LeadFlow rebuilt after sandbox reset (engine, endpoints, dashboard, smoke tests green, dev-server curl verified).
- **2026-08-26 · session #2**: P1 FinAudit IDP built end-to-end (backend, dashboard, 8 tests green, README, vercel.json, local uvicorn smoke verified).
- **2026-08-26 · session #1**: Deleted legacy 5-project portfolio (documind-rag-mcp, stategraph-agent, old zerotrust-sql, docuextract, llmshield) per owner instruction. Writing new resumable docs system for the 7-project spec.
