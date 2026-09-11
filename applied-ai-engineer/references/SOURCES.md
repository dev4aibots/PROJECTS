# Research ledger

Retrieved 2026-09-11. These sources inform principles, not an endorsement of every product or claim. No live model/price benchmarking was performed. Recheck mutable pages when adopting a dependency.

| Source | Read scope and claim used | Limitation / action |
|---|---|---|
| [Upstream pinned repository](https://github.com/rohitg00/ai-engineering-from-scratch/tree/d18b8fe5a913c46011a3b06cb6ebd6a924414fd3) | Local inventory, selected applied lesson review; see AUDIT.md | All 523 not semantically/execution audited |
| [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Full fetched article; workflow vs agent, simplest sufficient architecture, tool contracts | Originally 2024; article itself warns tooling has changed. Principles, not current SDK selection |
| [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | Full fetched article; tasks/trials/graders, environment outcomes, judge calibration, regression suites | Vendor perspective; reported benchmarks not independently reproduced |
| [MCP authorization 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) | Versioned specification read; discovery, issuer/audience binding, PKCE, CIMD vs compatibility DCR | Match host and SDK negotiated protocol; transport auth is not business authorization |
| [MCP authorization 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization) | Older spec read for comparison; no token passthrough | Do not use older client-registration guidance as the current profile |
| [OWASP prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) | Full fetched risk page; indirect injection, least privilege, approval and adversarial tests | Mitigations reduce impact; no complete prompt-level prevention guarantee |
| [PostgreSQL row security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) | Full fetched documentation; default deny, WITH CHECK, owners/BYPASSRLS, policy combinations | 'current' is mutable; pin deployed PG version and test runtime role |
| [AWS timeouts/retries/jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | Attempted fetch; ordinary request failed, rendered retry returned unrelated shell | NOT a successfully read source; verify independently before citing specific claims |

## Research questions answered

- Can instructions replace an execution boundary? No: skills/context guide behavior; host/application permissions must enforce it.
- Is a self-review score a sufficient release gate? No: use executable tests, environment-state outcomes, independent review and calibrated evaluation.
- Must this user build models from scratch first? Not for the specified API-first role; focus on application boundaries and operating evidence.

## Refresh contract

Before changing a dependency/provider: record official URL, version, date, claim and observed compatibility test. Stop on unresolved contradictions affecting auth/data/cost. Do not scrape entire websites or execute suggested commands automatically. Update the catalog via an explicit reviewed diff when upstream commit changes. References are cited, not vendored; obey upstream licensing if copying code later.
