/**
 * DuraSupport — durable pause/resume support workflow engine.
 *
 * Core idea: a *durable state machine*, not a long-running process. A workflow
 * runs step-by-step; when it hits a human-approval gate it persists its full
 * state and RETURNS (zero compute while paused). A later webhook (/api/approve)
 * loads the state and resumes exactly where it left off.
 *
 * Zero dependencies. Real integrations (Groq drafts, Slack interactive
 * messages) activate only when env vars are set; otherwise deterministic demo
 * mode keeps the live URL fully functional with no keys.
 */
'use strict';

const crypto = require('crypto');

// ---------------------------------------------------------------------------
// Seeded knowledge base (retrieval corpus)
// ---------------------------------------------------------------------------
const KB = [
  {
    id: 'kb1', title: 'API documentation & getting started',
    body: 'Full API docs live at docs.example.com/api. Authentication uses bearer tokens created on the dashboard under Settings → API Keys. Quickstart guides cover Node, Python and cURL examples.',
  },
  {
    id: 'kb2', title: 'Refund policy',
    body: 'Refunds are available within 30 days of a charge. Duplicate or double charges are refunded in full once verified. Refunds are returned to the original payment method within 5–10 business days.',
  },
  {
    id: 'kb3', title: 'Subscription cancellation',
    body: 'You can cancel a subscription anytime from Billing → Plan → Cancel. Cancellation takes effect at the end of the current billing period; no further charges occur afterwards.',
  },
  {
    id: 'kb4', title: 'Billing & invoices',
    body: 'Invoices are emailed monthly and available under Billing → Invoices. You can update your payment card, billing address and tax/VAT ID from the same page.',
  },
  {
    id: 'kb5', title: 'Rate limits & quotas',
    body: 'Free plan allows 60 requests/min; Pro allows 600 requests/min. HTTP 429 responses include a Retry-After header. Contact sales for custom enterprise quotas.',
  },
  {
    id: 'kb6', title: 'Password reset & account access',
    body: 'Use the Forgot Password link on the sign-in page to receive a reset email. Reset links expire after 60 minutes. If you no longer control your email, contact support for identity verification.',
  },
];

const STATUSES = [
  'RECEIVED', 'RETRIEVING', 'DRAFTING', 'CLASSIFYING',
  'AWAITING_APPROVAL', 'SENDING', 'RESOLVED', 'ESCALATED_HUMAN',
];

// ---------------------------------------------------------------------------
// Retrieval: token-overlap similarity (deterministic, dependency-free)
// ---------------------------------------------------------------------------
const STOP = new Set(['the', 'a', 'an', 'i', 'my', 'is', 'are', 'to', 'of', 'and', 'or', 'in', 'on', 'for', 'it', 'this', 'that', 'was', 'be', 'me', 'you', 'we', 'do', 'can', 'have', 'has', 'with']);

function tokenize(text) {
  return String(text || '').toLowerCase().replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/).filter(t => t.length > 1 && !STOP.has(t));
}

function similarity(aTokens, bTokens) {
  if (!aTokens.length || !bTokens.length) return 0;
  const b = new Set(bTokens);
  let overlap = 0;
  for (const t of new Set(aTokens)) if (b.has(t)) overlap++;
  // normalized like cosine on binary vectors
  return overlap / Math.sqrt(new Set(aTokens).size * b.size);
}

function retrieve(query, k = 3) {
  const q = tokenize(query);
  return KB
    .map(a => ({ ...a, score: +similarity(q, tokenize(a.title + ' ' + a.body)).toFixed(4) }))
    .sort((x, y) => y.score - x.score)
    .slice(0, k);
}

// ---------------------------------------------------------------------------
// Classification: is this ticket "sensitive" (needs a human approval gate)?
// ---------------------------------------------------------------------------
const SENSITIVE_PATTERNS = [
  { intent: 'refund', re: /\b(refund|charge ?back|double[- ]charg|over ?charg|money back)\b/i },
  { intent: 'cancellation', re: /\b(cancel|terminat|close (my )?account|unsubscrib)\b/i },
  { intent: 'billing_dispute', re: /\b(dispute|incorrect (charge|invoice)|billing (error|issue|problem))\b/i },
];

function classify(text) {
  for (const p of SENSITIVE_PATTERNS) {
    if (p.re.test(text)) return { sensitive: true, intent: p.intent, method: 'pattern' };
  }
  return { sensitive: false, intent: 'general_support', method: 'pattern' };
}

