"""Smoke + verification-math tests for FinAudit IDP (demo mode, no keys)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from fastapi.testclient import TestClient  # noqa: E402
import index  # noqa: E402

client = TestClient(index.app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["mode"] in ("demo", "live-gemini")


def test_clean_invoice_auto_approves():
    r = client.post("/api/documents", json={"sample_id": "clean"})
    assert r.status_code == 201
    doc = r.json()
    assert doc["status"] == "AUTO_APPROVED"
    assert doc["verification"]["verified"] is True
    assert float(doc["confidence"]) >= 0.85
    # every check passed
    assert all(c["pass"] for c in doc["verification"]["checks"])


def test_mismatch_invoice_routes_to_review():
    r = client.post("/api/documents", json={"sample_id": "mismatch"})
    assert r.status_code == 201
    doc = r.json()
    assert doc["status"] == "NEEDS_REVIEW"
    assert doc["verification"]["verified"] is False
    assert "arithmetic_mismatch" in doc["routing"]["reasons"]
    # the seeded mismatch has a bad line 3 AND a bad grand total
    failing = [c for c in doc["verification"]["checks"] if not c["pass"]]
    assert len(failing) >= 2
    grand = next(c for c in doc["verification"]["checks"] if c["check"] == "grand_total")
    assert grand["pass"] is False
    assert grand["discrepancy"] != "0.00"


def test_custom_invoice_math_exact_decimals():
    """0.1 + 0.2 style float traps must not create false mismatches."""
    inv = {
        "vendor": "Float Trap Co", "invoice_number": "FT-1", "date": "2026-01-01",
        "currency": "USD", "tax_id": "X-1",
        "line_items": [
            {"description": "a", "quantity": "3", "unit_price": "0.10", "amount": "0.30"},
            {"description": "b", "quantity": "1", "unit_price": "0.20", "amount": "0.20"},
        ],
        "tax": "0.05", "stated_total": "0.55",
    }
    r = client.post("/api/documents", json={"invoice": inv})
    assert r.status_code == 201
    assert r.json()["verification"]["verified"] is True


def test_low_confidence_routes_to_review():
    """Invoice missing tax_id/invoice_number scores below 0.85 → review queue."""
    inv = {
        "vendor": "Sketchy Vendor", "invoice_number": "", "date": "2026-01-01",
        "currency": "USD",
        "line_items": [
            {"description": "thing", "quantity": "1", "unit_price": "10.00", "amount": "10.00"},
        ],
        "tax": "0", "stated_total": "10.00",
    }
    r = client.post("/api/documents", json={"invoice": inv})
    doc = r.json()
    assert doc["status"] == "NEEDS_REVIEW"
    assert any("low_confidence" in reason for reason in doc["routing"]["reasons"])


def test_review_workflow():
    doc_id = client.post("/api/documents", json={"sample_id": "mismatch"}).json()["id"]
    r = client.post(f"/api/documents/{doc_id}/review", json={"action": "approve", "note": "verified manually"})
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"
    # cannot re-review
    r2 = client.post(f"/api/documents/{doc_id}/review", json={"action": "reject"})
    assert r2.status_code == 409


def test_list_and_stats():
    r = client.get("/api/documents")
    assert r.status_code == 200
    assert r.json()["count"] >= 1
    s = client.get("/api/stats").json()
    assert s["total_documents"] >= 1
    assert s["review_queue_depth"] >= 0


def test_unknown_sample_rejected():
    r = client.post("/api/documents", json={"sample_id": "nope"})
    assert r.status_code == 400
