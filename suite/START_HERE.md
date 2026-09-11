# Start here — durable project memory

This program implements the latest request for **three full-stack products**, not the older automation portfolio. Product scope, implementation state, and learning evidence are deliberately separate.

## Read in this order (under five minutes)
1. [STATUS.json](STATUS.json): active task and task dependency graph.
2. [Handoff](docs/HANDOFF.md): exact command/action to resume and known blockers.
3. [Roadmap](docs/ROADMAP.md): acceptance criteria for every milestone.
4. [Active project](docs/projects/clientflow/PRD.md) and its `ARCHITECTURE.md`, `FILES.md`, `LEARNING.md`.
5. [Agent protocol](docs/AGENT_PROTOCOL.md): compulsory work cycle.

## Documentation map
- `docs/REQUIREMENTS.md`: interpreted user requirements and assumptions, not invented commitments.
- `docs/RESEARCH.md`: dated official sources, design references, costs and limitations.
- `docs/ARCHITECTURE.md`: overall stack, deployment topology, auth/data diagrams, decisions.
- `docs/DATABASE.md`: common schema contract and migration rules.
- `docs/SECURITY_TESTING.md`: authorization matrix, test pyramid, abuse controls, release gates.
- `docs/DESIGN.md`: shared interaction standards and individual product identities.
- `docs/DEPLOYMENT.md`: local-to-Vercel/Supabase runbook; credentials are the final user step.
- `docs/MAINTENANCE.md`: debugging, recovery, backups, upgrades and incident response.
- `docs/LEARNING.md`: junior curriculum, code-reading method and technical interview practice.
- `docs/PORTFOLIO.md`: truthful presentation, walkthrough script and certificate positioning.
- `docs/ROADMAP.md`: ordered milestones with acceptance criteria.
- `docs/FILE_MANIFEST.md`: index of per-file ledgers; planned is not implemented.
- `docs/CHANGELOG.md`: session-level durable decisions and verification evidence.
- `docs/projects/{clientflow,supportdesk,invoicehub}/`: PRD, architecture/schema, file ledger, learning guide.

## Status vocabulary
`planned` = specified only; `in_progress` = active implementation; `blocked` = explicit dependency unavailable; `verified` = listed automated checks passed for the bounded task. Product release is a separate task. Never infer that a verified UI means verified RLS, real AI, or hosted deployment.

## Prompt to copy to the next AI
```text
You are continuing an existing repository, not starting a new project.
Read AGENTS.md then suite/START_HERE.md, suite/STATUS.json, suite/docs/HANDOFF.md.
Use repository files and actual test output as memory. Follow the active task only.
Read its project PRD/ARCHITECTURE/FILES/LEARNING documents and referenced source.
Run the documented baseline commands before editing. Report discrepancies.
Finish one vertical slice, add adversarial tests, update learning explanations,
file ledger and handoff; commit and update the PR. Keep only the three requested products; do not restore removed legacy apps.
Continue sequentially through the roadmap; do not scaffold all projects at once.
No fake success, fake authentication, silent mock fallback, or unverified release claims.
If interrupted, write the exact next action, changed files, tests, blockers and risks.
The owner should only need credentials, migration/configuration steps and deployment
AFTER all implementation/release gates are complete. Do not shift unfinished code to them.
```

## Interruptions during documentation
If STATUS says DOCS is active, complete the missing documents in ROADMAP before coding. A filename in the map is not evidence the file is written. Check existence and contents. Keep this entry point and HANDOFF usable even if other documents are incomplete.
