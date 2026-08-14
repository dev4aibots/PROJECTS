# LLMShield

A drop-in FastAPI security and observability gateway for LLM calls. It independently validates input, redacts heuristic PII, blocks known prompt-injection patterns, routes Groq to Gemini fallback, validates output, emits fail-open Langfuse traces, and stores privacy-safe request metadata.

> **Security boundary:** heuristic guards are defense in depth, not a guarantee. See [threat model](docs/threat-model.md) and [limitations](docs/limitations.md).

## Verified local evidence

- **17/17 backend tests**: blocking, provider short-circuit, Luhn/PII, fallback, both-providers-down, empty/oversized output, malformed requests, fail-open telemetry, logs, and stats.
- **40-case frozen corpus**: 15 clean, 15 known-pattern injection, 10 PII; both guards observed 1.00 precision, 1.00 recall, and 0.00 false-positive rate on this deliberately bounded fixture.
- **Production frontend gate**: TypeScript check and Next.js build pass.
- No live provider, Postgres, Langfuse, or deployment success is claimed.

## Pipeline

```text
POST /api/gateway
  → length + injection + PII input checks
  → BLOCK short-circuit (no provider call)
  → Groq primary → Gemini fallback on provider failure
  → non-empty + size + PII output checks
  → hash-only request log + safe response envelope + trace
```

Code boundaries are explicit: `guards/`, `providers.py`, `service.py`, `repository.py`, `observability.py`, `models.py`, and thin FastAPI routes in `main.py`.

## Credential-free quickstart

```bash
cd projects/llmshield
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=backend pytest -q backend/tests
python evals/run.py
PYTHONPATH=backend uvicorn app.main:app --port 8000
```

In another shell:

```bash
cd projects/llmshield/frontend
npm ci
npm run typecheck && npm run build
npm run dev
```

Open `http://localhost:3000/app`. The default `PROVIDER_MODE=deterministic` is explicit and makes the full application path reproducible without secrets.

## API

| Route | Purpose |
|---|---|
| `POST /api/gateway` | guarded completion envelope |
| `GET /api/logs?limit=50` | recent hash-only request metadata |
| `GET /api/stats` | totals, blocked/warn/fallback percentages, p50/p95 latency |
| `GET /api/health` | configured mode, providers, persistence, tracing |
| `GET /api/attacks` | predefined demo cases |

Provider outage returns a structured `503`; empty completion returns a structured `502`; oversized output is truncated and marked; malformed input returns FastAPI field-level `422`; tracing failures are logged but never fail the request.

## Owner deployment handoff

1. Copy `.env.example` into provider/Vercel settings.
2. Create Postgres/Supabase, apply `migrations/001_llmshield.sql`, and set `DATABASE_URL` using a server-only role.
3. Set `PROVIDER_MODE=live`; supply Groq and/or Gemini credentials.
4. Optionally supply Langfuse keys and host.
5. Set production `CORS_ORIGINS` and frontend `NEXT_PUBLIC_API_BASE_URL`.
6. Deploy API and frontend, then run `python scripts/live_smoke.py https://<api-host>`.
7. Verify a fallback event and Langfuse span structure, then capture the screenshots in `DEMO_SCRIPT.md`.

See [evaluation](docs/evaluation.md), [observability](docs/observability.md), [decisions](DECISIONS.md), and [audit](AUDIT.md).
