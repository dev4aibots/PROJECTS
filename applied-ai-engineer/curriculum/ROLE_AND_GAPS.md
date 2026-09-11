# Personalized role and job-readiness audit

## Recommended target

**Applied AI Engineer with a strong AI Backend Engineering specialization**, building multi-tenant AI employees, integrations and SaaS. A secondary client-facing title is **AI Solutions Engineer**, provided you can deliver secure implementations rather than only demos. This is a target, not a claim that you are already senior.

Your reported n8n/Make/API/Docker/Linux/SaaS exposure is useful for mapping business workflows and shipping integration slices. The main risk is outsourcing core decisions to coding agents without being able to diagnose their failures. International client work also needs written acceptance criteria, access/data agreements, cost ownership, time-zone handoffs and support boundaries; English polish does not replace technical evidence.

| Role | Fit now as a target | Why / additional evidence |
|---|---|---|
| Applied AI Engineer | Primary | End-to-end AI product outcomes, evaluation and maintenance match your intended work |
| LLM Engineer | Good specialization | APIs, RAG, context and evals; title can sometimes include fine-tuning/model serving, clarify job scope |
| AI Backend Engineer | Primary technical spine | FastAPI, PostgreSQL, Redis, queues, tenant/auth boundaries and integrations |
| AI Platform Engineer | Later | Requires demonstrated shared infrastructure, governance, SRE, provisioning and multi-team operations |
| AI Automation Engineer | Useful entry/commercial overlap | n8n/Make strength; add versioning, replay, secrets, testing and robust backend state |
| AI Agent Engineer | Product specialization, not default architecture | Need bounded actions, evaluation, state and human escalation; avoid autonomous-by-default design |
| ML Engineer | Optional later branch | Needs independent datasets, leakage prevention, training/serving/drift competence beyond using APIs |
| Research Engineer | Not current target | Math-heavy model experiments/training are misaligned with stated priorities |
| AI Solutions Engineer | Strong client-facing option | Requires requirements discovery, proposals, demos, tradeoffs, integration ownership and handover |

## What is already reported covered

API/backend flow, authentication vs authorization, tenant isolation/IDOR, service/repository layers, PostgreSQL/Redis/queues, LLM APIs/context, RAG/retrieval metrics, tools/agents/state/MCP, guardrails, evaluation, observability, reliability and performance. Practical exposure also reported to automation, Docker/Linux/Git/Next.js and deployment. Do not restart these as vocabulary lessons without an assessment.

## What is superficial?

**Unknown.** You reported coverage, not demonstrated depth. It would be dishonest to name specific skills as proven superficial. High-risk validation candidates: tenant identity through workers/vector/cache paths; SQL transactions/migrations/constraints; duplicate external effects; async cancellation; real integration tests; evaluation leakage; restore/rollback; measuring p95 and cost. Failure in these assessments determines targeted remediation.

## Critical evidence missing

| Responsibility | Required proof | Next action |
|---|---|---|
| Understand/design | Independent requirements and data-flow diagram with alternatives | Baseline architecture section |
| Implement/review | Small tenant-isolated endpoint, transactions and adversarial tests, explain AI-generated diff | Phase 2/3 vertical slice |
| AI quality | Versioned holdout, retrieval/generation/tool metrics, abstention and error analysis | Phase 5/9 evaluated support pipeline |
| Debug | Reproduction, ranked hypotheses, discriminating test, fix and regression | Broken labs then unfamiliar bug |
| Operate | Deployed staging, alerts, provider outage, backup restore, rollback and budget evidence | Phase 10/11/13 drills |
| Communicate | PR, ADR, incident report and operator handoff another engineer can follow | Job simulation |

Current verdict: **job readiness not established**, not 'unemployable'. Strong vocabulary is plausible but not independently assessed. Employment depends on evidence and role scope, not completion counts. Seniority cannot be conferred by a prompt.

## Exact next phase and progression

Take Phase 0 / assessments/BASELINE.md. Budget 90–120 minutes for the initial independent assessment, then a separately timed guided repair. If API/security reasoning is sound, skip introductory lectures and implement Phase 2/3. If Python code-reading fails, remediate Phase 1 narrowly. If security fails, block external writes and remediate the boundary before capstone autonomy. Scores update only after observed work.

Use the 17-phase roadmap as a competency map, not a compulsory linear course. Thread security/testing/observability into every phase; introduce architecture during baseline and revisit at Phase 14. Default portfolio: one strong multi-tenant support/AI employee platform plus two substantial debugging/integration case studies, not dozens of toy chatbots.
