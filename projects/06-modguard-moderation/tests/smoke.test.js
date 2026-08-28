/** Smoke tests — zero-dep. Run: node tests/smoke.test.js */
'use strict';
const assert = require('assert');
const http = require('http');
const path = require('path');
const fs = require('fs');

delete process.env.GEMINI_API_KEY;
delete process.env.KV_REST_API_URL;
delete process.env.SLACK_WEBHOOK_URL;

const lib = require(path.join(__dirname, '..', 'api', '_lib.js'));

const PORT = 3106;
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const m = url.pathname.match(/^\/api\/([a-z-]+)\/?$/);
  if (m) {
    const file = path.join(__dirname, '..', 'api', `${m[1]}.js`);
    if (fs.existsSync(file)) return require(file)(req, res);
  }
  res.statusCode = 404;
  res.end('{}');
});

function call(method, p, body) {
  return new Promise((resolve, reject) => {
    const req = http.request({ port: PORT, path: p, method, headers: { 'content-type': 'application/json' } }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(data) }));
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

(async () => {
  lib.resetAll();
  await new Promise(r => server.listen(PORT, r));

  // 1. health
  const h = await call('GET', '/api/health');
  assert.strictEqual(h.body.status, 'ok');
  assert.strictEqual(h.body.mode, 'demo');
  assert.strictEqual(h.body.cache_backend, 'in-memory-lru-500');

  // 2. clean content allows
  const clean = await call('POST', '/api/moderate', { content: 'Had a great time hiking this weekend, the views were beautiful!' });
  assert.strictEqual(clean.status, 200);
  assert.strictEqual(clean.body.action, 'allow');
  assert.strictEqual(clean.body.allowed, true);
  assert.strictEqual(clean.body.cached, false);

  // 3. scam content blocks (shortener + urgency + money)
  const scamText = 'URGENT: your account suspended! Verify your account now and send crypto to claim your prize http://bit.ly/x9z — expires in 24 hours';
  const scam = await call('POST', '/api/moderate', { content: scamText, user_id: 'u42' });
  assert.strictEqual(scam.body.action, 'block');
  assert.strictEqual(scam.body.allowed, false);
  assert.ok(scam.body.flagged_categories.includes('scam'), 'scam category flagged');
  assert.ok(scam.body.max_score >= 0.8);

  // 4. second identical call → cached:true with same verdict
  const scam2 = await call('POST', '/api/moderate', { content: scamText });
  assert.strictEqual(scam2.body.cached, true);
  assert.strictEqual(scam2.body.action, 'block');
  assert.strictEqual(scam2.body.hash, scam.body.hash);

  // 5. harassment flags/blocks
  const har = await call('POST', '/api/moderate', { content: 'shut up loser, you are pathetic and nobody likes you' });
  assert.notStrictEqual(har.body.action, 'allow');
  assert.ok(har.body.flagged_categories.includes('harassment'));

  // 6. PII detection
  const pii = await call('POST', '/api/moderate', { content: 'contact me at jane.doe@example.com or 555-123-4567, card 4111 1111 1111 1111' });
  assert.ok(pii.body.flagged_categories.includes('pii'), 'pii flagged');
  assert.ok(pii.body.evidence.pii.includes('email'));
  assert.ok(pii.body.evidence.pii.includes('credit_card'));

  // 7. incidents recorded (scam + harassment + pii; not clean, not cached repeat)
  const inc = await call('GET', '/api/incidents');
  assert.strictEqual(inc.body.count, 3);
  assert.strictEqual(inc.body.incidents[0].id, 'inc_0003');
  const blocked = await call('GET', '/api/incidents?action=block');
  assert.ok(blocked.body.count >= 1);

  // 8. stats math: 5 requests, 1 cache hit
  const st = await call('GET', '/api/stats');
  assert.strictEqual(st.body.total, 5);
  assert.strictEqual(st.body.cache_hits, 1);
  assert.strictEqual(st.body.cache_hit_rate, +(1 / 5).toFixed(3));
  assert.strictEqual(st.body.actions.allow, 1);
  assert.strictEqual(st.body.actions.allow + st.body.actions.flag + st.body.actions.block, 5);
  assert.ok(st.body.p50_latency_ms.cached !== null && st.body.p50_latency_ms.uncached !== null);
  assert.ok(st.body.p50_latency_ms.cached <= st.body.p50_latency_ms.uncached, 'cached path is faster');

  // 9. validation: missing content → 400
  const bad = await call('POST', '/api/moderate', {});
  assert.strictEqual(bad.status, 400);

  // 10. unit: sha256 stable, verdict assembly thresholds
  assert.strictEqual(lib.sha256('a'), lib.sha256('a'));
  const v = lib.assembleVerdict({ categories: [{ name: 'spam', score: 0.6, flagged: true }], evidence: {}, engine: 'rules' });
  assert.strictEqual(v.action, 'flag');

  server.close();
  console.log('✅ modguard: all smoke tests passed');
})().catch(e => { console.error('❌', e.message); process.exit(1); });
