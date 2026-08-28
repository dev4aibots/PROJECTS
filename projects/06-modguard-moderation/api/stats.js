/**
 * GET /api/stats — totals, cache hit rate, p50 latency cached vs uncached,
 * per-action and per-category counts. Proves the cache fast-path claim.
 */
'use strict';
const lib = require('./_lib.js');

module.exports = (req, res) => {
  if (req.method !== 'GET') return lib.json(res, 405, { error: 'GET only' });
  const s = lib.STATS;
  return lib.json(res, 200, {
    total: s.total,
    cache_hits: s.cache_hits,
    cache_hit_rate: s.total ? +(s.cache_hits / s.total).toFixed(3) : 0,
    p50_latency_ms: {
      cached: lib.p50(s.latencies_cached),
      uncached: lib.p50(s.latencies_uncached),
    },
    actions: s.actions,
    category_counts: s.category_counts,
    incidents: lib.INCIDENTS.length,
  });
};
