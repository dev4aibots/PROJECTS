# Requirements and assumptions

## User commitments mapped to artifacts
| Request | Implementation contract | Evidence |
|---|---|---|
| Three impressive usable platforms | PRDs for ClientFlow, SupportDesk AI, InvoiceHub; sequential delivery | Product release tasks CF-08, SD-05, IH-05 |
| Zero-context resumption | AGENTS → START_HERE → STATUS → HANDOFF → per-project FILES | State verifier, Git checkpoint, next-action command |
| Documentation before code | Product, stack, architecture, schema, testing, design and learning plans first | DOCS milestone |
| File-by-file tracking | FILES ledger lists path, exports, purpose, gate and status | Read against actual filesystem; no unchecked blanket claims |
| Credentials/deploy last | Local services and fixtures for development; remote setup in FINAL | No unfinished source code assigned to owner |
| Understand A–Z | Shared curriculum + implementation-specific learning maps and exercises | Explain/change/debug/revert demonstrations |
| Industry-quality UI | Product-specific design tokens, keyboard UX, mobile and a11y testing | Screenshots, Playwright, axe, manual audit |
| Free stack | Open-source libraries, personal Vercel demos, one Supabase Free project | Dated constraints in RESEARCH; optional paid operations never required for demo |
| Portfolio and interview support | Demo scripts, architecture tradeoffs, bug case studies | Evidence-linked claims only |

## Defaults adopted, not questions left blocking work
- English UI, UTC storage, locale-aware display. Target current desktop/mobile browsers. WCAG 2.2 AA is a target, not a certification.
- Three independent Next.js applications in one repo; deploy separately. One shared Supabase project for portfolio economy. Shared identity is intentional; each workspace belongs to exactly one product.
- Authentication: GitHub OAuth first (no SMTP requirement), email/password plus recovery when SMTP is configured. Never disable email confirmation to fake a working signup.
- No subscription billing, payment processing, bank feeds, medical data, or government invoice compliance. InvoiceHub records manually reported payments; it does not move money.
- Demo data is synthetic and explicitly labeled; visitor changes remain in a browser session in early UI milestones. Live mode is a separate verified backend path.
- SupportDesk v1 accepts pasted text / small UTF-8 text or Markdown documents. PDF parsing/OCR, arbitrary website crawling, messaging integrations and autonomous actions are later extensions, not silently promised.
- ClientFlow invitation delivery starts with copyable expiring links; email transport is optional. Links still require authenticated verified-email acceptance.
- Limits default small: page size 25, project title 100 chars, comment 4,000 chars, file 5 MiB; SupportDesk document 100 KiB, question 2,000 chars, bounded retrieval and provider tokens. Validate at server and DB.
- Certificates are educational context, not fabricated qualifications. Do not generate a certificate or claim a course completed.

## Scope-change policy
User changes get an explicit decision entry, affected tasks and migration impact. Do not expand scope merely to look sophisticated. Reliability, accessibility, evidence and comprehension are the impressive features.
