import { describe, expect, it } from 'vitest';
import { safeNextPath, callbackUrl, loginUrlFor, DEFAULT_AFTER_LOGIN } from '@/lib/auth/redirects';
import { classifyRoute, isProtectedPath, PRIVATE_NO_STORE } from '@/lib/auth/routes';

// Open-redirect gate (docs/SECURITY_TESTING.md). Every rejected input must fall
// back to the in-app default, never to the attacker's value.
describe('safeNextPath', () => {
  it('accepts allow-listed relative paths with query strings', () => {
    expect(safeNextPath('/app')).toBe('/app');
    expect(safeNextPath('/app/10000000-0000-4000-8000-00000000000a?view=board')).toBe('/app/10000000-0000-4000-8000-00000000000a?view=board');
    expect(safeNextPath('/onboarding')).toBe('/onboarding');
  });
  it('strips fragments', () => {
    expect(safeNextPath('/app/x#token=abc')).toBe('/app/x');
  });
  it.each([
    ['https://evil.example/app', 'absolute URL'],
    ['//evil.example/app', 'protocol-relative'],
    ['/\\evil.example', 'backslash host trick'],
    ['/app\\..\\login', 'backslash traversal'],
    ['javascript:alert(1)', 'scheme'],
    ['app', 'missing leading slash'],
    ['/login', 'not allow-listed prefix'],
    ['/demo/projects', 'demo is public, not a login destination'],
    ['/application', 'prefix must match a whole segment'],
    ['/app/../login', 'dot segments'],
    ['/app%0d%0aSet-Cookie:x=y', 'encoded CRLF'],
    ['/app\nX: y', 'raw newline'],
    ['/app hello', 'whitespace'],
    ['/%2f%2fevil.example', 'encoded double slash'],
    ['', 'empty'],
    [`/app/${'a'.repeat(600)}`, 'too long'],
    [42, 'non-string'],
    [null, 'null'],
    [undefined, 'undefined'],
    [['/app'], 'array (duplicate query key)'],
  ])('rejects %j (%s)', (input) => {
    expect(safeNextPath(input)).toBe(DEFAULT_AFTER_LOGIN);
  });
  it('honours a custom fallback', () => {
    expect(safeNextPath('https://evil.example', '/onboarding')).toBe('/onboarding');
  });
});

describe('callbackUrl / loginUrlFor', () => {
  it('builds the provider return URL on the given origin only', () => {
    expect(callbackUrl('https://clientflow.example')).toBe('https://clientflow.example/auth/callback');
    expect(callbackUrl('https://clientflow.example', '/app/abc')).toBe('https://clientflow.example/auth/callback?next=%2Fapp%2Fabc');
    expect(callbackUrl('https://clientflow.example', 'https://evil.example')).toBe('https://clientflow.example/auth/callback');
  });
  it('remembers only safe attempted paths on the login URL', () => {
    expect(loginUrlFor('http://127.0.0.1:3000', '/app/abc', '?q=1')).toBe('http://127.0.0.1:3000/login?next=%2Fapp%2Fabc%3Fq%3D1');
    expect(loginUrlFor('http://127.0.0.1:3000', '/app')).toBe('http://127.0.0.1:3000/login');
    expect(loginUrlFor('http://127.0.0.1:3000', '//evil.example')).toBe('http://127.0.0.1:3000/login');
  });
});

describe('classifyRoute', () => {
  it('classifies protected, entry, flow and public paths', () => {
    expect(classifyRoute('/app')).toBe('protected');
    expect(classifyRoute('/app/x/projects')).toBe('protected');
    expect(classifyRoute('/onboarding')).toBe('protected');
    expect(classifyRoute('/application')).toBe('public');
    expect(classifyRoute('/login')).toBe('auth-entry');
    expect(classifyRoute('/auth/callback')).toBe('auth-flow');
    expect(classifyRoute('/auth/recovery')).toBe('auth-flow');
    expect(classifyRoute('/demo/projects')).toBe('public');
    expect(classifyRoute('/')).toBe('public');
    expect(isProtectedPath('/app')).toBe(true);
    expect(isProtectedPath('/demo')).toBe(false);
  });
  it('exports a no-store directive that forbids shared caching', () => {
    expect(PRIVATE_NO_STORE).toContain('private');
    expect(PRIVATE_NO_STORE).toContain('no-store');
  });
});
