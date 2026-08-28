'use strict';
const lib = require('./_lib.js');

module.exports = (req, res) => lib.json(res, 200, {
  service: 'modguard-moderation',
  status: 'ok',
  mode: process.env.GEMINI_API_KEY ? 'live' : 'demo',
  cache_backend: process.env.KV_REST_API_URL ? 'upstash' : 'in-memory-lru-500',
  slack_alerts: Boolean(process.env.SLACK_WEBHOOK_URL),
  categories: lib.CATEGORIES,
  thresholds: { flag_at: lib.FLAG_AT, block_at: lib.BLOCK_AT },
  time: new Date().toISOString(),
});
