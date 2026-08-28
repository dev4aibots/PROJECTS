/** Smoke tests — zero-dep. Run: node tests/smoke.test.js */
'use strict';
const assert = require('assert');
const http = require('http');
const path = require('path');

const lib = require(path.join(__dirname, '..', 'api', '_lib.js'));
const mcp = require(path.join(__dirname, '..', 'api', 'mcp.js'));
const traces = require(path.join(__dirname, '..', 'api', 'traces.js'));
const keys = require(path.join(__dirname, '..', 'api', 'keys.js'));
const health = require(path.join(__dirname, '..', 'api', 'health.js'));

const PORT = 3907;
const routes = { mcp, traces, keys, health };

const server = http.createServer(async (req, res) => {
  const m = new URL(req.url, 'http://x').pathname.match(/^\/api\/([a-z-]+)\/?$/);
  if (m && routes[m[1]]) return routes[m[1]](req, res);
  res.statusCode = 404; res.end('{}');
});

function call(pathname, { method = 'GET', body, headers = {} } = {}) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const req = http.request({ port: PORT, path: pathname, method, headers: { 'content-type': 'application/json', ...headers } }, res => {
      let buf = '';
      res.on('data', c => buf += c);
      res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(buf || '{}') }));
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

const RO = { 'x-api-key': 'mcp_demo_readonly' };
const ADMIN = { authorization: 'Bearer mcp_demo_admin' };
const rpc = (method, params, id = 1) => ({ jsonrpc: '2.0', id, method, ...(params ? { params } : {}) });

