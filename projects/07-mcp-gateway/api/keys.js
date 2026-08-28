/**
 * GET /api/keys — demo keys, their scopes and live token-bucket state.
 * (Safe to expose: these are public demo credentials. With MCP_API_KEYS set,
 * only key labels/scopes/buckets are listed — real keys are masked.)
 */
'use strict';
const lib = require('./_lib.js');

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') return lib.json(res, 204, {});
  const keys = lib.loadKeys();
  const custom = Boolean(process.env.MCP_API_KEYS);
  const out = Object.entries(keys).map(([k, v]) => ({
    key: custom ? k.slice(0, 4) + '…' + k.slice(-2) : k,
    label: v.label || 'custom key',
    scopes: v.scopes || [],
    bucket: lib.bucketState(k),
  }));
  return lib.json(res, 200, {
    mode: custom ? 'custom (MCP_API_KEYS)' : 'demo',
    rate_limit: { capacity: lib.BUCKET_CAPACITY, refill_per_min: lib.REFILL_PER_MIN },
    keys: out,
  });
};
