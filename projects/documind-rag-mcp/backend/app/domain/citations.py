"""Deterministic citation validation.

The LLM's citations are treated as hostile input: every citation must name a
chunk that was actually retrieved, and its excerpt must appear in that chunk's
content. Citations that fail are stripped; an answer whose citations ALL fail
is downgraded to a refusal. The LLM cannot fabricate a source that survives
this gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ..domain.models import (
    Citation,
    GroundedAnswer,
    LLMAnswerDraft,
    RetrievedChunk,
    make_refusal,
)


@dataclass
class CitationValidationResult:
    answer: GroundedAnswer
    stripped_count: int
    violation: bool


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _find_chunk(
    chunks: list[RetrievedChunk], chunk_id: UUID | None, document_id: UUID | None, page: int | None
) -> RetrievedChunk | None:
    if chunk_id is not None:
        for c in chunks:
            if c.chunk_id == chunk_id:
                return c
    if document_id is not None and page is not None:
        for c in chunks:
            if c.document_id == document_id and c.page_number == page:
                return c
    return None


def _parse_uuid(value: object) -> UUID | None:
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def validate_citations(
    draft: LLMAnswerDraft,
    retrieved: list[RetrievedChunk],
    confidence: float,
) -> CitationValidationResult:
    """Validate an LLM draft against the actual retrieved evidence.

    Rules, in order, per citation:
      1. It must resolve to a retrieved chunk (by chunk_id, or document+page).
      2. Its excerpt must be a non-trivial substring of that chunk's content
         (whitespace/case-insensitive).
    Answers with zero surviving citations become refusals.
    """
    valid: list[Citation] = []
    stripped = 0

    for raw in draft.citations:
        if not isinstance(raw, dict):
            stripped += 1
            continue
        chunk_id = _parse_uuid(raw.get("chunk_id"))
        document_id = _parse_uuid(raw.get("document_id"))
        page_raw = raw.get("page")
        page = int(page_raw) if isinstance(page_raw, (int, float, str)) and str(page_raw).isdigit() else None
        excerpt = str(raw.get("excerpt", "")).strip()

        chunk = _find_chunk(retrieved, chunk_id, document_id, page)
        if chunk is None:
            stripped += 1
            continue
        if len(excerpt) < 10 or _normalize(excerpt) not in _normalize(chunk.content):
            stripped += 1
            continue

        valid.append(
            Citation(
                document_id=chunk.document_id,
                filename=chunk.filename,
                page=chunk.page_number,
                excerpt=excerpt[:500],
                chunk_id=chunk.chunk_id,
            )
        )

    if not valid:
        return CitationValidationResult(make_refusal(), stripped, violation=stripped > 0)

    answer = GroundedAnswer(
        answer=draft.answer.strip(),
        citations=valid,
        grounded=True,
        confidence=confidence,
    )
    return CitationValidationResult(answer, stripped, violation=stripped > 0)
