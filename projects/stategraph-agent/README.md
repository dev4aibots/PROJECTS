# StateGraph — Human-governed multi-agent research

A four-agent workflow that checkpoints state, pauses risky output, resumes after a human decision, and keeps long-term context isolated by user.

## Architecture

`START → Research → Analyst → Reviewer → [approval?] → Writer → END`

The supervisor only routes typed state. Research uses model knowledge only—there is **no live web search**. `thread_id == task_run_id`; the deployment migration stores versioned JSON checkpoints.

## Run

```bash
pip install -r requirements-dev.txt
PYTHONPATH=backend uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

## Verify

```bash
PYTHONPATH=backend pytest -q backend/tests
cd frontend && npm run typecheck && npm run build
```

Verified local boundaries include approval interrupt, rejection without Writer, duplicate-decision no-op, completed resume no-op, validation, missing resources, and cross-user memory isolation. Local mode is process-memory/deterministic; hosted Postgres, providers, telemetry, and deployment remain owner credential gates.

See `PLAN.md`, `DECISIONS.md`, `docs/state-machine.md`, `AUDIT.md`, and `DEMO_SCRIPT.md`.
