# Bootstrap an Unfamiliar Projects Repository

Use this procedure once when the docs system is first added, and again when new top-level project folders appear. Do not change project code during bootstrap unless required to run a harmless discovery command.

## Phase 0 — Establish safety

1. Confirm repository root and git state.
2. Read repository instruction files and root documentation.
3. Identify uncommitted owner work; do not overwrite it.
4. Identify available runtime/package tools without installing or upgrading anything yet.
5. Record remote/branch information and repository-specific commit/PR rules.

## Phase 1 — Inventory folders

Inspect root and at most two useful levels below it. Classify each folder as:

- independent project;
- shared package/library;
- repository tooling;
- generated/build/vendor content;
- documentation/assets;
- unknown.

A project usually has one or more of: package manifest, build file, source tree, README, tests, deploy config, lockfile, or an independently runnable entry point.

Populate `docs/PROJECTS.md`, including unknown folders. Do not silently ignore a plausible project.

## Phase 2 — Assess each project without rewriting it

For each detected project, inspect:

- local instruction and README files;
- manifests, lockfiles, runtime versions, scripts;
- source entry points and route/UI structure;
- tests and test configuration;
- migrations/schema and persistent storage;
- environment examples and deployment configuration;
- TODO/FIXME/placeholder/mock markers;
- recent project-scoped git history if available.

Run only cheap, non-destructive discovery checks. Do not run migrations against shared environments or incur provider costs.

Create `docs/projects/<project-id>/` from the four templates. Replace placeholders with verified facts. Keep uncertain statements under `Assumptions and open questions`.

## Phase 3 — Derive each project's real goal

Use this evidence order:

1. latest owner instruction;
2. project-specific specification/README/issues;
3. implemented user flows and tests;
4. assets, samples, configuration, and naming;
5. cautious inference.

Write a one-sentence outcome and concrete acceptance scenarios in `BRIEF.md`. Separate:

- in scope now;
- optional future work;
- explicitly out of scope;
- unknown decisions.

Never copy another project's goal merely because its docs are more detailed.

## Phase 4 — Baseline reality

For each project, record what can be run safely:

- dependency/install status;
- typecheck/lint/unit/integration/build commands;
- current result and known environmental gaps;
- primary happy path and most important failure path;
- whether deployment exists and whether it has been verified.

A failing baseline is not shameful. Record it accurately in `PROOF.md` and convert failures into checklist tasks.

## Phase 5 — Prioritize

Order projects using:

1. owner priority;
2. dependency order;
3. ability to reach a complete demonstrable state;
4. portfolio impact of finishing versus starting;
5. risk and blocker availability.

Prefer finishing an almost-complete project over starting several projects. Keep only one `ACTIVE` project.

## Phase 6 — Exit gate

Bootstrap is complete when:

- [ ] every plausible project folder appears in the registry
- [ ] every in-scope project has populated BRIEF, CHECKLIST, RESUME, and PROOF files
- [ ] assumptions are distinguished from facts
- [ ] baseline checks are recorded
- [ ] cross-project dependencies are documented
- [ ] one project is active with one exact ready task
- [ ] root `RESUME.md` gives a cold agent the next command

Commit the documentation baseline if git policy and repository access allow it. Then continue through `WORK_PROTOCOL.md`.
