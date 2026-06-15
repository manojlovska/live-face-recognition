from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.services.face_similarity import FaceSimilarityEngine
from tests.image_helpers import make_image_data_url


class MissingRuntime:
    @property
    def model_id(self) -> str:
        return "celeba-face-similarity-cpu"

    def status(self) -> dict[str, object]:
        return {
            "ready": False,
            "models": {
                "detector": "missing",
                "embedder": "missing",
            },
            "gallery": "not_loaded",
            "load_error": None,
            "errors": {
                "detector": None,
                "embedder": None,
            },
            "load_attempted": False,
            "cpu_only": True,
            "opencv_available": True,
            "assets": {},
        }

    def readiness_summary(self) -> dict[str, object]:
        return {
            "models": "models_missing",
            "gallery": "not_loaded",
            "assets": {},
            "load_error": None,
        }

    def detector_state(self) -> str:
        return "missing"

    def get_detector(self) -> object | None:
        return None


class FailingDetector:
    def setInputSize(self, _size: tuple[int, int]) -> None:  # noqa: N802 - OpenCV API
        raise AssertionError("detector should not be called")

    def detect(self, _image: np.ndarray) -> tuple[None, np.ndarray]:
        raise AssertionError("detector should not be called")


class LoadedRuntime(MissingRuntime):
    def __init__(self) -> None:
        self._detector = FailingDetector()

    def status(self) -> dict[str, object]:
        return {
            "ready": False,
            "models": {
                "detector": "loaded",
                "embedder": "missing",
            },
            "gallery": "not_loaded",
            "load_error": None,
            "errors": {
                "detector": None,
                "embedder": None,
            },
            "load_attempted": True,
            "cpu_only": True,
            "opencv_available": True,
            "assets": {},
        }

    def readiness_summary(self) -> dict[str, object]:
        return {
            "models": "detector_loaded_gallery_missing",
            "gallery": "not_loaded",
            "assets": {},
            "load_error": None,
        }

    def detector_state(self) -> str:
        return "loaded"

    def get_detector(self) -> object | None:
        return self._detector


def build_app(runtime) -> object:
    get_settings.cache_clear()
    app = create_app()
    app.state.model_runtime = runtime
    app.state.face_similarity_engine = FaceSimilarityEngine(runtime)
    return app


def test_missing_auth_still_returns_401(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(build_app(LoadedRuntime()))

    response = client.post(
        "/v1/face/similarity",
        json={"image": make_image_data_url("JPEG"), "top_k": 5, "return_face_boxes": True},
    )

    assert response.status_code == 401


def test_invalid_image_validation_happens_before_detection(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    runtime = LoadedRuntime()
    client = TestClient(build_app(runtime))

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={"image": "data:image/jpeg;base64,@@@", "top_k": 5, "return_face_boxes": True},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_image_base64"


def test_valid_image_with_detector_missing_returns_engine_not_ready(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(build_app(MissingRuntime()))

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
    assert response.json()["error"]["code"] == "engine_not_ready"
