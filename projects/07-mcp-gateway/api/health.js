'use strict';
const lib = require('./_lib.js');

module.exports = async (req, res) => lib.json(res, 200, {
  status: 'ok',
  service: lib.SERVER_INFO.name,
  version: lib.SERVER_INFO.version,
  protocol: lib.PROTOCOL_VERSION,
  mode: process.env.MCP_API_KEYS ? 'custom-keys' : 'demo',
  tools: lib.TOOLS.map(t => t.name),
  rate_limit: { capacity: lib.BUCKET_CAPACITY, refill_per_min: lib.REFILL_PER_MIN },
  langfuse_export: Boolean(process.env.LANGFUSE_PUBLIC_KEY && process.env.LANGFUSE_SECRET_KEY),
  time: new Date().toISOString(),
});
