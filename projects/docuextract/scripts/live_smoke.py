#!/usr/bin/env python3
"""Authenticated post-deploy smoke for a disposable invoice and owner token."""
from __future__ import annotations

import argparse
import mimetypes
import os
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", help="Deployed API origin, for example https://api.example.com")
    parser.add_argument("invoice", type=Path, help="Disposable real invoice PDF, PNG, or JPEG")
    parser.add_argument("--keep", action="store_true", help="Keep the uploaded smoke document")
    args = parser.parse_args()
    token = os.getenv("DOCUEXTRACT_SMOKE_TOKEN", "").strip()
    if not token:
        parser.error("DOCUEXTRACT_SMOKE_TOKEN is required")
    if not args.invoice.is_file():
        parser.error("invoice path must be an existing file")

    base_url = args.base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {token}"}
    content_type = mimetypes.guess_type(args.invoice.name)[0] or "application/octet-stream"
    document_id = ""
    with httpx.Client(timeout=60, headers=headers) as client:
        health = client.get(f"{base_url}/api/health")
        health.raise_for_status()
        health_body = health.json()
        if not health_body.get("repository", {}).get("ready"):
            raise RuntimeError("repository readiness failed")

        with args.invoice.open("rb") as source:
            uploaded = client.post(
                f"{base_url}/api/documents/upload",
                files={"file": (args.invoice.name, source, content_type)},
            )
        uploaded.raise_for_status()
        document_id = uploaded.json()["id"]
        try:
            processed = client.post(f"{base_url}/api/documents/{document_id}/process")
            processed.raise_for_status()
            body = processed.json()
            if body.get("status") not in {"verified", "verification_failed"}:
                raise RuntimeError(f"unexpected extraction status: {body.get('status')}")

            detail = client.get(f"{base_url}/api/documents/{document_id}")
            detail.raise_for_status()
            listing = client.get(f"{base_url}/api/documents")
            listing.raise_for_status()
            if document_id not in {item["id"] for item in listing.json()["documents"]}:
                raise RuntimeError("uploaded document missing from owner-scoped listing")
            print(f"Live smoke passed with status={body['status']} id={document_id}")
        finally:
            if document_id and not args.keep:
                deleted = client.delete(f"{base_url}/api/documents/{document_id}")
                deleted.raise_for_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
