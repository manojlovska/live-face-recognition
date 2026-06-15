from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from tests.image_helpers import make_image_data_url


def build_app() -> object:
    get_settings.cache_clear()
    return create_app()


def test_missing_auth_still_returns_401(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        json={"image": make_image_data_url("JPEG"), "top_k": 5, "return_face_boxes": True},
    )

    assert response.status_code == 401


def test_valid_auth_with_valid_image_returns_engine_not_ready(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    monkeypatch.setenv("FACE_MAX_IMAGE_BYTES", "1024")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={"image": make_image_data_url("JPEG"), "top_k": 5, "return_face_boxes": True},
    )

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "message": "Face similarity engine is not ready. Models and gallery are not loaded.",
            "type": "service_unavailable",
            "code": "engine_not_ready",
        }
    }


def test_valid_auth_with_malformed_data_url_returns_400(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={"image": "not-a-data-url", "top_k": 5, "return_face_boxes": True},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_image_data_url"


def test_valid_auth_with_unsupported_mime_type_returns_415(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={
            "image": "data:image/gif;base64,ZmFrZQ==",
            "top_k": 5,
            "return_face_boxes": True,
        },
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_image_type"


def test_valid_auth_with_invalid_base64_returns_400(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={"image": "data:image/jpeg;base64,@@@", "top_k": 5, "return_face_boxes": True},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_image_base64"


def test_valid_auth_with_too_large_image_returns_413(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    monkeypatch.setenv("FACE_MAX_IMAGE_BYTES", "16")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={
            "image": "data:image/jpeg;base64,eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHg=",
            "top_k": 5,
            "return_face_boxes": True,
        },
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "image_too_large"


def test_valid_auth_with_non_image_bytes_returns_400(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={
            "image": "data:image/png;base64,bm90IGFuIGltYWdl",
            "top_k": 5,
            "return_face_boxes": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_image"
