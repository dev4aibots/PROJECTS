/**
 * MCP Gateway — protocol-level tool host (MCP spec 2024-11-05, JSON-RPC 2.0)
 * with API-key auth, per-key token-bucket rate limiting, and live traces.
 *
 * Demo mode: two public demo keys, seeded in-memory company DB, in-memory
 * traces. Production knobs: MCP_API_KEYS env (JSON: {key:{scopes:[...]}}) and
 * Langfuse export when LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY are set.
 *
 * Zero dependencies — Node stdlib only.
 */
'use strict';
const crypto = require('crypto');

const PROTOCOL_VERSION = '2024-11-05';
const SERVER_INFO = { name: 'mcp-gateway', version: '1.0.0' };

// ---------------------------------------------------------------------------
// AUTH — demo keys, overridable via MCP_API_KEYS env
// ---------------------------------------------------------------------------
const DEMO_KEYS = {
  mcp_demo_readonly: { scopes: ['read'], label: 'Demo read-only key' },
  mcp_demo_admin: { scopes: ['read', 'write'], label: 'Demo admin key' },
};

function loadKeys() {
  if (process.env.MCP_API_KEYS) {
    try {
      const parsed = JSON.parse(process.env.MCP_API_KEYS);
      if (parsed && typeof parsed === 'object' && Object.keys(parsed).length) return parsed;
    } catch (_) { /* fall through to demo keys */ }
  }
  return DEMO_KEYS;
}

function extractKey(req) {
  const h = req.headers || {};
  if (h['x-api-key']) return String(h['x-api-key']).trim();
  const auth = h.authorization || '';
  const m = /^Bearer\s+(.+)$/i.exec(auth);
  return m ? m[1].trim() : null;
}

// ---------------------------------------------------------------------------
// RATE LIMIT — token bucket per key: capacity 20, refill 10/min
// ---------------------------------------------------------------------------
const BUCKET_CAPACITY = 20;
const REFILL_PER_MIN = 10;
const BUCKETS = new Map(); // key → {tokens, last}

function refill(b, now) {
  const elapsedMin = (now - b.last) / 60000;
  b.tokens = Math.min(BUCKET_CAPACITY, b.tokens + elapsedMin * REFILL_PER_MIN);
  b.last = now;
}

function takeToken(key, now = Date.now()) {
  let b = BUCKETS.get(key);
  if (!b) { b = { tokens: BUCKET_CAPACITY, last: now }; BUCKETS.set(key, b); }
  refill(b, now);
  if (b.tokens >= 1) { b.tokens -= 1; return { ok: true, remaining: Math.floor(b.tokens) }; }
  const waitMs = Math.ceil(((1 - b.tokens) / REFILL_PER_MIN) * 60000);
  return { ok: false, remaining: 0, retry_after_ms: waitMs };
}

function bucketState(key, now = Date.now()) {
  const b = BUCKETS.get(key);
  if (!b) return { tokens: BUCKET_CAPACITY, capacity: BUCKET_CAPACITY };
  refill(b, now);
  return { tokens: Math.floor(b.tokens * 100) / 100, capacity: BUCKET_CAPACITY };
}

