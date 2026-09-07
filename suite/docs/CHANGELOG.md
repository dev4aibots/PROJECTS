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
