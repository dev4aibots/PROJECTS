# SupportDesk planned file ledger

Relative to `suite/apps/supportdesk/`. No application files exist until SD-01. Add exact routes/components at each task start. Common Next config/test files follow ClientFlow patterns with independent package lock; do not copy credentials or unrelated business logic.

| File | Symbols / contract | Gate | State |
|---|---|---|---|
| package.json | independent scripts/dependencies | SD-01 | planned |
| package-lock.json | reproducible exact versions | SD-01 | planned |
| src/app/layout.tsx | brand and root boundaries | SD-01 | planned |
| src/app/app/[workspaceId]/inbox/page.tsx | authorized conversation list | SD-01 | planned |
| src/components/inbox.tsx | queue/thread/source layout | SD-01 | planned |
| src/lib/conversations.ts | allowed state transitions | SD-01 | planned |
| src/lib/knowledge/ingest.ts | size/type normalize/hash/chunk | SD-02 | planned |
| src/lib/knowledge/retrieve.ts | tenant-scoped published retrieval | SD-02 | planned |
| src/app/app/[workspaceId]/knowledge/actions.ts | authorized ingestion/publication | SD-02 | planned |
| src/lib/ai/answer.ts | mode orchestration and no-answer path | SD-03 | planned |
| src/lib/ai/provider.ts | server-only request timeout/schema validation | SD-03 | planned |
| src/lib/ai/citations.ts | subset validation and DTO | SD-03 | planned |
| src/app/api/support/[publicSlug]/messages/route.ts | bounded public message endpoint | SD-04 | planned |
| src/lib/quotas.ts | persistent reservation/check | SD-04 | planned |
| src/lib/leads.ts | consent/validation/export | SD-04 | planned |
| src/components/support-widget.tsx | accessible public chat/handoff | SD-04 | planned |
| tests/ingest.test.ts | empty/UTF-8/oversize/dedupe | SD-02 | planned |
| tests/answers.test.ts | unknown sources/timeouts/injection fixtures | SD-03 | planned |
| tests/inbox.spec.ts | E2E conversation/handoff/mobile | SD-05 | planned |
| tests/fixtures/evaluation.json | known/unknown/malicious questions | SD-05 | planned |
| suite/supabase/migrations/<timestamp>_supportdesk.sql | SD schema, grants and policies | SD-01 | planned |
| suite/supabase/tests/supportdesk_rls.test.sql | direct tenant/public-token isolation | SD-05 | planned |

## Required expansion
Record auth utility paths and actual config files before SD-01 completion. Update each implementation file with exact exports and test evidence; architecture-only rows must remain planned. Resolve unspecified provider package/env details at SD-03 using fresh official documentation.
