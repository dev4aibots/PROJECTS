import { describe, expect, it } from 'vitest';
import { parseWorkspaceInput, mapWorkspaceRpcError, isUuid, workspaceInitials, WORKSPACE_NAME_MAX } from '@/lib/workspaces';

describe('parseWorkspaceInput', () => {
  it('trims and accepts a valid name', () => {
    const r = parseWorkspaceInput({ name: '  Studio North  ' });
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.data.name).toBe('Studio North');
  });
  it.each([
    [{ name: '' }, 'empty'],
    [{ name: '   ' }, 'whitespace only'],
    [{ name: 'x'.repeat(WORKSPACE_NAME_MAX + 1) }, 'too long'],
    [{ name: 42 }, 'wrong type'],
    [{}, 'missing'],
    [null, 'null body'],
    ['Studio', 'not an object'],
  ])('rejects %j (%s) with a field error', (input) => {
    const r = parseWorkspaceInput(input);
    expect(r.ok).toBe(false);
    if (!r.ok) { expect(r.result.ok).toBe(false); if (!r.result.ok) { expect(r.result.code).toBe('validation'); expect(r.result.fields?.name).toBeTruthy(); } }
  });
  it('accepts exactly the SQL upper bound', () => {
    expect(parseWorkspaceInput({ name: 'x'.repeat(WORKSPACE_NAME_MAX) }).ok).toBe(true);
  });
});

describe('mapWorkspaceRpcError', () => {
  it('maps the SQLSTATEs raised by platform_create_workspace', () => {
    expect(mapWorkspaceRpcError({ code: '42501' })).toMatchObject({ ok: false, code: 'unauthenticated' });
    expect(mapWorkspaceRpcError({ code: '54000' })).toMatchObject({ ok: false, code: 'quota' });
    expect(mapWorkspaceRpcError({ code: '22023' })).toMatchObject({ ok: false, code: 'validation' });
    expect(mapWorkspaceRpcError({ code: '23514' })).toMatchObject({ ok: false, code: 'validation' });
  });
  it('never leaks raw provider text for unknown failures', () => {
    const r = mapWorkspaceRpcError({ code: 'PGRST301', message: 'JWSError JWSInvalidSignature at row 3' });
    expect(r.ok).toBe(false);
    if (!r.ok) { expect(r.code).toBe('backend'); expect(r.message).not.toContain('JWS'); }
    expect(mapWorkspaceRpcError(null)).toMatchObject({ ok: false, code: 'backend' });
  });
});

describe('isUuid / workspaceInitials', () => {
  it('validates route params before they reach the database', () => {
    expect(isUuid('10000000-0000-4000-8000-00000000000a')).toBe(true);
    expect(isUuid('10000000-0000-4000-8000-00000000000A')).toBe(true);
    expect(isUuid('not-a-uuid')).toBe(false);
    expect(isUuid("10000000-0000-4000-8000-00000000000a' or 1=1")).toBe(false);
    expect(isUuid('')).toBe(false);
    expect(isUuid(undefined)).toBe(false);
  });
  it('builds a two-character mark from any name', () => {
    expect(workspaceInitials('Studio North')).toBe('SN');
    expect(workspaceInitials('acme')).toBe('AC');
    expect(workspaceInitials('   ')).toBe('·');
    expect(workspaceInitials('北京 设计')).toBe('北设');
  });
});
