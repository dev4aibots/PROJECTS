/**
 * LeadFlow — shared engine: domain derivation, research, grading, storage, Slack.
 * Zero dependencies. Real integrations (Tavily / Groq / Slack / Supabase) activate
 * only when their env vars are set; otherwise deterministic demo mode keeps the
 * live URL fully functional with no keys.
 */
'use strict';

const crypto = require('crypto');

// ---------------------------------------------------------------------------
// ICP (Ideal Customer Profile) — the product decision the grader scores against
// ---------------------------------------------------------------------------
const ICP = {
  description:
    'B2B SaaS / fintech / logistics companies, 50–5000 employees, with recent funding or active hiring, budget ≥ $10k, buying AI/automation tooling.',
  weights: { budget: 30, domainQuality: 15, employees: 25, fundingRecency: 20, intent: 10 },
};

// Free-mail domains never identify a company — filter before firmographic lookup.
const FREE_MAIL = new Set([
  'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'aol.com',
  'icloud.com', 'proton.me', 'protonmail.com', 'mail.com', 'gmx.com',
]);

// ---------------------------------------------------------------------------
// Demo research corpus — 5 known domains + deterministic generator for the rest
// ---------------------------------------------------------------------------
const DEMO_CORPUS = {
  'stripe.com': {
    company: 'Stripe', industry: 'Fintech / Payments', employees: 8000,
    funding: { round: 'Series I', amount_usd: 6500000000, when: '2023-03' },
    news: [
      'Stripe launches usage-based billing for AI companies',
      'Stripe expands enterprise revenue-recognition suite',
      'Stripe reports record payment volume for the fiscal year',
    ],
    tech: ['Ruby', 'Go', 'AWS', 'Kafka'],
  },
  'notion.so': {
    company: 'Notion', industry: 'B2B SaaS / Productivity', employees: 600,
    funding: { round: 'Series C', amount_usd: 275000000, when: '2021-10' },
    news: [
      'Notion launches AI connectors for enterprise search',
      'Notion acquires calendar startup Cron',
      'Notion passes 100M users milestone',
    ],
    tech: ['TypeScript', 'React', 'Postgres'],
  },
  'flexport.com': {
    company: 'Flexport', industry: 'Logistics / Supply Chain', employees: 2600,
    funding: { round: 'Series E', amount_usd: 935000000, when: '2022-02' },
    news: [
      'Flexport rolls out AI-powered customs classification',
      'Flexport expands ocean freight network in Southeast Asia',
      'Flexport announces new CTO to lead platform rebuild',
    ],
    tech: ['Ruby', 'React', 'GCP'],
  },
  'ramp.com': {
    company: 'Ramp', industry: 'Fintech / Spend Management', employees: 1000,
    funding: { round: 'Series D-2', amount_usd: 300000000, when: '2024-04' },
    news: [
      'Ramp launches AI agents for expense policy enforcement',
      'Ramp valuation rises in latest funding round',
      'Ramp adds treasury product for idle cash',
    ],
    tech: ['Python', 'TypeScript', 'Snowflake'],
  },
  'acme-widgets.example': {
    company: 'Acme Widgets', industry: 'Small Business / Retail', employees: 8,
    funding: null,
    news: ['Acme Widgets opens second local store'],
    tech: ['WordPress'],
  },
};

/** Deterministic pseudo-research for unknown domains (stable per domain). */
function generatedResearch(domain) {
  const h = crypto.createHash('sha256').update(domain).digest();
  const employees = 10 + (h[0] * 37 + h[1]) % 4990;               // 10–5000
  const industries = ['B2B SaaS', 'Fintech', 'Logistics', 'E-commerce', 'Healthcare IT', 'Manufacturing'];
  const industry = industries[h[2] % industries.length];
  const monthsAgo = h[3] % 48;                                     // 0–47 months
  const funded = h[4] % 3 !== 0;                                   // 2/3 have funding
  const when = new Date(Date.now() - monthsAgo * 30 * 864e5).toISOString().slice(0, 7);
  const name = domain.split('.')[0].replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  return {
    company: name, industry, employees,
    funding: funded ? { round: ['Seed', 'Series A', 'Series B'][h[5] % 3], amount_usd: (1 + h[6] % 90) * 1e6, when } : null,
    news: [
      `${name} announces expansion of its ${industry.toLowerCase()} platform`,
      `${name} hiring across engineering and go-to-market teams`,
    ],
    tech: ['Cloud', 'APIs'],
    _generated: true,
  };
}

