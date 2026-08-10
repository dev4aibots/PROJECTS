# DOCUMENTATION & PORTFOLIO-POLISH PROMPT — Day 10, per project

> Run ONLY after the project is live and verified. This converts a working repo into a repo that survives the hiring manager's 90-second scan.

---

```
The application is deployed and verified at: <LIVE_URL>
GitHub repo: <REPO_URL>

Transform this repository into a portfolio artifact optimized for a hiring
manager who will spend 90 seconds on it. Do NOT change core functionality.
Only: documentation, diagrams, error copy, loading/empty states, demo data,
screenshots scaffolding.

==================================================
README.md — REWRITE TO THIS EXACT STRUCTURE
==================================================

1. Title + one-line pitch + badges row (live demo link, tests passing,
   license MIT)
2. "▶ Live demo: <URL>  ·  🎥 2-min video: <placeholder>" — first screen,
   above the fold
3. Screenshot (placeholder path assets/screenshot-main.png — tell me the
   exact 2–3 screenshots to take and at what step)
4. THE PROBLEM (3 sentences, business language, no jargon)
5. THE SOLUTION (3 sentences + the one differentiator sentence, e.g. "the
   system refuses to answer when evidence is missing" / "AI proposes,
   deterministic code verifies" / "LLM SQL never touches the DB unvalidated")
6. ARCHITECTURE — Mermaid diagram of the real system (verify it renders on
   GitHub: no unsupported syntax)
7. KEY ENGINEERING DECISIONS — 5 bullets max, each linking into DECISIONS.md
8. EVALUATION RESULTS — the real table from docs/evaluation.md, including
   any before/after tuning numbers. If a number is mediocre, keep it and
   add one sentence of failure analysis. Honesty reads as seniority.
9. FAILURE HANDLING — a table: failure mode → system behavior → test file
10. TECH STACK — compact table
11. QUICKSTART — clone → env → migrate → run, minimal commands that
    actually work (verify them)
12. API — 3 most interesting endpoints with real curl + real JSON response
    (captured from the live system, secrets redacted)
13. TESTING — how to run, what's covered, current test count (real number)
14. LIMITATIONS — free-tier constraints, serverless constraints, security
    caveats, what you would build next with real infrastructure. This
    section signals judgment; write it carefully.
15. License + author footer: built by <NAME> — <LINKEDIN> — <PORTFOLIO_URL>

==================================================
SUPPORTING FILES
==================================================

- DECISIONS.md: 6–10 decisions, each in the format:
  Context → Options considered → Choice → Why → Tradeoff accepted.
- AUDIT.md: keep it (from the audit prompt) — link it from the README
  ("this repo was adversarially audited; findings and fixes documented").
- docs/: verify architecture.md, database.md (Mermaid erDiagram),
  evaluation.md, limitations.md, testing.md, deployment.md are current
  and consistent with the final code. Fix drift.
- DEMO_SCRIPT.md: a 90–120 second shot-by-shot script for my demo video:
    0:00 problem in one sentence (voiceover text written out)
    0:10 the happy path (exact clicks, exact inputs to type)
    0:40 the FAILURE/SECURITY case (the differentiator moment)
    1:10 the engineering proof (tests running / Langfuse trace / eval table)
    1:40 live URL + GitHub + close
  Write the exact voiceover sentences — I will read them verbatim.

==================================================
UI POLISH PASS (no new features)
==================================================

- Every async action has a loading state; every list has an empty state
  with a helpful hint; every failure shows a human error message with a
  retry where sensible.
- Landing page: pitch, 3–4 feature cards, architecture image, "Open Demo"
  + GitHub buttons. Nothing else.
- Add a small footer on /app: "Portfolio demo on free-tier infrastructure —
  responses may be rate-limited" (sets expectations for recruiters).
- Consistent spacing/typography; dark-mode-safe if trivial, skip otherwise.

==================================================
RESUME BULLETS + LINKEDIN BLURB
==================================================

Generate for me, grounded ONLY in what this repo actually does:
- 3 resume bullet variants (XYZ format: accomplished X, measured by Y,
  by doing Z) using the REAL eval numbers and REAL test counts
- a 2-sentence LinkedIn "Featured" blurb
- a 1-sentence portfolio-card description
No invented metrics. If a metric doesn't exist, use a concrete fact
(e.g., "8/8 SQL injection attack classes blocked, verified by 50-case
security corpus") instead of a made-up percentage.

Finally: run the full test suite and frontend build one last time to prove
the polish pass broke nothing, and show me the output.
```
