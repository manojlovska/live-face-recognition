import pytest
from fastapi.testclient import TestClient

from app.api.errors import EngineNotReadyError
from app.config import get_settings
from app.main import create_app
from app.services.face_similarity import FaceSimilarityEngine, FaceSimilarityRequest
from app.services.image_input import decode_data_url_image
from tests.image_helpers import make_image_data_url


def build_app() -> object:
    get_settings.cache_clear()
    return create_app()


def test_face_similarity_missing_auth_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        json={"image": "data:image/jpeg;base64,AAA"},
    )

    assert response.status_code == 401


def test_face_similarity_wrong_auth_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer wrong-key"},
        json={"image": "data:image/jpeg;base64,AAA"},
    )

    assert response.status_code == 401


def test_face_similarity_malformed_request_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={"top_k": 5},
    )

    assert response.status_code == 422


def test_face_similarity_invalid_top_k_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={"image": "data:image/jpeg;base64,AAA", "top_k": 21},
    )

    assert response.status_code == 422


def test_face_similarity_valid_request_returns_engine_not_ready(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    monkeypatch.setenv("FACE_MAX_IMAGE_BYTES", "1024")
    client = TestClient(build_app())

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={
            "image": make_image_data_url("JPEG"),
            "top_k": 5,
            "return_face_boxes": True,
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "message": ("Face similarity engine is not ready. Models and gallery are not loaded."),
            "type": "service_unavailable",
            "code": "engine_not_ready",
        }
    }


def test_stub_engine_reports_not_ready() -> None:
    engine = FaceSimilarityEngine()

    assert engine.is_ready() is False


def test_stub_engine_analyze_raises_not_ready() -> None:
    engine = FaceSimilarityEngine()
    decoded_image = decode_data_url_image(make_image_data_url("JPEG"), 1024)

    with pytest.raises(EngineNotReadyError):
        engine.analyze(
            FaceSimilarityRequest(
                image=make_image_data_url("JPEG"),
                top_k=5,
                return_face_boxes=True,
            ),
            decoded_image,
        )
