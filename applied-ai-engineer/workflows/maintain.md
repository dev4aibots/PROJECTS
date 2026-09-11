# Operate, maintain and improve

Release is the start of an operational obligation. Use a named owner and frequency appropriate to risk; the schedule below is a starting proposal.

- Daily while piloting: error budget, unresolved incidents, failed/unknown actions, queue age, tenant cost outliers and safety events.
- Weekly: sample sanitized trajectories, grade production feedback, inspect retrieval misses, reconcile action/billing ledgers, review DLQ and add regression fixtures.
- Monthly: dependency/advisory review, token/credential rotation checks, restore drill, capacity/cost forecast, access review and retention/deletion audit.
- On any model/prompt/embedding/SDK change: freeze current baseline, version datasets, run regression + adversarial suites, compare per-slice quality/cost/latency, shadow without real side effects, canary with minimum samples and explicit rollback triggers.

Risks carry likelihood, impact, detectability, affected boundary, mitigation, owner, due date, evidence and revisit trigger. Never close a risk because a README says it is handled. Keep rollback artifacts and migrations compatible with both versions during rollout. Changed embeddings require index versioning and re-index evaluation, not mixing vectors silently.

Turn incidents into owned tests and operational controls. A proposed new agent rule includes why it is needed, evidence, scope and retirement criteria. Compare its benefit against extra false blocks/context cost. Humans approve policy changes; the agent does not self-modify its authority.
