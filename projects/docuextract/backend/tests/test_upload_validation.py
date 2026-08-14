from io import BytesIO

import pytest
from PIL import Image
from reportlab.pdfgen.canvas import Canvas

from app.upload_validation import InvalidDocument, validate_document


def pdf_bytes(pages=1):
    output = BytesIO()
    canvas = Canvas(output)
    for page in range(pages):
        canvas.drawString(40, 700, f"Page {page + 1}")
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def image_bytes(kind="PNG"):
    output = BytesIO()
    Image.new("RGB", (16, 12), "white").save(output, kind)
    return output.getvalue()


def test_accepts_decoded_pdf_png_and_jpeg():
    validate_document("application/pdf", pdf_bytes())
    validate_document("image/png", image_bytes("PNG"))
    validate_document("image/jpeg", image_bytes("JPEG"))


def test_rejects_corrupt_and_over_page_limit_pdfs():
    with pytest.raises(InvalidDocument, match="corrupt|unreadable"):
        validate_document("application/pdf", b"%PDF not actually a PDF")
    with pytest.raises(InvalidDocument, match="limited to 5 pages"):
        validate_document("application/pdf", pdf_bytes(6))


def test_rejects_image_encoding_mismatch_and_corruption():
    with pytest.raises(InvalidDocument, match="does not match"):
        validate_document("image/jpeg", image_bytes("PNG"))
    with pytest.raises(InvalidDocument, match="corrupt|unreadable"):
        validate_document("image/png", b"\x89PNG\r\n\x1a\ntruncated")
