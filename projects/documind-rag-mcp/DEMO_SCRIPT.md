# DocuMind 90–120 Second Demo Script

Use the generated `sample_docs/refund_policy.pdf`. Do not show a live-provider or deployment badge unless those integrations have been verified first.

## 0:00–0:10 — Problem

**Screen:** Landing page, title and architecture visible.

**Voiceover:** “Most document chat demos answer even when the evidence is weak. DocuMind takes the opposite approach: every answer must map to an exact retrieved page, or the system refuses.”

## 0:10–0:40 — Grounded happy path

**Screen:** Click **Open demo**. Upload `refund_policy.pdf`; wait for the status to become ready. Type: `What are the refund conditions?`

**Voiceover:** “I upload a generated company refund policy. Processing is split into resumable page batches, so retries do not duplicate chunks. I ask for the refund conditions, and the answer arrives with a page citation and a confidence derived from retrieval scores—not invented by the model.”

**Screen:** Expand the citation/source card. Hold on filename, page, similarity, and excerpt.

**Voiceover:** “The source inspector shows the exact retrieved excerpt, page number, and similarity used to validate the response.”

## 0:40–1:05 — Differentiator failure case

**Screen:** Ask: `What is the CEO's salary?` Show the amber insufficient-evidence result.

**Voiceover:** “Now I ask something the document cannot answer. No chunk passes the evidence gate, so DocuMind does not call the chat model. It returns an intentional, non-error refusal with no citations.”

**Screen:** Briefly show a test name for prompt injection or cross-session access.

**Voiceover:** “Prompt-injection screening, session-scoped repositories, and deterministic citation validation provide additional boundaries instead of trusting model output.”

## 1:05–1:35 — Engineering proof

**Screen:** Terminal: run `cd backend && python -m pytest -q`; then show `docs/evaluation.md`.

**Voiceover:** “The backend suite covers ingestion failures, provider fallback, malformed output, isolation, MCP, and grounded refusal. The frozen fifteen-case offline evaluation records retrieval hit, citation accuracy, faithfulness support, and exactly five unanswerable questions.”

**Screen:** Run `python scripts/test_mcp.py` against the local server; hold on `All MCP tools verified.`

**Voiceover:** “The official Streamable HTTP MCP endpoint calls the same services as REST. This smoke script invokes every tool and verifies cross-session denial.”

## 1:35–1:50 — Close

**Screen:** README architecture and limitations links; if available, show verified GitHub and live URLs.

**Voiceover:** “The repository includes reproducible tests, evaluation methodology, architecture decisions, the original audit and remediation, and explicit limits. Live cloud integrations remain clearly separated from what is proven locally.”

## Screenshot capture plan

1. **Grounded answer:** ready refund policy, answer, and expanded page-one source visible together.
2. **Honest refusal:** CEO salary question and amber insufficient-evidence card.
3. **Engineering proof:** evaluation table beside terminal output from the MCP smoke or test suite.

Capture from the current build after final verification; store images under `assets/` only when they exist.
