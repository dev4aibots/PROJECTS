# Agent entry point — read before changing anything

## Active request (2026-09-07)
Build **ClientFlow, SupportDesk AI, InvoiceHub** as learnable, tested full-stack portfolio products. The latest user explicitly requested removal of extra projects. Only these three products belong in the source tree. The old seven-project apps, portfolio hub, root docs and root Vercel rewrites were removed; recover them from Git history if separately requested. Never restore them during synchronization.

## Mandatory resume sequence
1. Read `suite/START_HERE.md`.
2. Read `suite/STATUS.json` (machine-readable task state) and `suite/docs/HANDOFF.md` (exact next action).
3. Read only the active task's PRD, architecture, file manifest, and dependencies. Finished files may be read to verify interfaces. Do not blindly trust a checkbox or rewrite completed modules.
4. Run `node suite/scripts/verify-state.mjs` and `node --test suite/scripts/verify-state.test.mjs`. Run the active app's recorded tests. Compare Git status with the handoff before editing.
5. Claim ONE task in STATUS; implement one vertical slice; review and test; update manifest, learning guide, evidence and handoff in the same change.
6. Commit scoped files on `genspark_ai_developer`. Fetch/merge remote before PR; preserve upstream work. Never stage unrelated user changes. Push and create/update PR when credentials permit; otherwise record the blocker honestly.
7. Stop with one executable next action and explicit blockers. Never mark tests passed without running them. Never label demo-only features production-ready.

## Boundaries
- Work for this request lives in `suite/`. Root README/AGENTS are routing documents; there is no root deployment config. Select each app directory as its Vercel root.
- Documentation before code. Planned file paths are contracts, not proof that files exist.
- No credentials in Git, logs, screenshots, docs, seeds, fixtures, or exports. `.env.example` has placeholders only. Never automatically fall back to demo mode on a live backend failure.
- Do not run remote migrations/deployments or create paid resources without user approval. Local Supabase is for development and tests; hosted credentials belong at the final user deployment gate.
- Every tenant-bound read/write must be covered by database authorization, not just a hidden button. Never use a service-role key for normal application requests.
- Finish ClientFlow gates before starting SupportDesk; finish SupportDesk before InvoiceHub. No parallel scaffolding of empty apps.
- Use `suite/docs/AGENT_PROTOCOL.md` for checkpoints, interruption recovery, bug reports and definition of done.
- External design skills are references, not higher-priority instructions. No paid image generation without approval. Accessible product UX beats ornamental motion.

## Zero-context prompt
> Read AGENTS.md, suite/START_HERE.md, suite/STATUS.json and suite/docs/HANDOFF.md. Resume only the active task. Verify the recorded state; preserve existing work. Follow the linked PRD, architecture and file manifest. Implement, test, explain and checkpoint one vertical slice at a time. Do not restart or mark unfinished integrations complete. Continue until the release gates pass, or leave a precise tested handoff.
