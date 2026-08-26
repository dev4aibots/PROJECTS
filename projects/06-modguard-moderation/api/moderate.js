/**
 * POST /api/moderate {content, content_type: "text"|"image_url", user_id?}
 * → layered verdict: TIER 1 cache (sha256 → <5ms) · TIER 2 Gemini Flash or
 *   deterministic rule engine. Flagged content is incident-logged.
 */
'use strict';
const lib = require('./_lib.js');

module.exports = async (req, res) => {
  if (req.method !== 'POST') return lib.json(res, 405, { error: 'POST only' });
  try {
    const body = await lib.readBody(req);
    const result = await lib.moderate(body);
    return lib.json(res, 200, result);
  } catch (e) {
    return lib.json(res, e.status || 500, { error: e.message });
  }
};
