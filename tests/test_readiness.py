from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def test_readyz_returns_not_ready(monkeypatch, tmp_path) -> None:
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
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["service"] == "CelebA Face Similarity API"
    assert body["version"] == "0.1.0"
    assert body["checks"]["api"] == "ok"
    assert body["checks"]["models"] == "models_missing"
    assert body["checks"]["gallery"] == "missing"
    assert body["checks"]["model_assets"]["manifest_path"] == str(tmp_path / "model_manifest.json")
    assert body["checks"]["model_assets"]["manifest_state"] == "missing"
    assert body["checks"]["model_assets"]["detector"]["exists"] is False
    assert body["checks"]["model_assets"]["detector"]["checksum_status"] == "file_missing"
    assert body["checks"]["model_assets"]["embedder"]["exists"] is False
    assert body["checks"]["model_assets"]["embedder"]["checksum_status"] == "file_missing"
