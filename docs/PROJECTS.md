# Projects Registry — repository source of coordination truth

Last verified: `2026-08-10 16:10 UTC`
Verified by: DocuMind final local audit/remediation and handoff review

## Registry

| Priority | Project ID | Folder | Status | Goal source | Current milestone | Proof | Blocker |
|---:|---|---|---|---|---|---|---|
| 1 | `documind-rag-mcp` | `projects/documind-rag-mcp` | `BLOCKED` | `02-project-1-enterprise-rag-mcp.md` | `P6-T4 live deploy/smoke` | `projects/documind-rag-mcp/PROOF.md` | Owner-managed Supabase/providers/Langfuse/Vercel |
| 2 | `stategraph-agent` | `projects/stategraph-agent` | `ACTIVE` | `03-project-2-stategraph-agents.md` | `Phase 0 plan and contracts` | `projects/stategraph-agent/PROOF.md` | — |
| 3 | `zerotrust-sql` | `projects/zerotrust-sql` | `PLANNED` | `04-project-3-zerotrust-sql.md` | `Phase 0` | `projects/zerotrust-sql/PROOF.md` | — |
| 4 | `docuextract` | `projects/docuextract` | `PLANNED` | `05-project-4-docuextract.md` | `Phase 0` | `projects/docuextract/PROOF.md` | — |
| 5 | `llmshield` | `projects/llmshield` | `PLANNED` | `06-project-5-llmshield.md` | `Phase 0` | `projects/llmshield/PROOF.md` | — |

## Active project

- Project: `stategraph-agent`
- Folder: `projects/stategraph-agent`
- Why active: DocuMind has no safe local milestone work remaining and is blocked only at owner-managed live deployment; StateGraph is the next specified core priority.
- Resume: `projects/stategraph-agent/RESUME.md`
- First ready task: `P0-T1` — review `03-project-2-stategraph-agents.md` and produce a plan-only `projects/stategraph-agent/PLAN.md`.

## Dependency order

No runtime dependency is verified between the five projects. They are sequenced for portfolio focus. Bonus EvalBoard and Portfolio Hub remain deferred until all core projects are deployed, audited, and documented as required by their specification.

## Repository-wide blockers

| ID | Blocker | Affected projects | Owner/external action | Safe work remaining |
|---|---|---|---|---|
| `B-001` | Live Supabase, providers, Langfuse, and Vercel are unconfigured | DocuMind deployment; later all projects | supply/configure credentials and cloud projects; approve cost-incurring checks | Other projects' planning, local implementation, tests, fixtures, and docs |

## Completion roll-up

- In-scope projects: `5`
- Complete: `0`
- Active: `1`
- Planned: `3`
- Blocked: `1`
- Out of scope/deferred bonus projects: `2`

The repository is not complete while any core project remains `PLANNED`, `ACTIVE`, or externally `BLOCKED`.
