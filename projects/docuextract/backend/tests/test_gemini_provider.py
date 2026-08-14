from types import SimpleNamespace

import pytest

from app.models import Invoice
from app.provider import ExtractionError, GeminiExtractor, ProviderUnavailable


VALID = {
    "invoice_number": "INV-9",
    "vendor_name": "Example Vendor",
    "invoice_date": "2026-08-14",
    "currency": "USD",
    "subtotal": "10.00",
    "tax": "1.00",
    "total": "11.00",
    "line_items": [{
        "description": "Service",
        "quantity": "1",
        "unit_price": "10.00",
        "line_total": "10.00",
    }],
}


class Models:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.call = None

    def generate_content(self, **kwargs):
        self.call = kwargs
        if self.error:
            raise self.error
        return self.response


class Client:
    def __init__(self, response=None, error=None):
        self.models = Models(response, error)


def test_live_extractor_sends_actual_bytes_and_validates_schema():
    client = Client(SimpleNamespace(parsed=Invoice.model_validate(VALID), text=""))
    extractor = GeminiExtractor(
        api_key="", client=client,
        part_factory=lambda data, mime: {"bytes": data, "mime": mime},
    )

    invoice = extractor.extract("real.pdf", b"%PDF real invoice bytes")

    assert invoice.invoice_number == "INV-9"
    assert client.models.call["contents"][1] == {
        "bytes": b"%PDF real invoice bytes", "mime": "application/pdf"
    }
    assert client.models.call["config"]["response_schema"] is Invoice


def test_malformed_structured_output_fails_without_fabrication():
    client = Client(SimpleNamespace(parsed=None, text='{"vendor_name":"missing fields"}'))
    extractor = GeminiExtractor(
        api_key="", client=client, part_factory=lambda *_: object())
    with pytest.raises(ExtractionError, match="one correction attempt"):
        extractor.extract("invoice.png", b"\x89PNG")


def test_one_bounded_schema_correction_can_recover():
    class RepairModels:
        def __init__(self):
            self.calls = []

        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return SimpleNamespace(parsed=None, text='{"vendor_name":"missing fields"}')
            return SimpleNamespace(parsed=Invoice.model_validate(VALID), text="")

    repair_models = RepairModels()
    extractor = GeminiExtractor(
        api_key="",
        client=SimpleNamespace(models=repair_models),
        part_factory=lambda data, mime: {"bytes": data, "mime": mime},
    )
    invoice = extractor.extract("invoice.pdf", b"%PDF actual bytes")
    assert invoice.invoice_number == "INV-9"
    assert len(repair_models.calls) == 2
    assert repair_models.calls[0]["contents"][1] == repair_models.calls[1]["contents"][1]
    assert "failed schema validation" in repair_models.calls[1]["contents"][0]
    assert repair_models.calls[1]["config"]["max_output_tokens"] == 4096


def test_transient_provider_failure_is_retryable():
    client = Client(error=RuntimeError("timeout"))
    extractor = GeminiExtractor(
        api_key="", client=client, part_factory=lambda *_: object())
    with pytest.raises(ProviderUnavailable):
        extractor.extract("invoice.jpg", b"\xff\xd8")