// ---------------------------------------------------------------------------
// DEMO COMPANY DB — customers, orders, inventory, knowledge base
// ---------------------------------------------------------------------------
const DB = {
  customers: [
    { customer_id: 'CUST-1001', name: 'Ava Thompson', email: 'ava@nimbusretail.com', plan: 'enterprise', mrr_usd: 2400, since: '2023-04-11', open_tickets: 1 },
    { customer_id: 'CUST-1002', name: 'Ben Ortiz', email: 'ben@quartzlabs.io', plan: 'pro', mrr_usd: 480, since: '2024-01-29', open_tickets: 0 },
    { customer_id: 'CUST-1003', name: 'Chloe Nakamura', email: 'chloe@ferrostack.dev', plan: 'pro', mrr_usd: 520, since: '2023-11-02', open_tickets: 2 },
    { customer_id: 'CUST-1004', name: 'Dmitri Volkov', email: 'dmitri@polarsync.app', plan: 'starter', mrr_usd: 99, since: '2025-06-17', open_tickets: 0 },
  ],
  orders: [
    { order_id: 'ORD-9001', customer_id: 'CUST-1001', total_usd: 1299.0, status: 'delivered', refunded_usd: 0 },
    { order_id: 'ORD-9002', customer_id: 'CUST-1002', total_usd: 249.5, status: 'delivered', refunded_usd: 0 },
    { order_id: 'ORD-9003', customer_id: 'CUST-1003', total_usd: 89.99, status: 'shipped', refunded_usd: 0 },
  ],
  inventory: [
    { sku: 'SKU-A100', name: 'Aurora Standing Desk', category: 'furniture', stock: 42, reorder_at: 10, price_usd: 649 },
    { sku: 'SKU-A200', name: 'Nimbus Task Chair', category: 'furniture', stock: 7, reorder_at: 15, price_usd: 329 },
    { sku: 'SKU-B300', name: 'Photon 4K Monitor', category: 'electronics', stock: 118, reorder_at: 25, price_usd: 449 },
    { sku: 'SKU-B310', name: 'Photon Light Bar', category: 'electronics', stock: 3, reorder_at: 20, price_usd: 79 },
    { sku: 'SKU-C500', name: 'Halcyon Notebook 3-pack', category: 'office', stock: 260, reorder_at: 50, price_usd: 24 },
  ],
  kb: [
    { doc_id: 'KB-01', title: 'Refund policy', body: 'Refunds are available within 30 days of delivery. Partial refunds require manager approval above $500. Refunds post to the original payment method in 5-7 business days.' },
    { doc_id: 'KB-02', title: 'Shipping timelines', body: 'Standard shipping takes 3-5 business days. Expedited shipping is 1-2 business days. Furniture items ship freight and take 7-10 business days.' },
    { doc_id: 'KB-03', title: 'Warranty coverage', body: 'Electronics carry a 2-year limited warranty covering manufacturing defects. Furniture carries a 5-year structural warranty. Warranty claims require the order id and photos of the defect.' },
    { doc_id: 'KB-04', title: 'Enterprise SLA', body: 'Enterprise plan includes a 99.9% uptime SLA, 4-hour support response, a dedicated CSM, and quarterly business reviews.' },
    { doc_id: 'KB-05', title: 'Password reset and SSO', body: 'Users can reset passwords from the login page. Enterprise customers can enable SAML SSO; SCIM provisioning syncs users hourly.' },
  ],
};

// ---------------------------------------------------------------------------
// TOOL REGISTRY — 4 tools with JSON Schema inputSchema
// ---------------------------------------------------------------------------
const TOOLS = [
  {
    name: 'get_customer_record',
    description: 'Fetch a customer record by customer_id or email. Returns profile, plan, MRR and open tickets.',
    scope: 'read',
    inputSchema: {
      type: 'object',
      properties: {
        customer_id: { type: 'string', description: 'Customer id, e.g. CUST-1001' },
        email: { type: 'string', description: 'Customer email address' },
      },
    },
  },
  {
    name: 'query_inventory',
    description: 'Query product inventory. Filter by sku, category, or low_stock (items at/below reorder point).',
    scope: 'read',
    inputSchema: {
      type: 'object',
      properties: {
        sku: { type: 'string', description: 'Exact SKU, e.g. SKU-A200' },
        category: { type: 'string', description: 'Category filter: furniture | electronics | office' },
        low_stock: { type: 'boolean', description: 'If true, only items at or below their reorder point' },
      },
    },
  },
  {
    name: 'trigger_refund',
    description: 'Issue a refund against an order. Requires the write scope. Refuses amounts above the remaining refundable total.',
    scope: 'write',
    inputSchema: {
      type: 'object',
      properties: {
        order_id: { type: 'string', description: 'Order id, e.g. ORD-9002' },
        amount: { type: 'number', description: 'Refund amount in USD' },
        reason: { type: 'string', description: 'Reason for the refund' },
      },
      required: ['order_id', 'amount', 'reason'],
    },
  },
  {
    name: 'search_knowledge_base',
    description: 'Keyword search over the support knowledge base. Returns top_k scored snippets.',
    scope: 'read',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Search query' },
        top_k: { type: 'number', description: 'Max results (default 3)' },
      },
      required: ['query'],
    },
  },
];

