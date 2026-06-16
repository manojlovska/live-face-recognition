from __future__ import annotations

from types import SimpleNamespace

from app.config import Settings
from app.services import model_runtime as model_runtime_module
from app.services.model_runtime import (
    MODEL_STATE_ERROR,
    MODEL_STATE_LOADED,
    MODEL_STATE_MISSING,
    MODEL_STATE_PRESENT_NOT_LOADED,
    ModelRuntime,
)


def _build_settings(tmp_path, *, auto_load: bool = False) -> Settings:
    return Settings(
        model_asset_dir=str(tmp_path),
        yunet_model_path=str(tmp_path / "face_detection_yunet.onnx"),
        sface_model_path=str(tmp_path / "face_recognition_sface.onnx"),
        model_manifest_path=str(tmp_path / "model_manifest.json"),
        model_auto_load=auto_load,
        gallery_dir=str(tmp_path / "gallery"),
        gallery_embeddings_path=str(tmp_path / "gallery" / "gallery_embeddings.npy"),
        gallery_metadata_path=str(tmp_path / "gallery" / "gallery_metadata.jsonl"),
        gallery_manifest_path=str(tmp_path / "gallery" / "gallery_manifest.json"),
        gallery_auto_load=False,
    )


def test_missing_model_files_do_not_crash(tmp_path) -> None:
    runtime = ModelRuntime(_build_settings(tmp_path))

    status = runtime.status()

    assert runtime.is_ready() is False
    assert status["models"]["detector"] == MODEL_STATE_MISSING
    assert status["models"]["embedder"] == MODEL_STATE_MISSING
    assert status["gallery"] == "missing"
    assert status["cpu_only"] is True


def test_runtime_load_failure_is_graceful(monkeypatch, tmp_path) -> None:
    detector_path = tmp_path / "face_detection_yunet.onnx"
    embedder_path = tmp_path / "face_recognition_sface.onnx"
    detector_path.write_bytes(b"detector")
    embedder_path.write_bytes(b"embedder")

    class FailingFaceDetectorYN:
        @staticmethod
        def create(*_args, **_kwargs):
            raise RuntimeError("detector failed")

    class FailingFaceRecognizerSF:
        @staticmethod
        def create(*_args, **_kwargs):
            return object()

    fake_cv2 = SimpleNamespace(
        FaceDetectorYN=FailingFaceDetectorYN,
        FaceRecognizerSF=FailingFaceRecognizerSF,
        dnn=SimpleNamespace(DNN_BACKEND_OPENCV=3, DNN_TARGET_CPU=4),
    )
    monkeypatch.setattr(model_runtime_module, "cv2", fake_cv2)

    runtime = ModelRuntime(_build_settings(tmp_path))
    status = runtime.load_models()

    assert status["models"]["detector"] == MODEL_STATE_ERROR
    assert status["models"]["embedder"] == MODEL_STATE_LOADED
    assert status["load_error"] == "detector_load_failed: RuntimeError: detector failed"


def test_runtime_uses_cpu_backend_and_target(monkeypatch, tmp_path) -> None:
    detector_path = tmp_path / "face_detection_yunet.onnx"
    embedder_path = tmp_path / "face_recognition_sface.onnx"
    detector_path.write_bytes(b"detector")
    embedder_path.write_bytes(b"embedder")

    captured = {"detector": None, "embedder": None}

    class FakeFaceDetectorYN:
        @staticmethod
        def create(*args):
            captured["detector"] = args
            return object()

    class FakeFaceRecognizerSF:
        @staticmethod
        def create(*args):
            captured["embedder"] = args
            return object()

    fake_cv2 = SimpleNamespace(
        FaceDetectorYN=FakeFaceDetectorYN,
        FaceRecognizerSF=FakeFaceRecognizerSF,
        dnn=SimpleNamespace(DNN_BACKEND_OPENCV=11, DNN_TARGET_CPU=12),
    )
    monkeypatch.setattr(model_runtime_module, "cv2", fake_cv2)

    runtime = ModelRuntime(_build_settings(tmp_path, auto_load=True))
    status = runtime.status()

    assert runtime.cpu_only is True
    assert status["models"]["detector"] == MODEL_STATE_LOADED
    assert status["models"]["embedder"] == MODEL_STATE_LOADED
    assert status["gallery"] == "missing"
    assert runtime.readiness_summary()["models"] == "embedding_only"
    assert captured["detector"] is not None
    assert captured["embedder"] is not None
    assert captured["detector"][6] == fake_cv2.dnn.DNN_BACKEND_OPENCV
    assert captured["detector"][7] == fake_cv2.dnn.DNN_TARGET_CPU
    assert captured["embedder"][2] == fake_cv2.dnn.DNN_BACKEND_OPENCV
    assert captured["embedder"][3] == fake_cv2.dnn.DNN_TARGET_CPU


def test_present_files_without_auto_load_are_not_loaded(tmp_path) -> None:
    detector_path = tmp_path / "face_detection_yunet.onnx"
    embedder_path = tmp_path / "face_recognition_sface.onnx"
    detector_path.write_bytes(b"detector")
    embedder_path.write_bytes(b"embedder")

    runtime = ModelRuntime(_build_settings(tmp_path))
    status = runtime.status()

    assert status["models"]["detector"] == MODEL_STATE_PRESENT_NOT_LOADED
    assert status["models"]["embedder"] == MODEL_STATE_PRESENT_NOT_LOADED
    assert status["gallery"] == "missing"
    assert runtime.is_ready() is False
