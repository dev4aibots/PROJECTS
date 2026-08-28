/**
 * ModGuard — layered AI content moderation with a <50ms cached fast path.
 *
 * TIER 1: sha256(content) → verdict cache (Upstash REST if KV_REST_API_URL is
 *         set, else in-memory LRU of 500). Cache hits skip all analysis.
 * TIER 2: GEMINI_API_KEY → Gemini Flash policy evaluation. Without a key, a
 *         deterministic rule engine (category lexicons, scam-link heuristics,
 *         PII regexes) produces the same verdict shape — the live demo works
 *         with zero keys.
 *
 * Flagged content → incident log (+ optional Slack webhook alert).
 * Zero dependencies.
 */
'use strict';

const crypto = require('crypto');

// ---------------------------------------------------------------------------
// Policy categories
// ---------------------------------------------------------------------------
const CATEGORIES = ['spam', 'scam', 'harassment', 'hate', 'violence', 'self_harm', 'sexual', 'pii'];

// Action thresholds on max category score
const BLOCK_AT = 0.8;
const FLAG_AT = 0.5;

// ---------------------------------------------------------------------------
// TIER 1 — verdict cache: sha256 → verdict. In-memory LRU(500) or Upstash.
// ---------------------------------------------------------------------------
const LRU_MAX = 500;
const lru = new Map(); // Map preserves insertion order → cheap LRU

function sha256(s) {
  return crypto.createHash('sha256').update(String(s)).digest('hex');
}

function lruGet(key) {
  if (!lru.has(key)) return null;
  const v = lru.get(key);
  lru.delete(key);
  lru.set(key, v); // refresh recency
  return v;
}

function lruSet(key, value) {
  if (lru.has(key)) lru.delete(key);
  lru.set(key, value);
  if (lru.size > LRU_MAX) lru.delete(lru.keys().next().value); // evict oldest
}

async function cacheGet(key) {
  const base = process.env.KV_REST_API_URL;
  const token = process.env.KV_REST_API_TOKEN;
  if (base && token) {
    try {
      const r = await fetch(`${base}/get/modguard:${key}`, {
        headers: { authorization: `Bearer ${token}` },
      });
      const d = await r.json();
      return d.result ? JSON.parse(d.result) : null;
    } catch { /* fall through to LRU */ }
  }
  return lruGet(key);
}

async function cacheSet(key, value) {
  const base = process.env.KV_REST_API_URL;
  const token = process.env.KV_REST_API_TOKEN;
  if (base && token) {
    try {
      await fetch(`${base}/set/modguard:${key}?EX=86400`, {
        method: 'POST',
        headers: { authorization: `Bearer ${token}` },
        body: JSON.stringify(value),
      });
      return;
    } catch { /* fall through to LRU */ }
  }
  lruSet(key, value);
}

// ---------------------------------------------------------------------------
// TIER 2a — deterministic rule engine (demo mode / Gemini fallback)
// ---------------------------------------------------------------------------
const LEXICONS = {
  spam: [
    'buy now', 'limited offer', 'act now', 'click here', 'free money', 'winner',
    'congratulations you', 'work from home', 'earn $$$', 'guaranteed income',
    'no risk', 'double your', '100% free', 'exclusive deal', 'subscribe now',
  ],
  scam: [
    'send crypto', 'send bitcoin', 'wire transfer', 'gift card', 'western union',
    'verify your account', 'account suspended', 'urgent action required',
    'claim your prize', 'inheritance', 'nigerian prince', 'seed phrase',
    'wallet address', 'investment opportunity', 'guaranteed returns',
    'crypto giveaway', 'giveaway', 'you won', 'claim now', 'send 0',
    'double your crypto', 'airdrop', 'connect your wallet', 'private key',
  ],
  harassment: [
    'you are pathetic', 'you are worthless', 'nobody likes you', 'kill yourself',
    'you idiot', 'you moron', 'shut up loser', 'you are trash', 'go away freak',
    'everyone hates you',
  ],
  hate: [
    'all [group] are', 'go back to your country', 'subhuman', 'vermin people',
    'racial slur', 'ethnic cleansing',
  ],
  violence: [
    'i will hurt you', 'i will kill', 'beat you up', 'find where you live',
    'watch your back', 'bomb threat', 'shoot up',
  ],
  self_harm: [
    'want to end it all', 'no reason to live', 'hurting myself', 'suicide plan',
  ],
  sexual: [
    'explicit adult content', 'nsfw link', 'onlyfans promo',
  ],
};

