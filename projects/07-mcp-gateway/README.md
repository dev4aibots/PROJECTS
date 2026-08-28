# 🔌 MCP Gateway — Protocol-Level Tool Host with Auth, Rate Limits & Live Traces

> **The problem:** teams want to expose internal tools (CRM lookups, inventory, refunds) to AI agents, but a raw HTTP wrapper has no standard contract, no per-consumer auth, no rate protection, and no audit trail. When the agent misbehaves, nobody can answer "who called what, when, and what came back?"

**MCP Gateway** is a JSON-RPC 2.0 server implementing the **Model Context Protocol (spec 2024-11-05)** that any MCP client — Claude Desktop, Cursor, custom agents — can speak natively, wrapped in three production layers:

1. **API-key auth with scopes** — `X-API-Key` or `Authorization: Bearer`; keys carry `read`/`write` scopes and destructive tools (`trigger_refund`) demand `write`.
2. **Per-key token-bucket rate limiting** — capacity 20, refill 10/min; exhaustion returns JSON-RPC `-32029` with HTTP 429 + `Retry-After`.
3. **Full telemetry** — every call traced (`trace_id`, key, tool, args, ok, latency_ms, result_bytes) with optional Langfuse export.

Zero npm dependencies — Node stdlib only.

## Architecture

```
POST /api/mcp  (JSON-RPC 2.0)
   │
   ├─ 1 AUTH        X-API-Key / Bearer → key + scopes        bad key → -32001 (401)
   ├─ 2 RATE LIMIT  token bucket per key (20 cap, 10/min)    empty  → -32029 (429)
   ├─ 3 DISPATCH    initialize · tools/list · tools/call     scope miss → -32003
   │                  ├ get_customer_record {customer_id|email}          [read]
   │                  ├ query_inventory {sku?|category?|low_stock?}      [read]
   │                  ├ trigger_refund {order_id, amount, reason}        [write]
   │                  └ search_knowledge_base {query, top_k}             [read]
   └─ 4 TRACE       {trace_id, key, tool, ok, latency_ms, result_bytes}
                    → GET /api/traces · Langfuse export if keys set
```

Tool-level failures (e.g. over-refund) follow the MCP spec: they return a **result** with `isError: true`, not a protocol error — the agent can read the message and self-correct.

## Endpoints

| Endpoint | Description |
|---|---|
| `POST /api/mcp` | JSON-RPC 2.0 MCP endpoint (single or batch) |
| `GET /api/traces` | Call telemetry, newest first (`?tool=`, `?ok=`, `?limit=`) |
| `GET /api/keys` | Demo keys, scopes, live token-bucket state |
| `GET /api/health` | Service/protocol/tool/rate-limit info |

## Demo keys

| Key | Scopes |
|---|---|
| `mcp_demo_readonly` | `read` |
| `mcp_demo_admin` | `read`, `write` |

Override in production with `MCP_API_KEYS` env: `{"sk_live_x":{"scopes":["read","write"],"label":"prod agent"}}` (the `/api/keys` endpoint then masks key material).

## Quick start

```bash
node dev-server.js            # → http://localhost:3007 (dashboard + API)
node tests/smoke.test.js      # zero-dep smoke suite
```

```bash
# speak MCP by hand:
curl -s localhost:3007/api/mcp -H 'x-api-key: mcp_demo_admin' -d '{
  "jsonrpc":"2.0","id":1,"method":"tools/call",
  "params":{"name":"trigger_refund","arguments":{"order_id":"ORD-9002","amount":50,"reason":"damaged"}}}'
```

### Connect from Claude Desktop / Cursor

```json
{ "mcpServers": { "company-tools": {
    "url": "https://<your-deploy>/api/mcp",
    "transport": "http",
    "headers": { "X-API-Key": "mcp_demo_admin" } } } }
```

## Deploy

`npx vercel --prod` — each `api/*.js` file becomes a serverless function; `public/` is static. Optional env: `MCP_API_KEYS`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`.

## Tests

`tests/smoke.test.js` covers: initialize/tools/list/tools/call happy paths · bad key → `-32001` · missing `write` scope on `trigger_refund` → `-32003` · bucket exhaustion → `-32029` with `retry_after_ms` · tool-level `isError` on over-refund · batch requests · trace recording with filters · keys/bucket state.

## Design notes

1. **The protocol is the product:** the dashboard always shows raw JSON-RPC request/response panes — that exact payload is what an MCP client sends, so the demo doubles as documentation.
2. **Custom error codes stay in JSON-RPC's reserved server range** (`-32001` auth, `-32003` scope, `-32029` rate limit) so spec-compliant clients degrade gracefully.
3. **Rate limiting is per-key, not per-IP:** agents share egress IPs; the key is the billing/abuse boundary.
4. **Tool errors ≠ protocol errors:** per MCP spec, business failures return `isError: true` results the model can reason about; protocol errors are reserved for auth/limits/malformed calls.
5. **State honesty:** buckets/traces/demo DB are in-memory per serverless instance for the demo; Redis (Upstash) is the documented production swap for buckets and traces.
