from fastapi.testclient import TestClient

from app.main import app


def test_readyz_returns_not_ready() -> None:
    client = TestClient(app)

    response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "CelebA Face Similarity API",
        "version": "0.1.0",
        "checks": {
            "api": "ok",
            "models": "models_missing",
            "gallery": "missing",
            "model_assets": {
                "manifest_path": "models/model_manifest.json",
                "manifest_state": "missing",
                "detector": {
                    "name": "opencv-yunet",
                    "path": "models/face_detection_yunet.onnx",
                    "exists": False,
                    "checksum_status": "file_missing",
                    "checksum": None,
                    "expected_sha256": None,
                    "source": None,
                },
                "embedder": {
                    "name": "opencv-sface",
                    "path": "models/face_recognition_sface.onnx",
                    "exists": False,
                    "checksum_status": "file_missing",
                    "checksum": None,
                    "expected_sha256": None,
                    "source": None,
                },
            },
            "gallery_details": {
                "state": "missing",
                "loaded": False,
                "load_attempted": False,
                "error": None,
                "error_code": None,
                "manifest_state": "missing",
                "manifest_path": "data/gallery/gallery_manifest.json",
                "embeddings_path": "data/gallery/gallery_embeddings.npy",
                "metadata_path": "data/gallery/gallery_metadata.jsonl",
                "version": None,
                "item_count": 0,
                "embedding_dim": None,
            },
        },
    }
