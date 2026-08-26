'use strict';
const lib = require('./_lib.js');
module.exports = (req, res) => lib.json(res, 200, {
  status: 'ok',
  service: 'leadflow-enrichment',
  mode: (process.env.TAVILY_API_KEY || process.env.GROQ_API_KEY) ? 'live' : 'demo',
  integrations: {
    tavily_research: Boolean(process.env.TAVILY_API_KEY),
    groq_grading: Boolean(process.env.GROQ_API_KEY),
    slack_alerts: Boolean(process.env.SLACK_WEBHOOK_URL),
    supabase: Boolean(process.env.DATABASE_URL),
  },
  icp: lib.ICP.description,
  time: new Date().toISOString(),
});
