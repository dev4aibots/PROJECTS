# SupportDesk AI — product requirements

## Problem
Small businesses need traceable support answers based on their own published information, with a reliable handoff when the system cannot answer. Target users: business owner, support teammate, customer. Not an autonomous multi-agent business operator.

## v1 acceptance stories
| ID | Story | Acceptance |
|---|---|---|
| SD-P1 | Owner configures a business workspace | Auth and roles; only own workspace knowledge/inbox |
| SD-P2 | Owner uploads/pastes FAQ knowledge | UTF-8 TXT/MD, max 100 KiB; validate/normalize/dedupe; publish/unpublish source; error states |
| SD-P3 | Customer asks a question | Retrieve only public active source chunks for this business; show excerpts/citations or no-answer |
| SD-P4 | Configured AI synthesizes an answer | Server adapter, bounded prompt, only returned source IDs accepted, no secrets/tools, fallback is explicitly retrieval-only/error, not fake generation |
| SD-P5 | Customer needs human help | Conversation becomes needs_human; new AI responses stop until reopened; teammate response persisted |
| SD-P6 | Customer opts into follow-up | Explicit consent + email validation, saved lead within own conversation/workspace; no silent PII collection |
| SD-P7 | Team manages inbox | Filter open/needs_human/resolved, assignment, persisted messages, accessible thread/source layout |
| SD-P8 | Owner understands performance | Actual counts for answer modes, handoffs, unanswered and response failures; no invented satisfaction score |

## Scope and edge cases
One agent per workspace; no payments or actions on behalf of customer. No automatic refunds, external browsing, SMS, WhatsApp, voice, PDF OCR or agent swarm. Retrieval uses Postgres full-text search first; pgvector only as a measured later decision. Unsupported language/empty/noisy input returns explanation, not confident hallucination.

Document deletion/unpublish removes retrieval eligibility immediately; recorded past citations retain safe historical title/snippet snapshots according to retention policy. Duplicate message idempotency key returns existing result. Concurrent replies must serialize handoff state. AI/provider error preserves customer message and offers human handoff/retry. Rate limits shared across serverless workers in DB; server-memory counters are insufficient.

## Privacy and limits
Synthetic data for public portfolio. Lead consent timestamp; owner can export/delete according to documented retention. Questions 2,000 chars; top 5 chunks, bounded combined source characters and output tokens. No raw documents in logs. Public widget gets no direct database read privilege.

## Success criteria
All auth/RLS and widget-token attacks denied; evaluation examples prove source retrieval and refusal behavior for known/unknown questions. Real provider quality is measured separately from deterministic unit tests. Retrieval-only mode is useful and honest, but is NOT marketed as generated AI.
