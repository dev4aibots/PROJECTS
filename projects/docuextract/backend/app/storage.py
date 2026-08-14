"""Private object-storage adapters for uploaded invoice bytes."""
from __future__ import annotations

import os
from pathlib import PurePosixPath
from typing import Any, Protocol
from urllib.parse import quote, urlparse
from uuid import UUID

import httpx


class StorageUnavailable(RuntimeError):
    pass


class ObjectStorage(Protocol):
    mode: str

    def put(
        self,
        owner_id: UUID,
        document_id: str,
        filename: str,
        data: bytes,
        content_type: str,
    ) -> str: ...

    def get(self, path: str) -> bytes: ...
    def delete(self, path: str) -> None: ...


def object_path(owner_id: UUID, document_id: str, filename: str) -> str:
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix not in {".pdf", ".png", ".jpg", ".jpeg"}:
        raise ValueError("unsupported storage suffix")
    return f"{owner_id}/{document_id}/source{suffix}"


class MemoryStorage:
    mode = "memory"

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def reset(self) -> None:
        self.objects.clear()

    def put(
        self,
        owner_id: UUID,
        document_id: str,
        filename: str,
        data: bytes,
        content_type: str,
    ) -> str:
        path = object_path(owner_id, document_id, filename)
        self.objects[path] = bytes(data)
        return path

    def get(self, path: str) -> bytes:
        try:
            return self.objects[path]
        except KeyError as exc:
            raise StorageUnavailable("document object is unavailable") from exc

    def delete(self, path: str) -> None:
        self.objects.pop(path, None)


class SupabaseStorage:
    """Server-only adapter for a private Supabase Storage bucket."""

    mode = "supabase-private"

    def __init__(
        self,
        base_url: str,
        service_role_key: str,
        bucket: str,
        client: Any | None = None,
    ) -> None:
        if urlparse(base_url).scheme != "https":
            raise RuntimeError("SUPABASE_URL must use HTTPS")
        if not service_role_key or not bucket:
            raise RuntimeError("Supabase storage key and bucket are required")
        self.base_url = base_url.rstrip("/")
        self.bucket = bucket
        self.client = client or httpx.Client(
            timeout=20,
            headers={
                "Authorization": f"Bearer {service_role_key}",
                "apikey": service_role_key,
            },
        )

    def _object_url(self, path: str) -> str:
        safe_path = quote(path, safe="/")
        return f"{self.base_url}/storage/v1/object/{quote(self.bucket)}/{safe_path}"

    def put(
        self,
        owner_id: UUID,
        document_id: str,
        filename: str,
        data: bytes,
        content_type: str,
    ) -> str:
        path = object_path(owner_id, document_id, filename)
        try:
            response = self.client.post(
                self._object_url(path),
                content=data,
                headers={"Content-Type": content_type, "x-upsert": "false"},
            )
            response.raise_for_status()
            return path
        except httpx.HTTPError as exc:
            raise StorageUnavailable("private object upload failed") from exc

    def get(self, path: str) -> bytes:
        try:
            response = self.client.get(self._object_url(path))
            response.raise_for_status()
            return bytes(response.content)
        except httpx.HTTPError as exc:
            raise StorageUnavailable("private object download failed") from exc

    def delete(self, path: str) -> None:
        try:
            response = self.client.delete(
                f"{self.base_url}/storage/v1/object/{quote(self.bucket)}",
                json={"prefixes": [path]},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise StorageUnavailable("private object deletion failed") from exc


def build_storage(mode: str | None = None) -> ObjectStorage:
    selected = (mode or os.getenv("APP_MODE", "local")).strip().lower()
    if selected == "local":
        return MemoryStorage()
    if selected == "live":
        return SupabaseStorage(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
            os.getenv("SUPABASE_STORAGE_BUCKET", "invoices"),
        )
    raise RuntimeError("APP_MODE must be local or live")
