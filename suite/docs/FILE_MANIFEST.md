# File registry index

Per-project ledgers are intentionally granular. A path marked planned may not exist. A verified file can be read or changed when needed, but only after inspecting dependencies and updating tests. Files are not immutable just because an agent ticked a checkbox.

| Area | Ledger |
|---|---|
| ClientFlow source, tests and config | [projects/clientflow/FILES.md](projects/clientflow/FILES.md) |
| SupportDesk source, tests and config | [projects/supportdesk/FILES.md](projects/supportdesk/FILES.md) |
| InvoiceHub source, tests and config | [projects/invoicehub/FILES.md](projects/invoicehub/FILES.md) |
| Common migration contract | [DATABASE.md](DATABASE.md), actual file statuses in ClientFlow ledger |

## Documentation inventory
`../START_HERE.md`, `../STATUS.json`, `AGENT_PROTOCOL.md`, `HANDOFF.md`, `REQUIREMENTS.md`, `RESEARCH.md`, `ARCHITECTURE.md`, `DATABASE.md`, `DESIGN.md`, `SECURITY_TESTING.md`, `ROADMAP.md`, `DEPLOYMENT.md`, `MAINTENANCE.md`, `LEARNING.md`, `PORTFOLIO.md`, `FILE_MANIFEST.md`, `CHANGELOG.md`; each product has PRD, ARCHITECTURE, FILES, LEARNING.

## Entry format
`path | key symbols/responsibility | task | status/evidence`.
For a changed file, include the symbol names rather than unstable line numbers. Tests and Git provide code-level provenance; copying the full source into docs creates stale duplicated code and is prohibited. The learning guide links the real implementation instead.
