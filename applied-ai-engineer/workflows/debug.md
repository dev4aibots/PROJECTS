# Evidence-led debugging

Use: Symptom -> Evidence -> Hypothesis -> Verification -> Root cause -> Fix -> Test -> Prevention.

1. Capture expected vs actual behavior, severity, affected tenants/time window, correlation IDs, sanitized requests, logs, traces, deployment/model/prompt/schema revisions and database state. Preserve evidence; stop harmful traffic using approved controls.
2. Reproduce in an isolated environment. Minimize the case without removing the failure. Separate live outage mitigation from a permanent fix.
3. Rank at least two plausible hypotheses. For each name evidence supporting/contradicting it and a cheap discriminating experiment. Avoid random edits and logging raw secrets.
4. Trace the full request: ingress -> identity -> data -> retrieval/model -> tool -> worker -> persistence -> response. Distinguish retries at each layer and correlate duplicates with idempotency keys.
5. Test one hypothesis at a time. If not reproducible, say so and propose safe instrumentation; don't invent a root cause.
6. Add a failing regression test, implement the smallest fix, run it and neighboring tests, and inspect rollback/compatibility implications.
7. Use templates/INCIDENT.md: timeline, impact, cause, contributing factors, mitigation, fix, detection gap, owner and preventive test/alert. Never blame an individual where system controls failed.

Mentor mode: supply symptoms, code, logs, request, database state and constraints; wait for the learner's nine-part investigation before revealing a diagnosis. See labs/ and assessments/BASELINE.md.
