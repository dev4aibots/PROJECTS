import { describe, expect, it } from 'vitest';
import { readAuthConfig, looksLikeSecretKey, isValidSupabaseUrl, resolveAppOrigin, ENV_URL, ENV_KEY } from '@/lib/auth/config';
import { deriveDisplayName, normaliseEmail, passwordProblem, DISPLAY_NAME_MAX } from '@/lib/auth/identity';

const jwt = (payload: object) => `eyJhbGciOiJIUzI1NiJ9.${Buffer.from(JSON.stringify(payload)).toString('base64url')}.sig`;

describe('readAuthConfig', () => {
  it('reports missing variables without throwing', () => {
    const cfg = readAuthConfig({});
    expect(cfg.configured).toBe(false);
    if (!cfg.configured) { expect(cfg.reason).toBe('missing'); expect(cfg.missing).toHaveLength(2); }
  });
  it('accepts a publishable key and trims a trailing slash', () => {
    const cfg = readAuthConfig({ [ENV_URL]: 'https://abc.supabase.co/', [ENV_KEY]: 'sb_publishable_abc' });
    expect(cfg).toEqual({ configured: true, url: 'https://abc.supabase.co', key: 'sb_publishable_abc' });
  });
  it('accepts the legacy anon key variable', () => {
    const cfg = readAuthConfig({ [ENV_URL]: 'http://127.0.0.1:54321', NEXT_PUBLIC_SUPABASE_ANON_KEY: jwt({ role: 'anon' }) });
    expect(cfg.configured).toBe(true);
  });
  it('rejects secret / service-role keys so they can never reach a browser', () => {
    expect(looksLikeSecretKey('sb_secret_abc')).toBe(true);
    expect(looksLikeSecretKey(jwt({ role: 'service_role' }))).toBe(true);
    expect(looksLikeSecretKey(jwt({ role: 'anon' }))).toBe(false);
    expect(looksLikeSecretKey('sb_publishable_abc')).toBe(false);
    const cfg = readAuthConfig({ [ENV_URL]: 'https://abc.supabase.co', [ENV_KEY]: 'sb_secret_abc' });
    expect(cfg.configured).toBe(false);
    if (!cfg.configured) expect(cfg.reason).toBe('secret_key_rejected');
  });
  it('rejects malformed or credential-bearing URLs', () => {
    expect(isValidSupabaseUrl('https://abc.supabase.co')).toBe(true);
    expect(isValidSupabaseUrl('http://127.0.0.1:54321')).toBe(true);
    expect(isValidSupabaseUrl('http://abc.supabase.co')).toBe(false);
    expect(isValidSupabaseUrl('https://user:pw@abc.supabase.co')).toBe(false);
    expect(isValidSupabaseUrl('ftp://abc')).toBe(false);
    expect(isValidSupabaseUrl('not a url')).toBe(false);
    const cfg = readAuthConfig({ [ENV_URL]: 'not a url', [ENV_KEY]: 'sb_publishable_abc' });
    expect(cfg.configured).toBe(false);
    if (!cfg.configured) expect(cfg.reason).toBe('invalid_url');
  });
});

describe('resolveAppOrigin', () => {
  it('prefers the configured origin over the request origin', () => {
    expect(resolveAppOrigin('http://forged.host', { NEXT_PUBLIC_APP_ORIGIN: 'https://clientflow.example/some/path' })).toBe('https://clientflow.example');
  });
  it('falls back to the request origin when unset or invalid', () => {
    expect(resolveAppOrigin('http://127.0.0.1:3000', {})).toBe('http://127.0.0.1:3000');
    expect(resolveAppOrigin('http://127.0.0.1:3000', { NEXT_PUBLIC_APP_ORIGIN: 'nope' })).toBe('http://127.0.0.1:3000');
    expect(resolveAppOrigin('http://127.0.0.1:3000', { NEXT_PUBLIC_APP_ORIGIN: 'javascript:x' })).toBe('http://127.0.0.1:3000');
  });
});

describe('deriveDisplayName', () => {
  it('prefers provider names, then email local part, then a neutral label', () => {
    expect(deriveDisplayName('a@b.co', { full_name: '  Ada   Lovelace ' })).toBe('Ada Lovelace');
    expect(deriveDisplayName('a@b.co', { user_name: 'ada' })).toBe('ada');
    expect(deriveDisplayName('ada.l@b.co', {})).toBe('ada.l');
    expect(deriveDisplayName(null, null)).toBe('New member');
    expect(deriveDisplayName('@b.co', {})).toBe('New member');
  });
  it('always satisfies the SQL length check and strips control characters', () => {
    expect(deriveDisplayName(null, { name: 'x'.repeat(500) })).toHaveLength(DISPLAY_NAME_MAX);
    expect(deriveDisplayName(null, { name: 'Ada\u0000\u0007 Lovelace\n' })).toBe('Ada Lovelace');
    expect(deriveDisplayName(null, { name: 42 })).toBe('New member');
  });
});

describe('normaliseEmail / passwordProblem', () => {
  it('normalises the domain and rejects malformed addresses', () => {
    expect(normaliseEmail('  Ada@Example.COM ')).toBe('Ada@example.com');
    expect(normaliseEmail('ada')).toBeNull();
    expect(normaliseEmail('@example.com')).toBeNull();
    expect(normaliseEmail('ada@')).toBeNull();
    expect(normaliseEmail('ada@localhost')).toBeNull();
    expect(normaliseEmail('a da@example.com')).toBeNull();
    expect(normaliseEmail(`${'a'.repeat(260)}@example.com`)).toBeNull();
    expect(normaliseEmail(123)).toBeNull();
  });
  it('bounds passwords', () => {
    expect(passwordProblem('')).toBe('Enter a password.');
    expect(passwordProblem('short')).toMatch(/at least 10/);
    expect(passwordProblem('x'.repeat(129))).toMatch(/at most 128/);
    expect(passwordProblem('a-perfectly-fine-passphrase')).toBeNull();
    expect(passwordProblem(undefined)).toBe('Enter a password.');
  });
});
