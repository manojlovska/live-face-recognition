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


class FakeSFaceEmbedder:
    def __init__(self, *, feature: np.ndarray | None = None, fail: bool = False) -> None:
        self.feature_vector = feature if feature is not None else np.arange(128, dtype=np.float32)
        self.fail = fail
        self.align_calls: list[tuple[tuple[int, ...], tuple[int, ...]]] = []

    def alignCrop(self, image: np.ndarray, face: np.ndarray) -> np.ndarray:  # noqa: N802 - OpenCV API
        self.align_calls.append((tuple(image.shape), tuple(face.shape)))
        return image

    def feature(self, _aligned_face: np.ndarray) -> np.ndarray:  # noqa: N802 - OpenCV API
        if self.fail:
            raise RuntimeError("sface failed")
        return self.feature_vector


class EmbeddingRuntime:
    def __init__(self, detector: object, embedder: object) -> None:
        self._detector = detector
        self._embedder = embedder

    @property
    def model_id(self) -> str:
        return "celeba-face-similarity-cpu"

    def status(self) -> dict[str, object]:
        return {
            "ready": False,
            "models": {
                "detector": "loaded",
                "embedder": "loaded",
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
            "models": "embedding_models_loaded_gallery_missing",
            "gallery": "not_loaded",
            "assets": {},
            "load_error": None,
        }

    def detector_state(self) -> str:
        return "loaded"

    def embedder_state(self) -> str:
        return "loaded"

    def get_detector(self) -> object:
        return self._detector

    def get_embedder(self) -> object:
        return self._embedder


def build_app(runtime: EmbeddingRuntime):
    get_settings.cache_clear()
    app = create_app()
    app.state.model_runtime = runtime
    app.state.face_similarity_engine = FaceSimilarityEngine(runtime)
    return app


def _face_row() -> np.ndarray:
    return np.array(
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


def test_valid_image_with_detector_and_embedder_returns_embedding_only(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    detector = FakeYuNetDetector(_face_row())
    embedder = FakeSFaceEmbedder()
    client = TestClient(build_app(EmbeddingRuntime(detector, embedder)))

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
    assert body["object"] == "face_similarity.embedding_result"
    assert body["model"] == "celeba-face-similarity-cpu"
    assert body["mode"] == "embedding_only"
    assert body["faces"][0]["box"] == [100, 80, 220, 220]
    assert body["faces"][0]["detection_score"] == 0.97
    assert body["faces"][0]["embedding"]["generated"] is True
    assert body["faces"][0]["embedding"]["returned"] is False
    assert body["faces"][0]["embedding"]["dimension"] == 128
    assert "vector" not in body["faces"][0]["embedding"]
    assert body["faces"][0]["top_matches"] == []
    assert "embeddings" not in body
    assert embedder.align_calls[0][0] == (8, 8, 3)
    assert detector.input_size == (8, 8)


def test_no_faces_returns_empty_embedding_result(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    detector = FakeYuNetDetector(np.empty((0, 15), dtype=np.float32))
    embedder = FakeSFaceEmbedder()
    client = TestClient(build_app(EmbeddingRuntime(detector, embedder)))

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
        "object": "face_similarity.embedding_result",
        "model": "celeba-face-similarity-cpu",
        "mode": "embedding_only",
        "faces": [],
        "disclaimer": ("No faces detected. CelebA similarity matching is not implemented yet."),
    }


def test_embedder_failure_is_reported_in_embedding_metadata(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    detector = FakeYuNetDetector(_face_row())
    embedder = FakeSFaceEmbedder(fail=True)
    client = TestClient(build_app(EmbeddingRuntime(detector, embedder)))

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
    assert body["mode"] == "embedding_only"
    assert body["faces"][0]["embedding"]["generated"] is False
    assert body["faces"][0]["embedding"]["returned"] is False
    assert body["faces"][0]["embedding"]["error"] == "embedding_failed"
    assert "vector" not in body["faces"][0]["embedding"]
