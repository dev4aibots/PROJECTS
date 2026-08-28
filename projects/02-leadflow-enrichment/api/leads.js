/**
 * POST /api/leads  — webhook: ingest lead → enrich → grade → dossier
 * GET  /api/leads  — list CRM · GET /api/leads?id=… — one dossier
 */
'use strict';
const lib = require('./_lib.js');

module.exports = async (req, res) => {
  try {
    await lib.ensureSeed();

    if (req.method === 'GET') {
      const url = new URL(req.url, 'http://x');
      const id = url.searchParams.get('id');
      if (id) {
        const rec = lib.store.leads.find(l => l.id === id);
        if (!rec) return lib.json(res, 404, { error: `lead ${id} not found` });
        return lib.json(res, 200, rec);
      }
      return lib.json(res, 200, {
        count: lib.store.leads.length,
        leads: lib.store.leads.map(l => ({
          id: l.id, created_at: l.created_at, name: l.lead.name,
          company: l.firmographics.company, tier: l.grading.tier,
          score: l.grading.score, action: l.recommended_action,
        })),
      });
    }

    if (req.method === 'POST') {
      let body;
      try {
        body = await lib.readBody(req);
      } catch (_) {
        return lib.json(res, 400, { error: 'invalid JSON body' });
      }
      const rec = await lib.processLead(body);
      return lib.json(res, 201, rec);
    }

    return lib.json(res, 405, { error: 'method not allowed' });
  } catch (e) {
    return lib.json(res, e.status || 500, { error: e.message });
  }
};
