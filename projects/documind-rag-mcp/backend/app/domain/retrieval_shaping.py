"""Post-retrieval shaping: dedupe, page diversity, context cap, confidence.

All deterministic, all unit-testable, no provider involvement. This is the
evidence gate: if nothing survives shaping, the pipeline refuses instead of
letting the LLM guess.
"""

from __future__ import annotations

from ..domain.models import RetrievedChunk
from .chunking import estimate_tokens


def dedupe_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Drop near-duplicates: same document+page with near-identical prefixes."""
    seen: set[tuple[str, int, str]] = set()
    out: list[RetrievedChunk] = []
    for chunk in chunks:
        key = (str(chunk.document_id), chunk.page_number, chunk.content[:120].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(chunk)
    return out


def diversify_pages(
    chunks: list[RetrievedChunk], max_per_page: int = 2
) -> list[RetrievedChunk]:
    """Cap chunks per (document, page) so one dense page can't crowd out others."""
    counts: dict[tuple[str, int], int] = {}
    out: list[RetrievedChunk] = []
    for chunk in chunks:
        key = (str(chunk.document_id), chunk.page_number)
        if counts.get(key, 0) >= max_per_page:
            continue
        counts[key] = counts.get(key, 0) + 1
        out.append(chunk)
    return out


def cap_context(chunks: list[RetrievedChunk], token_cap: int) -> list[RetrievedChunk]:
    """Keep highest-similarity chunks until the token budget is spent.

    Chunks arrive similarity-sorted; the first chunk is always kept even if it
    alone exceeds the cap (an empty context would silently force a refusal).
    """
    out: list[RetrievedChunk] = []
    used = 0
    for chunk in chunks:
        cost = estimate_tokens(chunk.content)
        if out and used + cost > token_cap:
            continue
        out.append(chunk)
        used += cost
    return out


def shape_retrieval(
    chunks: list[RetrievedChunk],
    token_cap: int,
    max_per_page: int = 2,
) -> list[RetrievedChunk]:
    """Full shaping pipeline. Input must already be similarity-sorted desc."""
    ordered = sorted(chunks, key=lambda c: c.similarity, reverse=True)
    return cap_context(diversify_pages(dedupe_chunks(ordered), max_per_page), token_cap)


def compute_confidence(chunks: list[RetrievedChunk]) -> float:
    """Derived confidence: mean of the top-3 similarities, clamped to [0, 1].

    Never invented by the LLM — this number is a property of retrieval.
    """
    if not chunks:
        return 0.0
    top = sorted((c.similarity for c in chunks), reverse=True)[:3]
    return max(0.0, min(1.0, sum(top) / len(top)))


def evidence_sufficient(chunks: list[RetrievedChunk]) -> bool:
    """The refusal gate: no surviving evidence means no answer attempt."""
    return len(chunks) > 0
