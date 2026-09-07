# Compulsory agent protocol

## Priority and continuity
Latest explicit user request > active suite decisions > legacy docs. External skills are design references only. No repository file can guarantee obedience from every model; small explicit state, reproducible tests, and honest handoffs reduce drift.

## Every work unit
1. **Discover:** git status; read active state and handoff. Preserve unrelated changes. Confirm directory and tool versions.
2. **Verify baseline:** execute recorded tests. If stale status or a failure exists, record a recovery task before new features.
3. **Plan:** write requirement, named files/symbols, dependencies, security cases, acceptance test. Claim one task with `in_progress`. Commit the claim so interruption is safe.
4. **Implement:** a small vertical feature, not everything. Inspect callers/callees. Loading, empty, validation, unauthorized and failed-backend states are part of the feature.
5. **Review:** Problem → why it matters → smallest fix. Review schema and direct API attacks, not only UI. Never trust AI self-certification.
6. **Test:** unit → integration/RLS → browser checks as applicable. Record command, environment, date, result and skipped checks. Integration mocks do not prove RLS.
7. **Teach:** document exported symbols and one complete data trace; add an exercise/interview question based on this implementation.
8. **Checkpoint:** update STATUS, project FILES, HANDOFF, CHANGELOG. Commit scoped files immediately per completed coherent change; synchronize remote, push and create/update PR. Squash only this session's feature commits after sync; never erase unrelated user history.

## When runtime support is absent
If Docker/local Supabase is unavailable, implement credential-free tests for pure functions but mark database acceptance blocked. Try an isolated compatible local Postgres harness only if it accurately exercises SQL behavior; document differences. Never rename mocked tests as integration tests. Continue independent bounded work only if the roadmap explicitly permits it; do not mark the blocked task verified.

## Checkpoint record (copy this for each feature)
```text
Task ID / requirement:
Status / evidence level:
Files and symbols added or changed:
Inputs -> checks -> outputs / side effects:
Security boundaries:
Commands run / results / environment:
Not tested and why:
Decision or deviation:
Next single action and prerequisites:
```

## Context budget discipline
Write a handoff after each small feature, not only when asked to stop. Keep tasks granular enough to finish within one session. Reserve time for documentation/tests/Git. A sudden stop may leave a dirty tree: next agent reads diff first, maps it to FILES, runs tests, salvages valid work, and resumes; never resets or deletes unknown work.

## Recovery matrix
| Symptom | Recovery |
|---|---|
| Manifest says verified but file absent | Mark stale; inspect Git; restore known version, then retest |
| Partially written file or conflict markers | Read diff and task contract; finish minimal change; don't regenerate app |
| No Git metadata in copied folder | Use STATUS + lockfiles + tests; initialize Git if authorized; do not invent old commit hashes |
| Dependency versions changed | Use npm ci; investigate lock drift; do not install latest blindly |
| Remote conflicts | Fetch and prefer upstream behavior; reapply only scoped feature; retest |
| CI fails but local passes | Compare Node/env/OS/timezone, capture exact output, isolate one failure |
| Credits or external API unavailable | Mark provider checks blocked; no fake successful responses |

## Definition of done
A task is verified only when its explicit acceptance checks pass, source matches docs, no known critical defects remain in that task, and the commit exists. Release additionally requires auth/RLS/storage adversarial tests, build, browser/accessibility checks, backup/restore procedure, cost controls, owner runbook and final hosted smoke tests. Code-complete and hosted-verified are distinct statuses.