// URL shorteners commonly used to mask scam links
const SHORTENERS = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'cutt.ly', 'rb.gy', 'is.gd', 'shorturl.at'];

const PII_PATTERNS = [
  { name: 'email', re: /[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i },
  { name: 'phone', re: /(\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b/ },
  { name: 'credit_card', re: /\b(?:\d[ -]?){13,16}\b/ },
  { name: 'ssn', re: /\b\d{3}-\d{2}-\d{4}\b/ },
];

const URGENCY = ['urgent', 'immediately', 'right now', 'within 24 hours', 'last chance', 'expires', 'final notice', 'act fast'];
const MONEY = ['$', 'usd', 'payment', 'money', 'cash', 'crypto', 'bitcoin', 'eth', 'ethereum', 'bank', 'fee', 'deposit', 'refund'];

/**
 * Normalize text for phrase matching: lowercase, strip punctuation to spaces,
 * collapse whitespace. Without this, "Congratulations! You won" would not match
 * the lexicon phrase "congratulations you" — evasion by punctuation is the most
 * common trivial bypass of substring-based moderation.
 */
function normalize(s) {
  return String(s || '')
    .toLowerCase()
    .replace(/[^\p{L}\p{N}$]+/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Word-boundary term test against normalized text. Used for short signal terms
 * (URGENCY/MONEY) where plain substring matching would false-positive — e.g.
 * "eth" inside "whether"/"method", or "fee" inside "coffee".
 */
function hasTerm(text, term) {
  const t = normalize(term);
  if (!t) return false;
  if (t === '$') return text.includes('$');
  return new RegExp(`(?:^| )${t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?: |$)`).test(text);
}

function scoreLexicon(text, phrases) {
  let hits = 0;
  const matched = [];
  for (const p of phrases) {
    if (text.includes(normalize(p))) { hits++; matched.push(p); }
  }
  // 1 hit → 0.6, 2 → 0.85, 3+ → 0.97
  const score = hits === 0 ? 0 : Math.min(0.97, 0.35 + hits * 0.25);
  return { score, matched };
}

function ruleEngine(content) {
  const text = normalize(content);
  // Domains keep their dots, so shortener detection runs on the raw lowercase
  // text — normalizing would turn "t.co" into "t co" and false-positive on
  // ordinary prose like "isn't correct".
  const raw = String(content || '').toLowerCase();
  const categories = [];
  const evidence = {};

  for (const cat of CATEGORIES) {
    let score = 0;
    let matched = [];
    if (LEXICONS[cat]) {
      ({ score, matched } = scoreLexicon(text, LEXICONS[cat]));
    }

    if (cat === 'scam') {
      // scam-link heuristics: shortener + (urgency|money) escalates
      const shortener = SHORTENERS.find(s => raw.includes(s));
      const urgency = URGENCY.some(u => hasTerm(text, u));
      const money = MONEY.some(m => hasTerm(text, m));
      if (shortener) {
        matched.push(`shortened link (${shortener})`);
        score = Math.max(score, urgency || money ? 0.9 : 0.55);
      }
      if (urgency && money) {
        matched.push('urgency + money pattern');
        score = Math.max(score, 0.75);
      }
    }

    if (cat === 'pii') {
      const found = PII_PATTERNS.filter(p => p.re.test(content || ''));
      if (found.length) {
        matched = found.map(f => f.name);
        score = Math.min(0.97, 0.55 + found.length * 0.15);
      }
    }

    if (matched.length) evidence[cat] = matched;
    categories.push({ name: cat, score: +score.toFixed(2), flagged: score >= FLAG_AT });
  }
  return { categories, evidence, engine: 'rules' };
}

// ---------------------------------------------------------------------------
// TIER 2b — Gemini Flash policy evaluation (only when GEMINI_API_KEY is set)
// ---------------------------------------------------------------------------
async function aiEngine(content, contentType) {
  const prompt =
    `You are a content-moderation policy engine. Score this ${contentType} on each category ` +
    `from 0.0 to 1.0: ${CATEGORIES.join(', ')}. Reply ONLY with JSON: ` +
    `{"categories":[{"name":"spam","score":0.0},...]}.\n\nCONTENT:\n${content}`;

  // Provider 1: Gemini
  if (process.env.GEMINI_API_KEY) {
    try {
      const r = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${process.env.GEMINI_API_KEY}`,
        {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
        },
      );
      if (r.ok) {
        const d = await r.json();
        const raw = d.candidates?.[0]?.content?.parts?.[0]?.text || '';
        const parsed = JSON.parse(raw.replace(/```json|```/g, '').trim());
        const byName = Object.fromEntries((parsed.categories || []).map(c => [c.name, c.score]));
        const categories = CATEGORIES.map(name => {
          const score = +(byName[name] || 0).toFixed(2);
          return { name, score, flagged: score >= FLAG_AT };
        });
        return { categories, evidence: {}, engine: 'gemini-1.5-flash' };
      }
    } catch (_) { /* failover */ }
  }

  // Provider 2: Groq
  if (process.env.GROQ_API_KEY) {
    try {
      const r = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: { authorization: `Bearer ${process.env.GROQ_API_KEY}`, 'content-type': 'application/json' },
        body: JSON.stringify({
          model: 'llama-3.1-8b-instant', response_format: { type: 'json_object' },
          messages: [{ role: 'system', content: prompt }],
        }),
      });
      if (r.ok) {
        const d = await r.json();
        const parsed = JSON.parse(d.choices[0].message.content);
        const byName = Object.fromEntries((parsed.categories || []).map(c => [c.name, c.score]));
        const categories = CATEGORIES.map(name => {
          const score = +(byName[name] || 0).toFixed(2);
          return { name, score, flagged: score >= FLAG_AT };
        });
        return { categories, evidence: {}, engine: 'groq/llama-3.1-8b' };
      }
    } catch (_) { /* failover */ }
  }

  // Provider 3: NVIDIA NIM
  if (process.env.NVIDIA_API_KEY) {
    try {
      const r = await fetch('https://integrate.api.nvidia.com/v1/chat/completions', {
        method: 'POST',
        headers: { authorization: `Bearer ${process.env.NVIDIA_API_KEY}`, 'content-type': 'application/json' },
        body: JSON.stringify({
          model: 'meta/llama-3.1-70b-instruct',
          messages: [{ role: 'system', content: prompt }],
        }),
      });
      if (r.ok) {
        const d = await r.json();
        const txt = d.choices[0].message.content;
        const m = txt.match(/\{[\s\S]*\}/);
        if (m) {
          const parsed = JSON.parse(m[0]);
          const byName = Object.fromEntries((parsed.categories || []).map(c => [c.name, c.score]));
          const categories = CATEGORIES.map(name => {
            const score = +(byName[name] || 0).toFixed(2);
            return { name, score, flagged: score >= FLAG_AT };
          });
          return { categories, evidence: {}, engine: 'nvidia/llama-3.1-70b' };
        }
      }
    } catch (_) { /* failover */ }
  }

  return ruleEngine(content);
}

// ---------------------------------------------------------------------------
// Verdict assembly
// ---------------------------------------------------------------------------
function assembleVerdict(analysis) {
  const max = Math.max(...analysis.categories.map(c => c.score), 0);
  const flagged = analysis.categories.filter(c => c.flagged).map(c => c.name);
  const action = max >= BLOCK_AT ? 'block' : max >= FLAG_AT ? 'flag' : 'allow';
  const severity = max >= BLOCK_AT ? 'high' : max >= FLAG_AT ? 'medium' : 'none';
  return {
    allowed: action !== 'block',
    action,
    severity,
    max_score: +max.toFixed(2),
    flagged_categories: flagged,
    categories: analysis.categories,
    evidence: analysis.evidence,
    engine: analysis.engine,
  };
}

// ---------------------------------------------------------------------------
// Stats + incidents (in-memory per instance; documented swap for KV/Postgres)
// ---------------------------------------------------------------------------
const STATS = {
  total: 0,
  cache_hits: 0,
  actions: { allow: 0, flag: 0, block: 0 },
  category_counts: Object.fromEntries(CATEGORIES.map(c => [c, 0])),
  latencies_cached: [],
  latencies_uncached: [],
};

const INCIDENTS = []; // newest first
let INCIDENT_SEQ = 0;

function p50(arr) {
  if (!arr.length) return null;
  const s = [...arr].sort((a, b) => a - b);
  return +s[Math.floor(s.length / 2)].toFixed(2);
}

function recordStats(verdict, cached, latencyMs) {
  STATS.total++;
  if (cached) STATS.cache_hits++;
  STATS.actions[verdict.action]++;
  for (const c of verdict.flagged_categories) STATS.category_counts[c]++;
  const bucket = cached ? STATS.latencies_cached : STATS.latencies_uncached;
  bucket.push(latencyMs);
  if (bucket.length > 1000) bucket.shift();
}

function logIncident(content, verdict, userId) {
  const inc = {
    id: `inc_${String(++INCIDENT_SEQ).padStart(4, '0')}`,
    time: new Date().toISOString(),
    user_id: userId || 'anonymous',
    action: verdict.action,
    severity: verdict.severity,
    flagged_categories: verdict.flagged_categories,
    max_score: verdict.max_score,
    excerpt: String(content).slice(0, 140),
  };
  INCIDENTS.unshift(inc);
  if (INCIDENTS.length > 200) INCIDENTS.pop();
  // Slack alert (fire and forget) only when webhook configured
  const hook = process.env.SLACK_WEBHOOK_URL;
  if (hook) {
    fetch(hook, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        text: `🚨 ModGuard ${verdict.action.toUpperCase()} [${verdict.severity}] ` +
              `${verdict.flagged_categories.join(', ')} — "${inc.excerpt}"`,
      }),
    }).catch(() => {});
  }
  return inc;
}

// ---------------------------------------------------------------------------
// Main moderation pipeline
// ---------------------------------------------------------------------------
async function moderate({ content, content_type = 'text', user_id }) {
  if (!content || typeof content !== 'string') {
    const err = new Error('content (string) is required');
    err.status = 400;
    throw err;
  }
  const t0 = process.hrtime.bigint();
  const hash = sha256(content);
  const steps = [{ step: 'received', detail: `${content.length} chars, type=${content_type}` }];

  // TIER 1 — cache
  steps.push({ step: 'hash', detail: hash.slice(0, 16) + '…' });
  const cachedVerdict = await cacheGet(hash);
  if (cachedVerdict) {
    const latency = Number(process.hrtime.bigint() - t0) / 1e6;
    steps.push({ step: 'cache_check', detail: 'HIT — verdict served from cache' });
    recordStats(cachedVerdict, true, latency);
    return { ...cachedVerdict, cached: true, hash, latency_ms: +latency.toFixed(2), steps };
  }
  steps.push({ step: 'cache_check', detail: 'MISS — running analysis' });

  // TIER 2 — analysis
  const analysis = await aiEngine(content, content_type);
  steps.push({ step: 'ai_analysis', detail: `policy evaluation (${analysis.engine})` });

  const verdict = assembleVerdict(analysis);
  await cacheSet(hash, verdict);
  steps.push({ step: 'verdict_cached', detail: `action=${verdict.action}, cached for identical content` });

  if (verdict.action !== 'allow') {
    const inc = logIncident(content, verdict, user_id);
    steps.push({ step: 'incident_logged', detail: inc.id });
  }

  const latency = Number(process.hrtime.bigint() - t0) / 1e6;
  recordStats(verdict, false, latency);
  return { ...verdict, cached: false, hash, latency_ms: +latency.toFixed(2), steps };
}

function resetAll() {
  lru.clear();
  INCIDENTS.length = 0;
  INCIDENT_SEQ = 0;
  STATS.total = 0;
  STATS.cache_hits = 0;
  STATS.actions = { allow: 0, flag: 0, block: 0 };
  STATS.category_counts = Object.fromEntries(CATEGORIES.map(c => [c, 0]));
  STATS.latencies_cached = [];
  STATS.latencies_uncached = [];
}

// ---------------------------------------------------------------------------
// HTTP helpers (shared by all endpoints)
// ---------------------------------------------------------------------------
function json(res, status, body) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json');
  res.setHeader('access-control-allow-origin', '*');
  res.end(JSON.stringify(body, null, 2));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', c => { data += c; if (data.length > 1e6) req.destroy(); });
    req.on('end', () => {
      try { resolve(data ? JSON.parse(data) : {}); }
      catch { reject(Object.assign(new Error('invalid JSON body'), { status: 400 })); }
    });
    req.on('error', reject);
  });
}

module.exports = {
  CATEGORIES, BLOCK_AT, FLAG_AT,
  moderate, ruleEngine, assembleVerdict, sha256,
  cacheGet, cacheSet,
  STATS, INCIDENTS, p50, resetAll,
  json, readBody,
};