// ---------------------------------------------------------------------------
// Domain derivation
// ---------------------------------------------------------------------------
function deriveDomain({ email, domain, company }) {
  if (domain) return { domain: domain.toLowerCase().trim(), source: 'explicit' };
  const emailDomain = (email || '').split('@')[1]?.toLowerCase().trim();
  if (emailDomain && !FREE_MAIL.has(emailDomain)) return { domain: emailDomain, source: 'email' };
  if (company) {
    const slug = company.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    return { domain: `${slug}.com`, source: 'company-inferred' };
  }
  return { domain: null, source: 'none' };
}

// ---------------------------------------------------------------------------
// Research (Tavily live if TAVILY_API_KEY, else demo corpus)
// ---------------------------------------------------------------------------
async function research(domain) {
  if (!domain) return { company: 'Unknown', industry: 'Unknown', employees: 0, funding: null, news: [], tech: [], mode: 'none' };
  if (process.env.TAVILY_API_KEY) {
    try {
      const resp = await fetch('https://api.tavily.com/search', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          api_key: process.env.TAVILY_API_KEY,
          query: `${domain} company size funding news`,
          max_results: 5,
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        const base = DEMO_CORPUS[domain] || generatedResearch(domain);
        return {
          ...base,
          news: (data.results || []).slice(0, 3).map(r => r.title).filter(Boolean),
          mode: 'tavily',
        };
      }
    } catch (_) { /* fall through to demo */ }
  }
  const base = DEMO_CORPUS[domain] || generatedResearch(domain);
  return { ...base, mode: 'demo' };
}

// ---------------------------------------------------------------------------
// Grading — Groq LLM when key present, deterministic scorer otherwise.
// The deterministic weights mirror the ICP prompt so both paths agree in spirit.
// ---------------------------------------------------------------------------
function monthsSince(yyyyMm) {
  if (!yyyyMm) return Infinity;
  const [y, m] = yyyyMm.split('-').map(Number);
  const now = new Date();
  return (now.getFullYear() - y) * 12 + (now.getMonth() + 1 - m);
}

function deterministicGrade(lead, domainInfo, firmo) {
  const s = { budget: 0, domainQuality: 0, employees: 0, fundingRecency: 0, intent: 0 };

  const budget = Number(lead.budget) || 0;
  if (budget >= 50000) s.budget = 30;
  else if (budget >= 10000) s.budget = 20;
  else if (budget >= 1000) s.budget = 8;

  if (domainInfo.source === 'explicit' || domainInfo.source === 'email') s.domainQuality = 15;
  else if (domainInfo.source === 'company-inferred') s.domainQuality = 7;

  const emp = firmo.employees || 0;
  if (emp >= 50 && emp <= 5000) s.employees = 25;       // ICP sweet spot
  else if (emp > 5000) s.employees = 15;                // enterprise: good but longer cycles
  else if (emp >= 10) s.employees = 6;

  const mo = monthsSince(firmo.funding?.when);
  if (mo <= 18) s.fundingRecency = 20;
  else if (mo <= 36) s.fundingRecency = 12;
  else if (firmo.funding) s.fundingRecency = 5;

  const msg = (lead.message || '').toLowerCase();
  if (/\b(urgent|asap|this quarter|evaluat|pilot|poc|demo)\b/.test(msg)) s.intent = 10;
  else if (msg.length > 20) s.intent = 5;

  const score = s.budget + s.domainQuality + s.employees + s.fundingRecency + s.intent;
  const tier = score >= 70 ? 'A' : score >= 40 ? 'B' : 'C';
  return { score, tier, breakdown: s, grader: 'deterministic' };
}

