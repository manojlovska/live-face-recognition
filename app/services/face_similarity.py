from __future__ import annotations

import numpy as np
from fastapi import Request
from pydantic import BaseModel, Field

from app.api.errors import EngineNotReadyError
from app.services.image_input import DecodedImage
from app.services.model_runtime import (
    MODEL_STATE_ERROR,
    MODEL_STATE_LOADED,
    MODEL_STATE_MISSING,
    MODEL_STATE_PRESENT_NOT_LOADED,
    ModelRuntime,
)


class FaceSimilarityRequest(BaseModel):
    image: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    return_face_boxes: bool = True


class FaceSimilarityEngine:
    def __init__(self, model_runtime: ModelRuntime | None = None) -> None:
        self._model_runtime = model_runtime

    def is_ready(self) -> bool:
        return False

    def analyze(
        self,
        request: FaceSimilarityRequest,
        image: DecodedImage,
    ) -> dict[str, object]:
        runtime = self._require_runtime()
        if runtime.detector_state() != MODEL_STATE_LOADED:
            raise EngineNotReadyError

        detector = runtime.get_detector()
        if detector is None:
            raise EngineNotReadyError

        try:
            faces = _run_yunet_detection(detector, image)
        except Exception as exc:  # pragma: no cover - exercised via model/runtime failures
            raise EngineNotReadyError from exc

        return _build_detection_response(
            model_id=runtime.model_id,
            faces=faces,
        )

    def status(self) -> dict[str, object]:
        runtime_status = self._runtime_status()
        return {
            "state": self.state(),
            "ready": self.is_ready(),
            "mode": "detection_only"
            if runtime_status["models"]["detector"] == MODEL_STATE_LOADED
            else "not_ready",
            "models": runtime_status["models"],
            "gallery": runtime_status["gallery"],
            "load_error": runtime_status["load_error"],
            "assets": runtime_status["assets"],
            "cpu_only": runtime_status["cpu_only"],
        }

    def state(self) -> str:
        runtime_status = self._runtime_status()
        detector_state = runtime_status["models"]["detector"]
        if detector_state == MODEL_STATE_ERROR:
            return "detector_error"
        if detector_state == MODEL_STATE_MISSING:
            return "models_missing"
        if detector_state == MODEL_STATE_LOADED:
            return "detector_loaded_gallery_missing"
        if detector_state == MODEL_STATE_PRESENT_NOT_LOADED:
            return "engine_not_ready"
        return "engine_not_ready"

    def _require_runtime(self) -> ModelRuntime:
        if self._model_runtime is None:
            raise EngineNotReadyError
        return self._model_runtime

    def _runtime_status(self) -> dict[str, object]:
        runtime = self._model_runtime
        if runtime is None:
            return {
                "ready": False,
                "models": {
                    "detector": MODEL_STATE_MISSING,
                    "embedder": MODEL_STATE_MISSING,
                },
                "gallery": "not_loaded",
                "load_error": None,
                "assets": {},
                "cpu_only": True,
            }

        return runtime.status()


def get_engine(request: Request) -> FaceSimilarityEngine:
    return request.app.state.face_similarity_engine


def _run_yunet_detection(detector: object, image: DecodedImage) -> list[dict[str, object]]:
    if hasattr(detector, "setInputSize"):
        detector.setInputSize((image.width, image.height))

    bgr_image = image.rgb_array[:, :, ::-1].copy()
    detection_result = detector.detect(bgr_image)
    faces = _extract_faces_array(detection_result)
    if faces.size == 0:
        return []

    return [_format_face(row) for row in _reshape_face_rows(faces)]


def _extract_faces_array(detection_result: object) -> np.ndarray:
    if isinstance(detection_result, tuple):
        if len(detection_result) == 0:
            return np.empty((0, 15), dtype=np.float32)
        faces = detection_result[-1]
    else:
        faces = detection_result

    if faces is None:
        return np.empty((0, 15), dtype=np.float32)

    array = np.asarray(faces, dtype=np.float32)
    if array.size == 0:
        return np.empty((0, 15), dtype=np.float32)
    return array


def _reshape_face_rows(faces: np.ndarray) -> np.ndarray:
    if faces.ndim == 1:
        return faces.reshape(1, -1)
    if faces.ndim > 2:
        return faces.reshape(-1, faces.shape[-1])
    return faces


def _format_face(face: np.ndarray) -> dict[str, object]:
    flattened = np.asarray(face, dtype=np.float32).reshape(-1)
    if flattened.shape[0] < 15:
        return {
            "box": [int(round(value)) for value in flattened[:4]],
            "detection_score": float(round(float(flattened[-1]), 6)) if flattened.size else 0.0,
            "landmarks": None,
            "top_matches": [],
        }

    return {
        "box": [int(round(value)) for value in flattened[:4]],
        "detection_score": float(round(float(flattened[14]), 6)),
        "landmarks": {
            "right_eye": [int(round(flattened[4])), int(round(flattened[5]))],
            "left_eye": [int(round(flattened[6])), int(round(flattened[7]))],
            "nose_tip": [int(round(flattened[8])), int(round(flattened[9]))],
            "right_mouth_corner": [int(round(flattened[10])), int(round(flattened[11]))],
            "left_mouth_corner": [int(round(flattened[12])), int(round(flattened[13]))],
        },
        "top_matches": [],
    }


def _build_detection_response(
    *,
    model_id: str,
    faces: list[dict[str, object]],
) -> dict[str, object]:
    if faces:
        disclaimer = "Detection-only result. Similarity matching is not implemented yet."
    else:
        disclaimer = "No faces detected. Similarity matching is not implemented yet."

    return {
        "object": "face_similarity.detection_result",
        "model": model_id,
        "mode": "detection_only",
        "faces": faces,
        "disclaimer": disclaimer,
    }
