# Resumable Work Protocol

Use this loop after repository bootstrap.

## Session start

1. Follow the boot sequence in `AGENTS.md`.
2. Compare root resume, project resume, checklist, git status, and recent commits.
3. If they disagree, inspect code/tests and repair the docs before coding.
4. Confirm the current item is ready and not blocked by an unmet dependency.
5. Define its acceptance check in one sentence.

Do not reread every document. Open only the active project's relevant technical docs.

## Task sizing

Choose a task small enough to implement, verify, document, and hand off coherently. Good units include:

- one API behavior plus tests;
- one complete UI action wired through persistence;
- one migration plus repository/service tests;
- one failure mode across the relevant layers;
- one documentation correction backed by code inspection.

Avoid vague items such as "finish backend" or "polish app". Break them into observable outcomes.

## Implementation sequence

1. **Observe:** reproduce current behavior or read the exact code path.
2. **Specify:** confirm acceptance criteria and non-goals.
3. **Change:** make the smallest project-scoped implementation.
4. **Check locally:** run focused format/type/unit checks.
5. **Check behavior:** run integration, smoke, UI, or service checks that fit the change.
6. **Check failure:** test at least one relevant invalid/dependency/security path.
7. **Review:** inspect the diff, generated artifacts, dependency changes, and secret exposure.
8. **Record:** append concise proof and update checklist/resume.
9. **Commit:** follow repository git policy with a focused message.

## Verification ladder

Use the strongest available level without pretending unavailable infrastructure exists:

1. static/parse/format checks;
2. typecheck and lint;
3. focused unit tests;
4. full project tests;
5. integration tests with local or isolated dependencies;
6. local runtime smoke and primary flow;
7. production build/package;
8. preview deployment smoke;
9. live production smoke and monitoring evidence.

Record what did not run and why. A lower level does not imply a higher level passed.

## Checkpoint format

Before pausing, update the project resume with:

```text
Current item: P2-T4 — concise title
State: in progress
Completed: exact files/behavior
Verified: command -> result
Failed attempt: approach and why, if useful
Working tree: clean OR exact files
Next command: copy-paste-safe command
Next edit: file/function/line area
Acceptance remaining: exact unmet condition
```

Update the root resume only with the repository pointer and highest-value constraints. Keep detailed chronology in the project resume or git history.

## Blocker handling

A blocker entry must answer:

- what exact operation is blocked;
- error or evidence;
- why the agent cannot safely resolve it;
- exact owner/external action required;
- how to verify resolution;
- safe remaining work, if any.

Do not call a task blocked merely because the first approach failed. Try reasonable, safe alternatives within project scope. Do not bypass permissions, disable security, fabricate credentials, or use mocks to conceal the blocker.

## Context-loss prevention

Checkpoint at phase boundaries and before operations likely to consume substantial context. If forced to choose between more code and a correct handoff, create the handoff first. A smaller verified change with an exact resume pointer is better than a larger undocumented partial change.

## Project transition

Switch projects only when the current project is `COMPLETE` or truly `BLOCKED`.

Before switching:

- run the project audit or record why it cannot run;
- update project proof and terminal status;
- update `PROJECTS.md` counts and active project;
- update root `RESUME.md`;
- choose the next project by documented priority/dependency;
- ensure the working tree is safely committed or explicitly documented.
