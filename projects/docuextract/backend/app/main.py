"""Owner-scoped DocuExtract API."""
from __future__ import annotations

import os
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .auth import Principal, current_principal
from .models import Invoice
from .provider import ExtractionError, ProviderUnavailable, build_extractor
from .repository import build_repository
from .storage import StorageUnavailable, build_storage
from .upload_validation import InvalidDocument, validate_document
from .verification import verify

MAX_BYTES = 8 * 1024 * 1024
ALLOWED = {
    "application/pdf": ((".pdf",), b"%PDF"),
    "image/png": ((".png",), b"\x89PNG"),
    "image/jpeg": ((".jpg", ".jpeg"), b"\xff\xd8"),
}

app = FastAPI(title="DocuExtract", version="2.0")
origins = [
    value.strip()
    for value in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Demo-User-Id"],
)


@app.middleware("http")
async def private_api_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


repo = build_repository()
storage = build_storage()
extractor = build_extractor()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "extractor": extractor.model,
        "repository": repo.readiness(),
        "storage": storage.mode,
    }


@app.post("/api/documents/upload")
async def upload(
    file: UploadFile = File(...),
    principal: Principal = Depends(current_principal),
):
    data = await file.read(MAX_BYTES + 1)
    content_type = file.content_type or ""
    rule = ALLOWED.get(content_type)
    suffix = (
        "." + file.filename.rsplit(".", 1)[-1].lower()
        if file.filename and "." in file.filename
        else ""
    )
    if not rule or suffix not in rule[0]:
        raise HTTPException(400, "Only PDF, PNG, and JPEG invoices are accepted.")
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "File exceeds the 8MB limit.")
    if not data.startswith(rule[1]):
        raise HTTPException(400, "File signature does not match its declared type.")
    try:
        validate_document(content_type, data)
    except InvalidDocument as exc:
        raise HTTPException(400, str(exc)) from exc
    document_id = str(uuid4())
    try:
        storage_path = storage.put(
            principal.user_id,
            document_id,
            file.filename or "invoice",
            data,
            content_type,
        )
    except (StorageUnavailable, ValueError) as exc:
        raise HTTPException(503, "Private document storage is unavailable.") from exc
    try:
        document = repo.create(
            file.filename or "invoice",
            content_type,
            len(data),
            principal.user_id,
            storage_path,
            document_id,
        )
    except Exception as exc:
        try:
            storage.delete(storage_path)
        except StorageUnavailable:
            pass
        raise HTTPException(503, "Document persistence is unavailable.") from exc
    return repo.public(document)


@app.post("/api/documents/{document_id}/process")
def process(document_id: str, principal: Principal = Depends(current_principal)):
    document = repo.get(document_id, principal.user_id)
    if not document:
        raise HTTPException(404, "document not found")
    claim = repo.claim_processing(document_id, principal.user_id)
    if claim == "missing":
        raise HTTPException(404, "document not found")
    if claim == "busy":
        raise HTTPException(409, "document is already processing")
    if claim == "complete":
        completed = repo.get(document_id, principal.user_id)
        if not completed:
            raise HTTPException(404, "document not found")
        return repo.public(completed)
    try:
        data = storage.get(document["storage_path"])
        invoice = extractor.extract(document["filename"], data)
        result = verify(invoice)
    except ExtractionError as exc:
        failed = repo.update(
            document_id,
            principal.user_id,
            status="failed_extraction",
            error=str(exc),
        )
        return repo.public(failed)
    except (ProviderUnavailable, StorageUnavailable):
        repo.update(
            document_id,
            principal.user_id,
            status="uploaded",
            error="Extraction provider unavailable; retry later.",
        )
        raise HTTPException(503, "Extraction provider unavailable; retry later.")

    duplicate = repo.invoice_number_exists(
        invoice.invoice_number, principal.user_id, document_id
    )
    labels = {
        field: (
            "verified"
            if field
            in {"invoice_date", "currency", "subtotal", "tax", "total", "line_items"}
            else "unverified"
        )
        for field in Invoice.model_fields
    }
    labels["raw_extraction"] = "ai_extracted"
    updated = repo.update(
        document_id,
        principal.user_id,
        status=result.status.lower(),
        invoice=invoice.model_dump(mode="json"),
        verification=result.model_dump(),
        trust_labels=labels,
        possible_duplicate=duplicate,
        raw_extraction=invoice.model_dump(mode="json"),
        provider_model=extractor.model,
        schema_version="invoice-v1",
    )
    return repo.public(updated)


@app.get("/api/documents")
def documents(principal: Principal = Depends(current_principal)):
    return {"documents": repo.list(principal.user_id)}


@app.get("/api/documents/{document_id}")
def detail(document_id: str, principal: Principal = Depends(current_principal)):
    document = repo.get(document_id, principal.user_id)
    if not document:
        raise HTTPException(404, "document not found")
    return repo.public(document)


@app.delete("/api/documents/{document_id}")
def delete(document_id: str, principal: Principal = Depends(current_principal)):
    document = repo.get(document_id, principal.user_id)
    if not document:
        raise HTTPException(404, "document not found")
    try:
        storage.delete(document["storage_path"])
    except StorageUnavailable as exc:
        raise HTTPException(503, "Private document storage is unavailable.") from exc
    repo.delete(document_id, principal.user_id)
    return {"deleted": True}
