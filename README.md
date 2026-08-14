# Applied AI Engineering Portfolio

Five focused proof-of-work projects demonstrating grounded RAG, agent orchestration, deterministic LLM security boundaries, multimodal extraction, and guardrail evaluation.

> **Current status:** active deployment-readiness work. Local verification is not presented as public production proof. Live URLs, screenshots and model metrics will be added only after hosted smoke tests pass.

## Flagship projects

| Project | Engineering signal | Current readiness |
|---|---|---|
| [DocuMind RAG + MCP](projects/documind-rag-mcp) | evidence-gated RAG, pgvector, provider fallback, REST + MCP, citation validation | strong local implementation; identity and hosted proof remain |
| [ZeroTrust SQL](projects/zerotrust-sql) | scope-aware SQLGlot policy, capability roles, private durable audit, distributed limits, attack corpus | credential-free source complete; owner-hosted role/provider proof remains |
| [LLMShield](projects/llmshield) | input/output guards, PII redaction, provider fallback, privacy-safe telemetry | current active project: auth, distributed limits and stronger held-out eval remain |

## Additional projects

| Project | Engineering signal | Current readiness |
|---|---|---|
| [StateGraph Agent](projects/stategraph-agent) | real LangGraph `StateGraph`, checkpointer, human interrupt/resume, memory isolation | real local orchestration added; durable Postgres/tools/auth remain |
| [DocuExtract](projects/docuextract) | Gemini byte/PDF structured extraction adapter plus independent Decimal verification | live provider path exists; persistence/ownership/live eval remain |

## Portfolio thesis

Models propose; deterministic code owns trust decisions. Across the projects this appears as citation membership, SQL AST policy, financial arithmetic verification, human approval interrupts, scoped ownership, output validation and explicit refusal.

## Readiness standard

“Deployment-ready” means a fresh clone passes tests/build/eval and launch needs no source edits—only cloud resources, migrations, credentials, deploy commands and live proof capture. See:

- [Master implementation plan](docs/IMPLEMENTATION_MASTER_PLAN.md)
- [Agent resume guide](docs/AGENT_RESUME_GUIDE.md)
- [Project registry](docs/PROJECTS.md)
- [Portfolio proof standard](docs/PORTFOLIO_STANDARD.md)

Every project has a detailed `docs/projects/<project>/DEPLOYMENT_READY_PLAN.md`, live checklist, proof record and resume pointer.

## Local verification

Run each project's documented commands from its folder. Counts in READMEs are dated local observations and may change as implementation expands. CI and hosted evidence are release gates, not implied here.

## Publication checklist

Before job applications promote only projects with: green CI, real hosted URL, tested identity/ownership, rate/size limits, live model/database smoke, dated eval artifact, three screenshots, 90–120 second demo, architecture diagram, limitations, license and contact links.

This repository contains fictional demo data only. Never commit credentials or personal documents.
