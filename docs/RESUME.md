# Repository resume — start here

Updated: 2026-08-14
Branch: `genspark_ai_developer`
PR target: https://github.com/dev4aibots/PROJECTS/pull/1 (verify after push)

## Owner goal

Keep Dev4AIbots removed and make five focused AI proof-of-work projects deployment-ready so launch later requires only owner cloud resources, migrations, credentials, deployment and live evidence capture.

## Completed in this continuation

- Restored the 32.tar.gz five-project handoff without importing archive Git metadata and kept the explicitly removed Dev4AIbots project absent.
- Closed StateGraph credential-free gates: held-out routing/citation evaluation, refresh/reconnect and memory UX, four browser E2E scenarios, privacy-safe request correlation, deployment preflight and authenticated live-smoke script.
- Fixed the terminal-state race so a stale pending approval cannot resume a canceled graph in either repository implementation.
- Corrected the Supabase magic-link callback to the deployed frontend root.
- Re-ran every project backend, evaluation, frontend typecheck/build, and production dependency audit gate.
- Finished ZeroTrust SQL credential-free hardening: scope-aware lineage, scoped authentication, privacy-safe durable audit, distributed rate limits, capability-role preflight, fail-closed startup, authenticated smoke coverage, and four Chromium E2E scenarios.
- Squashed the portfolio branch to one commit and force-updated PR #1 after syncing with `origin/main`.

## Last observed verification

| Project | Backend/eval | Frontend |
|---|---|---|
| DocuMind | 135 tests; authored deterministic metrics all 100% (15 cases) | 3 tests; typecheck/build; 0 production vulnerabilities |
| StateGraph | 34 passed; 1 credential-gated Postgres test skipped; held-out metrics 1.0/1.0 | typecheck/build; 4 Chromium E2E; 0 production vulnerabilities |
| ZeroTrust SQL | 78 tests; 13/13 deterministic eval | typecheck/build; 4 Chromium E2E; 0 production vulnerabilities |
| DocuExtract | 21 tests; 5/5 fixture verdicts | typecheck/build; 0 production vulnerabilities |
| LLMShield | 17 tests; 40-case bounded authored eval | typecheck/build; 0 production vulnerabilities |

These are local regression results, not hosted or model-quality proof.

## Resume now

1. Read `AGENTS.md`, `AGENT_RESUME_GUIDE.md`, `PROJECTS.md` and `IMPLEMENTATION_MASTER_PLAN.md`.
2. Active project: `llmshield`.
3. Implement scoped authentication and owner-safe access to private telemetry.
4. Replace process-local public-demo abuse limits with a distributed limiter selected in live mode.
5. Strengthen the held-out adversarial evaluation and add browser E2E for primary allow/block/redact/error states.
6. Run LLMShield tests/eval/frontend gates, update proof, then move to DocuMind identity/RLS.
7. Keep StateGraph, DocuExtract, and ZeroTrust terminal until the owner supplies disposable integration resources for their documented live gates.

## Known blockers and truthful gaps

- No owner cloud credentials or public URLs are configured.
- StateGraph is credential-free source complete, but PostgresSaver, role assumption, RLS and real Supabase JWTs have not been exercised against a real database.
- DocuExtract source includes authenticated ownership and Postgres/private-storage adapters, but needs disposable live Supabase/Gemini proof.
- ZeroTrust source includes lineage, authentication, distributed limits, durable audit, and E2E, but needs disposable live Postgres/provider proof.
- LLMShield needs scoped authentication, distributed limits, stronger held-out evaluation, and browser E2E.
- DocuMind needs production identity/RLS and hosted cross-tenant/RAG proof.
- Browser E2E is now verified for StateGraph only; hosted live smokes, portfolio media and current CI runs remain release gates.
- Owner action: copy `docs/templates/portfolio-ci.yml` to `.github/workflows/portfolio-ci.yml` with workflow-write permission.

## Exit protocol

Run `git status --short --branch`; leave no uncommitted source/docs; fetch/rebase without discarding owner changes; push `genspark_ai_developer`; verify/update PR; record exact next task and evidence here and in active project files.
