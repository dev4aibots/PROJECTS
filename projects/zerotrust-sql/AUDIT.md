# Adversarial Audit

Run: 2026-08-12. Scope: local code, API, tests, evaluation, frontend build, docs, and deployment configuration.

## Findings closed

- SQL is parsed structurally; multi-statement, non-SELECT, unknown tables/columns, unsafe functions, and excessive limits have direct tests.
- The decoy table is absent from schema context and denied at validator and executor layers.
- Generator/database failures return controlled errors without internal host leakage; audit remains attempted.
- Workbench controls call real API routes and render loading, empty, error, allowed, blocked, limit, result, and audit states.
- Claims distinguish local deterministic proof from unverified cloud behavior.

## Open findings

No critical or high local finding remains. Owner-gated items: apply/verify hosted migration and grants, seed hosted fictional data, configure providers and Langfuse, deploy, run live smoke, and capture visual evidence.
