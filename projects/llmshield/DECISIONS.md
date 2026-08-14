# Architecture Decisions

## Score injection families instead of binary phrase blocking

One normalized family hit warns and two or more block. This preserves evidence for suspicious phrases while reducing false positives from ordinary discussions of “instructions” or “systems.” Patterns live in YAML for review and corpus testing. Novel semantic attacks remain outside this heuristic boundary.

## Hash prompts; never persist plaintext in v1

Request logs store SHA-256 and operational metadata. This supports correlation and aggregate reliability proof without creating a prompt-content data store. `LOG_PROMPTS` remains reserved rather than silently enabling a risky mode; production plaintext debugging should require a separately reviewed retention policy.

## Redact PII before provider egress by default

`PII_POLICY=redact` produces a warning and replaces detected values. `block` supports strict deployments; `warn` intentionally sends the original prompt and must be selected explicitly. Output PII is always redacted before release.

## Keep observability fail-open

Trace IDs are issued for correlation on every request, including blocks and failures. Langfuse submission is wrapped so telemetry outages emit a warning but cannot take down the data path. This trades guaranteed trace delivery for request availability.

## Use explicit provider fallback

Live mode uses Groq first and Gemini second when both keys exist. Transient or malformed provider responses cross a typed boundary and never leak raw payloads. Deterministic mode is a visible local adapter, not an inferred live-provider claim.

## Use repository adapters

Memory persistence is sufficient for credential-free tests and is labeled process-local. Postgres uses connection-per-operation behavior suitable for serverless functions; statistics are computed in SQL and the migration enables RLS while requiring a server-only role.
