# Observability

One UUID trace ID is issued per gateway request, including blocked requests and provider failures. The in-process trace records `input-guards`, `llm-call`, and `output-guards` spans with policy metadata only—never prompt or answer content.

When Langfuse keys are configured, the HTTP sink submits a trace and child spans through the ingestion API. Submission is deliberately fail-open: connection, authentication, quota, or schema failures produce a sanitized warning containing only the exception class; they cannot fail the gateway request. The test suite injects a sink that always raises and proves the primary path still returns `200`.

Request logs persist prompt SHA-256, status, blockers, provider, fallback use, latency, optional token usage, and timestamp. Aggregate stats derive from those fields. Local memory logs and UUIDs prove application correlation only; they do not prove durable storage or a real Langfuse trace.

## Owner live verification

1. Configure Langfuse keys and host.
2. Send one clean, one blocked, and one forced-fallback request.
3. Confirm trace IDs match the API envelopes.
4. Confirm blocked traces contain no `llm-call`; fallback traces name the serving provider.
5. Confirm no prompt/answer plaintext exists in metadata.
6. Temporarily use an invalid host and confirm the gateway remains available.
