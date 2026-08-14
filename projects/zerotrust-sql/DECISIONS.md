# Engineering Decisions

1. **AST validation, not regex.** SQLGlot exposes statement, table, column, function, CTE, and subquery structure; regex is retained only for non-authoritative input flagging.
2. **Allowlists, not blocklists.** The supported schema and functions are finite. Unknown capabilities fail closed.
3. **Restricted role after validation.** Validators can contain bugs; the database role grants SELECT on only four tables, enforces read-only transactions, and times out work.
4. **AST LIMIT rewrite.** Structural rewriting avoids invalid concatenation after semicolons/comments and makes the executed query explicit.
5. **Blocked requests return a 200 envelope.** Blocking is a successful security outcome, and the same typed envelope lets the UI show all checks. Invalid input and unavailable dependencies still use 4xx/5xx.
6. **Deterministic local provider.** It proves the complete security path without credentials, but does not claim live-model quality.
7. **Process-memory local audit.** It keeps offline tests simple; hosted mode must write the migration-backed audit table.
