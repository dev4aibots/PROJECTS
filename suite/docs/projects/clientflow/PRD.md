# ClientFlow — product requirements

## Problem and users
Small web agencies scatter client approvals, tasks and files across email and spreadsheets. ClientFlow should answer: what are we delivering, who owns the next step, and what can the client see?
Users: owner (workspace/admin), teammate (delivery), client (limited portal). Not a general enterprise CRM or billing tool.

## v1 workflows and acceptance stories
| ID | Story | Acceptance |
|---|---|---|
| CF-P1 | As a teammate I organize projects by client, status and deadline | Create/edit validated project, search/filter/table/board; live save survives reload; empty/invalid/conflict states |
| CF-P2 | As an owner I set up an agency workspace | Authenticated onboarding creates workspace + owner atomically; A cannot read B |
| CF-P3 | As owner/admin I keep client contacts | Create/edit/archive client; contact validation; referenced clients not hard-deleted |
| CF-P4 | As teammate I coordinate tasks | Assign only current internal members, due date, todo/doing/done, version conflict detection |
| CF-P5 | As teammate I share updates safely | Internal comment/file never visible to client; explicit portal visibility; author from auth |
| CF-P6 | As owner/admin I invite a team/client user | Expiring single-use link; role/email verified; non-owner cannot create owners; last owner retained |
| CF-P7 | As client I view linked projects and submit requests | Only assigned client projects, portal-visible content; request persists with audit event |
| CF-P8 | As user I know what needs attention | Counts/deadline list from actual authorized records; in-app notifications and activity |

Project states: `planned`, `active`, `review`, `completed`, `archived`. These are collaboration labels, not billing states; internal users may move among them intentionally. Archived projects excluded from default active summaries; completed/archived cannot be overdue. Risk is derived from overdue date (or later explicit blocked task), not a decorative random value.

## Scope boundaries
Required: auth/workspaces, clients/projects, tasks/comments, invitations/roles, private files, client portal, search/pagination, responsive dashboard, audit and in-app notifications. Excluded v1: time billing, subscription payment, calendar sync, email campaign CRM, nested subtasks, drag-only controls, external analytics.

## Data and edge cases
Title 1–100 trimmed chars; description max 2,000; valid real calendar due date or blank; existing client; never arbitrary tenant selection from input. Duplicate project names allowed (different projects may share names); UUID identity is authoritative. Invalid UUID returns not-found; RLS denial doesn't disclose existence. Past due dates allowed because backlogs exist. Project date is date-only, not timestamp. Client contacts use synthetic examples in demo.

Concurrent edits use `version` increment and affected-row check. A deleted/archived client remains referentially valid but cannot be newly assigned. Long names wrap. Empty workspaces have onboarding CTAs. Failed saves leave input intact. Uploads use explicit pending/saved/failed metadata and cleanup; no falsely successful completion.

## CF-01 bounded implementation
Project workbench in `/demo` only; sample clients, project create/edit/status, table/board, URL search/status, overview and deadline summaries. In-memory state survives client navigation only, not reload; banner states this clearly. No login buttons that pretend to authenticate, no fake file/task actions. This is an interface/domain milestone, **not full-stack proof** until CF-02–08.

## Release definition
All stories verified with positive/negative tests and authorized DB persistence. Tenant/client/internal boundary tested via direct API, not screenshots. Recorded demo walkthrough, code map and maintenance procedure. Hosted setup remains FINAL.
