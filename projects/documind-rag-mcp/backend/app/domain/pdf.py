"""PDF validation and page-by-page text extraction (pypdf).

Validation is defense-in-depth: extension, declared MIME, magic bytes, size,
parseability, encryption, and page count. Extraction is page-scoped so that
citations can always name a real page, and a single unreadable page never
fails the whole document.
"""

from __future__ import annotations

import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ..core.errors import ValidationAppError

PDF_MAGIC = b"%PDF-"
MAX_PAGES = 500


def validate_pdf_upload(
    filename: str,
    content_type: str,
    data: bytes,
    max_bytes: int,
) -> int:
    """Validate an uploaded PDF end to end. Returns the page count.

    Raises ValidationAppError with a client-safe message on any failure.
    """
    if not filename or not filename.lower().endswith(".pdf"):
        raise ValidationAppError("Only .pdf files are accepted.")
    if content_type not in ("application/pdf", "application/x-pdf", "application/octet-stream"):
        raise ValidationAppError("The uploaded file must be a PDF (content type mismatch).")
    if len(data) == 0:
        raise ValidationAppError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise ValidationAppError(
            f"The file exceeds the {max_bytes // (1024 * 1024)} MB upload limit."
        )
    if not data.startswith(PDF_MAGIC):
        raise ValidationAppError("The file does not look like a valid PDF (bad header).")

    try:
        reader = PdfReader(io.BytesIO(data))
    except PdfReadError:
        raise ValidationAppError("The PDF is corrupt and could not be parsed.") from None
    except Exception:
        raise ValidationAppError("The PDF could not be read.") from None

    if reader.is_encrypted:
        raise ValidationAppError("Encrypted or password-protected PDFs are not supported.")

    try:
        page_count = len(reader.pages)
    except Exception:
        raise ValidationAppError("The PDF page structure is unreadable.") from None

    if page_count == 0:
        raise ValidationAppError("The PDF contains no pages.")
    if page_count > MAX_PAGES:
        raise ValidationAppError(f"PDFs are limited to {MAX_PAGES} pages.")
    return page_count


def extract_pages(data: bytes, first_page: int, last_page: int) -> list[tuple[int, str]]:
    """Extract text for pages [first_page, last_page] (1-based, inclusive).

    A single unreadable page yields empty text instead of failing the batch —
    partial-processing resume depends on this being deterministic.
    """
    reader = PdfReader(io.BytesIO(data))
    total = len(reader.pages)
    first = max(1, first_page)
    last = min(total, last_page)
    out: list[tuple[int, str]] = []
    for page_no in range(first, last + 1):
        try:
            text = reader.pages[page_no - 1].extract_text() or ""
        except Exception:
            text = ""  # a single unreadable page must not fail the document
        out.append((page_no, text.strip()))
    return out
