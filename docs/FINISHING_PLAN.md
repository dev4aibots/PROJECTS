# Portfolio Finishing Plan

Updated: `2026-08-10`

## Mission

Finish each core project locally to a deployment-ready, portfolio-grade standard. The AI agent owns implementation, tests, evaluation fixtures, documentation, and deployment configuration. The owner only supplies credentials, creates cloud resources, executes provider dashboards, deploys, captures screenshots/video, and approves any cost-bearing action.

## Non-negotiable completion gate

A project may move to `BLOCKED — owner deployment only` only when all local gates pass:

1. Typed domain contracts and explicit failure states.
2. Real service/repository boundaries with deterministic offline providers.
3. Primary API flow plus the highest-risk refusal/security flow.
4. Persistence migrations and owner-safe environment template.
5. Backend tests, failure tests, evaluation harness, and saved results.
6. Frontend loading/empty/error/success states and production build.
7. README, decisions, limitations, demo script, audit, proof, and resume.
8. No secrets, fake URLs, fake provider metrics, or unverified claims.

Live providers, hosted persistence, telemetry, and public deployment are separate owner gates and must never be inferred from local tests.

## Ordered execution

| Order | Project | Local definition of done | Owner-only final gate |
|---:|---|---|---|
| 1 | DocuMind | reproducible install; RAG/MCP tests, eval, build, local E2E | Supabase migrations, Gemini/Groq/Langfuse keys, Vercel deploy, live smoke |
| 2 | StateGraph | four-agent state machine, durable checkpoint adapter, approval/reject, idempotent resume, isolated memory, API/UI, evals | Supabase/provider/Langfuse configuration and deploy |
| 3 | ZeroTrust SQL | schema-aware generation, AST allowlist, mandatory limit, read-only execution, attack lab, audit log, evals | hosted Postgres/provider/Langfuse configuration and deploy |
| 4 | DocuExtract | structured invoice extraction, Decimal verification, invalid-document refusal, correction flow, evals | storage/provider/Langfuse configuration and deploy |
| 5 | LLMShield | injection/PII/content checks, redaction/blocking, provider gateway, logs/stats, adversarial evals | provider/Langfuse configuration and deploy |

## Per-project working loop

- Read the project specification and preserve its exact scope.
- Plan contracts before code; record architecture decisions.
- Implement the smallest end-to-end vertical slice.
- Add failure/security behavior before UI polish.
- Verify from cheap checks through runtime smoke and production build.
- Run the adversarial audit; critical/high findings block handoff.
- Update `CHECKLIST.md`, `PROOF.md`, `RESUME.md`, root registry, and this roll-up.
- Commit one coherent project milestone and update the pull request.

## Owner handoff package required for every project

- `.env.example` with descriptions but no secrets
- ordered migrations and exact apply instructions
- Vercel/serverless configuration
- `scripts/live_smoke.py` or equivalent
- deployment checklist with health, happy-path, refusal/security, persistence, and telemetry checks
- screenshot and 90–120 second demo capture plan

## Truthful repository completion

The repository is locally complete only when every core project is either `COMPLETE` or `BLOCKED — owner deployment only`, with local proof recorded. It is publicly complete only after the owner executes every cloud gate and the resulting URLs are smoke-tested and documented.
