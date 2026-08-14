# <Project Name> — Live Checklist

> This is live state, not an aspirational feature list. Update it in the same session as the work and proof it records.

Legend: `[ ]` ready · `[~]` partial/in progress · `[x]` verified · `[!]` blocked · `[-]` approved out of scope

## Phase 0 — Discovery and baseline

- [ ] `P0-T1` Verify project goal and acceptance scenarios against repository evidence
- [ ] `P0-T2` Map architecture, entry points, persistence, external dependencies, and deploy target
- [ ] `P0-T3` Run and record baseline checks in `PROOF.md`
- [ ] `P0-T4` Classify TODO/mock/placeholder paths that affect shipped scope
- [ ] `P0-T5` Resolve high-risk unknowns or record explicit assumptions

## Phase 1 — Core outcome

Break the primary happy path into end-to-end vertical slices, not isolated layers.

- [ ] `P1-T1` `<first observable outcome>`
  - Acceptance: `<specific behavior>`
  - Verify: `<command/procedure>`
- [ ] `P1-T2` `<next outcome>`
  - Acceptance: `<specific behavior>`
  - Verify: `<command/procedure>`

## Phase 2 — Reliability and safety

- [ ] `P2-T1` Validate hostile/invalid input relevant to this project
- [ ] `P2-T2` Handle external dependency failure with a safe user-visible result
- [ ] `P2-T3` Verify retries/idempotency/resume behavior where side effects exist
- [ ] `P2-T4` Verify secrets, authorization, data isolation, and logging boundaries as applicable
- [ ] `P2-T5` Add loading/error/empty or CLI/API error states as applicable

## Phase 3 — Tests and proof

- [ ] `P3-T1` Unit tests for critical pure/domain logic
- [ ] `P3-T2` Integration or contract tests for boundaries
- [ ] `P3-T3` End-to-end happy path and meaningful failure path
- [ ] `P3-T4` Project-appropriate evaluation/benchmark/accessibility/security evidence
- [ ] `P3-T5` Save reproducible results and limitations in `PROOF.md`

## Phase 4 — Delivery and portfolio

- [ ] `P4-T1` Production build/package and clean setup verification
- [ ] `P4-T2` Deployment and post-deploy smoke, if in scope
- [ ] `P4-T3` README architecture, quickstart, claims, and limitations synchronized
- [ ] `P4-T4` Real screenshot/demo capture plan and script
- [ ] `P4-T5` Decisions/tradeoffs documented without invented rationale

## Phase 5 — Adversarial audit

- [ ] `P5-T1` Run `docs/agents/AUDIT.md` and record findings
- [ ] `P5-T2` Fix all critical/high findings
- [ ] `P5-T3` Re-run full practical verification
- [ ] `P5-T4` Mark terminal status and update root registry/resume

## Blocked items

| Task | Exact blocker/proof | Owner/external action | Resolution check | Safe alternative work |
|---|---|---|---|---|
| — | — | — | — | — |

## Completion summary

- Scope completion: `<n/m>`
- Critical/high findings open: `<n>`
- Strongest proof: `<link/result>`
- External verification remaining: `<none or exact item>`
- Terminal status: `<not terminal/COMPLETE/BLOCKED/OUT_OF_SCOPE>`
