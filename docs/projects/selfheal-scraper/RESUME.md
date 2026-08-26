# RESUME — P5 SelfHeal Scraper (LIVE state doc — update after every checkpoint)

**Spec:** see BRIEF.md (frozen). **Dir:** `projects/05-selfheal-scraper`
**Verify command:** `cd projects/05-selfheal-scraper && pip install -r requirements.txt -q && python -m pytest tests/ -q`

## Checkpoints
| # | Checkpoint | Status |
|---|-----------|--------|
| C1 | Backend implemented (all endpoints, demo mode + real-API paths) | ✅ |
| C2 | Dashboard (public/index.html, 5-element formula) | ✅ |
| C3 | Tests written & green | ✅ (8 passed) |
| C4 | README + vercel.json + local run verified | ✅ (uvicorn smoke: v1 css → v2 heal v2-bump → v2 converged, drop alerts fired) |
| C5 | Manifest/checkpoint docs updated, committed | ✅ |

## NEXT ACTION
> P5 COMPLETE. Move to P6 (docs/projects/modguard-moderation/RESUME.md).

## Blockers
None.

## Decisions (scope changes with rationale — append-only)
None yet.

## Live deployment
Not deployed yet. After `npx vercel --prod`, record URL here.
