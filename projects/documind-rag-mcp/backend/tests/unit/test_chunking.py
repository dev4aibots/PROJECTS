"""Chunking tests: page scoping, determinism, overlap, token budgets."""

from uuid import uuid4

from app.domain.chunking import chunk_pages, estimate_tokens, normalize_text, split_sentences

DOC = uuid4()


def make_page_text(sentences: int, words_per_sentence: int = 20) -> str:
    return " ".join(
        "Word " * (words_per_sentence - 1) + f"sentence{i}." for i in range(sentences)
    )


class TestHelpers:
    def test_estimate_tokens_is_chars_over_four(self):
        assert estimate_tokens("") == 0
        assert estimate_tokens("abcd") == 1
        assert estimate_tokens("abcde") == 2

    def test_normalize_collapses_whitespace(self):
        assert normalize_text("a   b\t\tc\n\n\n  d  ") == "a b c\nd"

    def test_split_sentences_basic(self):
        out = split_sentences("First one. Second one! Third one? Fourth.")
        assert len(out) == 4

    def test_split_sentences_hard_splits_pathological_runs(self):
        giant = "word " * 3000  # no sentence punctuation at all
        parts = split_sentences(giant.strip())
        assert len(parts) > 1
        assert all(estimate_tokens(p) <= 1300 for p in parts)


class TestChunkPages:
    def test_chunks_never_cross_pages(self):
        pages = [(1, make_page_text(60)), (2, make_page_text(60))]
        chunks = chunk_pages(DOC, pages, target_tokens=300)
        assert {c.page_number for c in chunks} == {1, 2}
        for c in chunks:
            assert f"sentence" in c.content

    def test_deterministic_keys_for_idempotent_upsert(self):
        pages = [(1, make_page_text(80))]
        a = chunk_pages(DOC, pages, target_tokens=300)
        b = chunk_pages(DOC, pages, target_tokens=300)
        assert [(c.page_number, c.chunk_index, c.content) for c in a] == [
            (c.page_number, c.chunk_index, c.content) for c in b
        ]

    def test_chunk_indexes_unique_per_page(self):
        pages = [(1, make_page_text(120)), (2, make_page_text(120))]
        chunks = chunk_pages(DOC, pages, target_tokens=250)
        keys = [(c.page_number, c.chunk_index) for c in chunks]
        assert len(keys) == len(set(keys))

    def test_overlap_repeats_trailing_sentences(self):
        pages = [(1, make_page_text(100))]
        chunks = chunk_pages(DOC, pages, target_tokens=300, overlap_ratio=0.15)
        assert len(chunks) >= 2
        # the start of chunk N+1 should share content with the end of chunk N
        tail = chunks[0].content[-120:]
        marker = tail.split("sentence")[-1].rstrip(".")
        assert f"sentence{marker}" in chunks[1].content

    def test_blank_pages_produce_no_chunks(self):
        chunks = chunk_pages(DOC, [(1, ""), (2, "   \n \t ")])
        assert chunks == []

    def test_token_counts_close_to_target(self):
        pages = [(1, make_page_text(200))]
        chunks = chunk_pages(DOC, pages, target_tokens=400)
        # every chunk except possibly the last should be near the target
        for c in chunks[:-1]:
            assert 200 <= c.token_count <= 600

    def test_small_page_yields_single_chunk(self):
        chunks = chunk_pages(DOC, [(1, "Tiny page with one sentence.")], target_tokens=800)
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
