# ⏸️ DuraSupport — Durable Pause/Resume AI Support Workflows

> **The problem:** AI support agents that auto-send refund confirmations or cancellations are a liability. But holding a serverless function open while a manager decides is impossible — functions time out in seconds. **DuraSupport solves it with durable execution:** the workflow persists its full state at the approval gate and *returns* (zero compute while paused). A later webhook resumes it exactly where it stopped.

## Architecture — a durable state machine, not a long-running process

```
POST /api/tickets {customer, email, subject, body}
  → RETRIEVE   score seeded KB (token-overlap similarity) → top-3 context
  → DRAFT      GROQ_API_KEY set → Llama 3.3 drafts with KB context
               else → deterministic template composer (demo mode)
  → CLASSIFY   refund / cancellation / billing-dispute patterns → sensitive?
  ├─ sensitive → status AWAITING_APPROVAL, state persisted, Slack notified.
  │             ⏸ ZERO compute while paused — the function already returned.
  │             POST /api/approve {ticket_id, action} resumes:
  │               approve / edit → SEND → RESOLVED
  │               reject         → ESCALATED_HUMAN
  └─ non-sensitive → auto SEND → RESOLVED

Every transition appended to ticket.timeline[{step, status, at, detail}] — a full audit log.
```

## Quickstart (zero keys needed)

```bash
cd projects/03-durable-support
npm run dev            # → http://localhost:3003
npm test               # zero-dep smoke suite
```

## API

| Endpoint | Description |
|---|---|
| `POST /api/tickets` | Ingest a ticket, run the workflow until done or paused |
| `GET /api/tickets` | List all tickets with statuses |
| `GET /api/tickets?id=tkt_0002` | One ticket with full timeline |
| `POST /api/approve` | `{ticket_id, action: approve\|edit\|reject, edited_reply?}` — resume a paused workflow |
| `GET /api/health` | Mode, integrations, KB size |

### Try it

```bash
# Auto-resolving ticket (non-sensitive)
curl -s -X POST localhost:3003/api/tickets -H 'content-type: application/json' \
  -d '{"customer":"Ada","email":"ada@example.com","subject":"API docs?","body":"Where are the API docs and auth tokens?"}'
# → status: RESOLVED, sent_reply populated

# Sensitive ticket — pauses
curl -s -X POST localhost:3003/api/tickets -H 'content-type: application/json' \
  -d '{"customer":"Grace","email":"g@example.com","subject":"Refund","body":"Double charged, refund please"}'
# → status: AWAITING_APPROVAL

# Resume it
curl -s -X POST localhost:3003/api/approve -H 'content-type: application/json' \
  -d '{"ticket_id":"tkt_0003","action":"approve"}'
# → status: RESOLVED   (second call → 409: idempotency guard)
```

## Environment variables (all optional — demo mode without them)

| Var | Effect when set |
|---|---|
| `GROQ_API_KEY` | Replies drafted by Llama 3.3 70B with KB context |
| `SLACK_WEBHOOK_URL` | Real Slack message on every approval gate |

## Interview talking points

1. **Why not Temporal/Inngest?** Same durable-execution concept, zero infra: state in a store, resume via webhook. Demonstrates the *pattern* those platforms productize.
2. **The 409 guard matters:** a manager double-clicking "Approve" in Slack must not email the customer twice. Status-gated resume = idempotency.
3. **Why classify with patterns first?** Deterministic, auditable, free. The LLM path can extend it, but "is this a refund?" must never be probabilistic-only in a payment path.
4. **Timeline as audit log:** every transition timestamped — exactly what a compliance reviewer or a debugging engineer needs.
5. **State store honesty:** in-memory per serverless instance for the demo; the store module is a 20-line swap for Postgres/Supabase (`DATABASE_URL`) in production.
