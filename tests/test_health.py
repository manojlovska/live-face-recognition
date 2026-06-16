from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_healthz_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_settings_load_from_environment(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("APP_NAME", "Test Service")
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")

    settings = get_settings()

    assert settings.app_name == "Test Service"
    assert settings.app_version == "9.9.9"
    assert settings.environment == "test"
    assert settings.face_api_key == "local-dev-key"

    get_settings.cache_clear()
