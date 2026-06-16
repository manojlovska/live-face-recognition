from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

STATIC_DIR = Path(__file__).resolve().parents[1] / "app" / "static"


def _client() -> TestClient:
    return TestClient(create_app())


def test_demo_route_is_public_and_serves_local_assets() -> None:
    response = _client().get("/demo")

    assert response.status_code == 200
    assert "CelebA Face Similarity Demo" in response.text
    assert 'id="show-face-boxes"' in response.text
    assert 'id="overlay-canvas"' in response.text
    assert 'id="start-live-polling"' in response.text
    assert 'id="stop-live-polling"' in response.text
    assert 'id="polling-interval"' in response.text
    assert 'id="live-status"' in response.text
    assert 'id="last-success"' in response.text
    assert 'id="last-error"' in response.text
    assert 'href="/static/demo.css"' in response.text
    assert 'src="/static/demo.js"' in response.text
    assert "https://" not in response.text
    assert "cdn" not in response.text.lower()


def test_demo_route_does_not_require_auth() -> None:
    response = _client().get("/demo")

    assert response.status_code == 200


def test_protected_api_routes_still_require_auth() -> None:
    client = _client()
    response_models = client.get("/v1/models")
    response_similarity = client.post("/v1/face/similarity", json={})

    assert response_models.status_code == 401
    assert response_similarity.status_code == 401


def test_static_assets_exist_and_stay_framework_free() -> None:
    html = (STATIC_DIR / "demo.html").read_text(encoding="utf-8")
    js = (STATIC_DIR / "demo.js").read_text(encoding="utf-8")

    assert (STATIC_DIR / "demo.css").exists()
    assert "navigator.mediaDevices.getUserMedia" in js
    assert "/v1/face/similarity" in js
    assert "drawFaceBoxes" in js
    assert "faces" in js
    assert "Start live polling" in html
    assert "Stop live polling" in html
    assert "pollingInterval" in js
    assert "requestInFlight" in js
    assert "stopLivePolling" in js
    assert "setTimeout" in js
    assert "AbortController" in js
    assert "localStorage" not in js
    assert "sessionStorage" not in js
    assert "innerHTML" not in js
    assert "setInterval" not in js
    assert "WebSocket" not in js
    assert "EventSource" not in js
    assert "https://" not in js
    assert "cdn" not in js.lower()
    assert "https://" not in html
    assert "cdn" not in html.lower()
