// Redirect allow-list for the OAuth callback, login and sign-out flows (CF-03).
// Open redirects are a listed security gate (docs/SECURITY_TESTING.md). The
// rule is deliberately narrow: only same-origin paths under a fixed set of
// prefixes survive; everything else collapses to a safe default. Never build a
// redirect from `Host`, `Referer` or a raw query value.

/** Where a signed-in user lands when no (valid) `next` was supplied. */
export const DEFAULT_AFTER_LOGIN = '/app';
/** Where a signed-out visitor lands. */
export const DEFAULT_AFTER_LOGOUT = '/login';

/** Only these path prefixes may be used as post-login destinations. */
export const ALLOWED_NEXT_PREFIXES = ['/app', '/onboarding'] as const;

const MAX_NEXT_LENGTH = 512;

/**
 * Returns `raw` if it is a safe, same-origin, allow-listed relative path;
 * otherwise `fallback`. Accepts optional query string, strips fragments.
 */
export function safeNextPath(raw: unknown, fallback: string = DEFAULT_AFTER_LOGIN): string {
  if (typeof raw !== 'string') return fallback;
  if (raw.length === 0 || raw.length > MAX_NEXT_LENGTH) return fallback;
  // Must be an absolute-path reference, never protocol-relative or scheme-bearing.
  if (!raw.startsWith('/')) return fallback;
  if (raw.startsWith('//') || raw.startsWith('/\\')) return fallback;
  // Control characters, whitespace and encoded CR/LF can smuggle headers or a host.
  if (/[\u0000-\u001f\u007f\s]/.test(raw) || /%0[ad]/i.test(raw) || /%2f%2f/i.test(raw.slice(0, 8))) return fallback;
  // Backslashes are normalised to `/` by some user agents -> treat as unsafe.
  if (raw.includes('\\')) return fallback;
  // Parse against a dummy origin; if the origin changes the value was not relative.
  let url: URL;
  try {
    url = new URL(raw, 'https://relative.invalid');
  } catch {
    return fallback;
  }
  if (url.origin !== 'https://relative.invalid') return fallback;
  if (url.pathname.includes('..')) return fallback;
  const path = url.pathname;
  const allowed = ALLOWED_NEXT_PREFIXES.some(prefix => path === prefix || path.startsWith(`${prefix}/`));
  if (!allowed) return fallback;
  return `${path}${url.search}`;
}

/** Build the absolute URL the auth provider must return to. */
export function callbackUrl(origin: string, next?: string): string {
  const url = new URL('/auth/callback', origin);
  const safe = safeNextPath(next);
  if (safe !== DEFAULT_AFTER_LOGIN) url.searchParams.set('next', safe);
  return url.toString();
}

/** Build the login URL that remembers where an anonymous visitor tried to go. */
export function loginUrlFor(origin: string, attemptedPath: string, attemptedSearch = ''): string {
  const url = new URL(DEFAULT_AFTER_LOGOUT, origin);
  const safe = safeNextPath(`${attemptedPath}${attemptedSearch}`);
  if (safe !== DEFAULT_AFTER_LOGIN) url.searchParams.set('next', safe);
  return url.toString();
}
