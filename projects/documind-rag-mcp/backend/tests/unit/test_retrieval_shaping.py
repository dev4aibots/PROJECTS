"""Retrieval shaping tests: dedupe, diversity, cap, confidence, gate."""

from uuid import uuid4

from app.domain.models import RetrievedChunk
from app.domain.retrieval_shaping import (
    cap_context,
    compute_confidence,
    dedupe_chunks,
    diversify_pages,
    evidence_sufficient,
    shape_retrieval,
)

DOC = uuid4()


def rc(page=1, idx=0, content="content " * 20, sim=0.8, doc=None) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=doc or DOC,
        filename="f.pdf",
        page_number=page,
        chunk_index=idx,
        content=content,
        similarity=sim,
    )


class TestDedupe:
    def test_drops_same_page_same_prefix(self):
        a = rc(content="Identical prefix text " * 10)
        b = rc(content="Identical prefix text " * 10, idx=1)
        assert len(dedupe_chunks([a, b])) == 1

    def test_keeps_different_content(self):
        assert len(dedupe_chunks([rc(content="AAA " * 40), rc(content="BBB " * 40)])) == 2

    def test_same_prefix_on_different_pages_kept(self):
        a = rc(page=1, content="Same words " * 20)
        b = rc(page=2, content="Same words " * 20)
        assert len(dedupe_chunks([a, b])) == 2


class TestDiversity:
    def test_caps_per_page(self):
        chunks = [rc(page=1, idx=i, content=f"unique{i} " * 30) for i in range(5)]
        assert len(diversify_pages(chunks, max_per_page=2)) == 2

    def test_other_pages_unaffected(self):
        chunks = [rc(page=1, idx=0), rc(page=1, idx=1, content="other " * 40), rc(page=2)]
        assert len(diversify_pages(chunks, max_per_page=2)) == 3


class TestCap:
    def test_stops_at_budget(self):
        chunks = [rc(idx=i, content=("w" * 400), page=i + 1) for i in range(10)]  # ~100 tok each
        kept = cap_context(chunks, token_cap=250)
        assert len(kept) == 2

    def test_first_chunk_always_kept(self):
        huge = rc(content="x" * 40000)  # ~10k tokens
        assert cap_context([huge], token_cap=100) == [huge]


class TestConfidence:
    def test_empty_is_zero(self):
        assert compute_confidence([]) == 0.0

    def test_mean_of_top_three(self):
        chunks = [rc(sim=s) for s in (0.9, 0.8, 0.7, 0.1)]
        assert abs(compute_confidence(chunks) - 0.8) < 1e-9

    def test_clamped(self):
        assert 0.0 <= compute_confidence([rc(sim=1.0)]) <= 1.0


class TestGateAndPipeline:
    def test_gate_refuses_on_empty(self):
        assert evidence_sufficient([]) is False
        assert evidence_sufficient([rc()]) is True

    def test_shape_sorts_by_similarity_first(self):
        low = rc(sim=0.4, page=1, content="low " * 40)
        high = rc(sim=0.9, page=2, content="high " * 40)
        shaped = shape_retrieval([low, high], token_cap=4000)
        assert shaped[0].similarity == 0.9

    def test_full_pipeline_deterministic(self):
        chunks = [rc(page=p, idx=i, sim=0.5 + p * 0.01, content=f"c{p}-{i} " * 30)
                  for p in range(1, 6) for i in range(3)]
        a = shape_retrieval(list(chunks), token_cap=1000)
        b = shape_retrieval(list(chunks), token_cap=1000)
        assert [(c.chunk_id) for c in a] == [(c.chunk_id) for c in b]
