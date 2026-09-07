# Full-stack proof-of-work portfolio

Three products, built incrementally with AI assistance and documented so another developer—or an agent with no chat history—can continue safely.

| Product | Purpose | Implementation status |
|---|---|---|
| ClientFlow | Agency workspace, clients, projects, tasks and client portal | See [live task state](suite/STATUS.json) |
| SupportDesk AI | Grounded support answers with citations and human handoff | Planned; not a working platform yet |
| InvoiceHub | Invoice lifecycle, precise money calculations, expenses and PDF | Planned; not a working platform yet |

**Start here: [suite/START_HERE.md](suite/START_HERE.md).** Agents must read [AGENTS.md](AGENTS.md) first.

## Quality and honesty
Next.js + TypeScript + Supabase PostgreSQL/Auth/Storage + Tailwind. Vercel is the target for personal portfolio demos. A deployed UI is not proof of security or production readiness. Current evidence and release blockers live in the suite documentation. No job, income, certificate, or permanent-free hosting guarantee is made.

## Existing work is preserved
The previous seven-project AI automation portfolio remains under [`projects/`](projects/) with its original [roadmap](docs/MASTER_PLAN.md) and [deployment configuration](vercel.json). Its documentation is **legacy**, not the active build queue. Do not use the root Vercel configuration to deploy the new applications.

## Continue on another machine
Clone/download the full repository including `suite/` and lockfiles. Exclude `.env*` except `.env.example`, `node_modules`, `.next`, test artifacts, and `.git` if sharing a source archive. Give the next agent the prompt in `suite/START_HERE.md`; past chat is unnecessary. The machine-readable manifest and tests are the checkpoint, not an AI's claimed memory.