const TOOL_IMPL = {
  get_customer_record(args) {
    const { customer_id, email } = args || {};
    if (!customer_id && !email) throw toolErr('Provide customer_id or email');
    const c = DB.customers.find(x =>
      (customer_id && x.customer_id === customer_id) ||
      (email && x.email.toLowerCase() === String(email).toLowerCase()));
    if (!c) throw toolErr(`No customer matches ${customer_id || email}`);
    const orders = DB.orders.filter(o => o.customer_id === c.customer_id);
    return { ...c, orders };
  },
  query_inventory(args) {
    const { sku, category, low_stock } = args || {};
    let items = DB.inventory;
    if (sku) items = items.filter(i => i.sku === sku);
    if (category) items = items.filter(i => i.category === String(category).toLowerCase());
    if (low_stock) items = items.filter(i => i.stock <= i.reorder_at);
    return { count: items.length, items };
  },
  trigger_refund(args) {
    const { order_id, amount, reason } = args || {};
    if (!order_id || typeof amount !== 'number' || !reason) throw toolErr('order_id, amount (number) and reason are required');
    const o = DB.orders.find(x => x.order_id === order_id);
    if (!o) throw toolErr(`No order ${order_id}`);
    if (amount <= 0) throw toolErr('Refund amount must be positive');
    const remaining = Math.round((o.total_usd - o.refunded_usd) * 100) / 100;
    if (amount > remaining) throw toolErr(`Amount $${amount} exceeds remaining refundable $${remaining}`);
    o.refunded_usd = Math.round((o.refunded_usd + amount) * 100) / 100;
    return {
      refund_id: 'RF-' + crypto.randomBytes(4).toString('hex').toUpperCase(),
      order_id, amount_usd: amount, reason,
      remaining_refundable_usd: Math.round((o.total_usd - o.refunded_usd) * 100) / 100,
      status: 'processed',
    };
  },
  search_knowledge_base(args) {
    const { query, top_k } = args || {};
    if (!query) throw toolErr('query is required');
    const k = Math.max(1, Math.min(10, Number(top_k) || 3));
    const terms = String(query).toLowerCase().split(/\W+/).filter(t => t.length > 2);
    const scored = DB.kb.map(d => {
      const hay = (d.title + ' ' + d.body).toLowerCase();
      const score = terms.reduce((s, t) => s + (hay.includes(t) ? 1 : 0), 0);
      return { doc_id: d.doc_id, title: d.title, snippet: d.body.slice(0, 160), score };
    }).filter(d => d.score > 0).sort((a, b) => b.score - a.score);
    return { query, results: scored.slice(0, k) };
  },
};

function toolErr(message) { const e = new Error(message); e.isToolError = true; return e; }

// ---------------------------------------------------------------------------
// TELEMETRY — trace every call; optional Langfuse export
// ---------------------------------------------------------------------------
const TRACES = []; // newest first
const MAX_TRACES = 500;

function recordTrace(t) {
  TRACES.unshift(t);
  if (TRACES.length > MAX_TRACES) TRACES.length = MAX_TRACES;
  exportLangfuse(t);
}

function exportLangfuse(t) {
  const pub = process.env.LANGFUSE_PUBLIC_KEY, sec = process.env.LANGFUSE_SECRET_KEY;
  if (!pub || !sec) return;
  const host = process.env.LANGFUSE_HOST || 'https://cloud.langfuse.com';
  const body = JSON.stringify({
    batch: [{
      id: t.trace_id, type: 'trace-create',
      timestamp: t.ts,
      body: { id: t.trace_id, name: `mcp:${t.method}${t.tool ? ':' + t.tool : ''}`, metadata: t },
    }],
  });
  // fire-and-forget; never block the request path
  try {
    fetch(`${host}/api/public/ingestion`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        authorization: 'Basic ' + Buffer.from(`${pub}:${sec}`).toString('base64'),
      },
      body,
    }).catch(() => {});
  } catch (_) { /* fetch unavailable — skip */ }
}

