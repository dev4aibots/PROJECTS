'use strict';
const lib = require('./_lib.js');
module.exports = (req, res) => lib.json(res, 200, {
  status: 'ok',
  service: 'durable-support',
  mode: process.env.GROQ_API_KEY ? 'live' : 'demo',
  integrations: {
    groq_drafts: Boolean(process.env.GROQ_API_KEY),
    slack_approvals: Boolean(process.env.SLACK_WEBHOOK_URL),
  },
  kb_articles: lib.KB.length,
  statuses: lib.STATUSES,
  time: new Date().toISOString(),
});
