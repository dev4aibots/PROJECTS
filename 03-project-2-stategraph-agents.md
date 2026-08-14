# PROJECT 2 — StateGraph: Multi-Agent Orchestrator with Memory + Human-in-the-Loop

**Repo name:** `stategraph-agent`
**Days:** 4–5
**Hiring signal:** LangGraph (named in job listings), supervisor routing, durable state, long-term memory with pgvector, human approval workflow (the feature interviewers love), failure recovery.

> Paste `01-master-context.md` first, then this prompt.

---

```
==================================================
PROJECT SPECIFICATION
==================================================

PROJECT NAME: StateGraph — Stateful Multi-Agent Research Orchestrator

ONE-SENTENCE PITCH:
A supervisor-routed team of specialized LLM agents that researches a topic,
pauses for human approval on risky output, remembers user preferences across
tasks via semantic long-term memory, and survives crashes because every step
of state is persisted to Postgres.

WHY THIS EXISTS (README):
Single-prompt "agents" are demos. Production agent systems need durable
state, bounded autonomy, memory isolation, and a human veto. This project
demonstrates all four on serverless infrastructure — which forces the most
interesting engineering decision in the repo: checkpointing graph state to
Postgres so execution can resume across stateless function invocations.

==================================================
THE AGENT TEAM (exactly 4 — do not add more)
==================================================

Supervisor — routes based on typed state, never generates content itself.
Research Agent — decomposes the task, produces structured research notes
    (uses ONLY its own reasoning + the task input; NO live web search — state
    this limitation honestly in the UI and README: findings are
    model-knowledge-based, the architecture shows how a search tool would
    plug in via the tool registry).
Analyst Agent — turns notes into a structured analysis: key findings,
    comparisons, risks, confidence per finding.
Reviewer Agent — quality + risk check. Emits risk_flags. ANY risk flag
    (e.g., low-confidence claims, sensitive topic, contradictions) →
    requires_approval=true.
Writer Agent — only runs after approval (or when no risk was flagged);
    produces the final markdown deliverable.

Every inter-agent payload is a Pydantic model. Agents never exchange free
text where a schema is possible. Store every agent step in agent_events with
input/output summaries + duration + token usage.

==================================================
GRAPH & STATE (the heart of the project)
==================================================

Use LangGraph with a POSTGRES-BACKED CHECKPOINTER (langgraph-checkpoint-
postgres against the Supabase connection string; if it doesn't cooperate on
serverless, implement a minimal custom checkpointer that serializes graph
state into a graph_checkpoints table — either way, document the decision).

Graph:
  START → supervisor → research → supervisor → analyst → supervisor
        → reviewer → [risk?] → INTERRUPT (await approval) → writer → END
                   → [no risk] → writer → END

Requirements:
- thread_id == task_run_id. Any invocation is resumable by thread_id.
- Interrupts use LangGraph's interrupt/human-in-the-loop mechanism; the
  approval decision is injected on resume.
- Retry policy: each agent node retries once on transient LLM failure;
  second failure → task_run.status=failed with the stage recorded. NO fake
  final report from partial data — assert this in a test.
- Serverless execution model: POST /api/tasks starts the run and executes
  until it either finishes, hits the interrupt, or approaches the function
  time budget — persisting a checkpoint in each case. POST
  /api/tasks/{id}/resume continues from the checkpoint. The frontend polls
  status and auto-calls resume while status=in_progress. Document this
  "cooperative continuation" pattern in DECISIONS.md — top interview
  material.

==================================================
MEMORY (two layers, clearly separated)
==================================================

SHORT-TERM (per task run): the LangGraph checkpointed state — messages,
agent outputs, current node, error count, approval state.

LONG-TERM (across tasks, per user): after a run completes, a memory-
extraction step (LLM, structured output) proposes durable memories:
preferences ("user prefers tables over prose"), stable facts, past-task
summaries. Each memory → Gemini embedding → memories table (pgvector).
Before the research agent runs on a NEW task: embed the task, retrieve top-5
memories for THIS user_id above a similarity threshold, inject into context
with the label "Prior user context (may be irrelevant — ignore if so)".

MEMORY ISOLATION IS A HARD REQUIREMENT: every memory query filters by
user_id. Write a test that creates memories for user A and asserts user B's
retrieval never returns them. Mention this test in the README — data
isolation questions come up in every interview.

Demo users: seed two demo profiles (selectable via a dropdown, stored in
localStorage — no auth) so the demo video can SHOW memory isolation and
memory recall ("remembers I want competitor tables").

==================================================
DATABASE SCHEMA
==================================================

demo_users(id, name, created_at)                      -- 2 seeded rows
tasks(id, user_id, title, input, status, created_at)
task_runs(id, task_id, thread_id, current_node, status
          [pending|in_progress|awaiting_approval|completed|failed|rejected],
          error, started_at, completed_at)
agent_events(id, task_run_id, agent, event_type, input_summary,
          output_summary, duration_ms, token_usage, created_at)
approvals(id, task_run_id, reason, risk_flags jsonb, status, requested_at,
          resolved_at, resolution_note)
memories(id, user_id, memory_type, content, embedding vector,
          source_task_id, created_at)
graph_checkpoints(...)   -- per checkpointer choice

==================================================
API SURFACE
==================================================

POST /api/tasks                        {user_id, title, input}
GET  /api/tasks?user_id=
GET  /api/tasks/{id}                   status + latest run + result
POST /api/tasks/{id}/resume            idempotent (test double-resume!)
GET  /api/tasks/{id}/events            agent timeline
GET  /api/users/{id}/memories
DELETE /api/memories/{id}              user can prune memory
POST /api/approvals/{id}/approve       {note?}
POST /api/approvals/{id}/reject        {note?}
GET  /api/health

==================================================
FRONTEND
==================================================

/            Landing: pitch, agent-team diagram, feature cards
             (Durable state / Human veto / Semantic memory / Failure
             recovery).
/app         Dashboard:
             - user switcher (2 demo users)
             - new task form with 3 one-click example tasks
             - task list with status badges
/app/task/[id]
             - live agent timeline (poll 2s): per step → agent name, status
               icon, expandable input/output summary, duration
             - APPROVAL CARD when awaiting_approval: reason, risk flags,
               Approve / Reject buttons → timeline visibly resumes after
               approval (this is the demo-video money shot)
             - final result rendered as markdown
             - memory panel: which memories were injected into this run

==================================================
EVALUATION HARNESS
==================================================

evals/ pytest harness with mocked-LLM deterministic tests PLUS a small
live-run rubric:
- routing_correctness: given 6 synthetic state fixtures, supervisor picks
  the correct next node 6/6 (deterministic, mocked)
- schema_compliance: 20 recorded raw LLM outputs (fixtures, including 4
  malformed) → % parsed or correctly retried/failed
- interrupt_integrity: run → interrupt → simulate process death (new
  process) → resume → completes with consistent state
- memory_precision: 10 memory-retrieval queries against seeded memories →
  % of retrieved memories actually relevant (LLM-as-judge)
Write results to docs/evaluation.md; surface the table in README.

==================================================
FAILURE HANDLING (each gets a test)
==================================================

- LLM timeout mid-agent → retry → fallback provider → graceful fail
- malformed agent output → corrective retry → fail without corrupting state
- resume called twice concurrently → second call is a safe no-op (idempotency
  via status check + DB-level guard)
- resume on nonexistent/completed task → 404/409 structured errors
- rejection → run ends as rejected; writer NEVER ran (assert via agent_events)
- checkpoint write failure → surfaced, not swallowed

==================================================
PROJECT-SPECIFIC DOCS
==================================================

docs/state-machine.md — Mermaid stateDiagram of the graph incl. interrupt
docs/memory.md        — two-layer memory design, isolation guarantee, pruning
DECISIONS.md must cover: checkpointer choice, cooperative-continuation
pattern, why exactly 4 agents, why supervisor doesn't generate content,
why approvals are DB rows not just graph state.

Now begin with PHASE 0 (plan only, no code).
```

---

## Demo video beats
1. Create task as User A → agents execute live on the timeline
2. Reviewer flags risk → approval card → click Approve → graph resumes
3. Second task as User A → memory panel shows recalled preference
4. Switch to User B → show memories are empty (isolation)
5. Show Langfuse trace of the full run
