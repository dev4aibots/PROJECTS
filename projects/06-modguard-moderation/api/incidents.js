/**
 * GET /api/incidents — flagged/blocked content log, newest first.
 * Optional ?action=flag|block and ?limit=N filters.
 */
'use strict';
const lib = require('./_lib.js');

module.exports = (req, res) => {
  if (req.method !== 'GET') return lib.json(res, 405, { error: 'GET only' });
  const url = new URL(req.url, 'http://x');
  const action = url.searchParams.get('action');
  const limit = Math.min(parseInt(url.searchParams.get('limit') || '50', 10) || 50, 200);
  let items = lib.INCIDENTS;
  if (action) items = items.filter(i => i.action === action);
  return lib.json(res, 200, { count: items.length, incidents: items.slice(0, limit) });
};
