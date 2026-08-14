"""Decoded-media validation before any untrusted upload is persisted."""
from __future__ import annotations

from io import BytesIO

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_PDF_PAGES = 5
MAX_IMAGE_PIXELS = 25_000_000


class InvalidDocument(ValueError):
    pass


def validate_document(content_type: str, data: bytes) -> None:
    if content_type == "application/pdf":
        _validate_pdf(data)
        return
    if content_type in {"image/png", "image/jpeg"}:
        _validate_image(data, content_type)
        return
    raise InvalidDocument("Unsupported document media type.")


def _validate_pdf(data: bytes) -> None:
    try:
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise InvalidDocument("Encrypted PDFs are not accepted.")
        page_count = len(reader.pages)
    except InvalidDocument:
        raise
    except (PdfReadError, ValueError, TypeError, OSError) as exc:
        raise InvalidDocument("The PDF is corrupt or unreadable.") from exc
    if page_count < 1:
        raise InvalidDocument("The PDF must contain at least one page.")
    if page_count > MAX_PDF_PAGES:
        raise InvalidDocument(f"PDFs are limited to {MAX_PDF_PAGES} pages.")


def _validate_image(data: bytes, content_type: str) -> None:
    expected = "PNG" if content_type == "image/png" else "JPEG"
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format != expected:
                raise InvalidDocument("Image encoding does not match its declared type.")
            width, height = image.size
            image.verify()
    except InvalidDocument:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise InvalidDocument("The image is corrupt or unreadable.") from exc
    if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
        raise InvalidDocument("The image dimensions exceed the safe processing limit.")
