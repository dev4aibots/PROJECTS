/**
 * POST /api/approve {ticket_id, action: approve|edit|reject, edited_reply?}
 * RESUMES a workflow paused at AWAITING_APPROVAL — the durable-execution core.
 * 409 if the ticket is not paused (idempotency guard against double-clicks).
 */
'use strict';
const lib = require('./_lib.js');

module.exports = async (req, res) => {
  try {
    await lib.ensureSeed();
    if (req.method !== 'POST') return lib.json(res, 405, { error: 'method not allowed' });
    const body = await lib.readBody(req);
    const { ticket_id, action, edited_reply } = body;
    if (!ticket_id || !action) {
      return lib.json(res, 400, { error: 'required fields: ticket_id, action (approve|edit|reject)' });
    }
    const ticket = lib.approve(ticket_id, action, edited_reply);
    return lib.json(res, 200, ticket);
  } catch (e) {
    return lib.json(res, e.status || 500, { error: e.message });
  }
};
