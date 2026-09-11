// Pure identity helpers shared by server code and tests (CF-03).

/** Length bound mirrors SQL CHECK `platform_profiles_display_name_len` (1–80). */
export const DISPLAY_NAME_MAX = 80;
export const PASSWORD_MIN = 10;
export const PASSWORD_MAX = 128;
export const EMAIL_MAX = 254;

/**
 * Derive a display name for `platform_ensure_profile` from provider metadata,
 * falling back to the local part of the email, then a neutral label. The value
 * always satisfies the SQL CHECK so the profile upsert cannot fail on length.
 */
export function deriveDisplayName(email: string | null | undefined, metadata: Record<string, unknown> | null | undefined): string {
  const candidates: unknown[] = [metadata?.full_name, metadata?.name, metadata?.user_name, metadata?.preferred_username];
  for (const value of candidates) {
    if (typeof value === 'string') {
      const clean = collapse(value);
      if (clean) return clip(clean);
    }
  }
  if (typeof email === 'string' && email.includes('@')) {
    const local = collapse(email.split('@')[0]);
    if (local) return clip(local);
  }
  return 'New member';
}

function collapse(value: string): string {
  // Remove control characters and collapse whitespace; names are display-only text.
  return value.replace(/[\u0000-\u001f\u007f]/g, '').replace(/\s+/g, ' ').trim();
}

function clip(value: string): string {
  return Array.from(value).slice(0, DISPLAY_NAME_MAX).join('');
}

/** Normalise an email for the auth provider: trimmed and lower-cased domain. */
export function normaliseEmail(raw: unknown): string | null {
  if (typeof raw !== 'string') return null;
  const value = raw.trim();
  if (value.length === 0 || value.length > EMAIL_MAX) return null;
  const at = value.lastIndexOf('@');
  if (at < 1 || at === value.length - 1) return null;
  const local = value.slice(0, at);
  const domain = value.slice(at + 1).toLowerCase();
  if (/\s/.test(value) || !domain.includes('.') || domain.startsWith('.') || domain.endsWith('.')) return null;
  return `${local}@${domain}`;
}

/** Returns a user-facing error, or null when the password is acceptable. */
export function passwordProblem(value: unknown): string | null {
  if (typeof value !== 'string' || value.length === 0) return 'Enter a password.';
  if (value.length < PASSWORD_MIN) return `Use at least ${PASSWORD_MIN} characters.`;
  if (value.length > PASSWORD_MAX) return `Use at most ${PASSWORD_MAX} characters.`;
  return null;
}