(async () => {
  await new Promise(r => server.listen(PORT, r));
  lib.resetAll();

  // 1) health
  let r = await call('/api/health');
  assert.strictEqual(r.status, 200);
  assert.strictEqual(r.body.status, 'ok');
  assert.strictEqual(r.body.protocol, '2024-11-05');
  assert.strictEqual(r.body.tools.length, 4);

  // 2) bad key → -32001, HTTP 401
  r = await call('/api/mcp', { method: 'POST', body: rpc('initialize'), headers: { 'x-api-key': 'nope' } });
  assert.strictEqual(r.status, 401);
  assert.strictEqual(r.body.error.code, -32001);

  // 3) missing key → -32001
  r = await call('/api/mcp', { method: 'POST', body: rpc('initialize') });
  assert.strictEqual(r.body.error.code, -32001);

  // 4) initialize happy path
  r = await call('/api/mcp', { method: 'POST', body: rpc('initialize'), headers: RO });
  assert.strictEqual(r.status, 200);
  assert.strictEqual(r.body.jsonrpc, '2.0');
  assert.strictEqual(r.body.id, 1);
  assert.strictEqual(r.body.result.protocolVersion, '2024-11-05');
  assert.strictEqual(r.body.result.serverInfo.name, 'mcp-gateway');
  assert.ok(r.body.result.capabilities.tools);

  // 5) tools/list → 4 tools with inputSchema
  r = await call('/api/mcp', { method: 'POST', body: rpc('tools/list', null, 2), headers: RO });
  assert.strictEqual(r.body.result.tools.length, 4);
  const names = r.body.result.tools.map(t => t.name).sort();
  assert.deepStrictEqual(names, ['get_customer_record', 'query_inventory', 'search_knowledge_base', 'trigger_refund']);
  assert.ok(r.body.result.tools.every(t => t.inputSchema && t.inputSchema.type === 'object'));

  // 6) tools/call get_customer_record by email
  r = await call('/api/mcp', { method: 'POST', body: rpc('tools/call', { name: 'get_customer_record', arguments: { email: 'ava@nimbusretail.com' } }, 3), headers: RO });
  assert.strictEqual(r.body.result.isError, false);
  let payload = JSON.parse(r.body.result.content[0].text);
  assert.strictEqual(payload.customer_id, 'CUST-1001');
  assert.strictEqual(payload.orders.length, 1);

  // 7) tools/call query_inventory low_stock
  r = await call('/api/mcp', { method: 'POST', body: rpc('tools/call', { name: 'query_inventory', arguments: { low_stock: true } }, 4), headers: RO });
  payload = JSON.parse(r.body.result.content[0].text);
  assert.strictEqual(payload.count, 2); // SKU-A200 (7≤15) and SKU-B310 (3≤20)

  // 8) tools/call search_knowledge_base
  r = await call('/api/mcp', { method: 'POST', body: rpc('tools/call', { name: 'search_knowledge_base', arguments: { query: 'refund policy days', top_k: 2 } }, 5), headers: RO });
  payload = JSON.parse(r.body.result.content[0].text);
  assert.ok(payload.results.length >= 1);
  assert.strictEqual(payload.results[0].doc_id, 'KB-01');

  // 9) trigger_refund with read-only key → -32003 missing scope
  r = await call('/api/mcp', { method: 'POST', body: rpc('tools/call', { name: 'trigger_refund', arguments: { order_id: 'ORD-9002', amount: 50, reason: 'test' } }, 6), headers: RO });
  assert.strictEqual(r.body.error.code, -32003);

  // 10) trigger_refund with admin key → processed
  r = await call('/api/mcp', { method: 'POST', body: rpc('tools/call', { name: 'trigger_refund', arguments: { order_id: 'ORD-9002', amount: 50, reason: 'damaged item' } }, 7), headers: ADMIN });
  assert.strictEqual(r.body.result.isError, false);
  payload = JSON.parse(r.body.result.content[0].text);
  assert.strictEqual(payload.status, 'processed');
  assert.strictEqual(payload.remaining_refundable_usd, 199.5);

  // 11) over-refund → tool-level error (isError:true result, not protocol error)
  r = await call('/api/mcp', { method: 'POST', body: rpc('tools/call', { name: 'trigger_refund', arguments: { order_id: 'ORD-9002', amount: 9999, reason: 'nope' } }, 8), headers: ADMIN });
  assert.strictEqual(r.body.result.isError, true);
  assert.ok(r.body.result.content[0].text.includes('exceeds remaining refundable'));

  // 12) unknown tool → -32602; unknown method → -32601
  r = await call('/api/mcp', { method: 'POST', body: rpc('tools/call', { name: 'nope' }, 9), headers: RO });
  assert.strictEqual(r.body.error.code, -32602);
  r = await call('/api/mcp', { method: 'POST', body: rpc('bogus/method', null, 10), headers: RO });
  assert.strictEqual(r.body.error.code, -32601);

  // 13) batch request
  r = await call('/api/mcp', { method: 'POST', body: [rpc('ping', null, 11), rpc('tools/list', null, 12)], headers: RO });
  assert.ok(Array.isArray(r.body));
  assert.strictEqual(r.body.length, 2);
  assert.strictEqual(r.body[1].result.tools.length, 4);

  // 14) rate limit — exhaust the bucket → -32029, HTTP 429, retry-after set
  lib.resetAll();
  let limited = null;
  for (let i = 0; i < lib.BUCKET_CAPACITY + 5; i++) {
    const rr = await call('/api/mcp', { method: 'POST', body: rpc('ping', null, 100 + i), headers: RO });
    if (rr.status === 429) { limited = rr; break; }
  }
  assert.ok(limited, 'expected a 429 after exhausting the bucket');
  assert.strictEqual(limited.body.error.code, -32029);
  assert.ok(limited.body.error.data.retry_after_ms > 0);

  // 15) traces recorded with latency + filters
  r = await call('/api/traces');
  assert.ok(r.body.count >= 10);
  assert.ok(r.body.traces.every(t => typeof t.latency_ms === 'number' && t.trace_id.startsWith('tr_')));
  r = await call('/api/traces?tool=trigger_refund');
  assert.ok(r.body.traces.every(t => t.tool === 'trigger_refund'));
  r = await call('/api/traces?ok=false');
  assert.ok(r.body.traces.every(t => t.ok === false));

  // 16) keys endpoint — demo keys, scopes, bucket state
  r = await call('/api/keys');
  assert.strictEqual(r.body.mode, 'demo');
  assert.strictEqual(r.body.keys.length, 2);
  const admin = r.body.keys.find(k => k.key === 'mcp_demo_admin');
  assert.deepStrictEqual(admin.scopes, ['read', 'write']);
  assert.ok(typeof admin.bucket.tokens === 'number');

  server.close();
  console.log('✅ mcp-gateway: all smoke tests passed');
})().catch(e => { console.error('❌', e.message); process.exit(1); });
