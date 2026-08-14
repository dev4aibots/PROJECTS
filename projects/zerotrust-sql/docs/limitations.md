# Limitations

- Local generation uses explicit templates; live provider behavior is unverified.
- Local SQLite `query_only` approximates but does not prove hosted Postgres role policy.
- Local audit history is in process memory and resets on restart.
- No production authentication, tenant isolation, rate limiting, or data classification is included.
- CORS must be narrowed to the deployed frontend origin.
- Langfuse, Supabase/Postgres, Vercel, screenshots, and public URLs remain owner-gated.
