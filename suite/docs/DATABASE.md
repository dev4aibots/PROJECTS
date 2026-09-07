# Database contract

This is a design specification, not an applied migration. SQL files are created and tested in CF-02 onward.

## Shared tables (public schema)
| Table | Fields and constraints |
|---|---|
| `platform_profiles` | `id uuid PK REFERENCES auth.users`, `display_name text` 1–80 chars, timestamps; user can update own display name only |
| `platform_workspaces` | `id uuid PK`, `app text CHECK IN ('clientflow','supportdesk','invoicehub')`, `name text` 1–80, `created_by uuid REFERENCES auth.users`, timestamps; app/creator immutable |
| `platform_members` | `(workspace_id,user_id) PK`, FKs workspace/user, `role` owner/admin/member/client; `client` only valid in ClientFlow, timestamps |
| `platform_invitations` | `id uuid PK`, workspace, normalized recipient email, role (never owner), `token_hash` unique, expiry, accepted_at, creator; no raw tokens at rest |
| `platform_audit_events` | id, workspace, actor, action enum, entity ID/type, time, redacted metadata; append-only server-generated |

All IDs UUID; `timestamptz` for events; `date` for business deadlines; text limits in SQL as well as Zod. Unique `(workspace_id,id)` on entities referenced with composite FKs. Supporting indexes on all membership lookup/foreign key paths and list filters.

## Integrity beyond tenant filtering
```text
cf_tasks(workspace_id, project_id)
  -> cf_projects(workspace_id, id)
cf_projects(workspace_id, client_id)
  -> cf_clients(workspace_id, id)
```
A standalone project_id foreign key would allow a valid row to refer across tenants. Composite keys reject that even if the caller is a member of both workspaces. Created_by and workspace_id cannot be arbitrarily updated.

## Permission helpers
`platform_has_role(workspace, expected_app, allowed_roles)` returns boolean based on `auth.uid()` + current membership + workspace.app. If implemented security-definer to avoid membership RLS recursion, fix search_path, fully qualify table names, revoke public execution and grant only authenticated. Never accept user_id as authorization input. Test anonymous and arbitrary inputs. A helper is not a generic SQL execution escape hatch.

## Transactions and membership
- `platform_create_workspace(app,name)`: verify user, create workspace + owner atomically. Bound workspace count per user to prevent quota abuse.
- Invite accept: hash supplied token, lock invitation, check expiry, one-time use and authenticated verified email; insert membership and consume token atomically. Client invite also binds a client portal mapping within same transaction.
- Last owner cannot leave/demote/delete; role changes lock workspace row, audit in transaction. Normal users cannot directly mutate role columns.
- Invoice issue/payment and task version updates have their own bounded functions; no multi-request pseudo-transactions.

## Migrations
1. `202609070001_platform.sql` (planned): common types/tables, functions, grants, RLS.
2. `202609070002_clientflow.sql` (planned): cf tables + policies.
3. Subsequent timestamp files add invitations/storage as their gates are implemented.
4. SupportDesk and InvoiceHub migrations added later, not placeholder SQL now.

Each migration: fresh local DB → apply → adversarial SQL tests as real anon/authenticated roles → generate types → application integration tests. Do not test only as postgres/service_role (they bypass RLS). Tests use synthetic users A/B, multi-workspace user, client, removed member, anonymous visitor. Test WITH CHECK on inserts/updates, not SELECT alone.

## Data lifecycle
Archive projects with dependencies; don't cascade-delete financial history. Hard-delete user data only via a reviewed workspace deletion flow after export. Private storage objects require explicit cleanup; deleting SQL metadata is not deleting bytes. Shared Auth account deletion spans apps, so never offer casual per-app account deletion that destroys other products' data.
