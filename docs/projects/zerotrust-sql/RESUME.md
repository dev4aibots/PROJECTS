# RESUME — P4 ZeroTrust-SQL (LIVE state doc — update after every checkpoint)

**Spec:** see BRIEF.md (frozen). **Dir:** `projects/04-zerotrust-sql`
**Verify command:** `cd projects/04-zerotrust-sql && pip install -r requirements.txt -q && python -m pytest tests/ -q`

## Checkpoints
| # | Checkpoint | Status |
|---|-----------|--------|
| C1 | Backend implemented (all endpoints, demo mode + real-API paths) | ✅ |
| C2 | Dashboard (public/index.html, 5-element formula) | ✅ |
| C3 | Tests written & green | ✅ (16 passed) |
| C4 | README + vercel.json + local run verified | ✅ (uvicorn smoke: query APPROVED, injection BLOCKED, audit logged) |
| C5 | Manifest/checkpoint docs updated, committed | ✅ |

## NEXT ACTION
> P4 COMPLETE. Move to P5 (docs/projects/selfheal-scraper/RESUME.md).

## Blockers
None.

## Decisions (scope changes with rationale — append-only)
None yet.

## Live deployment
Not deployed yet. After `npx vercel --prod`, record URL here.
