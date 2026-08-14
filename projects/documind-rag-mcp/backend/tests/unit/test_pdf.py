"""PDF validation and extraction tests, including corrupt/encrypted/empty."""

import pytest

from app.core.errors import ValidationAppError
from app.domain.pdf import extract_pages, validate_pdf_upload
from tests.helpers import make_blank_pdf, make_encrypted_pdf, make_pdf

MAX = 10 * 1024 * 1024


class TestValidatePdfUpload:
    def test_valid_pdf_returns_page_count(self):
        data = make_pdf(["Page one text.", "Page two text.", "Page three text."])
        assert validate_pdf_upload("doc.pdf", "application/pdf", data, MAX) == 3

    def test_rejects_wrong_extension(self):
        data = make_pdf(["x"])
        with pytest.raises(ValidationAppError, match=r"\.pdf"):
            validate_pdf_upload("doc.txt", "application/pdf", data, MAX)

    def test_rejects_wrong_content_type(self):
        data = make_pdf(["x"])
        with pytest.raises(ValidationAppError, match="content type"):
            validate_pdf_upload("doc.pdf", "text/plain", data, MAX)

    def test_rejects_empty_body(self):
        with pytest.raises(ValidationAppError, match="empty"):
            validate_pdf_upload("doc.pdf", "application/pdf", b"", MAX)

    def test_rejects_oversize(self):
        data = make_pdf(["x"])
        with pytest.raises(ValidationAppError, match="upload limit"):
            validate_pdf_upload("doc.pdf", "application/pdf", data, max_bytes=10)

    def test_rejects_bad_magic_bytes(self):
        with pytest.raises(ValidationAppError, match="bad header"):
            validate_pdf_upload("doc.pdf", "application/pdf", b"NOTAPDF" * 100, MAX)

    def test_rejects_corrupt_pdf_with_valid_header(self):
        data = b"%PDF-1.7\n" + b"\x00garbage\xff" * 200
        with pytest.raises(ValidationAppError):
            validate_pdf_upload("doc.pdf", "application/pdf", data, MAX)

    def test_rejects_truncated_pdf(self):
        data = make_pdf(["Page one text."])[: len(make_pdf(["Page one text."])) // 3]
        with pytest.raises(ValidationAppError):
            validate_pdf_upload("doc.pdf", "application/pdf", data, MAX)

    def test_rejects_encrypted_pdf(self):
        with pytest.raises(ValidationAppError, match="ncrypted"):
            validate_pdf_upload("doc.pdf", "application/pdf", make_encrypted_pdf(), MAX)

    def test_error_messages_never_leak_internals(self):
        try:
            validate_pdf_upload("doc.pdf", "application/pdf", b"%PDF-1.7\ntrash", MAX)
        except ValidationAppError as e:
            msg = e.message.lower()
            for banned in ("traceback", "pypdf", "exception", "stack"):
                assert banned not in msg


class TestExtractPages:
    def test_extracts_each_page_separately(self):
        data = make_pdf(["Alpha content here.", "Beta content here."])
        pages = extract_pages(data, 1, 2)
        assert [p for p, _ in pages] == [1, 2]
        assert "Alpha" in pages[0][1]
        assert "Beta" in pages[1][1]

    def test_range_is_clamped_to_document(self):
        data = make_pdf(["Only page."])
        pages = extract_pages(data, 1, 99)
        assert len(pages) == 1

    def test_partial_batch_extraction(self):
        data = make_pdf(["P1.", "P2.", "P3.", "P4."])
        pages = extract_pages(data, 2, 3)
        assert [p for p, _ in pages] == [2, 3]

    def test_blank_pages_yield_empty_text(self):
        pages = extract_pages(make_blank_pdf(pages=1), 1, 1)
        assert pages == [(1, "")]
