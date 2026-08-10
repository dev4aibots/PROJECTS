# DEPLOYMENT-READINESS PROMPT — run before every Vercel deploy

> Paste after the audit passes. Then YOU do the actual deploy clicks and paste any error back to the agent.

---

```
Prepare this project for production deployment on Vercel Hobby +
Supabase Free. Work through this checklist executing each verification,
not just asserting it.

==================================================
BUILD & RUNTIME
==================================================

1. Frontend: run the production build. Zero errors, zero type errors.
   Fix warnings that indicate real problems (unused env vars, dynamic
   route mistakes).
2. Backend: verify the FastAPI app conforms to Vercel's Python runtime
   layout (api/ entrypoint exporting the ASGI app, or the documented
   FastAPI framework preset — pick the current official pattern and
   reference it in DEPLOYMENT.md).
3. requirements.txt: pin every dependency. Remove anything unused. Estimate
   installed size; if the bundle risks the Python function limit, cut or
   substitute (e.g., pypdf not pdfplumber+pandas). List final deps + size
   estimate in DEPLOYMENT.md.
4. vercel.json: routes/rewrites so /api/* hits FastAPI and everything else
   hits Next.js. Function maxDuration set explicitly to the Hobby maximum
   for the processing endpoints. Show me the final file and explain each line.
5. Cold-start audit: no heavyweight imports at module top-level that can be
   deferred; DB clients initialized lazily; no network calls at import time.

==================================================
ENVIRONMENT & SECRETS
==================================================

6. Enumerate EVERY env var the code reads (grep os.environ / process.env).
   Sync the list with .env.example (comments explaining each) and a table
   in DEPLOYMENT.md marked: required/optional, server/client, where to get it.
7. Confirm no server secret is readable by client code. Grep NEXT_PUBLIC_
   and justify each one.
8. Confirm .env, .vercel, node_modules, __pycache__ are gitignored and no
   secret exists anywhere in git history (search the log).

==================================================
EXTERNAL SERVICES
==================================================

9. Supabase: consolidate migrations into numbered idempotent files under
   migrations/ that I can paste into the Supabase SQL editor in order.
   Include the seed script instructions. Include the restricted-role
   migration where the project has one. Verify the app works against a
   FRESH Supabase project by following your own instructions.
10. Connection strategy: confirm the Supabase access pattern is serverless-
    safe (supabase-py HTTP client, or pooled Postgres via the pooler port —
    whichever the project uses, verify and document WHY).
11. LLM providers: verify one real call to Groq and one to Gemini succeed
    with test keys (I will provide), and that the 429-fallback path is
    exercised by a test.
12. Langfuse: verify traces appear with test keys; verify the app still
    functions with Langfuse env vars UNSET (observability must be optional
    for anyone cloning the repo).

==================================================
API URL HANDLING
==================================================

13. The frontend must work in: local dev (localhost:3000 + local API),
    Vercel preview, and Vercel production — with relative /api paths or a
    single NEXT_PUBLIC_API_BASE. No hardcoded URLs anywhere (grep http://
    and https:// to prove it).
14. CORS: same-origin in production, permissive only for localhost dev.

==================================================
POST-DEPLOY VERIFICATION SCRIPT
==================================================

15. Write scripts/verify_deployment.sh (curl-based) that takes the deployed
    base URL and checks: /api/health returns 200 with db+provider status;
    one core happy-path flow works; one invalid request returns a structured
    4xx; response headers don't leak server internals.

==================================================
DELIVERABLE
==================================================

DEPLOYMENT.md with EXACT click-by-click order:
  1. create Supabase project → run migrations 001..N → run seed
  2. get keys (which dashboard pages)
  3. get Groq/Gemini/Langfuse keys (URLs)
  4. Vercel import from GitHub → framework preset → env vars table
  5. deploy → run scripts/verify_deployment.sh <url>
  6. known limitations: Hobby duration caps, Supabase free-tier pause after
     inactivity (and that the demo may need a dashboard visit to un-pause),
     provider rate limits and what the user sees when they hit them.

Then give me the single ordered list of the exact actions I must perform
manually, and STOP. Do not claim the deployment works until I confirm the
live URL — then we run scripts/verify_deployment.sh against it together
and you fix anything it flags.
```
