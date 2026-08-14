"""Shared test helpers: build real PDFs in memory with reportlab."""

from __future__ import annotations

import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def make_pdf(pages_text: list[str]) -> bytes:
    """Build a real, parseable PDF with one text block per page."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for text in pages_text:
        y = 750
        for line in text.split("\n"):
            # naive wrap at 90 chars so long lines stay on the page
            while line:
                c.drawString(50, y, line[:90])
                line = line[90:]
                y -= 14
                if y < 50:
                    break
        c.showPage()
    c.save()
    return buf.getvalue()


def make_blank_pdf(pages: int = 1) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for _ in range(pages):
        c.showPage()
    c.save()
    return buf.getvalue()


def make_encrypted_pdf() -> bytes:
    """Build an encrypted PDF via pypdf."""
    from pypdf import PdfReader, PdfWriter

    plain = make_pdf(["secret content"])
    reader = PdfReader(io.BytesIO(plain))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("password")
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
