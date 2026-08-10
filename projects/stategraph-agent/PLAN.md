# Plan and contracts

FastAPI exposes typed task, event, approval, and memory contracts. A deterministic supervisor routes exactly four content agents, checkpoints after each node, interrupts on reviewer risk, and resumes decisions idempotently. Memory ownership is filtered before retrieval. Postgres migrations are the deployment persistence boundary; local mode remains intentionally deterministic. Tests cover completion, interrupt, approval, rejection, duplicate decisions, validation, missing tasks, and cross-user isolation.
