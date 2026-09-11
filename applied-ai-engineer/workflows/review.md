# Post-build audit and repair protocol

Use this on any existing project, not only tutorial projects. Start read-only. Do not accept the builder's summary as proof.

## Audit passes

1. **Requirements:** trace every promised behavior to code and test; identify missing contracts and hidden assumptions. Is the business problem actually solved?
2. **Architecture/data:** follow one request and one background job. Locate business logic, transaction boundaries, tenancy, caches, vectors and external side effects. Compare ADRs to reality.
3. **Security:** attempt cross-tenant reads/writes, forged object IDs, revoked membership, injected retrieval content, unauthorized tool calls, malicious file/URL inputs and leaked logs in a safe environment.
4. **Correctness/reliability:** malformed output, timeout after side effect, duplicate webhook, queue replay, stale cache, partial writes, cancellation, empty retrieval, fallback semantic mismatch and provider rate limits.
5. **Evaluation:** dataset provenance, disjoint holdout, sufficient samples, repeated trials, per-tenant/domain slices, final-state validation, calibrated judges and regressions.
6. **Operations:** real deployment evidence, dependency health, migrations, pool limits, SLOs, alert ownership, backups, tested restore, rollback target, cost limits and graceful shutdown.
7. **Future risks:** upcoming deprecations, SDK/model changes, embedding migrations, growing corpus, concurrent tenants, retention obligations, integration token rotation, billing reconciliation and operator handoff.
8. **Human competence (mentor only):** ask the learner to explain a trust boundary, diagnose one failure and change one requirement without generated answers.

## Finding format

ID | critical/high/medium/low | location | observed evidence | impact | reproduction | proposed fix | regression test | owner | deadline | status.

Critical: active isolation bypass, secret exposure or unsafe consequential action. High: data loss, major correctness or reliability gap. Medium: bounded degradation or maintainability risk. Low: small localized issue. Uncertain exploitability is a question to investigate, not a fabricated vulnerability.

## Remediation

Produce a prioritized repair plan, preserve correct work, get approval for scope changes, patch smallest root causes, rerun tests and evaluate regressions. Maintain before/after evidence. Never rewrite to hide a lack of understanding. Reject release with unresolved critical/high findings. For medium/low, an owner can explicitly accept risk with expiry and monitoring.

## Final verdict

Choose REJECT / CONDITIONAL PILOT / RECOMMEND RELEASE TO OWNER. Explain evidence and missing evidence. A model cannot approve its own release. A static read-only review cannot establish runtime security, performance or recovery. The next session rechecks the actual revision.
