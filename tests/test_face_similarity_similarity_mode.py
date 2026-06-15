from __future__ import annotations

from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app
from app.services.face_similarity import FaceSimilarityEngine
from app.services.gallery import GalleryStore
from tests.image_helpers import make_image_data_url

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "gallery"


class FakeYuNetDetector:
    def __init__(self, faces: np.ndarray) -> None:
        self.faces = faces
        self.input_size: tuple[int, int] | None = None

    def setInputSize(self, size: tuple[int, int]) -> None:  # noqa: N802 - OpenCV API
        self.input_size = tuple(size)

    def detect(self, _image: np.ndarray) -> tuple[None, np.ndarray]:
        return None, self.faces


class FakeSFaceEmbedder:
    def __init__(self) -> None:
        self.feature_vector = np.arange(1, 129, dtype=np.float32)

    def alignCrop(self, image: np.ndarray, _face: np.ndarray) -> np.ndarray:  # noqa: N802 - OpenCV API
        return image

    def feature(self, _aligned_face: np.ndarray) -> np.ndarray:  # noqa: N802 - OpenCV API
        return self.feature_vector


class SimilarityRuntime:
    def __init__(
        self, detector: object, embedder: object, gallery_store: GalleryStore | None
    ) -> None:
        self._detector = detector
        self._embedder = embedder
        self._gallery_store = gallery_store

    @property
    def model_id(self) -> str:
        return "celeba-face-similarity-cpu"

    def status(self) -> dict[str, object]:
        gallery_details = self._gallery_store.status() if self._gallery_store is not None else {}
        gallery_state = gallery_details.get("state", "missing")
        return {
            "ready": self.is_ready(),
            "models": {
                "detector": "loaded",
                "embedder": "loaded",
            },
            "gallery": gallery_state,
            "load_error": None,
            "errors": {
                "detector": None,
                "embedder": None,
            },
            "load_attempted": True,
            "cpu_only": True,
            "opencv_available": True,
            "assets": {},
            "gallery_details": gallery_details,
        }

    def readiness_summary(self) -> dict[str, object]:
        gallery_details = self._gallery_store.status() if self._gallery_store is not None else {}
        gallery_state = gallery_details.get("state", "missing")
        models_state = "loaded" if self.is_ready() else "embedding_only"
        return {
            "models": models_state,
            "gallery": gallery_state,
            "assets": {},
            "gallery_details": gallery_details,
            "load_error": None,
        }

    def is_ready(self) -> bool:
        return bool(self._gallery_store is not None and self._gallery_store.is_loaded())

    def detector_state(self) -> str:
        return "loaded"

    def embedder_state(self) -> str:
        return "loaded"

    def get_detector(self) -> object:
        return self._detector

    def get_embedder(self) -> object:
        return self._embedder

    def get_gallery_store(self) -> GalleryStore | None:
        return self._gallery_store


def _build_app(runtime: SimilarityRuntime):
    get_settings.cache_clear()
    app = create_app()
    app.state.model_runtime = runtime
    app.state.face_similarity_engine = FaceSimilarityEngine(runtime)
    return app


def _build_gallery_store() -> GalleryStore:
    settings = Settings(
        gallery_dir=str(FIXTURE_DIR),
        gallery_embeddings_path=str(FIXTURE_DIR / "gallery_embeddings.npy"),
        gallery_metadata_path=str(FIXTURE_DIR / "gallery_metadata.jsonl"),
        gallery_manifest_path=str(FIXTURE_DIR / "gallery_manifest.json"),
    )
    store = GalleryStore(settings)
    store.load()
    return store


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


def test_similarity_mode_returns_top_matches(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            SimilarityRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

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
    assert body["object"] == "face_similarity.result"
    assert body["mode"] == "similarity"
    assert body["gallery"] == {
        "state": "loaded",
        "version": "test-gallery-v1",
        "item_count": 3,
        "embedding_dim": 128,
    }
    assert body["faces"][0]["embedding"]["generated"] is True
    assert body["faces"][0]["embedding"]["returned"] is False
    assert "vector" not in body["faces"][0]["embedding"]
    assert [match["rank"] for match in body["faces"][0]["top_matches"]] == [1, 2, 3]
    top_match_ids = [match["celeba_identity_id"] for match in body["faces"][0]["top_matches"]]
    assert top_match_ids[0] == "test_identity_001"
    assert set(top_match_ids) == {
        "test_identity_001",
        "test_identity_002",
        "test_identity_003",
    }
    assert (
        body["faces"][0]["top_matches"][0]["similarity"]
        >= body["faces"][0]["top_matches"][1]["similarity"]
    )
    assert body["faces"][0]["top_matches"][0]["source_image"] is None
    assert "embeddings" not in body


def test_no_gallery_preserves_embedding_only_mode(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            SimilarityRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=None,
            )
        )
    )

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
    assert body["faces"][0]["embedding"]["generated"] is True
    assert body["faces"][0]["top_matches"] == []
    assert "gallery" not in body


def test_similarity_mode_no_faces_returns_empty_faces(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            SimilarityRuntime(
                detector=FakeYuNetDetector(np.empty((0, 15), dtype=np.float32)),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

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
        "object": "face_similarity.result",
        "model": "celeba-face-similarity-cpu",
        "mode": "similarity",
        "faces": [],
        "disclaimer": "No faces detected. Similarity result only; not identity verification.",
        "gallery": {
            "state": "loaded",
            "version": "test-gallery-v1",
            "item_count": 3,
            "embedding_dim": 128,
        },
    }


def test_invalid_image_still_fails_before_similarity(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            SimilarityRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

    response = client.post(
        "/v1/face/similarity",
        headers={"Authorization": "Bearer local-dev-key"},
        json={
            "image": "data:image/jpeg;base64,@@@",
            "top_k": 5,
            "return_face_boxes": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_image_base64"


def test_missing_auth_still_returns_401(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            SimilarityRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

    response = client.post(
        "/v1/face/similarity",
        json={
            "image": make_image_data_url("JPEG", size=(8, 8)),
            "top_k": 5,
            "return_face_boxes": True,
        },
    )

    assert response.status_code == 401
