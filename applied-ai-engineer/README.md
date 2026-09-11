# Applied AI Engineer Workbench

A portable, model-independent operating kit for **building, reviewing, debugging, evaluating and operating AI systems**. Supply your own chatbot, coding CLI, or API-powered agent. No bundled LLM, model weights, API credentials, subscriptions or runtime dependencies beyond Python 3.10+.

This is an engineering workbench, not an autonomous intelligence or a finished AI employee SaaS. It makes expectations explicit; your host supplies reasoning, web access, file editing and execution. It cannot guarantee correct code, prevent a malicious agent bypassing instructions, or certify production readiness.

## Start in five minutes

1. Extract this folder anywhere, or keep it beside an existing project. Do not overwrite that project's instructions.
2. Read [START_HERE.md](START_HERE.md). Terminal agents read [AGENTS.md](AGENTS.md).
3. Run `python3 forge.py doctor` and `python3 -m unittest discover -s tests -v` from this folder.
4. Create a task: `python3 forge.py init --task support-pilot --mode build --goal "Build tenant-isolated support with citations and escalation"`.
5. Generate a focused context pack: `python3 forge.py pack --task support-pilot --topic rag --topic backend --out workspace/support-pilot/CONTEXT.md`.
6. Give your AI the context pack and sanitized target-project files. Review its assumptions before allowing writes.

For a web chatbot with no file access, upload **CHATBOT_STARTER.txt** first. It contains the operating contract and task format, not all lessons. Upload selected playbooks or a generated pack when needed. Do not assume the chatbot can open a ZIP, browse GitHub or run tests; ask it to report its capabilities.

## What is inside

| Location | Purpose |
|---|---|
| `core/OPERATING_CONTRACT.md` | Non-negotiable evidence, scope, authority and stopping rules |
| `workflows/` | Build, review, debug, research, maintain, mentor and job simulation modes |
| `playbooks/` | Backend/data, LLM/RAG, agents/MCP, security, evaluations, operations and optional ML |
| `templates/` | PRD, architecture/ADR, threat model, evaluation, review, incident and handoff contracts |
| `references/AUDIT.md` | Personalized critique, exact upstream citations, overlap and production gaps |
| `references/lesson_catalog.json` | All 523 observed lesson paths with preliminary role-specific classification |
| `curriculum/` | 17 outcome-based phases; full skill inventory; role and job-readiness audit |
| `assessments/` | Baseline assessment, grading contract and realistic job tasks; no answer key in starter |
| `labs/` | Deliberately broken, offline systems to diagnose; never deploy them |
| `forge.py` | Offline task state, context packs, evidence receipts, gates, skills and retrieval scoring |
| `tests/` | Tests of the workbench itself, not proof of future projects |

## What the local commands really verify

`check` rejects missing/failed gates, missing artifacts, changed evidence hashes, changed snapshot files, missing snapshot files, malformed state and unresolved critical/high findings. It validates the **recorded evidence contract**; it does not understand whether a test is good or a report is true. Receipts are local declarations, not signed attestations. Humans/independent CI must re-run commands, inspect coverage, verify the declared source-file scope and authorize releases. A malicious writer can change state and receipts. This is not a security sandbox.

`eval-retrieval` scores exported retrieval results with deterministic metrics. It does not call embeddings or a model and cannot grade factual generation. `skill-set` records a reviewer's declared evidence and assistance level; it cannot determine competence. `pack` composes instructions and relevant documents; it does not call an agent.

## Finish and resume

Use `python3 forge.py status --task support-pilot`. Save exact commands, commit, environment, failures and next action in `workspace/support-pilot/HANDOFF.md`. Read [COMMANDS.md](COMMANDS.md) for the full evidence lifecycle. A session is complete only when its scope is verified or a precise blocker is recorded. A project release additionally needs a human decision, real integration evidence, staging drills and a rollback plan.

## Provenance and portability

Based on the user's Applied AI Engineer prompt, selectively informed by Rohit Ghumare's [AI Engineering from Scratch](https://github.com/rohitg00/ai-engineering-from-scratch) at commit `d18b8fe5a913c46011a3b06cb6ebd6a924414fd3`, audited 2026-09-11. Original guidance and code here are not a copy of the complete upstream course. Catalog citations link to the pinned upstream snapshot; online lessons require internet. Read [references/AUDIT.md](references/AUDIT.md) and [references/SOURCES.md](references/SOURCES.md) for scope and qualifications.

This workbench is standalone inside a larger portfolio repository; `suite/` and `projects/` outside this folder are unrelated preserved work. No live services or paid infrastructure are created by this toolkit. See [SECURITY.md](SECURITY.md) before sharing evidence.
