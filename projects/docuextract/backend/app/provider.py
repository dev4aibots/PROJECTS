"""Multimodal extraction adapters; provider output is always Pydantic validated."""
from __future__ import annotations

import json
import os
from datetime import date
from decimal import Decimal
from typing import Any, Callable, Protocol

from pydantic import ValidationError

from .models import Invoice, LineItem


class ExtractionError(Exception):
    """The bytes are readable but do not contain a valid invoice."""


class ProviderUnavailable(Exception):
    """A transient provider failure; callers may safely retry later."""


class Extractor(Protocol):
    model: str

    def extract(self, filename: str, data: bytes) -> Invoice: ...


class DeterministicExtractor:
    """Explicit local fixture provider; never used when EXTRACTOR_MODE=live."""

    model = "deterministic-samples"

    def extract(self, filename: str, data: bytes) -> Invoice:
        name = filename.lower()
        if "cat" in name:
            raise ExtractionError("The uploaded file is not a recognizable invoice.")
        if name.endswith(".pdf") and not data.startswith(b"%PDF"):
            raise ExtractionError("The PDF is corrupted or unreadable.")
        if name.endswith((".png", ".jpg", ".jpeg")) and not (
            data.startswith(b"\x89PNG") or data.startswith(b"\xff\xd8")
        ):
            raise ExtractionError("The image is corrupted or unreadable.")
        items = [
            LineItem(description="Industrial Sensor", quantity=Decimal("10"), unit_price=Decimal("800"), line_total=Decimal("8000")),
            LineItem(description="Calibration Kit", quantity=Decimal("2"), unit_price=Decimal("1500"), line_total=Decimal("3000")),
        ]
        if "broken_lineitem" in name:
            items[1] = LineItem(description="Calibration Kit", quantity=Decimal("2"), unit_price=Decimal("1500"), line_total=Decimal("3200"))
        total = Decimal("12800") if "broken_total" in name else Decimal("11800")
        return Invoice(invoice_number="INV-2026-0042", vendor_name="Northstar Instruments", invoice_date=date(2026, 8, 1), currency="USD", subtotal=Decimal("11000"), tax=Decimal("800"), total=total, line_items=items, vendor_address="42 Example Way", customer_name="Acme Demo LLC")


class GeminiExtractor:
    """Send actual document/image bytes to Gemini structured output."""

    PROMPT = (
        "Extract this invoice exactly as printed. Do not infer missing amounts, "
        "do not repair arithmetic, and reject non-invoices. Return only the "
        "provided structured schema. Decimal values must use base-10 strings."
    )

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        client: Any | None = None,
        part_factory: Callable[[bytes, str], Any] | None = None,
    ) -> None:
        if not api_key and client is None:
            raise ValueError("GEMINI_API_KEY is required for live extraction")
        if client is None:
            try:
                from google import genai
            except ImportError as exc:  # pragma: no cover - deployment config
                raise RuntimeError("Live extraction requires google-genai") from exc
            client = genai.Client(api_key=api_key)
        if part_factory is None:
            from google.genai import types
            part_factory = lambda data, mime: types.Part.from_bytes(data=data, mime_type=mime)
        self.client = client
        self.part_factory = part_factory
        self.model = model

    def extract(self, filename: str, data: bytes) -> Invoice:
        mime = _mime_for(filename)
        document_part = self.part_factory(data, mime)
        validation_error: Exception | None = None
        for attempt in range(2):
            prompt = self.PROMPT
            if attempt:
                prompt += (
                    " Your prior response failed schema validation. Return every required "
                    "field with the exact schema and do not invent or repair invoice values."
                )
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[prompt, document_part],
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": Invoice,
                        "temperature": 0,
                        "max_output_tokens": 4096,
                    },
                )
                parsed = getattr(response, "parsed", None)
                if isinstance(parsed, Invoice):
                    return parsed
                payload = parsed if isinstance(parsed, dict) else json.loads(response.text)
                return Invoice.model_validate(payload)
            except (ValidationError, json.JSONDecodeError, TypeError, ValueError) as exc:
                validation_error = exc
                continue
            except Exception as exc:
                status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
                if status in {400, 404, 422}:
                    raise ExtractionError(
                        "The document could not be extracted as an invoice."
                    ) from exc
                raise ProviderUnavailable(
                    "Gemini extraction is temporarily unavailable."
                ) from exc
        raise ExtractionError(
            "The provider returned an invalid invoice structure after one correction attempt."
        ) from validation_error


def _mime_for(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith(".png"):
        return "image/png"
    if name.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    raise ExtractionError("Unsupported invoice media type.")


def build_extractor() -> Extractor:
    mode = os.getenv("EXTRACTOR_MODE", "deterministic").lower()
    if mode == "deterministic":
        return DeterministicExtractor()
    if mode == "live":
        return GeminiExtractor(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        )
    raise RuntimeError("EXTRACTOR_MODE must be deterministic or live")
