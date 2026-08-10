# Resumable Project Repository Documentation

This folder is an operating system for AI coding agents that must finish multiple folder-based projects without relying on chat memory.

It deliberately contains no platform-specific product goal or mandatory technology stack. Each project's own brief is authoritative.

## Start here

| Need | File |
|---|---|
| Agent constitution and boot order | `../AGENTS.md` |
| Exact repository stopping point | `RESUME.md` |
| Inventory, priority, and active project | `PROJECTS.md` |
| What counts as portfolio-grade proof | `PORTFOLIO_STANDARD.md` |
| How to inventory an unfamiliar projects repo | `agents/BOOTSTRAP.md` |
| Repeatable implementation loop | `agents/WORK_PROTOCOL.md` |
| Adversarial completion audit | `agents/AUDIT.md` |
| Final all-projects audit | `agents/FINISH_REPOSITORY.md` |
| Templates for each project | `templates/` |
| Live per-project records | `projects/<project-id>/` |

## Live state versus stable guidance

- Stable guidance: `AGENTS.md`, this map, `PORTFOLIO_STANDARD.md`, and `agents/`.
- Repository live state: `RESUME.md` and `PROJECTS.md`.
- Project live state: `projects/<project-id>/CHECKLIST.md`, `RESUME.md`, and `PROOF.md`.
- Project intent: `projects/<project-id>/BRIEF.md`.
- Project technical truth: code, tests, configuration, migrations, and accepted decisions.

Do not put changing task status into stable guidance. Do not bury product requirements in a session log.

## Initial adoption

1. Copy this docs system into the root of the projects repository.
2. Tell the agent: `Read AGENTS.md and finish all in-scope projects resumably.`
3. The agent runs `agents/BOOTSTRAP.md`, populates `PROJECTS.md`, and creates one directory under `docs/projects/` per detected project using the templates.
4. The agent activates one project, verifies its current reality, and works through its checklist.
5. Every session ends with fresh resume and proof records.

## Design principles taken from the supplied references

- A zero-memory agent needs a short exact resume pointer plus a detailed checklist.
- A doc map prevents rereading the entire repository every session.
- Reality checks prevent stale checklists from becoming false authority.
- Phased work, explicit quality gates, and adversarial audits produce stronger results.
- Portfolio value comes from evaluation, failure handling, decisions, tests, honest limitations, live proof, and concise presentation.
- These are workflow patterns only; the source archive's platform-specific goals and fixed stack are intentionally excluded.
