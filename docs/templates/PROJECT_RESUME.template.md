# <Project Name> — Session Resume

> A new agent must be able to continue without conversation history.

Updated: `<YYYY-MM-DD HH:MM UTC>`  
Project folder: `<relative/path>`  
Branch/commit: `<branch> @ <sha>`  
Working tree: `<clean or exact files>`

## Exact current position

- Milestone: `<phase>`
- Checklist item: `<ID — title>`
- State: `<ready/in progress/blocked>`
- Acceptance remaining: `<one observable condition>`

## Resume commands

```bash
cd <repository-root>
<safe status/setup/test command>
```

Then open `<file/function>` and continue with `<exact next edit/action>`.

## Completed in the latest session

- `<behavior and file>`
- `<behavior and file>`

## Verification already run

| Command/procedure | Result | Scope | Timestamp |
|---|---|---|---|
| `<exact command>` | `<pass/fail with useful count>` | `<what it proves>` | `<UTC>` |

## Failed attempts and do-not-repeat notes

- `<approach>` failed because `<evidence>`. Next safe approach: `<action>`.

## Decisions/assumptions changed

- `<ID/link and concise change>`

## Environment and service state

- Runtime/dependencies: `<state>`
- Local services/background processes: `<none or IDs/ports>`
- External services: `<configured/unverified/blocked; never include secrets>`
- Generated/local-only artifacts: `<paths>`

## Blockers

- `<none OR exact error, evidence, required action, and resolution command>`

## Handoff checklist

- [ ] checklist reflects verified state
- [ ] proof ledger includes latest result
- [ ] next command is safe and copy-pasteable
- [ ] no unrecorded risky partial operation
- [ ] git state is exact
- [ ] no secrets in this file
