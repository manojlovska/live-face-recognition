from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import Settings
from app.services.model_assets import (
    CHECKSUM_FILE_MISSING,
    CHECKSUM_MISMATCH,
    ModelAssetManager,
)

try:  # pragma: no cover - import presence is environment-dependent
    import cv2
except ModuleNotFoundError:  # pragma: no cover - handled gracefully at runtime
    cv2 = None  # type: ignore[assignment]


MODEL_STATE_MISSING = "missing"
MODEL_STATE_PRESENT_NOT_LOADED = "present_not_loaded"
MODEL_STATE_LOADED = "loaded"
MODEL_STATE_ERROR = "error"
GALLERY_STATE_NOT_LOADED = "not_loaded"

_MODEL_INPUT_SIZE = (320, 320)


@dataclass(slots=True)
class LoadedModelBundle:
    detector: Any | None = None
    embedder: Any | None = None


class ModelRuntime:
    def __init__(
        self,
        settings: Settings,
        asset_manager: ModelAssetManager | None = None,
    ) -> None:
        self._settings = settings
        self._asset_manager = asset_manager or ModelAssetManager(settings)
        self._models = LoadedModelBundle()
        self._load_error: str | None = None
        self._load_attempted = False
        self._detector_state = MODEL_STATE_MISSING
        self._embedder_state = MODEL_STATE_MISSING
        if self._settings.model_auto_load:
            self.load_models()

    @property
    def cpu_only(self) -> bool:
        return True

    @property
    def opencv_available(self) -> bool:
        return (
            cv2 is not None and hasattr(cv2, "FaceDetectorYN") and hasattr(cv2, "FaceRecognizerSF")
        )

    def is_ready(self) -> bool:
        return False

    def load_models(self) -> dict[str, object]:
        self._load_attempted = True
        asset_status = self._asset_manager.status()
        detector_asset = asset_status["detector"]
        embedder_asset = asset_status["embedder"]
        self._models = LoadedModelBundle()

        if (
            detector_asset["checksum_status"] == CHECKSUM_MISMATCH
            or embedder_asset["checksum_status"] == CHECKSUM_MISMATCH
        ):
            self._load_error = "checksum_mismatch"
            self._detector_state = MODEL_STATE_ERROR
            self._embedder_state = MODEL_STATE_ERROR
            return self.status()

        if (
            detector_asset["checksum_status"] == CHECKSUM_FILE_MISSING
            or embedder_asset["checksum_status"] == CHECKSUM_FILE_MISSING
        ):
            self._load_error = None
            self._detector_state = (
                MODEL_STATE_MISSING
                if not detector_asset["exists"]
                else MODEL_STATE_PRESENT_NOT_LOADED
            )
            self._embedder_state = (
                MODEL_STATE_MISSING
                if not embedder_asset["exists"]
                else MODEL_STATE_PRESENT_NOT_LOADED
            )
            return self.status()

        if not self.opencv_available:
            self._load_error = "opencv_not_available"
            self._detector_state = MODEL_STATE_ERROR
            self._embedder_state = MODEL_STATE_ERROR
            return self.status()

        try:
            detector_path = Path(detector_asset["path"])
            embedder_path = Path(embedder_asset["path"])
            self._models.detector = cv2.FaceDetectorYN.create(  # type: ignore[union-attr]
                str(detector_path),
                "",
                _MODEL_INPUT_SIZE,
                0.9,
                0.3,
                5000,
                _cpu_backend_id(),
                _cpu_target_id(),
            )
            self._models.embedder = cv2.FaceRecognizerSF.create(  # type: ignore[union-attr]
                str(embedder_path),
                "",
                _cpu_backend_id(),
                _cpu_target_id(),
            )
        except Exception as exc:  # pragma: no cover - exercised with monkeypatched failure
            self._load_error = f"{exc.__class__.__name__}: {exc}"
            self._models = LoadedModelBundle()
            self._detector_state = MODEL_STATE_ERROR
            self._embedder_state = MODEL_STATE_ERROR
            return self.status()

        self._load_error = None
        self._detector_state = MODEL_STATE_LOADED
        self._embedder_state = MODEL_STATE_LOADED
        return self.status()

    def status(self) -> dict[str, object]:
        asset_status = self._asset_manager.status()
        detector_state = self._detector_state_for_asset(asset_status["detector"])
        embedder_state = self._embedder_state_for_asset(asset_status["embedder"])
        return {
            "ready": self.is_ready(),
            "models": {
                "detector": detector_state,
                "embedder": embedder_state,
            },
            "gallery": GALLERY_STATE_NOT_LOADED,
            "load_error": self._load_error,
            "load_attempted": self._load_attempted,
            "cpu_only": self.cpu_only,
            "opencv_available": self.opencv_available,
            "assets": asset_status,
        }

    def readiness_summary(self) -> dict[str, object]:
        status = self.status()
        return {
            "models": self._summarize_models(
                status["models"]["detector"],
                status["models"]["embedder"],
            ),
            "gallery": GALLERY_STATE_NOT_LOADED,
            "assets": status["assets"],
            "load_error": status["load_error"],
        }

    def _detector_state_for_asset(self, asset_status: dict[str, object]) -> str:
        if self._load_error is not None:
            return MODEL_STATE_ERROR
        if self._models.detector is not None:
            return MODEL_STATE_LOADED
        if asset_status["checksum_status"] == CHECKSUM_FILE_MISSING:
            return MODEL_STATE_MISSING
        return MODEL_STATE_PRESENT_NOT_LOADED

    def _embedder_state_for_asset(self, asset_status: dict[str, object]) -> str:
        if self._load_error is not None:
            return MODEL_STATE_ERROR
        if self._models.embedder is not None:
            return MODEL_STATE_LOADED
        if asset_status["checksum_status"] == CHECKSUM_FILE_MISSING:
            return MODEL_STATE_MISSING
        return MODEL_STATE_PRESENT_NOT_LOADED

    @staticmethod
    def _summarize_models(detector_state: str, embedder_state: str) -> str:
        if detector_state == MODEL_STATE_ERROR or embedder_state == MODEL_STATE_ERROR:
            return MODEL_STATE_ERROR
        if detector_state == MODEL_STATE_MISSING or embedder_state == MODEL_STATE_MISSING:
            return MODEL_STATE_MISSING
        if detector_state == MODEL_STATE_LOADED and embedder_state == MODEL_STATE_LOADED:
            return MODEL_STATE_LOADED
        return MODEL_STATE_PRESENT_NOT_LOADED


def _cpu_backend_id() -> int:
    if cv2 is None:
        return 0
    return int(getattr(getattr(cv2, "dnn", object()), "DNN_BACKEND_OPENCV", 0))


def _cpu_target_id() -> int:
    if cv2 is None:
        return 0
    return int(getattr(getattr(cv2, "dnn", object()), "DNN_TARGET_CPU", 0))
