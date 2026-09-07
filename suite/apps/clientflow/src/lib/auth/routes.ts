// Route classification for the auth proxy and layouts (CF-03). Pure; unit-tested.

/** Everything under these prefixes requires a verified session. */
export const PROTECTED_PREFIXES = ['/app', '/onboarding'] as const;
/** Auth entry points: a signed-in user is bounced away from these to the app. */
export const AUTH_ENTRY_PATHS = ['/login'] as const;
/** Never touched by the proxy: explicit credential-free demo and static assets. */
export const PUBLIC_PREFIXES = ['/demo', '/_next', '/favicon.ico'] as const;

export type RouteKind = 'protected' | 'auth-entry' | 'auth-flow' | 'public';

export function classifyRoute(pathname: string): RouteKind {
  if (PROTECTED_PREFIXES.some(p => pathname === p || pathname.startsWith(`${p}/`))) return 'protected';
  if (AUTH_ENTRY_PATHS.some(p => pathname === p)) return 'auth-entry';
  if (pathname === '/auth/callback' || pathname === '/auth/recovery' || pathname.startsWith('/auth/')) return 'auth-flow';
  return 'public';
}

export function isProtectedPath(pathname: string): boolean {
  return classifyRoute(pathname) === 'protected';
}

/** Cache directives every authenticated (or auth-state-dependent) response must carry. */
export const PRIVATE_NO_STORE = 'private, no-cache, no-store, must-revalidate, max-age=0';
