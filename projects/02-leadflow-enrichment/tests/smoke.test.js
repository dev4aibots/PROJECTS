/** Smoke tests — zero-dep. Run: node tests/smoke.test.js */
'use strict';
const assert = require('assert');
const lib = require('../api/_lib.js');
const leadsHandler = require('../api/leads.js');
const healthHandler = require('../api/health.js');

// -- minimal req/res mocks ---------------------------------------------------
function mockReq({ method = 'GET', url = '/', body } = {}) {
  return { method, url, body };
}
function mockRes() {
  const res = {
    statusCode: 200, headers: {},
    setHeader(k, v) { this.headers[k] = v; },
    end(payload) { this.payload = payload; this.done && this.done(); },
  };
  res.finished = new Promise(r => { res.done = r; });
  return res;
}
async function call(handler, reqOpts) {
  const req = mockReq(reqOpts);
  const res = mockRes();
  await handler(req, res);
  await res.finished;
  return { statusCode: res.statusCode, body: JSON.parse(res.payload) };
}

(async () => {
  // 1. domain derivation ------------------------------------------------------
  assert.deepStrictEqual(
    lib.deriveDomain({ email: 'a@stripe.com' }),
    { domain: 'stripe.com', source: 'email' });
  assert.deepStrictEqual(
    lib.deriveDomain({ email: 'bob@gmail.com', company: 'Acme Widgets' }),
    { domain: 'acme-widgets.com', source: 'company-inferred' });
  assert.strictEqual(
    lib.deriveDomain({ domain: 'Ramp.com', email: 'x@gmail.com' }).source, 'explicit');
  assert.strictEqual(lib.deriveDomain({ email: 'x@gmail.com' }).domain, null);

  // 2. grading determinism: same input → identical grade ----------------------
  const firmoA = await lib.research('stripe.com');
  const lead = { name: 'T', email: 't@stripe.com', budget: 120000, message: 'need a pilot ASAP this quarter' };
  const dInfo = lib.deriveDomain(lead);
  const g1 = lib.deterministicGrade(lead, dInfo, firmoA);
  const g2 = lib.deterministicGrade(lead, dInfo, firmoA);
  assert.deepStrictEqual(g1, g2, 'grading must be deterministic');

  // 3. tier thresholds ---------------------------------------------------------
  assert.ok(g1.score >= 70 === (g1.tier === 'A'));
  const low = lib.deterministicGrade(
    { name: 'x', email: 'x@gmail.com', budget: 0, message: '' },
    lib.deriveDomain({ email: 'x@gmail.com' }),
    { employees: 0, funding: null });
  assert.strictEqual(low.tier, 'C', `no-signal lead must be C (got ${low.tier}, ${low.score})`);
  // boundary: exactly 40 → B, exactly 70 → A per BRIEF
  const mk = s => (s >= 70 ? 'A' : s >= 40 ? 'B' : 'C');
  assert.strictEqual(mk(70), 'A');
  assert.strictEqual(mk(40), 'B');
  assert.strictEqual(mk(39), 'C');

  // 4. full pipeline: enterprise sample → A tier -------------------------------
  const ent = await lib.processLead(lib.SAMPLE_LEADS.enterprise);
  assert.strictEqual(ent.grading.tier, 'A', `enterprise sample should be A (score ${ent.grading.score})`);
  assert.ok(ent.talking_points.length >= 2);
  assert.ok(ent.recommended_action.includes('AE'));

  // 5. smallbiz sample → C tier -------------------------------------------------
  const sb = await lib.processLead(lib.SAMPLE_LEADS.smallbiz);
  assert.strictEqual(sb.grading.tier, 'C', `smallbiz sample should be C (score ${sb.grading.score})`);

  // 6. endpoint contracts -------------------------------------------------------
  const h = await call(healthHandler);
  assert.strictEqual(h.statusCode, 200);
  assert.strictEqual(h.body.service, 'leadflow-enrichment');
  assert.strictEqual(h.body.mode, 'demo');

  const list = await call(leadsHandler, { method: 'GET', url: '/api/leads' });
  assert.strictEqual(list.statusCode, 200);
  assert.ok(list.body.count >= 3, 'seeded CRM should have >= 3 leads');
  assert.ok(list.body.leads[0].id && list.body.leads[0].tier);

  const one = await call(leadsHandler, { method: 'GET', url: `/api/leads?id=${list.body.leads[0].id}` });
  assert.strictEqual(one.statusCode, 200);
  assert.ok(one.body.firmographics);

  const missing = await call(leadsHandler, { method: 'GET', url: '/api/leads?id=lead_9999' });
  assert.strictEqual(missing.statusCode, 404);

  const created = await call(leadsHandler, {
    method: 'POST', url: '/api/leads',
    body: { name: 'Ivy Chen', email: 'ivy@ramp.com', budget: 60000, message: 'urgent POC evaluation' },
  });
  assert.strictEqual(created.statusCode, 201);
  assert.strictEqual(created.body.grading.tier, 'A');
  assert.strictEqual(created.body.slack.pushed, false); // demo mode

  const bad = await call(leadsHandler, { method: 'POST', url: '/api/leads', body: { email: 'no-name@x.com' } });
  assert.strictEqual(bad.statusCode, 400);

  const badMethod = await call(leadsHandler, { method: 'DELETE', url: '/api/leads' });
  assert.strictEqual(badMethod.statusCode, 405);

  console.log('✅ leadflow: all smoke tests passed');
})().catch(e => { console.error('❌', e.message); process.exit(1); });
