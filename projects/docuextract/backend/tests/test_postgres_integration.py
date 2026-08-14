"""Credential-gated durability, RLS, transaction and lease proof.

Set DOCUEXTRACT_TEST_DATABASE_URL only to an expendable Postgres database. The
suite applies every migration and creates/deletes uniquely identified rows.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest

DATABASE_URL = os.getenv("DOCUEXTRACT_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DOCUEXTRACT_TEST_DATABASE_URL is not configured",
)


def apply_migrations() -> None:
    import psycopg

    root = Path(__file__).resolve().parents[2]
    with psycopg.connect(DATABASE_URL, autocommit=True) as connection:
        for path in sorted((root / "migrations").glob("*.sql")):
            connection.execute(path.read_text())


def test_restart_owner_isolation_atomic_lease_and_normalized_result():
    from app.repository import PostgresRepository

    apply_migrations()
    owner_id = uuid4()
    other_owner_id = uuid4()
    document_id = str(uuid4())
    repository = PostgresRepository(DATABASE_URL)
    repository.open()
    try:
        repository.create(
            "invoice.pdf",
            "application/pdf",
            1024,
            owner_id,
            f"{owner_id}/{document_id}/source.pdf",
            document_id,
        )
        assert repository.get(document_id, owner_id) is not None
        assert repository.get(document_id, other_owner_id) is None

        with ThreadPoolExecutor(max_workers=8) as executor:
            outcomes = list(
                executor.map(
                    lambda _: repository.claim_processing(document_id, owner_id),
                    range(8),
                )
            )
        assert outcomes.count("claimed") == 1
        assert outcomes.count("busy") == 7

        invoice = {
            "invoice_number": f"INV-{document_id[:8]}",
            "vendor_name": "Fictional Integration Vendor",
            "invoice_date": "2026-08-14",
            "currency": "USD",
            "subtotal": "10.00",
            "tax": "1.00",
            "total": "11.00",
            "line_items": [{
                "description": "Integration service",
                "quantity": "1",
                "unit_price": "10.00",
                "line_total": "10.00",
            }],
        }
        verification = {
            "status": "VERIFIED",
            "checks": [{
                "name": "total",
                "field": "total",
                "expected": "11.00",
                "actual": "11.00",
                "passed": True,
                "delta": "0.00",
            }],
            "tolerance": "0.02",
        }
        repository.update(
            document_id,
            owner_id,
            status="verified",
            invoice=invoice,
            verification=verification,
            raw_extraction=invoice,
            provider_model="integration-fixture",
            schema_version="invoice-v1",
        )
    finally:
        repository.close()

    restarted = PostgresRepository(DATABASE_URL)
    restarted.open()
    try:
        restored = restarted.get(document_id, owner_id)
        assert restored["status"] == "verified"
        assert restored["invoice"]["invoice_number"] == invoice["invoice_number"]
        assert restarted.get(document_id, other_owner_id) is None
        assert restarted.delete(document_id, other_owner_id) is False
        assert restarted.delete(document_id, owner_id) is True
    finally:
        restarted.close()