// ---------------------------------------------------------------------------
// Draft composer — Groq (Llama 3) when GROQ_API_KEY is set, else KB template
// ---------------------------------------------------------------------------
async function draftReply(ticket, articles) {
  const sysMsg = 'You are a concise, friendly support agent. Use ONLY the provided KB context. Sign off as "DuraSupport Team".';
  const userMsg = `Ticket from ${ticket.customer} <${ticket.email}>\nSubject: ${ticket.subject}\n\n${ticket.body}\n\nKB context:\n${articles.map(a => `- ${a.title}: ${a.body}`).join('\n')}`;

  // 1. Groq
  if (process.env.GROQ_API_KEY) {
    try {
      const r = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: { authorization: `Bearer ${process.env.GROQ_API_KEY}`, 'content-type': 'application/json' },
        body: JSON.stringify({
          model: 'llama-3.3-70b-versatile', temperature: 0.3,
          messages: [{ role: 'system', content: sysMsg }, { role: 'user', content: userMsg }],
        }),
      });
      if (r.ok) {
        const data = await r.json();
        const text = data.choices?.[0]?.message?.content;
        if (text) return { reply: text.trim(), engine: 'groq/llama-3.3-70b' };
      }
    } catch (_) { /* failover */ }
  }

  // 2. NVIDIA NIM
  if (process.env.NVIDIA_API_KEY) {
    try {
      const r = await fetch('https://integrate.api.nvidia.com/v1/chat/completions', {
        method: 'POST',
        headers: { authorization: `Bearer ${process.env.NVIDIA_API_KEY}`, 'content-type': 'application/json' },
        body: JSON.stringify({
          model: 'meta/llama-3.1-70b-instruct', temperature: 0.3,
          messages: [{ role: 'system', content: sysMsg }, { role: 'user', content: userMsg }],
        }),
      });
      if (r.ok) {
        const data = await r.json();
        const text = data.choices?.[0]?.message?.content;
        if (text) return { reply: text.trim(), engine: 'nvidia/llama-3.1-70b' };
      }
    } catch (_) { /* failover */ }
  }

  // 3. Mistral AI
  if (process.env.MISTRAL_API_KEY) {
    try {
      const r = await fetch('https://api.mistral.ai/v1/chat/completions', {
        method: 'POST',
        headers: { authorization: `Bearer ${process.env.MISTRAL_API_KEY}`, 'content-type': 'application/json' },
        body: JSON.stringify({
          model: 'mistral-small-latest', temperature: 0.3,
          messages: [{ role: 'system', content: sysMsg }, { role: 'user', content: userMsg }],
        }),
      });
      if (r.ok) {
        const data = await r.json();
        const text = data.choices?.[0]?.message?.content;
        if (text) return { reply: text.trim(), engine: 'mistral-small' };
      }
    } catch (_) { /* failover */ }
  }
  // Deterministic template composer
  const top = articles[0];
  const reply = [
    `Hi ${ticket.customer},`,
    '',
    `Thanks for reaching out about "${ticket.subject}".`,
    '',
    top ? `${top.body}` : 'Our team is looking into your request.',
    '',
    articles.length > 1 ? `You may also find this helpful: ${articles.slice(1).map(a => a.title).join(' · ')}.` : '',
    'If anything is still unclear, just reply to this email and we will take another look.',
    '',
    'Best regards,',
    'DuraSupport Team',
  ].filter(l => l !== null).join('\n').replace(/\n{3,}/g, '\n\n');
  return { reply, engine: 'template' };
}

// ---------------------------------------------------------------------------
// Slack notification (approval request) — real webhook if configured
// ---------------------------------------------------------------------------
async function notifySlack(ticket) {
  const payload = {
    text: `🔔 Approval needed — ticket ${ticket.id} (${ticket.classification.intent}) from ${ticket.customer}: "${ticket.subject}". Approve / Edit / Reject via POST /api/approve.`,
  };
  if (process.env.SLACK_WEBHOOK_URL) {
    try {
      await fetch(process.env.SLACK_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(payload),
      });
      return { sent: true, channel: 'slack-webhook' };
    } catch (_) { /* fall through */ }
  }
  return { sent: false, channel: 'demo (set SLACK_WEBHOOK_URL to enable)', preview: payload.text };
}

// ---------------------------------------------------------------------------
// Store — in-memory per serverless instance; DATABASE_URL would swap this
// for a real Postgres store in production (documented in README).
// ---------------------------------------------------------------------------
const store = { tickets: new Map(), seq: 0, seeded: false };

function nextId() {
  store.seq += 1;
  return `tkt_${String(store.seq).padStart(4, '0')}`;
}

function now() { return new Date().toISOString(); }

function addStep(ticket, step, status, detail) {
  ticket.timeline.push({ step, status, at: now(), detail });
}

