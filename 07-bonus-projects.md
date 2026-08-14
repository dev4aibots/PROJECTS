# BONUS PROJECTS 6 & 7 — ONLY if the core five are deployed, audited, and documented

> Hard rule: do NOT start these unless Projects 1–5 are all live with demo videos. Five excellent repos beat seven rushed ones. These exist because (a) research shows "LLM evaluation pipeline" is an explicitly recommended hire-signal project, and (b) a portfolio hub multiplies the value of everything else.

---

## PROJECT 6 — EvalBoard: LLM Evaluation Pipeline & Regression Dashboard (½–1 day)

**Repo name:** `evalboard`
**Hiring signal:** "The ones who get hired know how to write tests for non-deterministic systems." This project also *connects* your portfolio — it evaluates Project 1 — which signals systems thinking.

> Paste `01-master-context.md` first, then:

```
PROJECT NAME: EvalBoard — Continuous Evaluation & Regression Tracking for
LLM Apps

ONE-SENTENCE PITCH:
A reusable evaluation pipeline that runs golden-dataset evals against any
LLM endpoint (demoed against my deployed DocuMind RAG API), stores every
run in Postgres, and renders a regression dashboard showing metric drift
across runs, models, and prompt versions.

SCOPE (strict, this is a small project):
- evals run via a POST /api/eval-runs endpoint that takes {target_base_url,
  dataset_id, config{model?, threshold?, notes}} and executes the golden
  dataset against the target's public API (my DocuMind deployment),
  respecting free-tier rate limits (sequential with delay, resumable via
  cursor exactly like DocuMind's processing pattern)
- metrics per case: retrieval_hit, faithfulness (LLM-as-judge through the
  provider abstraction, judge prompt versioned in the repo),
  citation_accuracy, refusal_correctness, latency_ms
- DB: datasets, dataset_cases, eval_runs, case_results (all normalized;
  a run is comparable to any other run)
- dashboard (/app): run list; run detail with per-case pass/fail drill-down
  (question, answer, judge rationale); COMPARISON VIEW: pick 2 runs →
  per-metric delta table with green/red arrows — this is the screenshot
  that gets you interviews
- seed: ship the DocuMind golden dataset as the default dataset + one
  recorded baseline run (fixtures) so the dashboard is never empty
- honest docs: LLM-as-judge caveats (bias, variance), why deterministic
  checks are preferred where possible; docs/methodology.md
- tests: metric computations unit-tested with recorded fixtures; judge
  parsing failure path; resumable-run integrity test

Everything else (stack, standards, phases, audit) per the master context.
Begin with PHASE 0.
```

**Resume line it earns:** "Built a regression-tracking evaluation pipeline for LLM systems; caught a 14-point faithfulness drop when swapping models before it reached the demo." (Run a real model swap so the number is real.)

---

## PROJECT 7 — Portfolio Hub (½ day, no backend)

**Repo name:** `devraj-portfolio` (deploy at your custom domain or vercel.app)

> This one does NOT need the master context. Paste directly:

```
Build a single-page portfolio site. Next.js + TypeScript + Tailwind, static,
deployed on Vercel. NO backend, NO database, NO CMS, NO 3D, NO animation
libraries beyond subtle CSS transitions. It must load instantly and read
in 10 seconds.

Content structure (I will provide final copy; scaffold with placeholders):

1. Hero: NAME — "AI Engineer · Agentic systems, RAG & LLM applications."
   Sub-line: "I build and deploy AI systems with evaluation suites,
   security guardrails, and honest failure handling."
   Buttons: GitHub · LinkedIn · Resume (PDF) · Email
2. PROOF OF WORK — exactly 5 project cards (+1 if EvalBoard exists), each:
   name, one-line differentiator, tech chips (max 5), and three links:
   LIVE DEMO / GITHUB / 2-MIN VIDEO. Card order: DocuMind RAG+MCP,
   StateGraph, ZeroTrust SQL, DocuExtract, LLMShield.
   Each card shows ONE real metric from the project's eval
   (e.g., "8/8 attack classes blocked", "faithfulness 0.91").
3. HOW I WORK — 4 short bullets: eval-first, security-aware, serverless-
   pragmatic, documented decisions (link one DECISIONS.md as evidence).
4. STACK — one compact row of technology names, no skill bars.
5. Footer: email, GitHub, LinkedIn.

Design: dark, premium-minimal, generous whitespace, one accent color,
system font stack or one Google font. Mobile-first. Lighthouse ≥95 on all
categories — verify with the build.

Also generate: the resume PDF content section for these 5 projects (I'll
paste into my resume), and meta/OG tags so links unfurl nicely on LinkedIn.
```

---

## Why NOT more projects
Research is unambiguous: hiring managers scan for depth signals (evals, failure handling, audits, live deploys) and are actively suspicious of many shallow repos. 5 deep + 1 eval + 1 hub is the ceiling for 10 days. Spend surplus time on demo videos and interview prep (`11-interview-answers.md`) — the ROI is higher than an eighth repo.
