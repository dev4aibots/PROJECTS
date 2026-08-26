# BRIEF — P3 DuraSupport (frozen spec)

**Dir** `projects/03-durable-support` · **Stack** Node serverless (zero deps) · **Signal:** durable pause/resume workflows across human Slack approvals with zero server timeouts.

## Architecture — a durable state machine, not a long-running process
```
POST /api/tickets {customer, email, subject, body}
  → step RETRIEVE: score seeded KB articles (token-overlap cosine-ish similarity) → top-3 context
  → step DRAFT: GROQ_API_KEY → Llama 3 drafts reply w/ KB context; else template composer from KB
  → step CLASSIFY: billing/refund/cancellation keywords or LLM intent → sensitive?
  → sensitive → status AWAITING_APPROVAL, workflow state + draft persisted, Slack interactive msg sent.
       ZERO compute while paused (state lives in store; serverless fn already returned).
  → POST /api/approve {ticket_id, action: approve|edit|reject, edited_reply?} → resume:
       approve/edit → step SEND (simulated email) → RESOLVED; reject → ESCALATED_HUMAN
  → non-sensitive → auto-send → RESOLVED
Every step appended to ticket.timeline[{step, status, at, detail}].
```

## Endpoints
`POST /api/tickets` · `GET /api/tickets` · `GET /api/tickets?id=` · `POST /api/approve` · `GET /api/health`.

## Dashboard
Ticket form + samples ("Where are my API docs?" → auto-resolve; "I want a refund" → approval gate) · timeline stepper per ticket · manager approval panel mimicking the Slack message (Approve / Edit / Reject buttons wired to /api/approve) · KB panel · raw JSON toggle.

## Acceptance
smoke test: refund ticket pauses at AWAITING_APPROVAL, approve resumes → RESOLVED, reject → ESCALATED_HUMAN, docs ticket auto-resolves; timeline complete.
