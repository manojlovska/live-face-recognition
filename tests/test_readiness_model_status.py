from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "gallery"


def build_app() -> object:
    get_settings.cache_clear()
    return create_app()


def test_readyz_reports_missing_models_by_default(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MODEL_ASSET_DIR", str(tmp_path))
    monkeypatch.setenv("YUNET_MODEL_PATH", str(tmp_path / "face_detection_yunet.onnx"))
    monkeypatch.setenv("SFACE_MODEL_PATH", str(tmp_path / "face_recognition_sface.onnx"))
    monkeypatch.setenv("MODEL_MANIFEST_PATH", str(tmp_path / "model_manifest.json"))
    monkeypatch.setenv("MODEL_AUTO_LOAD", "false")
    monkeypatch.setenv("GALLERY_DIR", str(tmp_path / "gallery"))
    monkeypatch.setenv(
        "GALLERY_EMBEDDINGS_PATH",
        str(tmp_path / "gallery" / "gallery_embeddings.npy"),
    )
    monkeypatch.setenv(
        "GALLERY_METADATA_PATH",
        str(tmp_path / "gallery" / "gallery_metadata.jsonl"),
    )
    monkeypatch.setenv(
        "GALLERY_MANIFEST_PATH",
        str(tmp_path / "gallery" / "gallery_manifest.json"),
    )
    monkeypatch.setenv("GALLERY_AUTO_LOAD", "false")
    client = TestClient(build_app())

    response = client.get("/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["checks"]["models"] == "models_missing"
    assert body["checks"]["gallery"] == "missing"
    assert body["checks"]["model_assets"]["detector"]["checksum_status"] == "file_missing"
    assert body["checks"]["model_assets"]["embedder"]["checksum_status"] == "file_missing"


def test_readyz_reports_present_not_loaded_when_files_exist(monkeypatch, tmp_path) -> None:
    detector_path = tmp_path / "face_detection_yunet.onnx"
    embedder_path = tmp_path / "face_recognition_sface.onnx"
    manifest_path = tmp_path / "model_manifest.json"
    detector_path.write_bytes(b"detector")
    embedder_path.write_bytes(b"embedder")

    monkeypatch.setenv("MODEL_ASSET_DIR", str(tmp_path))
    monkeypatch.setenv("YUNET_MODEL_PATH", str(detector_path))
    monkeypatch.setenv("SFACE_MODEL_PATH", str(embedder_path))
    monkeypatch.setenv("MODEL_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("MODEL_AUTO_LOAD", "false")
    monkeypatch.setenv("GALLERY_DIR", str(tmp_path / "gallery"))
    monkeypatch.setenv(
        "GALLERY_EMBEDDINGS_PATH",
        str(tmp_path / "gallery" / "gallery_embeddings.npy"),
    )
    monkeypatch.setenv(
        "GALLERY_METADATA_PATH",
        str(tmp_path / "gallery" / "gallery_metadata.jsonl"),
    )
    monkeypatch.setenv(
        "GALLERY_MANIFEST_PATH",
        str(tmp_path / "gallery" / "gallery_manifest.json"),
    )
    monkeypatch.setenv("GALLERY_AUTO_LOAD", "false")

    client = TestClient(build_app())

    response = client.get("/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["checks"]["models"] == "present_not_loaded"
    assert body["checks"]["gallery"] == "missing"
    assert body["checks"]["model_assets"]["detector"]["exists"] is True
    assert body["checks"]["model_assets"]["embedder"]["exists"] is True


def test_readyz_reports_embedding_only_when_models_load_without_gallery(
    monkeypatch, tmp_path
) -> None:
    detector_path = tmp_path / "face_detection_yunet.onnx"
    embedder_path = tmp_path / "face_recognition_sface.onnx"
    manifest_path = tmp_path / "model_manifest.json"
    detector_path.write_bytes(b"detector")
    embedder_path.write_bytes(b"embedder")

    monkeypatch.setenv("MODEL_ASSET_DIR", str(tmp_path))
    monkeypatch.setenv("YUNET_MODEL_PATH", str(detector_path))
    monkeypatch.setenv("SFACE_MODEL_PATH", str(embedder_path))
    monkeypatch.setenv("MODEL_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("MODEL_AUTO_LOAD", "true")
    monkeypatch.setenv("GALLERY_DIR", str(tmp_path / "gallery"))
    monkeypatch.setenv(
        "GALLERY_EMBEDDINGS_PATH",
        str(tmp_path / "gallery" / "gallery_embeddings.npy"),
    )
    monkeypatch.setenv(
        "GALLERY_METADATA_PATH",
        str(tmp_path / "gallery" / "gallery_metadata.jsonl"),
    )
    monkeypatch.setenv(
        "GALLERY_MANIFEST_PATH",
        str(tmp_path / "gallery" / "gallery_manifest.json"),
    )
    monkeypatch.setenv("GALLERY_AUTO_LOAD", "false")

    class FakeDetector:
        @staticmethod
        def create(*_args, **_kwargs):
            return object()

    class FakeEmbedder:
        @staticmethod
        def create(*_args, **_kwargs):
            return object()

    # The runtime will see loaded detector/embedder objects via the monkeypatched
    # OpenCV module below, but readiness still stays 503 because gallery loading
    # is not implemented.
    fake_cv2 = type(
        "FakeCV2",
        (),
        {
            "FaceDetectorYN": FakeDetector,
            "FaceRecognizerSF": FakeEmbedder,
            "dnn": type("DNN", (), {"DNN_BACKEND_OPENCV": 0, "DNN_TARGET_CPU": 0})(),
        },
    )()

    from app.services import model_runtime as model_runtime_module

    monkeypatch.setattr(model_runtime_module, "cv2", fake_cv2)

    client = TestClient(build_app())

    response = client.get("/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["models"] == "embedding_only"
    assert body["checks"]["gallery"] == "missing"
    assert body["checks"]["model_assets"]["detector"]["exists"] is True
    assert body["checks"]["model_assets"]["embedder"]["exists"] is True


def test_readyz_reports_ready_when_models_and_gallery_load(monkeypatch, tmp_path) -> None:
    detector_path = tmp_path / "face_detection_yunet.onnx"
    embedder_path = tmp_path / "face_recognition_sface.onnx"
    detector_path.write_bytes(b"detector")
    embedder_path.write_bytes(b"embedder")

    monkeypatch.setenv("MODEL_ASSET_DIR", str(tmp_path))
    monkeypatch.setenv("YUNET_MODEL_PATH", str(detector_path))
    monkeypatch.setenv("SFACE_MODEL_PATH", str(embedder_path))
    monkeypatch.setenv("MODEL_AUTO_LOAD", "true")
    monkeypatch.setenv("GALLERY_DIR", str(FIXTURE_DIR))
    monkeypatch.setenv("GALLERY_EMBEDDINGS_PATH", str(FIXTURE_DIR / "gallery_embeddings.npy"))
    monkeypatch.setenv("GALLERY_METADATA_PATH", str(FIXTURE_DIR / "gallery_metadata.jsonl"))
    monkeypatch.setenv("GALLERY_MANIFEST_PATH", str(FIXTURE_DIR / "gallery_manifest.json"))
    monkeypatch.setenv("GALLERY_AUTO_LOAD", "true")

    class FakeDetector:
        @staticmethod
        def create(*_args, **_kwargs):
            return object()

    class FakeEmbedder:
        @staticmethod
        def create(*_args, **_kwargs):
            return object()

    fake_cv2 = type(
        "FakeCV2",
        (),
        {
            "FaceDetectorYN": FakeDetector,
            "FaceRecognizerSF": FakeEmbedder,
            "dnn": type("DNN", (), {"DNN_BACKEND_OPENCV": 0, "DNN_TARGET_CPU": 0})(),
        },
    )()

    from app.services import model_runtime as model_runtime_module

    monkeypatch.setattr(model_runtime_module, "cv2", fake_cv2)

    client = TestClient(build_app())

    response = client.get("/readyz")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["models"] == "loaded"
    assert body["checks"]["gallery"] == "loaded"


def test_readyz_reports_gallery_load_error(monkeypatch, tmp_path) -> None:
    detector_path = tmp_path / "face_detection_yunet.onnx"
    embedder_path = tmp_path / "face_recognition_sface.onnx"
    gallery_dir = tmp_path / "gallery"
    gallery_dir.mkdir()
    detector_path.write_bytes(b"detector")
    embedder_path.write_bytes(b"embedder")
    npy_path = gallery_dir / "gallery_embeddings.npy"
    npy_path.write_bytes(b"not-a-numpy-file")
    (gallery_dir / "gallery_metadata.jsonl").write_text(
        '{"row": 0, "celeba_identity_id": "test_identity_001"}\n',
        encoding="utf-8",
    )
    (gallery_dir / "gallery_manifest.json").write_text(
        (
            '{"gallery_version": "test-gallery-v1", '
            '"embedding_model": "opencv-sface", '
            '"embedding_dim": 128, '
            '"distance": "cosine", '
            '"metadata_format": "jsonl", '
            '"item_count": 1}'
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("MODEL_ASSET_DIR", str(tmp_path))
    monkeypatch.setenv("YUNET_MODEL_PATH", str(detector_path))
    monkeypatch.setenv("SFACE_MODEL_PATH", str(embedder_path))
    monkeypatch.setenv("MODEL_AUTO_LOAD", "true")
    monkeypatch.setenv("GALLERY_DIR", str(gallery_dir))
    monkeypatch.setenv("GALLERY_EMBEDDINGS_PATH", str(npy_path))
    monkeypatch.setenv("GALLERY_METADATA_PATH", str(gallery_dir / "gallery_metadata.jsonl"))
    monkeypatch.setenv("GALLERY_MANIFEST_PATH", str(gallery_dir / "gallery_manifest.json"))
    monkeypatch.setenv("GALLERY_AUTO_LOAD", "true")

    class FakeDetector:
        @staticmethod
        def create(*_args, **_kwargs):
            return object()

    class FakeEmbedder:
        @staticmethod
        def create(*_args, **_kwargs):
            return object()

    fake_cv2 = type(
        "FakeCV2",
        (),
        {
            "FaceDetectorYN": FakeDetector,
            "FaceRecognizerSF": FakeEmbedder,
            "dnn": type("DNN", (), {"DNN_BACKEND_OPENCV": 0, "DNN_TARGET_CPU": 0})(),
        },
    )()

    from app.services import model_runtime as model_runtime_module

    monkeypatch.setattr(model_runtime_module, "cv2", fake_cv2)

    client = TestClient(build_app())

    response = client.get("/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["checks"]["models"] == "gallery_error"
    assert body["checks"]["gallery"] == "error"
    assert body["status"] == "not_ready"


def test_healthz_still_returns_200_when_models_are_missing() -> None:
    client = TestClient(build_app())

    response = client.get("/healthz")

    assert response.status_code == 200
