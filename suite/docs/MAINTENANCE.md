# Maintenance and debugging playbook

## Weekly (owner/developer)
- [ ] Open each live demo and complete one workflow with synthetic data.
- [ ] Check service quota/error logs; keep account billing alerts enabled where available.
- [ ] Review dependency alerts, not automatic major-version upgrades.
- [ ] Export database and private storage manifest before important changes; keep copies private and encrypted.
- [ ] Confirm backups exclude plain secrets; check restore procedure in isolated environment periodically.

## Safe feature change
Write acceptance example → find UI → validator → action → DAL → RLS/constraint → test. Add a migration if persisted structure changes. Update types from DB, then UI. Prefer expand/migrate/contract: add nullable/new field, backfill, deploy compatible code, enforce constraint in a later migration. Never edit an applied migration. Commit, review preview, run negative tests, deploy, verify logs. Keep rollback code and data compatibility in mind.

## Debug without random rewrites
```text
Expected / actual:
Repro steps with synthetic IDs:
Browser network status and request ID:
Server sanitized error:
SQL policy/constraint involved:
Smallest failing test:
Hypothesis supported by evidence:
Minimal change and verification:
```

| Failure | Inspect first | Don't do |
|---|---|---|
| Login loops | Callback allowlist, cookie refresh propagation, canonical origin, browser cookie rules | Disable auth or confirmation |
| 403/empty data | Current auth.uid, workspace/app, membership, SELECT policy, query filter | Use service_role as workaround |
| Insert rejected | Zod error vs SQL constraint vs WITH CHECK; tenant FK | Remove RLS to make demo work |
| Save lost after refresh | Was route `/demo`? action result and DB write; no-store read | Pretend browser memory is persistence |
| Stale edits | Version column/affected row count; 409 conflict | Silently overwrite other user's work |
| File missing | Bucket/object path, upload result, metadata, policy and expiry | Make bucket public |
| AI wrong/no answer | Retrieved tenant chunks, citation IDs, cutoff, provider mode/error | More prompting without retrieval inspection |
| Invoice cent mismatch | Minor units, quantity scale, per-line rounding; identical server/PDF totals | Use JS float display as truth |
| Slow page | Network waterfall, DB explain, index selectivity, payload size | Add caching that leaks across users |

## Incident handling
Contain: disable only the affected feature/public endpoint or revoke leaked key. Do not delete logs/evidence. Assess: time range, affected workspace IDs, actual unauthorized access, no ungrounded breach claims. Fix minimal bug with regression test. Rotate exposed secrets and revoke sessions if needed. Restore in staging first; communicate honestly to affected users if real data was involved. Record postmortem and prevention step.

## Backup and rollback
Vercel rollback restores code, not database. Before schema changes, use Supabase/Postgres supported export tooling; back up DB schema/data and Storage separately; keep access restricted. Restore into an isolated project/local instance and verify row counts, relationships, auth implications and representative files. Do not restore by blindly wiping production. Migration reversal is not always safe; forward fixes often preserve data better.

## Upgrades
Use supported Node release matching `engines`. Change one dependency group, inspect release/security notes, npm install exact versions, run unit/typecheck/lint/build/SQL/E2E, inspect lock diff. Document skipped checks. Update deployment runtime deliberately. Never run `npm audit fix --force` without reviewing breaking changes.
