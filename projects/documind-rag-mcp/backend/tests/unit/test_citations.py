"""Citation validation tests — the anti-hallucination gate."""

from uuid import uuid4

from app.domain.citations import validate_citations
from app.domain.models import LLMAnswerDraft, REFUSAL_TEXT, RetrievedChunk

DOC = uuid4()


def rc(content="The refund period is thirty days from purchase date.", page=3):
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=DOC,
        filename="policy.pdf",
        page_number=page,
        chunk_index=0,
        content=content,
        similarity=0.85,
    )


def cite(chunk: RetrievedChunk, excerpt=None, **overrides) -> dict:
    d = {
        "chunk_id": str(chunk.chunk_id),
        "document_id": str(chunk.document_id),
        "page": chunk.page_number,
        "excerpt": excerpt if excerpt is not None else chunk.content[:40],
    }
    d.update(overrides)
    return d


class TestValidCitations:
    def test_valid_citation_passes(self):
        chunk = rc()
        draft = LLMAnswerDraft(answer="Refunds within 30 days.", citations=[cite(chunk)])
        result = validate_citations(draft, [chunk], confidence=0.8)
        assert result.answer.grounded is True
        assert result.stripped_count == 0
        assert result.answer.citations[0].page == 3
        assert result.answer.citations[0].filename == "policy.pdf"

    def test_resolves_by_document_and_page_without_chunk_id(self):
        chunk = rc()
        c = cite(chunk)
        del c["chunk_id"]
        draft = LLMAnswerDraft(answer="A.", citations=[c])
        result = validate_citations(draft, [chunk], confidence=0.7)
        assert result.answer.grounded is True

    def test_excerpt_match_is_case_and_whitespace_insensitive(self):
        chunk = rc()
        c = cite(chunk, excerpt="THE   REFUND period IS thirty")
        draft = LLMAnswerDraft(answer="A.", citations=[c])
        assert validate_citations(draft, [chunk], 0.7).answer.grounded is True

    def test_confidence_comes_from_retrieval_not_llm(self):
        chunk = rc()
        draft = LLMAnswerDraft(answer="A.", citations=[cite(chunk)])
        result = validate_citations(draft, [chunk], confidence=0.42)
        assert result.answer.confidence == 0.42


class TestFabrications:
    def test_fabricated_chunk_id_stripped(self):
        chunk = rc()
        fake = cite(chunk, chunk_id=str(uuid4()), document_id=str(uuid4()), page=99)
        draft = LLMAnswerDraft(answer="A.", citations=[fake])
        result = validate_citations(draft, [chunk], 0.8)
        assert result.answer.grounded is False
        assert result.answer.answer == REFUSAL_TEXT
        assert result.violation is True

    def test_fabricated_excerpt_stripped(self):
        chunk = rc()
        draft = LLMAnswerDraft(
            answer="A.", citations=[cite(chunk, excerpt="text that appears nowhere in evidence")]
        )
        result = validate_citations(draft, [chunk], 0.8)
        assert result.answer.grounded is False

    def test_trivially_short_excerpt_stripped(self):
        chunk = rc()
        draft = LLMAnswerDraft(answer="A.", citations=[cite(chunk, excerpt="The")])
        assert validate_citations(draft, [chunk], 0.8).answer.grounded is False

    def test_mixed_valid_and_fake_keeps_only_valid(self):
        chunk = rc()
        fake = cite(chunk, chunk_id=str(uuid4()), document_id=str(uuid4()), page=42)
        draft = LLMAnswerDraft(answer="A.", citations=[cite(chunk), fake])
        result = validate_citations(draft, [chunk], 0.8)
        assert result.answer.grounded is True
        assert len(result.answer.citations) == 1
        assert result.stripped_count == 1
        assert result.violation is True

    def test_garbage_citation_values_do_not_crash(self):
        chunk = rc()
        draft = LLMAnswerDraft(
            answer="A.",
            citations=[{"chunk_id": "not-a-uuid", "page": "NaN", "excerpt": 12345}],
        )
        result = validate_citations(draft, [chunk], 0.8)
        assert result.answer.grounded is False
        assert result.stripped_count == 1

    def test_non_dict_citation_rejected_at_model_boundary(self):
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LLMAnswerDraft(answer="A.", citations=["just a string"])  # type: ignore

    def test_no_citations_at_all_becomes_refusal(self):
        draft = LLMAnswerDraft(answer="Confident hallucination.", citations=[])
        result = validate_citations(draft, [rc()], 0.9)
        assert result.answer.grounded is False
        assert result.answer.confidence == 0.0
        assert result.violation is False
