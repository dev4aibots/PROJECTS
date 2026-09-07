# Durable change and evidence log

## 2026-09-07 — program setup
- Latest user request scoped to ClientFlow, SupportDesk AI and InvoiceHub. Legacy seven automation projects retained unchanged from main.
- Merged upstream and preferred remote tracking docs. Untracked FinAudit backup preserved locally in `.git/preexisting-finaudit-backup/`.
- Previous remote developer branch retained as `archive/pre-suite-developer-2026-09-07`; active branch now based on current main.
- Introduced root agent routing, suite entry point, structured tasks and mandatory handoff.
- Research: Vercel non-commercial Hobby, Supabase two-project limit, default SMTP constraints, SSR auth and design references. No service credentials/deployments used.
- PR: https://github.com/dev4aibots/PROJECTS/pull/2
- Documentation is a plan until task evidence states otherwise. Implementation starts only after DOCS checks pass.

## 2026-09-07 — scope correction and checkpoint recovery
- Latest request removes extras rather than retaining a separate legacy portfolio. Removed eight old app directories (seven automations plus hub), legacy root documentation and host rewrites. Source recovery remains in Git history; untracked local work was preserved under .git before synchronization.
- Restored the newest remote documentation checkpoint, matching the upload. Added executable state, documentation-link and verified-ledger checks with negative tests. DOCS remains active until those checks actually pass.
- Next bounded feature is CF-01; database/auth and the other apps are not implemented.

## 2026-09-07 — CF-01 verified: ClientFlow demo workbench
- Restored the newest checkpoint archive after the remote was force-reset to an empty tree (`e4bbba0`); recorded that commit as an ancestor with an `ours` merge so history is preserved and pushes fast-forward. Legacy seven-project trees remain only on `archive/*` branches.
- Production build made to fit a 1 GB container: per-icon imports via `src/components/icons.ts` (the `@phosphor-icons/react` barrel exhausted memory twice), Turbopack with `cpus: 1`, no browser source maps, 2 GB swap during compile.
- Added `tests/workbench.spec.ts`: 16 Playwright scenarios run on desktop Chrome and iPhone 13 — redirect/404/missing-record boundaries, URL-driven search/status/attention filters, hostile query degradation, inline board mutation with derived-count consistency, focused field errors with draft retention, create→edit with version note, reload boundary, axe WCAG 2.1 A/AA on five routes, skip link.
- axe reported three real contrast failures (footer/footnote 4.02:1; sand/blue/rose avatar initials <4.5:1). Fixed tokens now measure 5.1–5.5:1; 8–9 px text raised to 10–11 px.
- Evidence: lint clean, typecheck clean, Vitest 34/34, build 7 routes, Playwright 32/32. Ledger rows for CF-01 marked verified; README written; STATUS active task advanced to CF-02.
- Blocker noted for CF-02: no Docker/Supabase/psql in the sandbox. Next agent must obtain a real Postgres runtime or mark CF-02 blocked — never mock RLS.
- PR: https://github.com/dev4aibots/PROJECTS/pull/3
