# Deployment runbook — final owner steps

**Current document describes the target workflow, not proof that all commands are implemented.** Check STATUS and FILES first. No hosted deployment is authorized or performed during this build session.

## Three environments
1. **UI demo:** no credentials; explicit `/demo`, synthetic isolated data, never real authentication. Can be shown as a UI prototype only until live features exist.
2. **Local full-stack:** Supabase CLI + Docker; local Auth, Postgres, Storage; seeded test users. Agents complete all code and schema checks here before asking for hosted keys.
3. **Hosted personal demo:** one Supabase Free project; three Vercel projects. Production customer use needs service/hosting policy review and operational ownership.

## Agent code-complete prerequisites
- [ ] All three product release tasks verified, migration/type drift checked.
- [ ] Committed `.env.example` for each app lists required/public/server-only vars; no secrets present.
- [ ] Migration reset, unit, SQL, E2E, accessibility and build checks run from fresh install.
- [ ] Failure mode without config is explicit setup/unavailable, not pretend live success.
- [ ] Post-deploy smoke script/checklist and restore strategy are tested locally.

## Local development target commands
Run app commands inside its directory; run Supabase commands from `suite/` after its configuration exists.
```bash
cd suite/apps/clientflow
npm ci
npm run dev
# In a separate shell once CF-02 adds the files:
cd suite
npx supabase start
npx supabase db reset
npx supabase test db
```
Pin the Supabase CLI version when introduced. Never run `db reset` against a linked remote; it is a destructive local development command. Docker must be installed/running on the developer's machine; do not fake a local database when absent.

## Owner final setup (FINAL only)
1. Create/select one Supabase Free project, save database password in a password manager, choose a suitable region. Check remaining account quota and service terms.
2. Apply the reviewed migration chain using Supabase CLI link + `db push` after backup; inspect migration diff first. Do not paste guessed schemas from an old AI chat.
3. Configure Auth Site URL + exact redirect allowlist for all three HTTPS app callback URLs and localhost. Configure GitHub OAuth client ID/secret in Supabase (GitHub callback is Supabase's callback URL). Keep preview wildcard permissions narrow; production callbacks explicit.
4. If enabling email/password registration/recovery, configure custom SMTP and test confirmation/reset delivery. Leave confirmation on. OAuth-only is acceptable for the free demo.
5. Create private buckets through migrations/configuration as documented in CF-07, with limits and RLS. Never flip bucket public to fix an access bug.
6. In Vercel import the repo three times with root directories:
   - `suite/apps/clientflow`
   - `suite/apps/supportdesk`
   - `suite/apps/invoicehub`
   Framework: Next.js; install `npm ci`; build `npm run build`; Node version matches app engines. **Select the app root above**, not the repository root. No static export.
7. Add env variables by environment (preview vs production) and redeploy. Public Supabase URL/key are intended client configuration; backend provider keys remain server-only. Never use `NEXT_PUBLIC_` for private keys.
8. Create your own test accounts through normal signup/OAuth, not hardcoded public demo passwords. Seed synthetic data per workspace through a reviewed seed flow; keep it separate from real customer content.
9. Run all smoke checks below. Record URLs/version/date and limitations in handoff/release notes.

## Expected env contract (added as features exist)
| Variable | Scope | Notes |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Public | Project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Public | Publishable key; RLS provides authorization |
| `APP_ORIGIN` | Server | Exact canonical URL for redirects; don't trust incoming Host |
| `SUPPORT_ANSWER_MODE` | Server | `retrieval` or configured provider; invalid config fails closed |
| `SUPPORT_AI_API_KEY`, `SUPPORT_AI_MODEL` | Server | Optional; never exposed to UI; exact adapter variables finalized at SD-03 |
No service-role key is needed for ordinary app traffic. Privileged migration/seeding tokens must be separate, scoped operational inputs and absent from public apps.

## Hosted smoke checklist
- [ ] Sign in/out; refresh on private URL; expired session; OAuth callback and bad redirect rejected.
- [ ] Create workspace/client/project; refresh/browser restart proves database persistence.
- [ ] Account B cannot read/change A through direct Data API and app requests.
- [ ] Client portal cannot see internal comments/files; removed member loses access.
- [ ] Upload private file, signed link expires, foreign user cannot obtain a link.
- [ ] Support retrieval cites own published sources; unknown answer hands off; provider disabled/error not disguised.
- [ ] Invoice issue/payment/PDF works, duplicate payment ID has no double effect.
- [ ] Observe logs, quota usage, backup export and restore test record; no secret/PII leakage.

## Costs and reliability
Vercel Hobby non-commercial; Supabase Free can pause after inactivity and has no automatic backup feature. Check demos before interviews, not via automated usage-evasion pings. Real AI may cost money; retrieval-only remains useful but must not be mislabeled generated AI. Custom domain/SMTP/provider/paid production plans are optional costs; no permanent-zero-cost promise.