// ---------------------------------------------------------------------------
// The durable workflow: run until done or a pause point
// ---------------------------------------------------------------------------
async function createTicket({ customer, email, subject, body }) {
  const ticket = {
    id: nextId(),
    customer, email, subject, body,
    status: 'RECEIVED',
    created_at: now(),
    updated_at: now(),
    timeline: [],
    kb_context: [],
    classification: null,
    draft: null,
    sent_reply: null,
  };
  addStep(ticket, 'RECEIVE', 'RECEIVED', `Ticket received from ${email}`);

  // step RETRIEVE
  ticket.status = 'RETRIEVING';
  const articles = retrieve(`${subject} ${body}`);
  ticket.kb_context = articles;
  addStep(ticket, 'RETRIEVE', 'RETRIEVING', `Top KB: ${articles.map(a => `${a.id} (${a.score})`).join(', ')}`);

  // step DRAFT
  ticket.status = 'DRAFTING';
  const { reply, engine } = await draftReply(ticket, articles);
  ticket.draft = { reply, engine, drafted_at: now() };
  addStep(ticket, 'DRAFT', 'DRAFTING', `Reply drafted via ${engine} (${reply.length} chars)`);

  // step CLASSIFY
  ticket.status = 'CLASSIFYING';
  const cls = classify(`${subject} ${body}`);
  ticket.classification = cls;
  addStep(ticket, 'CLASSIFY', 'CLASSIFYING', `intent=${cls.intent} sensitive=${cls.sensitive} (${cls.method})`);

  if (cls.sensitive) {
    // PAUSE — persist state and return. Zero compute while awaiting approval.
    ticket.status = 'AWAITING_APPROVAL';
    const slack = await notifySlack(ticket);
    addStep(ticket, 'PAUSE', 'AWAITING_APPROVAL',
      `Sensitive intent "${cls.intent}" — human approval required. Slack notify: ${slack.sent ? 'sent' : slack.channel}`);
  } else {
    // auto-send
    sendReply(ticket, ticket.draft.reply, 'auto');
  }

  ticket.updated_at = now();
  store.tickets.set(ticket.id, ticket);
  return ticket;
}

function sendReply(ticket, reply, by) {
  ticket.status = 'SENDING';
  addStep(ticket, 'SEND', 'SENDING', `Emailing reply to ${ticket.email} (${by})`);
  ticket.sent_reply = { reply, sent_at: now(), by };
  ticket.status = 'RESOLVED';
  addStep(ticket, 'RESOLVE', 'RESOLVED', 'Reply delivered (simulated email). Ticket closed.');
  ticket.updated_at = now();
}

// Resume a paused workflow — the durable-execution core.
function approve(ticketId, action, editedReply) {
  const ticket = store.tickets.get(ticketId);
  if (!ticket) { const e = new Error(`ticket ${ticketId} not found`); e.status = 404; throw e; }
  if (ticket.status !== 'AWAITING_APPROVAL') {
    // Idempotency guard: a double-click must not send twice.
    const e = new Error(`ticket ${ticketId} is ${ticket.status}, not AWAITING_APPROVAL — cannot resume`);
    e.status = 409; throw e;
  }
  addStep(ticket, 'RESUME', 'AWAITING_APPROVAL', `Workflow resumed by manager action: ${action}`);

  if (action === 'approve') {
    sendReply(ticket, ticket.draft.reply, 'manager-approved');
  } else if (action === 'edit') {
    if (!editedReply || !editedReply.trim()) {
      const e = new Error('edit action requires edited_reply'); e.status = 400; throw e;
    }
    ticket.draft = { ...ticket.draft, reply: editedReply.trim(), edited_at: now() };
    addStep(ticket, 'EDIT', 'AWAITING_APPROVAL', 'Manager edited the draft before sending');
    sendReply(ticket, editedReply.trim(), 'manager-edited');
  } else if (action === 'reject') {
    ticket.status = 'ESCALATED_HUMAN';
    addStep(ticket, 'ESCALATE', 'ESCALATED_HUMAN', 'Manager rejected AI draft — escalated to human agent queue.');
    ticket.updated_at = now();
  } else {
    const e = new Error(`unknown action "${action}" — use approve | edit | reject`); e.status = 400; throw e;
  }
  return ticket;
}

// ---------------------------------------------------------------------------
// Seed demo tickets so the dashboard is never empty
// ---------------------------------------------------------------------------
async function ensureSeed() {
  if (store.seeded) return;
  store.seeded = true;
  await createTicket({
    customer: 'Ada Lovelace', email: 'ada@example.com',
    subject: 'Where are the API docs?',
    body: 'Hi, I just signed up and cannot find the API documentation or how to create an auth token.',
  });
  await createTicket({
    customer: 'Grace Hopper', email: 'grace@example.com',
    subject: 'Double charged this month',
    body: 'I was double charged on my last invoice and I want a refund for the duplicate charge.',
  });
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------
function json(res, status, obj) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json');
  res.setHeader('access-control-allow-origin', '*');
  res.end(JSON.stringify(obj, null, 2));
}

async function readBody(req) {
  let raw = '';
  for await (const chunk of req) raw += chunk;
  return raw ? JSON.parse(raw) : {};
}

module.exports = {
  KB, STATUSES,
  tokenize, similarity, retrieve, classify, draftReply,
  createTicket, approve, ensureSeed, store,
  json, readBody,
};
