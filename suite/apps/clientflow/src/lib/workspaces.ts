// Workspace onboarding domain (CF-03): pure validation and error mapping.
// Mirrors SQL: platform_workspaces_name_len CHECK (1–80) and the errcodes raised
// by platform_create_workspace. Kept dependency-light so it is unit-testable.
import { z } from 'zod';
import type { Enums, Tables } from '@/lib/database.types';

export const CLIENTFLOW_APP: Enums<'platform_app'> = 'clientflow';
export const WORKSPACE_NAME_MAX = 80;
export const WORKSPACE_QUOTA = 10;

export const workspaceNameSchema = z.object({
  name: z.string().trim().min(1, 'Enter a workspace name.').max(WORKSPACE_NAME_MAX, `Use ${WORKSPACE_NAME_MAX} characters or fewer.`),
});
export type WorkspaceInput = z.infer<typeof workspaceNameSchema>;

export type WorkspaceSummary = Pick<Tables<'platform_workspaces'>, 'id' | 'name' | 'created_at'> & { role: Enums<'platform_role'> };

export type CreateWorkspaceResult =
  | { ok: true; id: string }
  | { ok: false; code: 'validation' | 'unauthenticated' | 'quota' | 'backend'; message: string; fields?: { name?: string } };

export function parseWorkspaceInput(input: unknown): { ok: true; data: WorkspaceInput } | { ok: false; result: CreateWorkspaceResult } {
  const raw = typeof input === 'object' && input !== null ? input : {};
  const parsed = workspaceNameSchema.safeParse(raw);
  if (parsed.success) return { ok: true, data: parsed.data };
  const first = parsed.error.issues[0]?.message ?? 'Check the workspace name.';
  return { ok: false, result: { ok: false, code: 'validation', message: 'Check the highlighted field.', fields: { name: first } } };
}

/** Postgres SQLSTATE -> user-facing outcome. Never surfaces raw provider text. */
export function mapWorkspaceRpcError(error: { code?: string | null; message?: string | null } | null): CreateWorkspaceResult {
  switch (error?.code) {
    case '42501':
      return { ok: false, code: 'unauthenticated', message: 'Your session has ended. Sign in again to continue.' };
    case '54000':
      return { ok: false, code: 'quota', message: `You already own ${WORKSPACE_QUOTA} workspaces, which is the limit for this demo.` };
    case '22023':
    case '23514':
      return { ok: false, code: 'validation', message: 'Check the highlighted field.', fields: { name: `Use 1–${WORKSPACE_NAME_MAX} characters.` } };
    default:
      return { ok: false, code: 'backend', message: 'The workspace could not be created because the database did not respond as expected. Nothing was saved.' };
  }
}

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/** Route params are untrusted; a non-UUID never reaches the database. */
export function isUuid(value: unknown): value is string {
  return typeof value === 'string' && UUID_RE.test(value);
}

/** Two-letter avatar mark, safe for any Unicode input. */
export function workspaceInitials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return '·';
  if (words.length === 1) return Array.from(words[0]).slice(0, 2).join('').toUpperCase();
  return `${Array.from(words[0])[0]}${Array.from(words[1])[0]}`.toUpperCase();
}
