from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def _client(monkeypatch, **env) -> TestClient:
    get_settings.cache_clear()
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return TestClient(create_app())


def test_development_app_starts_with_missing_model_and_gallery_assets(monkeypatch) -> None:
    with _client(
        monkeypatch,
        APP_ENV="development",
        FACE_API_KEY="local-dev-key",
        MODEL_AUTO_LOAD="true",
        GALLERY_AUTO_LOAD="true",
    ) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_strict_validation_fails_startup_when_validation_has_errors(monkeypatch) -> None:
    with pytest.raises(RuntimeError, match="FACE_API_KEY"):
        with _client(
            monkeypatch,
            APP_ENV="development",
            STRICT_STARTUP_VALIDATION="true",
        ):
            pass


def test_production_default_api_key_fails_startup(monkeypatch) -> None:
    with pytest.raises(RuntimeError, match="FACE_API_KEY"):
        with _client(
            monkeypatch,
            APP_ENV="production",
            FACE_API_KEY="change-me-local-dev-key",
        ):
            pass


def test_production_safe_api_key_can_start_even_when_readiness_is_not_ready(
    monkeypatch,
) -> None:
    with _client(
        monkeypatch,
        APP_ENV="production",
        FACE_API_KEY="prod-safe-key",
        MODEL_AUTO_LOAD="true",
        GALLERY_AUTO_LOAD="true",
    ) as client:
        response = client.get("/readyz")
        diagnostics = client.get(
            "/v1/diagnostics/startup",
            headers={"Authorization": "Bearer prod-safe-key"},
        )

    assert response.status_code == 503
    assert diagnostics.status_code == 200
    assert diagnostics.json()["status"] in {"warning", "error", "ok"}