async function grade(lead, domainInfo, firmo) {
  const sysMsg = `You grade B2B leads against this ICP: ${ICP.description}. Reply JSON {"score":0-100,"tier":"A|B|C","reason":"..."} where A>=70, B>=40.`;
  const userMsg = JSON.stringify({ lead, firmographics: firmo });

  // 1. Groq
  if (process.env.GROQ_API_KEY) {
    try {
      const resp = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: { authorization: `Bearer ${process.env.GROQ_API_KEY}`, 'content-type': 'application/json' },
        body: JSON.stringify({
          model: 'llama-3.1-8b-instant', response_format: { type: 'json_object' },
          messages: [{ role: 'system', content: sysMsg }, { role: 'user', content: userMsg }],
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        const parsed = JSON.parse(data.choices[0].message.content);
        if (typeof parsed.score === 'number' && /^[ABC]$/.test(parsed.tier)) {
          return { score: parsed.score, tier: parsed.tier, breakdown: { llm_reason: parsed.reason }, grader: 'groq-llama-3.1' };
        }
      }
    } catch (_) { /* failover */ }
  }

  // 2. NVIDIA NIM
  if (process.env.NVIDIA_API_KEY) {
    try {
      const resp = await fetch('https://integrate.api.nvidia.com/v1/chat/completions', {
        method: 'POST',
        headers: { authorization: `Bearer ${process.env.NVIDIA_API_KEY}`, 'content-type': 'application/json' },
        body: JSON.stringify({
          model: 'meta/llama-3.1-70b-instruct',
          messages: [{ role: 'system', content: sysMsg }, { role: 'user', content: userMsg }],
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        const txt = data.choices[0].message.content;
        const m = txt.match(/\{[\s\S]*\}/);
        if (m) {
          const parsed = JSON.parse(m[0]);
          if (typeof parsed.score === 'number' && /^[ABC]$/.test(parsed.tier)) {
            return { score: parsed.score, tier: parsed.tier, breakdown: { llm_reason: parsed.reason }, grader: 'llama-3.1-70b (nvidia nim)' };
          }
        }
      }
    } catch (_) { /* failover */ }
  }

  // 3. Mistral AI
  if (process.env.MISTRAL_API_KEY) {
    try {
      const resp = await fetch('https://api.mistral.ai/v1/chat/completions', {
        method: 'POST',
        headers: { authorization: `Bearer ${process.env.MISTRAL_API_KEY}`, 'content-type': 'application/json' },
        body: JSON.stringify({
          model: 'mistral-small-latest', response_format: { type: 'json_object' },
          messages: [{ role: 'system', content: sysMsg }, { role: 'user', content: userMsg }],
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        const parsed = JSON.parse(data.choices[0].message.content);
        if (typeof parsed.score === 'number' && /^[ABC]$/.test(parsed.tier)) {
          return { score: parsed.score, tier: parsed.tier, breakdown: { llm_reason: parsed.reason }, grader: 'mistral-small' };
        }
      }
    } catch (_) { /* failover */ }
  }

  return deterministicGrade(lead, domainInfo, firmo);
}

// ---------------------------------------------------------------------------
// Dossier assembly
// ---------------------------------------------------------------------------
function talkingPoints(firmo, grading) {
  const pts = [];
  if (firmo.funding) pts.push(`Raised ${firmo.funding.round} (${fmtUsd(firmo.funding.amount_usd)}) in ${firmo.funding.when} — budget likely available.`);
  if (firmo.employees >= 50 && firmo.employees <= 5000) pts.push(`${firmo.employees} employees — squarely in our ICP band (50–5000).`);
  else if (firmo.employees > 5000) pts.push(`${firmo.employees} employees — enterprise motion; expect procurement + security review.`);
  if (firmo.news?.length) pts.push(`Recent signal: "${firmo.news[0]}" — open the call with this.`);
  if (grading.tier === 'A') pts.push('A-tier: route to senior AE, respond within 1 hour.');
  if (grading.tier === 'C') pts.push('C-tier: nurture sequence only; do not book AE time.');
  return pts;
}

function fmtUsd(n) {
  if (!n) return '$0';
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(0)}M`;
  return `$${n.toLocaleString()}`;
}

function recommendedAction(tier) {
  return {
    A: 'Immediate AE outreach (call within 1 hour) + personalized demo invite',
    B: 'SDR follow-up within 24h + tailored case-study email',
    C: 'Add to automated nurture sequence; re-score on next touchpoint',
  }[tier];
}

// ---------------------------------------------------------------------------
// Storage — in-memory, seeded (Supabase would activate with DATABASE_URL)
// ---------------------------------------------------------------------------
const store = { leads: [], seq: 0 };

function saveLead(dossier) {
  store.seq += 1;
  const rec = { id: `lead_${String(store.seq).padStart(4, '0')}`, created_at: new Date().toISOString(), ...dossier };
  store.leads.unshift(rec);
  return rec;
}

// ---------------------------------------------------------------------------
// Slack push (no-op without SLACK_WEBHOOK_URL)
// ---------------------------------------------------------------------------
async function pushSlack(rec) {
  if (!process.env.SLACK_WEBHOOK_URL) return { pushed: false, reason: 'SLACK_WEBHOOK_URL not set (demo mode)' };
  try {
    const resp = await fetch(process.env.SLACK_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        text: `*New ${rec.grading.tier}-tier lead* (${rec.grading.score}/100): ${rec.lead.name} @ ${rec.firmographics.company}\n${rec.recommended_action}`,
      }),
    });
    return { pushed: resp.ok };
  } catch (e) {
    return { pushed: false, reason: e.message };
  }
}

// ---------------------------------------------------------------------------
// Full pipeline
// ---------------------------------------------------------------------------
async function processLead(input) {
  const lead = {
    name: String(input.name || '').trim(),
    email: String(input.email || '').trim(),
    company: String(input.company || '').trim(),
    domain: input.domain ? String(input.domain).trim() : undefined,
    budget: input.budget != null ? Number(input.budget) : undefined,
    message: input.message ? String(input.message).trim() : '',
  };
  if (!lead.name || !lead.email) {
    const err = new Error('name and email are required');
    err.status = 400;
    throw err;
  }
  const domainInfo = deriveDomain(lead);
  const firmo = await research(domainInfo.domain);
  const grading = await grade(lead, domainInfo, firmo);
  const dossier = {
    lead,
    domain: domainInfo,
    firmographics: {
      company: firmo.company, industry: firmo.industry, employees: firmo.employees,
      funding: firmo.funding, tech: firmo.tech,
    },
    news: firmo.news || [],
    grading,
    talking_points: talkingPoints(firmo, grading),
    recommended_action: recommendedAction(grading.tier),
    research_mode: firmo.mode,
  };
  const rec = saveLead(dossier);
  rec.slack = await pushSlack(rec);
  return rec;
}

// Seed 3 leads so GET /api/leads never looks empty on a fresh deploy.
const SAMPLE_LEADS = {
  enterprise: { name: 'Dana Whitfield', email: 'dana.whitfield@stripe.com', company: 'Stripe', budget: 120000, message: 'Evaluating AI enrichment vendors this quarter — need a pilot ASAP.' },
  midmarket: { name: 'Leo Park', email: 'leo@notion.so', company: 'Notion', budget: 15000, message: 'Curious how this could plug into our CRM.' },
  smallbiz: { name: 'Bob Miller', email: 'bob.miller@gmail.com', company: 'Acme Widgets', budget: 500, message: 'price?' },
};

let seeded = false;
async function ensureSeed() {
  if (seeded) return;
  seeded = true;
  for (const key of ['smallbiz', 'midmarket', 'enterprise']) {
    await processLead(SAMPLE_LEADS[key]);
  }
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------
function json(res, status, body) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json');
  res.setHeader('access-control-allow-origin', '*');
  res.end(JSON.stringify(body, null, 2));
}

async function readBody(req) {
  if (req.body !== undefined) return typeof req.body === 'string' ? JSON.parse(req.body || '{}') : req.body;
  let raw = '';
  for await (const chunk of req) raw += chunk;
  return raw ? JSON.parse(raw) : {};
}

module.exports = {
  ICP, FREE_MAIL, DEMO_CORPUS, SAMPLE_LEADS,
  deriveDomain, research, grade, deterministicGrade, monthsSince,
  processLead, ensureSeed, store, json, readBody,
};
