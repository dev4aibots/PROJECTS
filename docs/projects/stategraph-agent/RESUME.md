# StateGraph — Multi-Agent Research Orchestrator — Session Resume

Updated: `2026-08-12`
Project folder: `projects/stategraph-agent`
Branch/commit: `genspark_ai_developer`
Working tree: `clean for this project`

## Exact current position

- Milestone: `Phase 6 — delivery complete locally`
- Checklist item: `P6-T4 — owner-managed live deployment`
- State: `BLOCKED — owner deployment only`
- All local gates (tests, failure paths, typecheck, production build, audit, docs) are verified; see `PROOF.md`.

## Resume commands

```bash
cd /home/user/webapp/projects/stategraph-agent
pip install -r requirements-dev.txt
PYTHONPATH=backend python -m pytest -q backend/tests
cd frontend && npm install && npm run typecheck && npm run build
```

## Verified prior work

- Deterministic four-agent supervisor with checkpoints, approval interrupt, idempotent resume/decisions, per-user memory isolation, and owner-only prune.
- Six-scenario backend suite passes; frontend typecheck and production build pass (re-verified 2026-08-12 in a fresh sandbox).
- Migrations (`migrations/001_stategraph.sql`), README, decisions, demo script, audit, and `.env.example` delivered.

## Environment and blockers

- Local: fully reproducible, no secrets needed (deterministic mode).
- Only remaining gate: owner-managed Supabase migrations, Gemini/Groq keys, Langfuse, and Vercel deployment plus live smoke — `P6-T4`.
