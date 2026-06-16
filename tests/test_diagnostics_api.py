from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def _client(monkeypatch) -> TestClient:
    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    return TestClient(create_app())


def test_diagnostics_route_requires_auth(monkeypatch) -> None:
    with _client(monkeypatch) as client:
        response = client.get("/v1/diagnostics/startup")

    assert response.status_code == 401


def test_diagnostics_route_returns_sanitized_startup_report(monkeypatch) -> None:
    with _client(monkeypatch) as client:
        response = client.get(
            "/v1/diagnostics/startup",
            headers={"Authorization": "Bearer local-dev-key"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "startup.diagnostics"
    assert body["status"] in {"ok", "warning", "error"}
    assert body["environment"] == "development"
    assert "summary" in body
    assert "checks" in body

    text = json.dumps(body)
    assert "local-dev-key" not in text
    assert "models/model_manifest.json" not in text
    assert "data/gallery/gallery_manifest.json" not in text
    assert "data:image" not in text
    assert ".env" not in text
