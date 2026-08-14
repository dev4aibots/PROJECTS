# Security Model

## Attackers

A hostile user, prompt-injected context, or an unreliable model may propose destructive, exfiltrating, multi-statement, or resource-abusive SQL.

## Layers

1. Input length/empty checks and suspicious-phrase logging.
2. Static allowlisted schema context; no live introspection and no decoy exposure.
3. Structured generation with one malformed-output retry and provider fallback.
4. SQLGlot parse, one-statement, SELECT-only, table, column, function, and export checks.
5. AST-enforced maximum 100 rows.
6. Read-only role/transaction, narrow grants, and five-second timeout.
7. Structured audit events without exposing stack traces.

## Residual risk

Valid SELECTs can still enable aggregate inference, expensive joins, timing leakage, or business-data exposure. Production requires authentication, per-tenant authorization, rate limits, query-cost controls, log retention rules, and monitoring. The local SQLite layer is evidence of behavior, not proof of hosted Postgres grants.