// ---------------------------------------------------------------------------
// JSON-RPC 2.0 — errors per spec + MCP gateway custom codes
// ---------------------------------------------------------------------------
// -32700 parse · -32600 invalid request · -32601 method not found ·
// -32602 invalid params · -32001 bad key · -32003 missing scope · -32029 rate limited
function rpcError(id, { code, message }, data) {
  const err = { code, message };
  if (data !== undefined) err.data = data;
  return { jsonrpc: '2.0', id: id === undefined ? null : id, error: err };
}
function rpcResult(id, result) { return { jsonrpc: '2.0', id, result }; }

function handleRpc(rpc, keyInfo) {
  const started = process.hrtime.bigint();
  const id = rpc && Object.prototype.hasOwnProperty.call(rpc, 'id') ? rpc.id : null;

  if (!rpc || rpc.jsonrpc !== '2.0' || typeof rpc.method !== 'string') {
    return rpcError(id, { code: -32600, message: 'Invalid Request: expected JSON-RPC 2.0 with a method' });
  }

  const trace = {
    trace_id: 'tr_' + crypto.randomBytes(6).toString('hex'),
    key: keyInfo.key, method: rpc.method, tool: null, args: null,
    ok: true, error: null, latency_ms: 0, result_bytes: 0,
    ts: new Date().toISOString(),
  };
  const finish = (resp) => {
    trace.latency_ms = Math.round(Number(process.hrtime.bigint() - started) / 1e3) / 1e3;
    trace.result_bytes = Buffer.byteLength(JSON.stringify(resp.result !== undefined ? resp.result : resp.error));
    if (resp.error) { trace.ok = false; trace.error = `${resp.error.code} ${resp.error.message}`; }
    recordTrace(trace);
    return resp;
  };

  switch (rpc.method) {
    case 'initialize':
      return finish(rpcResult(id, {
        protocolVersion: PROTOCOL_VERSION,
        serverInfo: SERVER_INFO,
        capabilities: { tools: { listChanged: false } },
      }));

    case 'tools/list':
      return finish(rpcResult(id, {
        tools: TOOLS.map(({ name, description, inputSchema }) => ({ name, description, inputSchema })),
      }));

    case 'tools/call': {
      const p = rpc.params || {};
      const name = p.name;
      const args = p.arguments || {};
      trace.tool = name || null;
      trace.args = args;
      const tool = TOOLS.find(t => t.name === name);
      if (!tool) return finish(rpcError(id, { code: -32602, message: `Unknown tool: ${name}` }));
      if (!keyInfo.scopes.includes(tool.scope)) {
        return finish(rpcError(id, { code: -32003, message: `Missing scope '${tool.scope}' for tool ${name}` },
          { your_scopes: keyInfo.scopes, required: tool.scope }));
      }
      try {
        const out = TOOL_IMPL[name](args);
        return finish(rpcResult(id, {
          content: [{ type: 'text', text: JSON.stringify(out, null, 2) }],
          isError: false,
        }));
      } catch (e) {
        if (e.isToolError) {
          // MCP spec: tool-level failures are results with isError:true, not protocol errors
          return finish(rpcResult(id, { content: [{ type: 'text', text: e.message }], isError: true }));
        }
        return finish(rpcError(id, { code: -32000, message: 'Tool execution failed' }, { detail: e.message }));
      }
    }

    case 'ping':
      return finish(rpcResult(id, {}));

    default:
      return finish(rpcError(id, { code: -32601, message: `Method not found: ${rpc.method}` }));
  }
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------
function json(res, status, body) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json');
  res.setHeader('access-control-allow-origin', '*');
  res.setHeader('access-control-allow-headers', 'content-type, x-api-key, authorization');
  res.setHeader('access-control-allow-methods', 'GET, POST, OPTIONS');
  res.end(JSON.stringify(body));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', c => { data += c; if (data.length > 1e6) { reject(new Error('Body too large')); req.destroy(); } });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

function resetAll() {
  BUCKETS.clear();
  TRACES.length = 0;
  for (const o of DB.orders) o.refunded_usd = 0;
}

module.exports = {
  PROTOCOL_VERSION, SERVER_INFO, TOOLS, DB, TRACES,
  BUCKET_CAPACITY, REFILL_PER_MIN,
  loadKeys, takeToken, bucketState, handleRpc, rpcError, rpcResult, extractKey,
  resetAll, json, readBody,
};
