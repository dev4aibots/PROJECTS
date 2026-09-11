# Security and verification gates

## Role matrix (deny unless explicitly allowed)
| Action | Owner | Admin | Member | Client | Anonymous |
|---|---|---|---|---|---|
| Read internal workspace projects | Yes | Yes | Yes | No; linked portal projects only | No |
| Create/update projects/tasks | Yes | Yes | Yes | No | No |
| Manage clients | Yes | Yes | No | No | No |
| Invite/remove normal members | Yes | Yes (not owners/admins) | No | No | No |
| Transfer owner/delete workspace | Yes; last-owner invariant | No | No | No | No |
| Read internal comments/files | Yes | Yes | Yes | No | No |
| Read portal-visible comments/files | Yes | Yes | Yes | Linked project only | No |
| Submit portal request/comment | Yes | Yes | Yes | Linked project; portal visibility only | No |
| View support inbox / draft answer | Yes | Yes | Yes | N/A | No |
| Issue invoices / record payments | Yes | Yes | No; draft editing only | N/A | No |

Support public widget is separately scoped to one business public knowledge base and one opaque conversation token; not membership or direct table access. It must not expose private inbox or documents. No public widget before rate/size/budget controls exist.

## Adversarial cases required
- User A forges workspace/project/client/file/message/invoice ID from B; reads/writes denied through both app and direct API.
- User who belongs to A and B tries cross-workspace FK insertion; DB rejects.
- Anonymous, expired session, removed member, downgraded role, unknown app, forged client_id.
- Client reads internal-only comment/file or changes `visibility` to internal; denied. A client with multiple portals still cannot see another client.
- Invite replay/expiry/email mismatch/role escalation, simultaneous last-owner removal.
- Private Storage URL guesses and signed-URL issuance without membership; foreign object delete; disallowed type/size, dangerous HTML/SVG served inline.
- Malicious document says ignore instructions or reveal other tenant data; retrieval scope enforced before model. Model never gets secrets or write tools.
- Duplicate support requests/payments, concurrent invoice issuing, stale task versions, provider timeouts, malformed provider responses.
- CSV formula injection, XSS strings in names/comments/PDF, open redirect to attacker domain, path traversal in filename.

## Test pyramid
| Level | Tool / purpose | Cannot prove |
|---|---|---|
| Unit | Vitest: validation, money, statuses, search, provider parsing | RLS or deployed auth |
| SQL integration | Local Supabase/Postgres: grants, constraints, functions, policies under anon/authenticated roles | Hosted SMTP, real OAuth settings |
| Service integration | App + local Supabase: sessions, mutation failures, pagination | Provider real-world answer quality |
| Browser | Playwright: user flows, mobile, reload, keyboard, error behavior; axe | Full accessibility compliance |
| Hosted smoke | Owner's final Vercel/Supabase: redirects, sessions, isolation, files, PDF | Unlimited load or third-party audit |

No real keys in CI. Fake provider fixtures are named fixtures. At least one explicit failure-path assertion for each stateful operation. CI should lint/typecheck/unit/build; browser and local Supabase jobs can be separate. A skipped DB test is a release blocker, not green coverage.

## Review and production code-complete checklist
- [ ] No service/admin key in browser bundles or application requests.
- [ ] All public-schema tables have RLS and restrictive grants; every policy tested.
- [ ] Authenticated pages not shared-cached; refresh cookies preserved; server actions reauthorize.
- [ ] Zod limits match SQL; integrity enforced transactionally; 409 conflict UX.
- [ ] Upload allowlist and bucket RLS; signed URLs expire; no unsafe inline attachments.
- [ ] Server-rendered strings escaped; no raw HTML from model/documents.
- [ ] Persistent DB-based quotas for public endpoints; no process-memory limiter as production control.
- [ ] Structured redacted logs and request IDs; errors safe but actionable.
- [ ] Secrets scanner/dependency audit findings triaged; lockfiles committed.
- [ ] Keyboard, focus, labels, contrast, zoom, 375px/1440px screenshots checked.
- [ ] Backup exported/restored in isolated test environment; limitations documented.
- [ ] Owner setup runbook tested from fresh clone; generated DB types match migrations.
- [ ] All product acceptance tests and documentation match implementation.
- [ ] Hosted credential checks tracked separately in FINAL.

Production-grade is a goal and review standard, not a certification. External security review is recommended before handling real customers or sensitive documents.
