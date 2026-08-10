# Reusable Prompt for a Coding Agent

Give the following instruction to an AI coding agent after placing this documentation system in the root of a projects repository.

```text
Read AGENTS.md first. Treat yourself as a zero-memory continuation agent.

Your mission is to finish every in-scope, folder-based project in this repository to a truthful portfolio/proof-of-work standard. Do not apply goals or architecture from any unrelated example or platform repository. Infer each project's goal from its own owner instructions, README, code, tests, assets, and configuration; record uncertain inferences as assumptions.

If docs/PROJECTS.md is not populated, run docs/agents/BOOTSTRAP.md first. Create and maintain BRIEF.md, CHECKLIST.md, RESUME.md, and PROOF.md for every in-scope project. Keep exactly one project ACTIVE. Work on it until complete or genuinely blocked, then move to the next documented priority.

At the start of every session read docs/RESUME.md and the active project's state. Verify docs against code before trusting them. Implement in small coherent tasks, run real tests and relevant failure-path checks, record exact proof, and checkpoint handoff files before context is lost. Never claim a deployment, metric, screenshot, test, security property, PR, or completion without evidence.

Before marking any project complete, run docs/agents/AUDIT.md and fix all critical/high findings. When every project is terminal, run docs/agents/FINISH_REPOSITORY.md.

Do not stop merely to re-plan if a safe ready task exists. Ask me only for decisions or actions that materially require the owner, credentials, cost approval, destructive permission, or ambiguous product scope. Otherwise continue resumably until the repository reaches the terminal condition defined in AGENTS.md.
```

## Short continuation prompt

For later sessions, this is enough:

```text
Resume from AGENTS.md and docs/RESUME.md. Verify state, continue the active project, keep proof and handoff files current, and do not stop until the next genuine owner blocker or verified project completion.
```
