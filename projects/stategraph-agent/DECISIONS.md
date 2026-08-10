# Engineering Decisions

- A minimal versioned JSON Postgres checkpointer keeps serverless state portable; `thread_id == task_run_id`.
- Cooperative continuation advances only to the next durable gate.
- Research, Analyst, Reviewer, and Writer have non-overlapping typed outputs; the supervisor routes but never authors content.
- Approval is a durable row for auditability and idempotency, not only graph state.
- Deterministic local mode proves orchestration, not live model quality or web research.
