/**
 * POST /api/mcp — JSON-RPC 2.0 MCP endpoint (spec 2024-11-05).
 * Auth via X-API-Key or Authorization: Bearer. Methods: initialize,
 * tools/list, tools/call, ping. Custom errors: -32001 bad key,
 * -32003 missing scope, -32029 rate limited.
 */
'use strict';
const lib = require('./_lib.js');

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') return lib.json(res, 204, {});
  if (req.method !== 'POST') return lib.json(res, 405, lib.rpcError(null, { code: -32600, message: 'POST only' }));

  try {
    // 1) AUTH
    const key = lib.extractKey(req);
    const keys = lib.loadKeys();
    if (!key || !keys[key]) {
      return lib.json(res, 401, lib.rpcError(null,
        { code: -32001, message: 'Invalid or missing API key' },
        { hint: 'Pass X-API-Key or Authorization: Bearer. Demo keys: mcp_demo_readonly, mcp_demo_admin' }));
    }
    const keyInfo = { key, scopes: keys[key].scopes || [] };

    // 2) RATE LIMIT — token bucket per key
    const bucket = lib.takeToken(key);
    if (!bucket.ok) {
      res.setHeader('retry-after', Math.ceil(bucket.retry_after_ms / 1000));
      return lib.json(res, 429, lib.rpcError(null,
        { code: -32029, message: 'Rate limit exceeded' },
        { capacity: lib.BUCKET_CAPACITY, refill_per_min: lib.REFILL_PER_MIN, retry_after_ms: bucket.retry_after_ms }));
    }

    // 3) PARSE
    const raw = await lib.readBody(req);
    let rpc;
    try { rpc = JSON.parse(raw); } catch (_) {
      return lib.json(res, 400, lib.rpcError(null, { code: -32700, message: 'Parse error: invalid JSON' }));
    }

    // 4) DISPATCH (batch supported per JSON-RPC 2.0)
    if (Array.isArray(rpc)) {
      if (!rpc.length) return lib.json(res, 400, lib.rpcError(null, { code: -32600, message: 'Empty batch' }));
      const out = rpc.map(r => lib.handleRpc(r, keyInfo));
      return lib.json(res, 200, out);
    }
    const resp = lib.handleRpc(rpc, keyInfo);
    return lib.json(res, 200, resp);
  } catch (e) {
    return lib.json(res, 500, lib.rpcError(null, { code: -32000, message: 'Server error' }, { detail: e.message }));
  }
};
