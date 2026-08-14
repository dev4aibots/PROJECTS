# Owner Deployment Runbook

The codebase must remain usable without secrets. This runbook lists the only work that cannot be completed safely by an offline coding agent: account creation, credential entry, hosted migrations, deployment approval, and visual capture.

## Security rules

- Put secrets only in provider/Vercel environment settings; never commit `.env`.
- Use server-side service keys only in backend projects. Browser code receives public URLs/anon keys only when documented.
- Use separate demo resources and least-privilege/read-only database roles where specified.
- Rotate any credential accidentally printed or committed.
- Confirm free-tier limits before enabling live evaluation.

## Standard deployment sequence

1. Open the project README and `.env.example`.
2. Create the named Supabase/database/storage resources.
3. Apply migrations in numeric order; save dashboard evidence.
4. Create Gemini/Groq/Langfuse credentials required by that project.
5. Run the project's live evaluation once and record the real model/provider and date.
6. Deploy backend first, set allowed frontend origins, and verify `/api/health`.
7. Deploy frontend with its public API base URL.
8. Run `scripts/live_smoke.py --base-url <backend-url>` when present.
9. Test happy path, refusal/security path, persistence after refresh, and telemetry.
10. Add only observed URLs/metrics to README and proof docs; capture screenshots and demo video.

## Project gates

### DocuMind

- Create Supabase project; enable pgvector/storage; apply `migrations/001` through `005`.
- Set backend Supabase, Gemini/Groq, Langfuse, and CORS variables from `.env.example`.
- Deploy backend and frontend as separate Vercel roots.
- Verify upload → process → grounded citation; out-of-corpus refusal; all four MCP tools; cross-session denial.

### StateGraph

- Apply all migrations; configure the Postgres checkpoint connection.
- Set provider and optional Langfuse variables.
- Verify risky task pauses, approval resumes exactly once, rejection never runs writer, and User B cannot see User A memory.

### ZeroTrust SQL

- Create a seeded demo database and a dedicated read-only execution role.
- Apply app/audit migrations; configure provider and optional Langfuse variables.
- Verify normal analytics, `DROP` rejection, piggyback rejection, unknown-column rejection, and mandatory row limit.

### DocuExtract

- Create extraction metadata/storage resources and apply migrations.
- Configure multimodal provider and optional Langfuse variables.
- Verify a valid invoice, intentionally broken total, non-invoice rejection, and owner correction workflow.

### LLMShield

- Apply request-log migrations and configure downstream provider plus optional Langfuse.
- Verify allowed request, injection block, PII redaction, provider outage, and aggregate stats.
- Confirm logs do not retain unredacted sensitive content.

## Evidence to return to the repository agent

For each project provide: backend URL, frontend URL, UTC deployment time, migration confirmation, live smoke output, live evaluation output, provider/model names, Langfuse trace URL or explicit omission, and screenshot/video links. Never send secret values.
