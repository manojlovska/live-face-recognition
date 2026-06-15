from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def build_app() -> object:
    get_settings.cache_clear()
    return create_app()


def test_readyz_reports_missing_models_by_default() -> None:
    client = TestClient(build_app())

    response = client.get("/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["checks"]["models"] == "missing"
    assert body["checks"]["gallery"] == "not_loaded"
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

    client = TestClient(build_app())

    response = client.get("/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["checks"]["models"] == "present_not_loaded"
    assert body["checks"]["gallery"] == "not_loaded"
    assert body["checks"]["model_assets"]["detector"]["exists"] is True
    assert body["checks"]["model_assets"]["embedder"]["exists"] is True


def test_healthz_still_returns_200_when_models_are_missing() -> None:
    client = TestClient(build_app())

    response = client.get("/healthz")

    assert response.status_code == 200
