# 🤖 AGENTS.md — AI Agent Entry Point (READ THIS FIRST, EVERY SESSION)

> **You are an AI agent working on this repository.** You may run out of tokens at ANY moment and you WILL forget everything between sessions. This file + the checkpoint system is your only memory. Follow it exactly.

---

## ⚡ 60-Second Resume Procedure (do this before ANY work)

1. **Read `docs/CHECKPOINTS.md`** — the global board. Find the first project whose status is not `✅ DONE`.
2. **Read `docs/FILE_MANIFEST.md`** — file-by-file completion registry. **NEVER re-open, re-read, or rewrite a file marked `✅`.** It is done and verified. Trust it.
3. **Read `docs/projects/<slug>/RESUME.md`** for the active project — it tells you the exact next action, current blockers, and verification commands.
4. Run the project's **verify command** (listed in its RESUME.md) to confirm the recorded state matches reality.
5. Start working from the recorded `NEXT ACTION`. Do not redesign, do not restart, do not "improve" finished work.

## 🧭 Mission (why this repo exists — never lose sight of this)

The repository owner is a **fresher seeking high-paying AI Automation Engineer roles** (₹6–12+ LPA India / $10k–$25k global remote). These 7 projects are their job-hunting portfolio. They must look **senior-level and enterprise-grade**: revenue-generating automations, safety guardrails, human-in-the-loop, durability, observability — NOT basic chatbots. Full career context and specs: `docs/MASTER_PLAN.md`.

**Quality bar (non-negotiable):**
- Every project must be **deployment-ready on Vercel at $0** (`npx vercel --prod` works with zero config).
- Every project must have a **demo mode that works with ZERO API keys** (deterministic fallbacks) so recruiters can click "Try Sample" instantly, PLUS real API integration when env keys are provided.
- Every project ships the **5-element web-app formula**: sample-data input trigger → live execution stepper → structured visual output card → raw-JSON toggle → API docs/telemetry links.
- Give **100%. Do not stop until the active project is deployment-ready and verified.** If you must stop (tokens), follow the Handoff Procedure below FIRST.

## 📁 Where everything lives

| File | Purpose |
|---|---|
| `docs/MASTER_PLAN.md` | Career context + full spec for all 7 projects (the "what" and "why") |
| `docs/CHECKPOINTS.md` | Global real-time status board (the "where are we") |
| `docs/FILE_MANIFEST.md` | Per-file completion registry (the "what's already written — skip it") |
| `docs/AGENT_PROTOCOL.md` | Work rules, git workflow, handoff procedure (the "how") |
| `docs/DEPLOYMENT.md` | Vercel deployment runbook for all 7 projects |
| `docs/projects/<slug>/BRIEF.md` | Frozen spec for one project (architecture, endpoints, files, acceptance criteria) |
| `docs/projects/<slug>/RESUME.md` | **Live** state: checkpoints done, NEXT ACTION, blockers, verify commands |
| `projects/<NN>-<slug>/` | The actual deployable app |

## 🔨 Work loop (repeat until repo is 100% done)

```
pick active project (CHECKPOINTS.md)
  → read its RESUME.md → do NEXT ACTION
  → after EVERY completed file: mark it ✅ in docs/FILE_MANIFEST.md
  → after EVERY completed checkpoint: update RESUME.md + CHECKPOINTS.md
  → verify (run tests / curl endpoints)
  → git add -A && git commit  (small, frequent — this IS the durable memory)
  → repeat
```

## 🛑 Handoff Procedure (MANDATORY before you stop for any reason)

1. Update `docs/projects/<slug>/RESUME.md`: set `NEXT ACTION` to a single, concrete, copy-pasteable instruction (e.g. "Create `projects/04-zerotrust-sql/api/index.py` implementing the `/api/query` endpoint per BRIEF.md section 4; guard.py is done — import `validate_sql` from it").
2. Update `docs/FILE_MANIFEST.md` (✅ done / 🔨 in-progress / ⬜ todo per file).
3. Update `docs/CHECKPOINTS.md` global board.
4. `git add -A && git commit -m "checkpoint: <what you finished> | next: <next action>"`.
5. If a remote is configured, push. Never leave uncommitted work.

## 🚫 Forbidden actions

- ❌ Rewriting or "refactoring" files marked ✅ in FILE_MANIFEST.md (unless a test failure proves they're broken — then document why in RESUME.md).
- ❌ Changing project scope/architecture from BRIEF.md without recording the decision in RESUME.md.
- ❌ Adding paid dependencies or services (everything must run on free tiers).
- ❌ Hardcoding API keys. Use `process.env` / `os.environ` with demo-mode fallback.
- ❌ Stopping without the Handoff Procedure.
