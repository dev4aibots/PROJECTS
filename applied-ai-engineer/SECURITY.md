# Security and limitations

The workbench is local advisory tooling. Markdown rules, JSON gates and hashes are not access control, tamper-proof attestation, or a sandbox. The same local user can rewrite all of them. Protect real CI/release rules with branch protection, reviewer ownership and independently controlled runners.

The CLI deliberately does **not** execute commands from task files, fetch URLs, call providers, deploy, install dependencies or run an autonomous loop. Receipts record execution performed by the operator/host; independently inspect and rerun them. Filesystem containment checks reject ordinary path traversal and symlink escape but cannot protect against a malicious concurrent filesystem writer or hostile OS. Single-writer task directories only. Do not use the tool as a multi-user service.

Do not store API keys, bearer tokens, patient/customer records, passwords, personal contact lists or production prompts in context packs. Sanitize evidence before hashing and exporting. Built-in checks are not comprehensive secret detection; manually inspect the allowlisted export. Even a redacted transcript can contain identifying context.

Untrusted repos and packages can execute code through imports, tests, hooks, build scripts and containers. Read first; run inside an appropriate disposable sandbox with no secrets, least filesystem access, restricted network and resource limits. The intentionally broken labs are offline exercises, not deployable applications.

Never trust a tenant ID from model arguments. Reauthorize in business code at execution time. Enforce membership on SQL, retrieval, caches, background jobs, object storage, exports and notifications. Use non-owner database roles for RLS tests; owners and BYPASSRLS can bypass policies. Validate output before client rendering or tool dispatch; raw HTML/SQL/shell output is not a safe fallback.

Human approvals in JSON are declarations, not authenticated approval records. A real product needs an identity-bound approval store, authorization checks and audit trail. A gate result does not authorize deployment, payment, data deletion or outbound communication.
