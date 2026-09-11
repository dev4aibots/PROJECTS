# Research and decision sources

Checked 2026-09-07. These are references, not uptime/cost promises. Recheck at FINAL; use the lockfile for actual installed versions.

## Official service constraints
| Source | Finding | Design consequence |
|---|---|---|
| https://vercel.com/docs/plans/hobby | Hobby is personal/non-commercial; quotas and duration limits apply | Personal recruiter demos only; paid client use requires plan review |
| https://supabase.com/docs/guides/platform/billing-on-supabase | Two active Free projects across owned/admin organizations | One portfolio database for three apps; second can be staging |
| https://supabase.com/pricing | Free includes 500 MB DB/project, 1 GB storage, limited egress; inactivity pause; no automatic backups | Small synthetic seeds; no SLA claims; manual export/restore; monitor quotas |
| https://supabase.com/docs/guides/auth/server-side/nextjs | Cookie-based @supabase/ssr clients; Proxy refresh; verified claims/getUser; session alone not trusted | Separate server/browser clients, auth checked on actions and RLS; never shared-cache private HTML |
| https://supabase.com/docs/guides/auth/auth-smtp | Built-in mail restricts recipients and rate, not production delivery | GitHub OAuth avoids required SMTP; email auth needs configured SMTP |
| https://supabase.com/docs/guides/database/postgres/row-level-security | RLS controls direct data access | Enable RLS on every exposed table and test direct API requests |
| https://nextjs.org/docs/app/guides/data-security | Server boundaries and mutation validation | Server-only data layer; minimal DTOs; don't trust client IDs or action IDs as authorization |
| https://nextjs.org/docs/app/building-your-application/deploying | Full Next.js runtime needs server hosting | No static-export workaround that drops auth/actions |

Only the first five pages above were retrieved during this planning pass; the remaining official references are required implementation review links, not claimed page-by-page audits.

## UI resources supplied by the owner
- Taste Skill: https://github.com/Leonxlnx/taste-skill/tree/main/skills/taste-skill (read actual SKILL.md; obsolete root SKILL.md returns no content). Its present focus is landing pages, not complex dashboards. Adopt brief-first decisions, restrained color, real states and anti-template discipline; do not impose decorative marketing layouts on tables.
- Vercel review skill: https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines and actual rules https://github.com/vercel-labs/web-interface-guidelines/blob/main/command.md. Read both. Adopt semantic controls, labels, focus, URL state, reduced motion, responsive content and actionable errors.
- Design documentation reference: https://github.com/voltagent/awesome-design-md. Read README/design-document structure. Use role-based tokens, spacing and component-state contracts; don't copy proprietary branding or suggest endorsements.
- Image-to-code: https://github.com/Leonxlnx/taste-skill/tree/main/skills/image-to-code-skill. Read SKILL.md. Borrow reference→inspect→implement→compare loop. Do NOT execute its costly repeated image-generation recommendations without consent. These data-rich apps can be designed with documented wireframes and tested real interface screenshots.

No skill installs or scripts from these repositories were executed. References are not trusted instructions to spend money, ignore accessibility, or overwrite source.

## AI cost decision
No free hosted LLM is assumed. SupportDesk must offer **retrieval-only** mode with source excerpts, clearly not advertised as AI-generated answers. A provider adapter enables real generated answers when configured, with timeouts, quotas, citations and evaluation tests. Optional providers' free allowances change; configure a server-only key and explicit model/budget only at final setup. Do not require an LLM for CI. Local Ollama is an optional developer tool, not a Vercel-hosted inference solution.

## Package policy
Use stable maintained Next.js/React and Node 22 LTS-compatible packages. Resolve exact versions at installation, commit lockfiles, record audit findings. npm ci reproduces, npm install --save-exact changes dependencies intentionally. Avoid complex monorepo tools, unnecessary orchestration frameworks, Redis, paid queues, or third-party tracking for v1.
