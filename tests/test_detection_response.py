from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.services.face_similarity import FaceSimilarityEngine
from tests.image_helpers import make_image_data_url


class FakeYuNetDetector:
    def __init__(self, faces: np.ndarray) -> None:
        self.faces = faces
        self.input_size: tuple[int, int] | None = None

    def setInputSize(self, size: tuple[int, int]) -> None:  # noqa: N802 - OpenCV API
        self.input_size = tuple(size)

    def detect(self, _image: np.ndarray) -> tuple[None, np.ndarray]:
        return None, self.faces


class LoadedRuntime:
    def __init__(self, detector: object) -> None:
        self._detector = detector

    @property
    def model_id(self) -> str:
        return "celeba-face-similarity-cpu"

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

    def get_detector(self) -> object:
        return self._detector


def build_app(runtime: LoadedRuntime):
    get_settings.cache_clear()
    app = create_app()
    app.state.model_runtime = runtime
    app.state.face_similarity_engine = FaceSimilarityEngine(runtime)
    return app


def test_valid_image_with_detector_loaded_returns_detection_only_response(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    faces = np.array(
        [
            [
                100.4,
                80.1,
                220.0,
                220.0,
                150.0,
                130.0,
                190.0,
                130.0,
                170.0,
                155.0,
                152.0,
                185.0,
                188.0,
                185.0,
                0.97,
            ]
        ],
        dtype=np.float32,
    )
    detector = FakeYuNetDetector(faces)
    client = TestClient(build_app(LoadedRuntime(detector)))

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={
            "image": make_image_data_url("JPEG", size=(8, 8)),
            "top_k": 5,
            "return_face_boxes": True,
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["object"] == "face_similarity.detection_result"
    assert body["model"] == "celeba-face-similarity-cpu"
    assert body["mode"] == "detection_only"
    assert body["faces"][0]["box"] == [100, 80, 220, 220]
    assert body["faces"][0]["detection_score"] == 0.97
    assert body["faces"][0]["landmarks"] == {
        "right_eye": [150, 130],
        "left_eye": [190, 130],
        "nose_tip": [170, 155],
        "right_mouth_corner": [152, 185],
        "left_mouth_corner": [188, 185],
    }
    assert body["faces"][0]["top_matches"] == []
    assert "embedding" not in body["faces"][0]
    assert "embeddings" not in body
    assert detector.input_size == (8, 8)


def test_valid_image_with_detector_loaded_and_no_faces_returns_empty_faces(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    detector = FakeYuNetDetector(np.empty((0, 15), dtype=np.float32))
    client = TestClient(build_app(LoadedRuntime(detector)))

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={
            "image": make_image_data_url("PNG", size=(8, 8)),
            "top_k": 5,
            "return_face_boxes": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "object": "face_similarity.detection_result",
        "model": "celeba-face-similarity-cpu",
        "mode": "detection_only",
        "faces": [],
        "disclaimer": "No faces detected. Similarity matching is not implemented yet.",
    }
