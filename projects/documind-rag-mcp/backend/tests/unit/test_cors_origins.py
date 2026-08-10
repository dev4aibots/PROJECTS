"""Configurable frontend origin tests."""

from app.core import settings as settings_module
from app.main import _LOCAL_ORIGINS, _allowed_origins


def _with_frontend_origin(monkeypatch, value: str) -> list[str]:
    monkeypatch.setenv("FRONTEND_ORIGIN", value)
    settings_module.get_settings.cache_clear()
    try:
        return _allowed_origins()
    finally:
        settings_module.get_settings.cache_clear()


def test_local_origins_are_always_allowed(monkeypatch):
    assert _with_frontend_origin(monkeypatch, "") == _LOCAL_ORIGINS


def test_https_frontend_origin_is_added(monkeypatch):
    origins = _with_frontend_origin(monkeypatch, "https://documind.example/")
    assert origins == [*_LOCAL_ORIGINS, "https://documind.example"]


def test_http_frontend_origin_is_supported_for_preview(monkeypatch):
    origins = _with_frontend_origin(monkeypatch, "http://preview.example")
    assert origins[-1] == "http://preview.example"


def test_invalid_frontend_origin_is_ignored(monkeypatch):
    assert _with_frontend_origin(monkeypatch, "javascript:alert(1)") == _LOCAL_ORIGINS


def test_duplicate_local_origin_not_added_twice(monkeypatch):
    origins = _with_frontend_origin(monkeypatch, "http://localhost:3000")
    assert origins == _LOCAL_ORIGINS
