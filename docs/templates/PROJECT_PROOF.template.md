# <Project Name> — Proof Ledger

> Record reproducible evidence, not confidence statements. Keep entries concise and append newest evidence near the top or in the relevant section.

## Current proof summary

| Claim/criterion | Status | Strongest evidence | Limitation |
|---|---|---|---|
| `<primary flow>` | `<verified/partial/unverified>` | `<entry/link>` | `<what remains>` |
| `<failure behavior>` | `<status>` | `<entry/link>` | `<what remains>` |
| `<build/test quality>` | `<status>` | `<entry/link>` | `<what remains>` |
| `<deploy/demo>` | `<status>` | `<entry/link>` | `<what remains>` |

## Verification entries

### `<YYYY-MM-DD HH:MM UTC>` — `<criterion or task ID>`

- Environment: `<OS/runtime/local/preview/production; relevant versions>`
- Commit: `<sha or uncommitted exact state>`
- Command/procedure:

```bash
<exact reproducible command or numbered manual procedure>
```

- Observed result: `<exit code, test counts, key response/state>`
- Proves: `<narrow claim this supports>`
- Does not prove: `<external/live/security/performance caveat>`
- Artifact/link: `<relative path or verified URL; no invented placeholder presented as real>`

## Evaluation or benchmark methodology

Use when applicable.

- Dataset/input: `<versioned path and size>`
- Metric definition: `<formula/pass condition>`
- Model/provider/configuration: `<if applicable>`
- Number of runs and variance: `<facts>`
- Date/environment: `<facts>`
- Result: `<honest table or link>`
- Known bias/limitations: `<facts>`

## Failure-path evidence

| Failure scenario | Expected safe behavior | Test/procedure | Result |
|---|---|---|---|
| `<invalid input/provider down/etc.>` | `<controlled response/no side effect>` | `<path/command>` | `<pass/fail>` |

## Deployment evidence

- Claimed URL: `<none until provided and verified>`
- Deployment commit: `<sha>`
- Post-deploy smoke command: `<command>`
- Result and timestamp: `<result>`
- Unverified services: `<none/list>`

## Audit findings

| Severity | Location | Finding | Proof | Fix/status |
|---|---|---|---|---|
| — | — | — | — | — |

## Owner-only verification/actions

| Action | Why agent cannot perform it | Exact steps | Success evidence |
|---|---|---|---|
| — | — | — | — |
