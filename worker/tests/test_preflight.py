from src import preflight


def test_preflight_accepts_default_local_configuration(monkeypatch):
    clear_optional_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("APNS_SEND_DIGEST", "false")

    assert preflight.validate() == []


def test_preflight_requires_provider_credentials(monkeypatch):
    clear_optional_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "openai")

    errors = preflight.validate()

    assert "OPENAI_API_KEY is required" in errors
    assert "EDGAR_IDENTITY is required" in errors


def test_preflight_requires_r2_configuration(monkeypatch):
    clear_optional_env(monkeypatch)
    monkeypatch.setenv("STORAGE_BACKEND", "r2")

    errors = preflight.validate()

    assert "R2_BUCKET is required" in errors
    assert "R2_ENDPOINT_URL is required" in errors
    assert "R2_ACCESS_KEY_ID is required" in errors
    assert "R2_SECRET_ACCESS_KEY is required" in errors


def test_preflight_requires_apns_credentials_when_push_enabled(monkeypatch):
    clear_optional_env(monkeypatch)
    monkeypatch.setenv("APNS_SEND_DIGEST", "true")

    errors = preflight.validate()

    assert "APNS_TOPIC is required" in errors
    assert "APNS_TEAM_ID is required" in errors
    assert "APNS_KEY_ID is required" in errors
    assert "APNS_PRIVATE_KEY or APNS_PRIVATE_KEY_PATH is required when APNS_SEND_DIGEST=true" in errors


def test_preflight_rejects_invalid_lookback(monkeypatch):
    clear_optional_env(monkeypatch)
    monkeypatch.setenv("EDGAR_LOOKBACK_DAYS", "0")

    assert "EDGAR_LOOKBACK_DAYS must be a positive integer" in preflight.validate()


def clear_optional_env(monkeypatch):
    for name in (
        "EDGAR_LOOKBACK_DAYS",
        "LLM_PROVIDER",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "STORAGE_BACKEND",
        "R2_BUCKET",
        "R2_ENDPOINT_URL",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "APNS_SEND_DIGEST",
        "APNS_ENV",
        "APNS_TOPIC",
        "APNS_TEAM_ID",
        "APNS_KEY_ID",
        "APNS_PRIVATE_KEY",
        "APNS_PRIVATE_KEY_PATH",
    ):
        monkeypatch.delenv(name, raising=False)
