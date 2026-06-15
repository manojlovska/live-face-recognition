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
        self._detector_error: str | None = None
        self._embedder_error: str | None = None
        self._load_attempted = False
        self._detector_state = MODEL_STATE_MISSING
        self._embedder_state = MODEL_STATE_MISSING
        if self._settings.model_auto_load:
            self.load_models()

    @property
    def cpu_only(self) -> bool:
        return True

    @property
    def model_id(self) -> str:
        return self._settings.model_id

    @property
    def opencv_available(self) -> bool:
        return (
            cv2 is not None and hasattr(cv2, "FaceDetectorYN") and hasattr(cv2, "FaceRecognizerSF")
        )

    def is_ready(self) -> bool:
        return False

    def load_models(self) -> dict[str, object]:
        self._load_attempted = True
        self._detector_error = None
        self._embedder_error = None
        asset_status = self._asset_manager.status()
        detector_asset = asset_status["detector"]
        embedder_asset = asset_status["embedder"]
        self._models = LoadedModelBundle()

        self._detector_state, self._models.detector, self._detector_error = self._load_model(
            asset_status=detector_asset,
            model_name="detector",
            path_key="path",
            creator=self._create_detector,
        )
        self._embedder_state, self._models.embedder, self._embedder_error = self._load_model(
            asset_status=embedder_asset,
            model_name="embedder",
            path_key="path",
            creator=self._create_embedder,
        )
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
            "load_error": self.load_error,
            "errors": {
                "detector": self._detector_error,
                "embedder": self._embedder_error,
            },
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

    @property
    def load_error(self) -> str | None:
        return self._detector_error or self._embedder_error

    def get_detector(self) -> Any | None:
        return self._models.detector

    def get_embedder(self) -> Any | None:
        return self._models.embedder

    def detector_state(self) -> str:
        return self._detector_state

    def embedder_state(self) -> str:
        return self._embedder_state

    def _detector_state_for_asset(self, asset_status: dict[str, object]) -> str:
        if self._models.detector is not None:
            return MODEL_STATE_LOADED
        if self._detector_error is not None:
            return MODEL_STATE_ERROR
        if asset_status["checksum_status"] == CHECKSUM_FILE_MISSING:
            return MODEL_STATE_MISSING
        return MODEL_STATE_PRESENT_NOT_LOADED

    def _embedder_state_for_asset(self, asset_status: dict[str, object]) -> str:
        if self._models.embedder is not None:
            return MODEL_STATE_LOADED
        if self._embedder_error is not None:
            return MODEL_STATE_ERROR
        if asset_status["checksum_status"] == CHECKSUM_FILE_MISSING:
            return MODEL_STATE_MISSING
        return MODEL_STATE_PRESENT_NOT_LOADED

    @staticmethod
    def _summarize_models(detector_state: str, embedder_state: str) -> str:
        if detector_state == MODEL_STATE_ERROR:
            return "detector_error"
        if detector_state == MODEL_STATE_MISSING:
            return "models_missing"
        if embedder_state == MODEL_STATE_ERROR:
            return "embedder_error"
        if detector_state == MODEL_STATE_LOADED and embedder_state == MODEL_STATE_LOADED:
            return "embedding_models_loaded_gallery_missing"
        if detector_state == MODEL_STATE_LOADED:
            return "detector_loaded_gallery_missing"
        if detector_state == MODEL_STATE_PRESENT_NOT_LOADED:
            return MODEL_STATE_PRESENT_NOT_LOADED
        if embedder_state == MODEL_STATE_PRESENT_NOT_LOADED:
            return MODEL_STATE_PRESENT_NOT_LOADED
        return MODEL_STATE_PRESENT_NOT_LOADED

    def _load_model(
        self,
        *,
        asset_status: dict[str, object],
        model_name: str,
        path_key: str,
        creator,
    ) -> tuple[str, Any | None, str | None]:
        exists = bool(asset_status["exists"])
        checksum_status = asset_status["checksum_status"]
        if not exists or checksum_status == CHECKSUM_FILE_MISSING:
            return MODEL_STATE_MISSING, None, None
        if checksum_status == CHECKSUM_MISMATCH:
            return MODEL_STATE_ERROR, None, "checksum_mismatch"
        if not self.opencv_available:
            return MODEL_STATE_ERROR, None, "opencv_not_available"

        try:
            model_path = Path(asset_status[path_key])
            model = creator(model_path)
        except Exception as exc:  # pragma: no cover - exercised with monkeypatched failure
            error_message = f"{model_name}_load_failed: {exc.__class__.__name__}: {exc}"
            return MODEL_STATE_ERROR, None, error_message

        return MODEL_STATE_LOADED, model, None

    def _create_detector(self, model_path: Path) -> Any:
        return cv2.FaceDetectorYN.create(  # type: ignore[union-attr]
            str(model_path),
            "",
            _MODEL_INPUT_SIZE,
            0.9,
            0.3,
            5000,
            _cpu_backend_id(),
            _cpu_target_id(),
        )

    def _create_embedder(self, model_path: Path) -> Any:
        return cv2.FaceRecognizerSF.create(  # type: ignore[union-attr]
            str(model_path),
            "",
            _cpu_backend_id(),
            _cpu_target_id(),
        )


def _cpu_backend_id() -> int:
    if cv2 is None:
        return 0
    return int(getattr(getattr(cv2, "dnn", object()), "DNN_BACKEND_OPENCV", 0))


def _cpu_target_id() -> int:
    if cv2 is None:
        return 0
    return int(getattr(getattr(cv2, "dnn", object()), "DNN_TARGET_CPU", 0))
