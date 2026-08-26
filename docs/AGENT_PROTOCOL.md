# AGENT_PROTOCOL.md — How agents work, commit, verify, and hand off

## Session start ritual (always)
1. `cat AGENTS.md` (rules) → `cat docs/CHECKPOINTS.md` (where) → `cat docs/projects/<active>/RESUME.md` (exact next step).
2. `git log --oneline -5` — the last commit message contains `next: …` from the previous agent. Cross-check with RESUME.md.
3. Consult `docs/FILE_MANIFEST.md`. Files marked ✅ are DONE AND VERIFIED — do not open them except to import from them.

## Building rules
- Work on ONE project at a time, in checkpoint order (C1 → C2 → …) as listed in its RESUME.md.
- Write a file completely, then immediately mark it in FILE_MANIFEST.md. Never leave a file half-written without marking it 🔨 with a note about what remains.
- Prefer boring, dependency-light code. Python: fastapi, pydantic, sqlglot, beautifulsoup4, httpx only. Node: zero npm dependencies (use built-ins + fetch); dashboards use Tailwind CDN + vanilla JS.
- Demo mode first: implement the deterministic fallback path, verify it, THEN wire the real API call behind `if (process.env.X)` / `if os.environ.get("X")`.
- Serverless statelessness: in-memory stores reset per cold start — that is acceptable for demo mode; code must still include the real DB path (Supabase/Neon/Upstash) behind env vars, and seeded demo data must repopulate on cold start so the dashboard never looks empty.

## Verification (before marking any checkpoint ✅)
- Python: `cd projects/<dir> && pip install -r requirements.txt -q && python -m pytest tests/ -q` plus boot check `python -c "from api.index import app"`.
- Node: `cd projects/<dir> && node tests/smoke.test.js` (plain-node test runner, no deps).
- Dashboard: open `public/index.html` logic mentally or via the dev server; every button must map to a real endpoint.

## Git workflow (this repo's durable memory)
- Branch: `genspark_ai_developer`.
- Commit after EVERY checkpoint (and at minimum every ~3 files): `git add -A && git commit -m "feat(<slug>): <what> | next: <concrete next action>"`.
- Before ending a session: Handoff Procedure (AGENTS.md) then final commit `checkpoint: …`.
- Before PR: `git fetch origin main && git rebase origin/main` (prefer remote on conflicts) → squash local commits (`git reset --soft <base> && git commit`) → `git push -f origin genspark_ai_developer` → open/update PR to `main` → share PR URL.

## Status vocabulary (used in all tracking docs)
- `⬜ TODO` — not started. `🔨 WIP` — started, see note. `✅ DONE` — written AND verified. `🧊 BLOCKED` — see blocker note in RESUME.md.

## When something is broken
- A ✅ file may only be reopened if a test/verification proves it broken. Record in the project RESUME.md: what failed, what you changed, why.
- Never downgrade scope silently. Scope changes go in RESUME.md under "Decisions".
