# DEPLOYMENT.md — Vercel Runbook ($0 budget, all 7 projects)

Each project is a standalone Vercel app. Deploy each from its own directory:

```bash
cd projects/<dir>
npx vercel           # preview
npx vercel --prod    # production
```

Or via the Vercel dashboard: import the GitHub repo 7 times, each time setting **Root Directory** to one `projects/<dir>`.

## Environment variables (ALL optional — demo mode works with none)

| Project | Var | Provider (free tier) | Enables |
|---|---|---|---|
| P1 FinAudit | `GEMINI_API_KEY` | Google AI Studio | real Vision extraction |
| P1, P2, P3, P6 | `SLACK_WEBHOOK_URL` | Slack Incoming Webhooks | real Slack alerts |
| P1, P2 | `SUPABASE_URL`, `SUPABASE_KEY` | supabase.com | persistent storage |
| P2, P4, P5 | `GROQ_API_KEY` | console.groq.com | real Llama 3 inference |
| P2 | `TAVILY_API_KEY` | tavily.com | real web search enrichment |
| P4 | `DATABASE_URL` | neon.tech (read-only role!) | real Postgres warehouse |
| P6 | `KV_REST_API_URL`, `KV_REST_API_TOKEN` | Upstash Redis | shared verdict cache |
| P7 | `MCP_API_KEYS` | — (comma-separated `key:scope` pairs) | override demo keys |
| P7 | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | langfuse.com | trace export |

## Per-project notes

- **Python projects (P1, P4, P5)**: Vercel auto-detects `api/index.py` with the Python runtime; `requirements.txt` at project root. Swagger lives at `/docs` in local dev; on Vercel it's `/api/docs` — a rewrite in `vercel.json` maps `/docs` too.
- **P5 cron**: `vercel.json` contains `{"crons":[{"path":"/api/cron","schedule":"0 */6 * * *"}]}` — Hobby plan allows daily+ schedules; adjust if Vercel rejects the frequency.
- **Node projects (P2, P3, P6, P7)**: zero npm dependencies; functions in `api/*.js` (CommonJS, `module.exports = handler`). No build step.
- **Read-only DB for P4**: if using Neon, create a role with `GRANT SELECT ONLY` and use that connection string — defense in depth beneath the AST guard.
- **Cold starts & demo data**: in-memory stores reseed demo data on cold start so dashboards are never empty. With DB env vars set, persistence is real.

## Local development

```bash
# Python projects
cd projects/01-finaudit-idp && pip install -r requirements.txt && uvicorn api.index:app --reload --port 8001

# Node projects (no deps needed)
cd projects/02-leadflow-enrichment && node dev-server.js   # serves public/ + api/ on :3000
```

## Post-deploy checklist (per project)
1. `curl https://<app>.vercel.app/api/health` → `{"status":"ok",...}`.
2. Open the dashboard, click every "Try Sample" button.
3. Record the live URL in `docs/projects/<slug>/RESUME.md`.
