/** Smoke tests — zero-dep. Run: node tests/smoke.test.js */
'use strict';
const assert = require('assert');
const http = require('http');
const path = require('path');

process.env.PORT = 3903;
const lib = require(path.join(__dirname, '..', 'api', '_lib.js'));
const tickets = require(path.join(__dirname, '..', 'api', 'tickets.js'));
const approve = require(path.join(__dirname, '..', 'api', 'approve.js'));

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  if (url.pathname === '/api/tickets') return tickets(req, res);
  if (url.pathname === '/api/approve') return approve(req, res);
  res.statusCode = 404; res.end('{}');
});

function call(method, p, body) {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: 'localhost', port: 3903, path: p, method,
      headers: { 'content-type': 'application/json' } }, res => {
      let raw = '';
      res.on('data', c => raw += c);
      res.on('end', () => resolve({ statusCode: res.statusCode, body: raw ? JSON.parse(raw) : {} }));
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

(async () => {
  await new Promise(r => server.listen(3903, r));

  // 1. Unit: retrieval ranks the refund KB article first for refund text
  const top = lib.retrieve('I want a refund for a double charge')[0];
  assert.strictEqual(top.id, 'kb2', 'refund query should retrieve kb2');

  // 2. Unit: classification
  assert.strictEqual(lib.classify('please refund me').sensitive, true);
  assert.strictEqual(lib.classify('cancel my subscription').intent, 'cancellation');
  assert.strictEqual(lib.classify('where are the docs').sensitive, false);

  // 3. Docs ticket auto-resolves (non-sensitive path)
  const docs = await call('POST', '/api/tickets', {
    customer: 'Test User', email: 'test@example.com',
    subject: 'Need API documentation', body: 'Where can I find the API docs and auth token setup?',
  });
  assert.strictEqual(docs.statusCode, 201);
  assert.strictEqual(docs.body.status, 'RESOLVED', 'docs ticket should auto-resolve');
  assert.ok(docs.body.sent_reply.reply.length > 20);

  // 4. Refund ticket pauses at AWAITING_APPROVAL (sensitive path)
  const refund = await call('POST', '/api/tickets', {
    customer: 'Angry Customer', email: 'angry@example.com',
    subject: 'Refund request', body: 'I was double charged, I want a refund now.',
  });
  assert.strictEqual(refund.statusCode, 201);
  assert.strictEqual(refund.body.status, 'AWAITING_APPROVAL', 'refund ticket must pause');
  assert.strictEqual(refund.body.classification.intent, 'refund');
  const rid = refund.body.id;

  // 5. Approve resumes → RESOLVED
  const ok = await call('POST', '/api/approve', { ticket_id: rid, action: 'approve' });
  assert.strictEqual(ok.statusCode, 200);
  assert.strictEqual(ok.body.status, 'RESOLVED');
  assert.strictEqual(ok.body.sent_reply.by, 'manager-approved');

  // 6. Idempotency guard: second approve → 409
  const dup = await call('POST', '/api/approve', { ticket_id: rid, action: 'approve' });
  assert.strictEqual(dup.statusCode, 409, 'double approve must be rejected');

  // 7. Reject path → ESCALATED_HUMAN
  const cancel = await call('POST', '/api/tickets', {
    customer: 'Leaving User', email: 'bye@example.com',
    subject: 'Cancel account', body: 'Please cancel my subscription immediately.',
  });
  assert.strictEqual(cancel.body.status, 'AWAITING_APPROVAL');
  const rej = await call('POST', '/api/approve', { ticket_id: cancel.body.id, action: 'reject' });
  assert.strictEqual(rej.statusCode, 200);
  assert.strictEqual(rej.body.status, 'ESCALATED_HUMAN');

  // 8. Edit path: manager rewrites the reply
  const bill = await call('POST', '/api/tickets', {
    customer: 'Disputer', email: 'd@example.com',
    subject: 'Billing dispute', body: 'There is an incorrect charge on my invoice, I dispute it.',
  });
  assert.strictEqual(bill.body.status, 'AWAITING_APPROVAL');
  const edited = await call('POST', '/api/approve', {
    ticket_id: bill.body.id, action: 'edit', edited_reply: 'Hi — we reviewed the charge and issued a correction. — DuraSupport Team',
  });
  assert.strictEqual(edited.statusCode, 200);
  assert.strictEqual(edited.body.status, 'RESOLVED');
  assert.strictEqual(edited.body.sent_reply.by, 'manager-edited');
  assert.ok(edited.body.sent_reply.reply.includes('issued a correction'));

  // 9. Validation: missing fields / bad email / unknown action / missing edit body
  assert.strictEqual((await call('POST', '/api/tickets', { customer: 'X' })).statusCode, 400);
  assert.strictEqual((await call('POST', '/api/tickets', { customer: 'X', email: 'bad', subject: 's', body: 'b' })).statusCode, 400);
  assert.strictEqual((await call('POST', '/api/approve', { ticket_id: 'tkt_9999', action: 'approve' })).statusCode, 404);

  // 10. Timeline completeness: paused→resumed ticket has full audit trail
  const detail = await call('GET', `/api/tickets?id=${rid}`);
  const steps = detail.body.timeline.map(s => s.step);
  for (const s of ['RECEIVE', 'RETRIEVE', 'DRAFT', 'CLASSIFY', 'PAUSE', 'RESUME', 'SEND', 'RESOLVE']) {
    assert.ok(steps.includes(s), `timeline missing step ${s}`);
  }

  // 11. List endpoint + seeded tickets present
  const list = await call('GET', '/api/tickets');
  assert.ok(list.body.count >= 4);

  server.close();
  console.log('✅ durasupport: all smoke tests passed');
})().catch(e => { console.error('❌', e.message); process.exit(1); });
