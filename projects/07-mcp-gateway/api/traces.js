/**
 * GET /api/traces — telemetry for every MCP call, newest first.
 * Optional ?tool=NAME, ?ok=true|false, ?limit=N filters.
 */
'use strict';
const lib = require('./_lib.js');

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') return lib.json(res, 204, {});
  const url = new URL(req.url, 'http://x');
  const tool = url.searchParams.get('tool');
  const ok = url.searchParams.get('ok');
  const limit = Math.max(1, Math.min(200, Number(url.searchParams.get('limit')) || 50));
  let items = lib.TRACES;
  if (tool) items = items.filter(t => t.tool === tool);
  if (ok !== null) items = items.filter(t => String(t.ok) === ok);
  return lib.json(res, 200, { count: items.length, traces: items.slice(0, limit) });
};
