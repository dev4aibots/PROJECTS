// Pure, dependency-free reading of the authentication environment (CF-03).
// Nothing here throws at import time: the app must build and serve /demo and a
// truthful "not configured" /login without any credentials. Values are never
// logged. Only browser-safe (publishable/anon) keys are accepted; a secret or
// service-role key pasted into a public variable is rejected outright so it can
// never reach a browser bundle (SECURITY_TESTING: no service key in requests).

export type AuthConfig =
  | { configured: true; url: string; key: string }
  | { configured: false; missing: string[]; reason: 'missing' | 'invalid_url' | 'secret_key_rejected' };

export type AuthEnv = Record<string, string | undefined>;

export const ENV_URL = 'NEXT_PUBLIC_SUPABASE_URL';
export const ENV_KEY = 'NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY';
export const ENV_KEY_LEGACY = 'NEXT_PUBLIC_SUPABASE_ANON_KEY';
export const ENV_ORIGIN = 'NEXT_PUBLIC_APP_ORIGIN';

/** True for keys that must never be shipped to a browser or used for user requests. */
export function looksLikeSecretKey(key: string): boolean {
  const k = key.trim();
  if (k.startsWith('sb_secret_')) return true;
  // Legacy JWT-shaped keys carry the role in the payload; reject service_role.
  const parts = k.split('.');
  if (parts.length === 3) {
    try {
      const payload = JSON.parse(Buffer.from(parts[1].replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8')) as { role?: unknown };
      if (payload.role === 'service_role') return true;
    } catch {
      /* not a JWT we can read; fall through */
    }
  }
  return false;
}

export function isValidSupabaseUrl(value: string): boolean {
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' && url.protocol !== 'http:') return false;
    if (url.protocol === 'http:' && !['127.0.0.1', 'localhost', 'host.docker.internal'].includes(url.hostname)) return false;
    return url.username === '' && url.password === '';
  } catch {
    return false;
  }
}

export function readAuthConfig(env: AuthEnv = process.env): AuthConfig {
  const url = (env[ENV_URL] ?? '').trim();
  const key = (env[ENV_KEY] ?? env[ENV_KEY_LEGACY] ?? '').trim();
  const missing: string[] = [];
  if (!url) missing.push(ENV_URL);
  if (!key) missing.push(`${ENV_KEY} (or ${ENV_KEY_LEGACY})`);
  if (missing.length) return { configured: false, missing, reason: 'missing' };
  if (!isValidSupabaseUrl(url)) return { configured: false, missing: [ENV_URL], reason: 'invalid_url' };
  if (looksLikeSecretKey(key)) return { configured: false, missing: [ENV_KEY], reason: 'secret_key_rejected' };
  return { configured: true, url: url.replace(/\/+$/, ''), key };
}

/**
 * Canonical origin used to build absolute redirect URLs (OAuth callback, password
 * recovery link). Behind a proxy `Host` can be forged, so an explicit
 * NEXT_PUBLIC_APP_ORIGIN wins; otherwise the request origin is used.
 */
export function resolveAppOrigin(requestOrigin: string, env: AuthEnv = process.env): string {
  const configured = (env[ENV_ORIGIN] ?? '').trim();
  const candidate = configured || requestOrigin;
  try {
    const url = new URL(candidate);
    if (url.protocol !== 'https:' && url.protocol !== 'http:') return requestOrigin;
    return url.origin;
  } catch {
    return requestOrigin;
  }
}
