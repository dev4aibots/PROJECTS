import { describe, expect, expectTypeOf, it } from 'vitest';
import { Constants, type Enums, type Tables, type TablesInsert, type TablesUpdate } from '../src/lib/database.types';
import { projectStatuses, type ProjectStatus } from '../src/lib/projects';

/**
 * CF-02 contract: the generated database types (from the applied migration
 * chain) and the Zod domain in projects.ts must describe the same world.
 * If a migration adds a status or the domain renames one, this file fails
 * BEFORE any runtime code touches Supabase. Runtime enforcement lives in the
 * pgTAP suite (suite/supabase/tests/clientflow_rls.test.sql).
 */
describe('generated database types mirror the domain', () => {
  it('cf_project_status enum equals projectStatuses literal set (values and order)', () => {
    expect([...Constants.public.Enums.cf_project_status]).toEqual([...projectStatuses]);
    expectTypeOf<Enums<'cf_project_status'>>().toEqualTypeOf<ProjectStatus>();
  });

  it('platform enums match the DATABASE.md contract', () => {
    expect([...Constants.public.Enums.platform_app]).toEqual(['clientflow', 'supportdesk', 'invoicehub']);
    expect([...Constants.public.Enums.platform_role]).toEqual(['owner', 'admin', 'member', 'client']);
  });

  it('cf_projects Row carries the tenant, integrity and concurrency columns', () => {
    expectTypeOf<Tables<'cf_projects'>>().toHaveProperty('workspace_id').toEqualTypeOf<string>();
    expectTypeOf<Tables<'cf_projects'>>().toHaveProperty('client_id').toEqualTypeOf<string>();
    expectTypeOf<Tables<'cf_projects'>>().toHaveProperty('version').toEqualTypeOf<number>();
    expectTypeOf<Tables<'cf_projects'>>().toHaveProperty('due_date').toEqualTypeOf<string | null>();
    expectTypeOf<Tables<'cf_projects'>>().toHaveProperty('created_by').toEqualTypeOf<string>();
  });

  it('server-managed columns are not writable from the app (column grants -> Insert/Update)', () => {
    // created_by is stamped by trigger from auth.uid(); created_at/updated_at by defaults/trigger.
    expectTypeOf<TablesInsert<'cf_projects'>>().not.toHaveProperty('created_by');
    expectTypeOf<TablesInsert<'cf_projects'>>().not.toHaveProperty('created_at');
    expectTypeOf<TablesUpdate<'cf_projects'>>().not.toHaveProperty('workspace_id');
    expectTypeOf<TablesUpdate<'cf_projects'>>().not.toHaveProperty('created_by');
    expectTypeOf<TablesUpdate<'cf_clients'>>().not.toHaveProperty('workspace_id');
  });

  it('platform tables are read-only or function-only for the app', () => {
    expectTypeOf<TablesInsert<'platform_workspaces'>>().toBeNever();
    expectTypeOf<TablesInsert<'platform_members'>>().toBeNever();
    expectTypeOf<TablesUpdate<'platform_members'>>().toBeNever();
    expectTypeOf<TablesInsert<'platform_profiles'>>().toBeNever();
    expectTypeOf<TablesUpdate<'platform_workspaces'>>().toEqualTypeOf<{ name?: string }>();
    expectTypeOf<TablesUpdate<'platform_profiles'>>().toEqualTypeOf<{ display_name?: string }>();
  });
});
