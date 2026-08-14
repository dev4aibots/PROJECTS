"""Sentence-aware, page-scoped chunking.

Chunks never cross page boundaries so every chunk maps to exactly one page —
this is what makes page-level citations trustworthy. Target ~800 tokens per
chunk with ~15% sentence overlap. Token counting uses a chars/4 heuristic
(cheap, deterministic, close enough for budgeting decisions).
"""

from __future__ import annotations

import re
from uuid import UUID

from ..domain.models import Chunk

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")
_WS_RE = re.compile(r"[ \t]+")


def estimate_tokens(text: str) -> int:
    """Deterministic token estimate: ~4 characters per token."""
    return max(0, (len(text) + 3) // 4)


def normalize_text(text: str) -> str:
    """Collapse repeated spaces/tabs and strip trivial whitespace lines."""
    lines = [_WS_RE.sub(" ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def split_sentences(text: str) -> list[str]:
    """Split into sentences; long unbroken runs are hard-split by words."""
    parts: list[str] = []
    for block in text.split("\n"):
        block = block.strip()
        if not block:
            continue
        parts.extend(s.strip() for s in _SENTENCE_RE.split(block) if s.strip())

    # Hard-split any pathological sentence longer than ~1200 tokens by words.
    out: list[str] = []
    for sentence in parts:
        if estimate_tokens(sentence) <= 1200:
            out.append(sentence)
            continue
        words = sentence.split(" ")
        buf: list[str] = []
        size = 0
        for word in words:
            size += estimate_tokens(word) + 1
            buf.append(word)
            if size >= 800:
                out.append(" ".join(buf))
                buf, size = [], 0
        if buf:
            out.append(" ".join(buf))
    return out


def chunk_pages(
    document_id: UUID,
    pages: list[tuple[int, str]],
    target_tokens: int = 800,
    overlap_ratio: float = 0.15,
) -> list[Chunk]:
    """Chunk extracted page texts into page-scoped, overlapping chunks.

    chunk_index is global per document call site: callers pass ALL pages of a
    batch and receive chunks whose (page_number, chunk_index) pair is unique
    and stable — reprocessing the same pages yields identical keys, which is
    what makes upsert_many idempotent.
    """
    chunks: list[Chunk] = []
    for page_number, raw_text in pages:
        text = normalize_text(raw_text)
        if not text:
            continue  # blank/unreadable page: no chunks, no failure
        sentences = split_sentences(text)
        if not sentences:
            continue

        chunk_index = 0
        i = 0
        while i < len(sentences):
            buf: list[str] = []
            size = 0
            j = i
            while j < len(sentences) and size < target_tokens:
                buf.append(sentences[j])
                size += estimate_tokens(sentences[j]) + 1
                j += 1

            content = " ".join(buf).strip()
            if content:
                chunks.append(
                    Chunk(
                        document_id=document_id,
                        page_number=page_number,
                        chunk_index=chunk_index,
                        content=content,
                        token_count=estimate_tokens(content),
                    )
                )
                chunk_index += 1

            if j >= len(sentences):
                break

            # Overlap: step back enough sentences to cover ~overlap_ratio tokens.
            overlap_budget = int(target_tokens * overlap_ratio)
            back = 0
            acc = 0
            while back < len(buf) - 1 and acc < overlap_budget:
                back += 1
                acc += estimate_tokens(buf[-back])
            i = max(i + 1, j - back)
    return chunks
