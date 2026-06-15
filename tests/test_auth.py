from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.security import require_api_key


def build_test_app() -> FastAPI:
    app = create_app()

    @app.get("/protected")
    def protected(_: None = Depends(require_api_key)) -> dict[str, bool]:
        return {"ok": True}

    return app


def test_missing_authorization_header_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    get_settings.cache_clear()
    client = TestClient(build_test_app())

    response = client.get("/protected")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {
        "error": {
            "message": "Invalid or missing API key.",
            "type": "authentication_error",
            "code": "invalid_api_key",
        }
    }


def test_malformed_authorization_header_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    get_settings.cache_clear()
    client = TestClient(build_test_app())

    response = client.get("/protected", headers={"Authorization": "Bearer"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_wrong_scheme_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    get_settings.cache_clear()
    client = TestClient(build_test_app())

    response = client.get("/protected", headers={"Authorization": "Basic local-dev-key"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_wrong_bearer_token_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    get_settings.cache_clear()
    client = TestClient(build_test_app())

    response = client.get("/protected", headers={"Authorization": "Bearer wrong-key"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_correct_bearer_token_is_accepted(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    get_settings.cache_clear()
    client = TestClient(build_test_app())

    response = client.get("/protected", headers={"Authorization": "Bearer local-dev-key"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_empty_or_unset_configured_api_key_fails_closed(monkeypatch) -> None:
    monkeypatch.delenv("FACE_API_KEY", raising=False)
    get_settings.cache_clear()
    client = TestClient(build_test_app())

    missing_key_response = client.get("/protected", headers={"Authorization": "Bearer anything"})

    monkeypatch.setenv("FACE_API_KEY", "")
    get_settings.cache_clear()
    empty_key_client = TestClient(build_test_app())
    empty_key_response = empty_key_client.get(
        "/protected",
        headers={"Authorization": "Bearer anything"},
    )

    assert missing_key_response.status_code == 401
    assert empty_key_response.status_code == 401
