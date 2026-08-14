# Resume guide for all future coding agents

This is the no-chat-memory handoff. The owner goal is to make all five projects deployment-ready: after local completion, only cloud creation, migrations, credentials, deploy and live proof remain.

## Mandatory start (every session)

```bash
cd /home/user/webapp
pwd
git status --short --branch
git fetch origin main genspark_ai_developer
```

Then read, in order:

1. `AGENTS.md`
2. `docs/RESUME.md`
3. `docs/PROJECTS.md`
4. `docs/IMPLEMENTATION_MASTER_PLAN.md`
5. Active project `BRIEF.md`, `DEPLOYMENT_READY_PLAN.md`, `CHECKLIST.md`, `RESUME.md`, `PROOF.md`
6. Active project code/tests/README and recent commits

Never resurrect `projects/dev4aibots`; the owner explicitly removed it.

## Non-negotiable truth rules

- A configured variable is not an integration. Trace factory selection to a runtime call and test it.
- A migration is not a connected database. Prove the production repository/executor is constructed.
- Deterministic fixtures prove regressions, not live model quality.
- No live URL, CI result, screenshot, trace, metric or deployment may be invented.
- Never mark a phase complete while tests fail or a critical/high audit issue remains.
- Do not ask for credentials until every credential-free contract, adapter, test, migration, script and UI state is complete.

## Current implementation order

1. Finish StateGraph durable Postgres checkpointer, real provider/tool and authenticated ownership.
2. Finish DocuExtract Postgres/storage repository and ownership around the new Gemini adapter.
3. Finish ZeroTrust alias-aware validation, auth/rate limits and Postgres integration tests.
4. Finish LLMShield scoped API keys, distributed limits, calibrated guard corpus and dashboard protection.
5. Finish DocuMind verified identity/RLS, serverless ingestion concurrency and expanded eval.
6. Add shared/per-project CI, E2E, deployment preflight and live-smoke gates.
7. Owner runs cloud launch phase and adds public proof.

One active milestone at a time. Cross-project CI/docs work is allowed only when it supplies the same verified gate without changing product behavior.

## Implementation loop

1. Reproduce current behavior and inspect tests.
2. Select the first unchecked phase task; write exact acceptance criteria into the project checklist if absent.
3. Implement the smallest end-to-end vertical slice (UI → API → service → persistence/provider → output).
4. Test success, invalid input, unauthorized ownership, provider/database outage, retry/idempotency and concurrency as relevant.
5. Run project tests/eval/typecheck/build; inspect diff and scan for secrets/placeholders.
6. Update project `PROOF.md`, `CHECKLIST.md`, `RESUME.md`, then repository `RESUME.md`/`PROJECTS.md` if status changed.
7. Commit with conventional scope, fetch/rebase remote (favor remote owner changes), push and update PR.

## Definition of a complete adapter

- protocol/interface and production implementation;
- explicit config factory and startup validation;
- typed outputs and sanitized errors;
- transient/permanent error classification, timeout and bounded retry where safe;
- contract tests with a fake transport/client;
- integration test or owner-gated live smoke;
- health/readiness reports mode without exposing secrets;
- docs/env/migration match actual code.

## Phase proof template

Record in `PROOF.md`:

```text
### YYYY-MM-DD — <phase/task>
Git SHA: <sha after commit>
Commands: <exact commands>
Observed: <counts/results, no guesses>
Failure paths: <what was exercised>
Artifacts: <relative paths or verified URLs>
Remaining: <next task/blocker>
```

## Before requesting owner credentials

Confirm the repository contains:

- complete `.env.example` and preflight validator;
- least-privilege migrations and rollback/repair notes;
- live adapter factory tests;
- seed command using fictional data;
- post-deploy smoke accepting URL/tokens through environment;
- exact Vercel project roots, build commands and CORS origins;
- no secrets in git or browser bundle;
- a short owner launch checklist.

## Final release gate per project

Tests, eval, frontend build/E2E, dependency audit, migration integration, security audit, live provider/database smoke, identity isolation, failure/fallback, p95/cost observation, accessibility, public URL, screenshots and demo must be recorded. Until then use `local prototype`, `integration-ready`, or `deployed demo`—never `production-ready`.
