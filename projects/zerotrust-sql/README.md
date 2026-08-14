# ZeroTrust SQL

Secure natural-language analytics where the model proposes SQL and a deterministic security boundary decides whether it executes.

## Evidence

- 57 backend tests pass.
- Security corpus: 25/25 malicious SQL fixtures blocked; 25/25 safe fixtures allowed.
- Golden end-to-end evaluation: 13/13 cases pass (one is an expected honest refusal).
- Next.js `/` and `/app` routes typecheck and build successfully.
- No live database, provider, telemetry, or deployment success is claimed.

## Architecture

`question → input guard → Groq/Gemini or deterministic draft → SQLGlot AST parse → statement/table/column/function allowlists → AST LIMIT rewrite → read-only sandbox → shaped result → audit`

The seeded local database contains 150 fictional customers, 40 products, 800 orders, and about 2,000 items. A decoy `internal_credentials` table exists but is excluded from schema context, rejected by validation, and denied by the execution layer.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000
# another terminal
cd frontend && npm ci && npm run dev
```

Open `http://localhost:3000/app`. Local mode needs no secrets.

## Verification

```bash
PYTHONPATH=backend python -m pytest -q backend/tests
PYTHONPATH=backend python evals/run.py
cd frontend && npm ci && npm run typecheck && npm run build
```

## API

`POST /api/query`, `GET /api/schema`, `GET /api/attacks`, `GET /api/audit`, `GET /api/audit/{id}`, `GET /api/health`.

Blocked SQL returns the normal response envelope with `security.allowed=false`; it never reaches execution. Provider and database outages use controlled 503 responses and are still audited.

## Deployment

Apply `migrations/001_zerotrust.sql`, seed only fictional demo data, connect the backend with the restricted role, configure variables from `.env.example`, deploy API and frontend, then run `scripts/live_smoke.py`. These owner-managed steps remain unverified.

See `docs/security-model.md`, `docs/evaluation.md`, `docs/limitations.md`, `DECISIONS.md`, `DEMO_SCRIPT.md`, and `AUDIT.md`.
