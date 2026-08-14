from scripts.preflight import validate


def test_local_preflight_passes_with_explicit_safe_modes():
    assert validate({
        "APP_MODE": "local",
        "AUTH_MODE": "local",
        "EXTRACTOR_MODE": "deterministic",
        "CORS_ORIGINS": "http://localhost:3000",
    }) == []


def test_live_preflight_requires_every_server_dependency():
    errors = validate({
        "APP_MODE": "live",
        "AUTH_MODE": "local",
        "EXTRACTOR_MODE": "deterministic",
        "CORS_ORIGINS": "*",
    })
    assert "AUTH_MODE must be live when APP_MODE=live" in errors
    assert "EXTRACTOR_MODE must be live when APP_MODE=live" in errors
    assert "CORS_ORIGINS cannot contain a wildcard" in errors
    assert "DATABASE_URL is required in live mode" in errors
    assert "SUPABASE_SERVICE_ROLE_KEY is required in live mode" in errors
    assert "GEMINI_API_KEY is required in live mode" in errors


def test_live_preflight_accepts_complete_https_configuration():
    assert validate({
        "APP_MODE": "live",
        "AUTH_MODE": "live",
        "EXTRACTOR_MODE": "live",
        "CORS_ORIGINS": "https://app.example.test",
        "DATABASE_URL": "postgresql://user:password@db.example.test/postgres",
        "SUPABASE_URL": "https://project.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "server-only",
        "SUPABASE_STORAGE_BUCKET": "invoices",
        "SUPABASE_JWT_ISSUER": "https://project.supabase.co/auth/v1",
        "GEMINI_API_KEY": "server-only",
    }) == []
