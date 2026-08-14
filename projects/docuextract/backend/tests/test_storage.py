from types import SimpleNamespace
from uuid import UUID

import pytest

from app.storage import MemoryStorage, SupabaseStorage, object_path

OWNER = UUID("00000000-0000-0000-0000-000000000001")


def test_memory_storage_uses_server_generated_owner_path_and_round_trips_bytes():
    storage = MemoryStorage()
    path = storage.put(OWNER, "document-id", "unsafe name.pdf", b"%PDF bytes", "application/pdf")
    assert path == f"{OWNER}/document-id/source.pdf"
    assert storage.get(path) == b"%PDF bytes"
    storage.delete(path)
    with pytest.raises(Exception, match="unavailable"):
        storage.get(path)


def test_object_path_rejects_unsupported_suffix():
    with pytest.raises(ValueError, match="unsupported"):
        object_path(OWNER, "document-id", "payload.exe")


class FakeClient:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(("post", url, kwargs))
        return SimpleNamespace(raise_for_status=lambda: None)

    def get(self, url, **kwargs):
        self.calls.append(("get", url, kwargs))
        return SimpleNamespace(content=b"private bytes", raise_for_status=lambda: None)

    def delete(self, url, **kwargs):
        self.calls.append(("delete", url, kwargs))
        return SimpleNamespace(raise_for_status=lambda: None)


def test_supabase_adapter_uploads_actual_bytes_without_public_url():
    client = FakeClient()
    storage = SupabaseStorage(
        "https://project.supabase.co", "server-secret", "invoices", client=client
    )
    path = storage.put(OWNER, "doc", "invoice.png", b"\x89PNG private", "image/png")
    method, url, kwargs = client.calls[0]
    assert method == "post"
    assert url.endswith(f"/storage/v1/object/invoices/{OWNER}/doc/source.png")
    assert kwargs["content"] == b"\x89PNG private"
    assert kwargs["headers"]["x-upsert"] == "false"
    assert storage.get(path) == b"private bytes"
    storage.delete(path)
    assert all("public" not in call[1] and "sign" not in call[1] for call in client.calls)
