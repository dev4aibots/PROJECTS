# LLMShield — Security and Observability Gateway — Verified Brief

Project ID: `llmshield`  
Folder: `projects/llmshield`  
Brief status: `implemented and locally verified; owner deployment blocked`  
Last verified: `2026-08-12`

## Outcome

Protect LLM calls with independent request/response guards, privacy-aware logging, provider fallback, and traces that never break the data path.

## Acceptance scenarios

1. Clean or redacted prompt traverses guards, provider boundary, output checks, log, stats, and typed response.
2. Known multi-family injection or strict-policy PII blocks before provider execution.
3. Primary failure falls back; complete provider outage, empty output, oversized output, malformed input, and tracing outage return controlled behavior.
4. Frozen corpus reports injection and PII confusion matrices without hiding clean-prompt false positives.
5. UI demonstrates loading, empty, error, result, check, stats, and privacy-safe history states.

## Scope and constraints

- Injection scoring, PII detection/redaction with Luhn, provider fallback, output guards, optional Langfuse, Postgres migration, attack corpus.
- FastAPI backend, Next.js frontend, tests/evals, decision records, and deployment handoff.
- No agents, vector database, file uploads, paid infrastructure, production auth, or fabricated live metrics.
- Provider calls remain mockable and local proof does not imply provider/database/tracing/deployment availability.

## Definition of done

The API/UI flow, failure handling, tests, evaluation, docs, production build, and adversarial audit pass with recorded proof. This local definition is met. Public completion remains blocked until the owner configures credentials/resources, deploys, and records a successful live smoke.
