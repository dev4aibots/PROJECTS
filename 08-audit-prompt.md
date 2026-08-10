# HOSTILE AUDIT PROMPT — run after EVERY project

> The single most important prompt in this pack. Coding agents routinely leave mock data, dead buttons, and unverified claims. This prompt makes the agent hunt its own lies. Paste it verbatim once the agent claims the project is complete.

---

```
STOP. Before we call this project done, switch roles completely.

You are now a hostile senior staff engineer performing a pre-production
audit of the codebase YOU just wrote. Assume the author (you) cut corners,
mocked things, and made claims without verifying them — because coding
agents always do. Your reputation depends on finding every instance.

Do NOT add features. Do NOT refactor for style. Find what is broken or fake.

==================================================
AUDIT PROCEDURE (execute it, don't just describe it)
==================================================

1. TRACE EVERY FRONTEND ACTION. For each button/form/link in the UI, trace:
   UI handler → API call → route → service → repository → database/LLM →
   response → UI state update.
   Flag any action that: calls nothing, calls a nonexistent endpoint, uses
   hardcoded/mock data, ignores errors, or never updates the UI on failure.

2. GREP FOR LIES. Search the codebase for: "mock", "fake", "dummy", "TODO",
   "FIXME", "placeholder", "hardcoded", "example.com", "lorem",
   "not implemented", "pass  #", "return []", "return {}", "console.log",
   commented-out code, and any suspiciously static data arrays in frontend
   components. Justify or eliminate every hit.

3. RUN EVERYTHING.
   - pytest: full suite, show the real output. Any skipped test → explain why.
   - next build (or the frontend build command): must succeed with zero errors.
   - Import check: python -c "import <every backend module>" — catch missing
     deps and circular imports.
   - Start the API locally and curl EVERY endpoint listed in the README:
     one happy-path call and one invalid-input call each. Show the actual
     responses.

4. DATABASE REALITY CHECK.
   - Do the migrations actually run in order on a FRESH database? Verify.
   - Does every table the code references exist in the migrations?
   - Are there queries that will fail at runtime (wrong column names,
     missing indexes causing seq scans on the hot path)?
   - Is every user-facing list actually reading from the DB and not from
     a fixture?

5. SERVERLESS COMPATIBILITY.
   - Any module-level state assumed to persist between requests?
   - Any file writes outside /tmp?
   - Any operation that can plausibly exceed the function time budget
     without checkpointing?
   - Bundle sanity: any heavyweight dependency (torch, opencv, chromadb)
     that will blow the Python bundle limit?

6. SECRETS AND SECURITY.
   - git log + working tree: is any secret committed anywhere (including
     in docs and test fixtures)?
   - Is any server-only env var referenced in client-side code (NEXT_PUBLIC
     leakage)?
   - Does any error response leak stack traces, SQL, or provider payloads?
   - Are the project's specific security claims TESTED (e.g., for ZeroTrust
     SQL: run the attack corpus; for LLMShield: run the eval; for RAG:
     poisoned-document test)?

7. RATE-LIMIT REALISM. Simulate a 429 from the primary provider (monkeypatch
   or fixture). Does fallback actually engage? Does the user see a sane
   message when both fail? Show the test proving it.

8. CLAIMS VS REALITY. Read the README top to bottom. Every claim ("supports
   X", "handles Y", "validated Z") must map to code + a test you can point
   to. Delete or fix any claim you cannot substantiate.

==================================================
OUTPUT FORMAT
==================================================

Produce the audit report FIRST, before fixing anything:

  CRITICAL — broken core flows, fake features, security holes, build failures
  HIGH     — missing error handling on real paths, untested security claims,
             serverless incompatibilities
  MEDIUM   — weak tests, missing states in UI, doc inaccuracies
  LOW      — style, naming, minor polish

For each finding: file:line, what's wrong, proof (command output or trace),
and the minimal fix.

Then fix ALL CRITICAL and HIGH findings only. After fixing:
re-run the full test suite + frontend build + endpoint curls and show the
outputs. Update the README if any claim changed.

Final deliverable: AUDIT.md at repo root — findings table, what was fixed,
what remains as MEDIUM/LOW (kept as honest known-issues), and the final
verification outputs. An honest AUDIT.md in the repo is itself a hiring
signal — write it like a professional post-review.

Do not tell me the project is done. Show me the passing output.
```
