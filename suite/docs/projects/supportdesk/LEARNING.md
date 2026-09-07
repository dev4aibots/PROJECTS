# SupportDesk learning guide (planned)

## Core concepts
RAG means retrieving relevant source information before asking a model to generate an answer. Retrieval-only returns matched excerpts without generation. They are different modes with different costs and failure cases. Similarity/full-text rank is not calibrated probability of truth.

Ingestion prepares sources → retrieval scopes/searches them → generation optionally synthesizes → citation validation rejects invented IDs → UI exposes evidence → human handoff covers uncertainty. Database isolation must happen before model input; a prompt saying “don't leak data” is not authorization.

## Code-reading order when built
Source validator/chunker → retrieval query and its RLS → message transaction/idempotency → provider adapter → citation validator → rendered thread. At each step trace one source ID and conversation ID. Examine which data reaches third-party provider and what is logged.

## Interview questions and answer guides
**Why full-text search instead of vectors first?** Simpler and free within Postgres, no embedding API required, good baseline for short FAQs. Measure recall on a dataset; vectors become justified only if they improve observed results.

**What prevents hallucination?** Nothing guarantees zero hallucinations. Constrain context, validate references, evaluate answers, show sources and hand off; distinguish citation validity from semantic entailment.

**What if the provider fails?** Preserve customer message, record safe error, offer retrieval excerpts/human handoff explicitly. Never replace failure with an unlabeled fake answer.

**What if two workers process one message?** Unique client_request_id plus transactional state prevents duplicate persisted results; provider-call reservation/retry rules limit duplicate spend. Avoid in-memory locks in serverless.

**How do you stop prompt injection?** Treat document instructions as data, provide no powerful tools/secrets, isolate tenant retrieval, constrain outputs and test attacks. Input filtering alone cannot guarantee prevention.

**What happens on human handoff?** State changes to needs_human; later generated response checks version/state and is not published if human ownership changed. Teammate response is auditable.

## Exercises
Add a new refusal test for a missing policy; unpublish source and verify immediate retrieval removal; simulate provider timeout; replay request ID; test foreign conversation token; calculate retrieval recall on 20 labeled questions. Explain results, do not invent accuracy percentages.

## Presentation
Show one known answer with cited text, one unsupported question handed off, and a malicious/cross-tenant test. Say which provider mode was actually tested. Until built, this document is the learning plan, not project evidence.
