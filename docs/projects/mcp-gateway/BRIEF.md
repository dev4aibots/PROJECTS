# BRIEF — P7 MCP Gateway (frozen spec)

**Dir** `projects/07-mcp-gateway` · **Stack** Node serverless, JSON-RPC 2.0 per MCP spec (2024-11-05) · **Signal:** protocol-level tool host with API-key auth, token-bucket rate limiting, and live traces.

## Architecture
```
POST /api/mcp  (JSON-RPC 2.0; header X-API-Key or Authorization: Bearer)
  methods: initialize → {protocolVersion, serverInfo, capabilities:{tools}}
           tools/list → 4 tools with JSON Schema inputSchema
           tools/call → dispatch with scope check
  tools (against seeded demo company DB):
    get_customer_record{customer_id|email} · query_inventory{sku?|category?|low_stock?}
    trigger_refund{order_id, amount, reason} [scope: write] · search_knowledge_base{query, top_k}
  AUTH: demo keys mcp_demo_readonly (scopes: read) & mcp_demo_admin (read,write); override via MCP_API_KEYS env
  RATE LIMIT: token bucket per key (capacity 20, refill 10/min) → JSON-RPC error -32029 when exhausted
  TELEMETRY: every call traced {trace_id, key, tool, args, ok, latency_ms, result_bytes, ts};
             GET /api/traces; Langfuse export if keys set
```

## Endpoints
`POST /api/mcp` · `GET /api/traces` · `GET /api/keys` (demo keys + scopes + bucket state) · `GET /api/health`.

## Dashboard
Interactive MCP playground: pick key → pick method/tool → arg form prefilled w/ samples → send → JSON-RPC request/response panes · stepper (Auth → Rate limit → Dispatch → Traced) · trace table w/ latency + status · rate-limit demo button ("burst 25 calls") showing 429-style errors · "connect from Claude Desktop / Cursor" config snippet · raw JSON always visible (it IS the protocol).

## Acceptance
smoke test: initialize/tools/list/tools/call happy paths; bad key → -32001; missing write scope on trigger_refund → -32003; bucket exhaustion → -32029; traces recorded.
