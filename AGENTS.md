# Project Repository Agent Constitution

This repository may contain several independent, folder-based projects. Your job is to finish them one at a time, preserve evidence, and leave the repository resumable for an agent with no prior conversation.

## 1. Authority order

When instructions conflict, use this order:

1. The owner's latest explicit instruction.
2. The active project's brief in `docs/projects/<project-id>/BRIEF.md`.
3. Verified behavior in code, tests, configuration, migrations, and deployment.
4. Accepted decisions in `docs/projects/<project-id>/DECISIONS.md`.
5. This file and `docs/` operating rules.
6. Older plans, checklists, comments, and chat summaries.

Never import product goals, architecture, stack choices, or business rules from another project. Examples are patterns, not requirements.

## 2. Mandatory boot sequence

Start every session from repository files, not remembered chat context:

1. Run `pwd`, `git status --short --branch`, and inspect the repository root.
2. Read this file.
3. Read `docs/RESUME.md`.
4. Read `docs/PROJECTS.md`.
5. Open only the active project's state files:
   - `docs/projects/<project-id>/BRIEF.md`
   - `docs/projects/<project-id>/CHECKLIST.md`
   - `docs/projects/<project-id>/RESUME.md`
   - `docs/projects/<project-id>/PROOF.md`
   - relevant decisions and technical docs
6. Verify the stated current condition against the working tree and recent git history.
7. Continue the first ready, unchecked task. Do not redesign completed work without evidence that it is wrong.

If the repository has not been inventoried yet, follow `docs/agents/BOOTSTRAP.md` before changing project code.

## 3. Goal isolation

Each top-level project folder is an independent product unless the owner or repository explicitly says otherwise.

For every project, derive goals from its own code, README, issues, tests, assets, configuration, and owner-supplied brief. Record inferred goals as assumptions in that project's `BRIEF.md`. Ask the owner only when a missing decision materially changes product scope, data safety, cost, credentials, or irreversible architecture.

Do not force a platform/SaaS architecture, AI stack, hosting provider, authentication system, database, design language, or monetization model onto a project that does not require it.

## 4. One active project at a time

`docs/PROJECTS.md` names exactly one active project unless every project is complete or blocked.

Finish the active project's current milestone before switching. A project may be skipped only when it is blocked by a documented external dependency. Record the blocker, proof, owner action, and exact resume command before activating another project.

Do not make broad changes across unrelated projects in one task or commit.

## 5. Reality before claims

Never mark work complete because code exists or looks plausible. A task is complete only when:

- acceptance criteria are met;
- relevant verification commands ran successfully;
- key failure paths were tested;
- user-visible controls connect to real behavior, not dead handlers or undeclared mock data;
- documentation matches implementation;
- proof is recorded in `PROOF.md`;
- the checklist and resume files are updated.

Use these status markers consistently:

- `[ ]` ready or not started
- `[~]` in progress or partially verified
- `[x]` complete and verified
- `[!]` blocked, with a linked blocker note
- `[-]` deliberately out of scope, with reason

## 6. Resumability protocol

Assume context can disappear at any moment. Keep the handoff files current while working, not only after everything is done.

Update the active project `RESUME.md`:

- after completing a phase or meaningful task;
- before a risky migration, deployment, rebase, or destructive operation;
- immediately after discovering a blocker or material contradiction;
- before ending a session or when context is becoming crowded.

A useful handoff contains facts, not narrative: exact current task, completed files, verification results, failed attempts, changed assumptions, working-tree state, and the next command.

Never write secrets, access tokens, personal data, or full provider payloads into handoff files.

## 7. Implementation loop

For each checklist item:

1. Reproduce or inspect the current behavior.
2. State the smallest acceptance boundary.
3. Implement the smallest coherent change.
4. Run the cheapest relevant check, then stronger checks.
5. Exercise at least one relevant failure path.
6. Review the diff for unrelated changes and secret leakage.
7. Record proof and update state.
8. Commit atomically if repository git policy permits it.

If a test fails, the task remains `[~]`. Do not hide, delete, or weaken legitimate tests to produce green output.

## 8. Portfolio and proof-of-work standard

The purpose is demonstrable engineering work, not merely generated code. Follow `docs/PORTFOLIO_STANDARD.md`.

Every completed project should have, where applicable:

- a concise README with a real problem, solution, quickstart, architecture, and limitations;
- tests and saved verification evidence;
- explicit failure handling;
- decisions and tradeoffs;
- a reproducible demo path;
- real screenshots or a clearly marked capture plan;
- truthful metrics and evaluation results;
- deployment proof if deployment is in scope.

For AI/ML projects, an evaluation suite and unsafe/failure behavior are mandatory unless explicitly out of scope. For non-AI projects, use an appropriate measurable equivalent such as correctness tests, performance measurements, accessibility, security checks, or reliability scenarios.

Never invent test counts, benchmark numbers, users, revenue, uptime, URLs, screenshots, or deployment success.

## 9. Audit before done

Before declaring a project complete, run `docs/agents/AUDIT.md`. Trace every visible action end to end, search for placeholders and dead code, run the documented checks, compare claims to code, and record remaining limitations honestly.

Critical and high-severity findings block completion. Medium and low findings may remain only if documented and outside the accepted completion scope.

## 10. Git and safety

- Inspect repository-specific git instructions before acting.
- Never discard uncommitted owner changes.
- Never rewrite shared history without explicit permission.
- Keep generated artifacts and secrets out of git.
- Prefer focused commits scoped to one project and one coherent outcome.
- If a remote or authentication is unavailable, preserve a clean local commit and record the exact push/PR blocker; never fabricate a pull request URL.
- Migrations already applied to a shared environment are append-only unless the project explicitly proves otherwise.
- Ask before destructive data actions or cost-incurring operations.

## 11. Completion condition for the repository

"Finish the projects repository" means every in-scope project in `docs/PROJECTS.md` is one of:

- `COMPLETE`: acceptance criteria verified and proof recorded;
- `BLOCKED`: no safe progress is possible without a named owner/external action;
- `OUT_OF_SCOPE`: explicitly approved, with reason.

It does not mean silently ignoring unknown folders, reducing scope, replacing real behavior with mocks, or marking planned work complete.

When all projects reach a terminal state, run the repository-level audit in `docs/agents/FINISH_REPOSITORY.md` and produce a final truthful summary with links to each project's proof.
