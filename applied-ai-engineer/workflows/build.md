# Build workflow

1. Inspect the target repo, existing tests, actual constraints and dirty files. Summarize what exists vs planned. Run safe baseline tests only after reviewing their commands.
2. Use templates/PROJECT_BRIEF.md. Ask at most five blocking questions first. If answers are unavailable, record reversible assumptions; do not assume permission for external writes.
3. Research only decisions that affect the design: SDK contract, supported transport, auth, retention, price or service limits. Use workflows/research.md and pinned sources.
4. Produce templates/ARCHITECTURE.md, acceptance cases, security boundaries and a smallest vertical slice. Decide deterministic workflow vs agent using measurable requirements.
5. Design failure and evaluation cases **before** implementation. Declare source snapshot files and verification gates. Task scope is not proven complete merely because it lists files.
6. Implement one end-to-end slice. Keep mocks separate from live adapters. Use migrations with forward/backward compatibility and a data recovery plan. No unrelated refactors.
7. Run unit + real dependency integration + relevant E2E/evaluation. Verify negative tenant tests, retries, duplicate actions, provider outages and output validation. Record actual output and environment.
8. Switch to workflows/review.md on the actual diff. Fix critical/high issues; rerun affected suites and regressions. At most two repair rounds before a new plan.
9. Produce deployment/rollback/restore instructions, evidence, known limitations and HANDOFF. Human decides release. Maintain a risk register for upcoming scale, model and provider changes.

Deliverable size should match the task: a one-line bug needs concise evidence, not a giant architecture report. Any N/A gate needs explicit scope rationale and reviewer acceptance; never N/A authorization for an exposed multi-tenant API.
