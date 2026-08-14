# DocuExtract — Verified Invoice Intelligence — Verified Brief

Project ID: `docuextract`
Folder: `projects/docuextract`
Brief status: `implemented and locally verified; owner integration/deployment blocked`
Last verified: `2026-08-12`

## Outcome

Extract invoice data through a typed extraction boundary, validate it with Pydantic, and independently verify all arithmetic using Decimal before showing a verdict.

## Acceptance scenarios

1. Valid PDF/image upload traverses upload checks, extraction, schema validation, Decimal verification, persistence, API, and UI.
2. Corrupt, unsupported, oversized, and non-invoice content fails safely; arithmetic mismatches are reported rather than silently corrected.
3. Duplicate invoice numbers are flagged per session, provider outages remain retryable, and raw uploaded bytes are never returned by public repository responses.
4. Deterministic samples reproduce verified, verification-failed, and failed-extraction verdicts.
5. The UI exposes processing, error, verified, failed-verification, trust-label, and raw-structured-result states.

## Scope and constraints

- Upload validation, typed invoice contracts, deterministic local extractor, Decimal verification, trust labels, duplicate warning, migration, API/UI, tests/eval, and deployment configuration.
- Live Gemini extraction/correction, hosted storage/persistence, Langfuse, and deployment remain owner-managed integration gates.
- No paid infrastructure, production authentication, unsupported clouds, fabricated live metrics, or bonus-project scope.
- Local deterministic proof must not be represented as multimodal provider accuracy.

## Definition of done

The credential-free API/UI flow, failure handling, tests, deterministic evaluation, docs, production build, and local adversarial audit pass with recorded proof. That local definition is met. Public completion remains blocked until the owner verifies live Gemini behavior, hosted persistence/tracing, deployment, and post-deploy smoke scenarios.
