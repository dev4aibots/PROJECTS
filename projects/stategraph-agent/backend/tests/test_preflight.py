from scripts.preflight import validate


def live_environment(**overrides):
    environment = {
        "APP_MODE": "live",
        "AUTH_MODE": "live",
        "DATABASE_URL": "postgresql://user:password@db.example.test/stategraph",
        "SUPABASE_JWT_ISSUER": "https://project.supabase.co/auth/v1",
        "TAVILY_API_KEY": "synthetic-test-key",
        "GROQ_API_KEY": "synthetic-test-key",
        "CORS_ORIGINS": "https://stategraph.example.test",
    }
    environment.update(overrides)
    return environment


def test_live_preflight_accepts_complete_safe_configuration():
    assert validate(live_environment()) == []


def test_live_preflight_rejects_local_auth_missing_provider_and_wildcard_cors():
    errors = validate(live_environment(
        AUTH_MODE="local",
        GROQ_API_KEY="",
        CORS_ORIGINS="*",
    ))
    assert "AUTH_MODE must be live when APP_MODE is live" in errors
    assert "at least one model provider key is required in live mode" in errors
    assert "CORS_ORIGINS cannot contain a wildcard" in errors


def test_live_preflight_rejects_insecure_urls_and_local_mode_needs_no_secrets():
    errors = validate(live_environment(
        DATABASE_URL="sqlite:///unsafe.db",
        SUPABASE_JWT_ISSUER="http://project.supabase.co/auth/v1",
        CORS_ORIGINS="http://localhost:3000/path",
    ))
    assert len(errors) == 3
    assert validate({"APP_MODE": "local", "AUTH_MODE": "local"}) == []
