from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def build_app() -> object:
    get_settings.cache_clear()
    return create_app()


def test_models_missing_auth_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    monkeypatch.setenv("FACE_MODEL_ID", "model-under-test")
    client = TestClient(build_app())

    response = client.get("/v1/models")

    assert response.status_code == 401


def test_models_wrong_auth_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    monkeypatch.setenv("FACE_MODEL_ID", "model-under-test")
    client = TestClient(build_app())

    response = client.get("/v1/models", headers={"Authorization": "Bearer wrong-key"})

    assert response.status_code == 401


def test_models_correct_auth_returns_configured_model(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    monkeypatch.setenv("FACE_MODEL_ID", "model-under-test")
    client = TestClient(build_app())

    response = client.get("/v1/models", headers={"Authorization": "Bearer local-dev-key"})

    assert response.status_code == 200
    assert response.json() == {
        "object": "list",
        "data": [
            {
                "id": "model-under-test",
                "object": "model",
                "created": 0,
                "owned_by": "local",
            }
        ],
    }
