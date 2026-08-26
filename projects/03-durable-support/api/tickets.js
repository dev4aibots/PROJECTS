/**
 * POST /api/tickets — ingest ticket → run durable workflow until done or paused
 * GET  /api/tickets — list · GET /api/tickets?id=… — one ticket w/ full timeline
 */
'use strict';
const lib = require('./_lib.js');

module.exports = async (req, res) => {
  try {
    await lib.ensureSeed();
    const url = new URL(req.url, 'http://x');

    if (req.method === 'GET') {
      const id = url.searchParams.get('id');
      if (id) {
        const t = lib.store.tickets.get(id);
        if (!t) return lib.json(res, 404, { error: `ticket ${id} not found` });
        return lib.json(res, 200, t);
      }
      const tickets = [...lib.store.tickets.values()].sort((a, b) => b.created_at.localeCompare(a.created_at));
      return lib.json(res, 200, {
        count: tickets.length,
        awaiting_approval: tickets.filter(t => t.status === 'AWAITING_APPROVAL').length,
        tickets: tickets.map(t => ({
          id: t.id, customer: t.customer, subject: t.subject,
          status: t.status, intent: t.classification?.intent,
          created_at: t.created_at, updated_at: t.updated_at,
        })),
      });
    }

    if (req.method === 'POST') {
      const body = await lib.readBody(req);
      const { customer, email, subject } = body;
      if (!customer || !email || !subject || !body.body) {
        return lib.json(res, 400, { error: 'required fields: customer, email, subject, body' });
      }
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
        return lib.json(res, 400, { error: 'invalid email' });
      }
      const ticket = await lib.createTicket({
        customer: String(customer).slice(0, 120),
        email: String(email).slice(0, 200),
        subject: String(subject).slice(0, 300),
        body: String(body.body).slice(0, 5000),
      });
      return lib.json(res, 201, ticket);
    }

    return lib.json(res, 405, { error: 'method not allowed' });
  } catch (e) {
    return lib.json(res, e.status || 500, { error: e.message });
  }
};
