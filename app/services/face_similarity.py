from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from fastapi import Request
from pydantic import BaseModel, Field

from app.core.errors import EngineNotReadyError
from app.services.gallery import GalleryStore
from app.services.image_input import DecodedImage
from app.services.model_runtime import (
    MODEL_STATE_ERROR,
    MODEL_STATE_LOADED,
    MODEL_STATE_MISSING,
    MODEL_STATE_PRESENT_NOT_LOADED,
    ModelRuntime,
)

_EMBEDDING_MODEL_NAME = "opencv-sface"


class FaceSimilarityRequest(BaseModel):
    image: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    return_face_boxes: bool = True


@dataclass(slots=True)
class FaceLandmarks:
    right_eye: tuple[float, float] | None
    left_eye: tuple[float, float] | None
    nose_tip: tuple[float, float] | None
    right_mouth_corner: tuple[float, float] | None
    left_mouth_corner: tuple[float, float] | None

    def as_dict(self) -> dict[str, list[int] | None]:
        return {
            "right_eye": _point_to_list(self.right_eye),
            "left_eye": _point_to_list(self.left_eye),
            "nose_tip": _point_to_list(self.nose_tip),
            "right_mouth_corner": _point_to_list(self.right_mouth_corner),
            "left_mouth_corner": _point_to_list(self.left_mouth_corner),
        }


@dataclass(slots=True)
class DetectedFace:
    box: tuple[float, float, float, float]
    detection_score: float
    landmarks: FaceLandmarks | None
    raw_detection_row: np.ndarray = field(repr=False, compare=False)

    def to_public_dict(self) -> dict[str, object]:
        face: dict[str, object] = {
            "box": [int(round(value)) for value in self.box],
            "detection_score": float(round(self.detection_score, 6)),
            "top_matches": [],
        }
        face["landmarks"] = self.landmarks.as_dict() if self.landmarks is not None else None
        return face


@dataclass(slots=True)
class FaceEmbedding:
    model: str
    generated: bool
    returned: bool
    dimension: int | None
    error: str | None = None
    vector: np.ndarray | None = field(default=None, repr=False, compare=False)

    def to_public_dict(self) -> dict[str, object]:
        public_embedding: dict[str, object] = {
            "model": self.model,
            "generated": self.generated,
            "returned": self.returned,
            "dimension": self.dimension,
        }
        if self.error is not None:
            public_embedding["error"] = self.error
        return public_embedding


@dataclass(slots=True)
class AnalyzedFace:
    detection: DetectedFace
    embedding: FaceEmbedding | None = None
    top_matches: list[dict[str, object]] = field(default_factory=list)

    def to_public_dict(self) -> dict[str, object]:
        face = self.detection.to_public_dict()
        if self.embedding is not None:
            face["embedding"] = self.embedding.to_public_dict()
        face["top_matches"] = self.top_matches
        return face


@dataclass(slots=True)
class FaceAnalysisResult:
    object_name: str
    model: str
    mode: str
    faces: list[AnalyzedFace]
    disclaimer: str
    gallery: dict[str, object] | None = None

    def to_public_dict(self) -> dict[str, object]:
        body = {
            "object": self.object_name,
            "model": self.model,
            "mode": self.mode,
            "faces": [face.to_public_dict() for face in self.faces],
            "disclaimer": self.disclaimer,
        }
        if self.gallery is not None:
            body["gallery"] = self.gallery
        return body


class FaceSimilarityEngine:
    def __init__(self, model_runtime: ModelRuntime | None = None) -> None:
        self._model_runtime = model_runtime

    def is_ready(self) -> bool:
        runtime = self._model_runtime
        return bool(runtime is not None and bool(getattr(runtime, "is_ready", lambda: False)()))

    def mode(self) -> str:
        runtime_status = self._runtime_status()
        detector_state = self._model_state(runtime_status, "detector")
        embedder_state = self._model_state(runtime_status, "embedder")
        gallery_state = self._gallery_state(runtime_status)

        if detector_state != MODEL_STATE_LOADED:
            return "engine_not_ready"
        if embedder_state != MODEL_STATE_LOADED:
            return "detection_only"
        if gallery_state == "loaded":
            return "similarity"
        return "embedding_only"

    def analyze(
        self,
        request: FaceSimilarityRequest,
        image: DecodedImage,
    ) -> dict[str, object]:
        runtime = self._require_runtime()
        detector_state = self._runtime_model_state(runtime, "detector")
        if detector_state != MODEL_STATE_LOADED:
            raise EngineNotReadyError

        detector = getattr(runtime, "get_detector", lambda: None)()
        if detector is None:
            raise EngineNotReadyError

        bgr_image = image.rgb_array[:, :, ::-1].copy()
        try:
            detected_faces = _run_yunet_detection(detector, bgr_image, image.width, image.height)
        except Exception as exc:  # pragma: no cover - exercised via model/runtime failures
            raise EngineNotReadyError from exc

        embedder_state = self._runtime_model_state(runtime, "embedder")
        embedder = getattr(runtime, "get_embedder", lambda: None)()
        gallery_store = getattr(runtime, "get_gallery_store", lambda: None)()
        gallery_loaded = bool(
            gallery_store is not None and bool(getattr(gallery_store, "is_loaded", lambda: False)())
        )

        if embedder_state != MODEL_STATE_LOADED or embedder is None:
            return _build_detection_response(
                model_id=runtime.model_id,
                faces=[AnalyzedFace(detection=face) for face in detected_faces],
            )

        analyzed_faces = [
            _analyze_face(
                face=face,
                embedder=embedder,
                bgr_image=bgr_image,
                top_k=request.top_k,
                gallery_store=gallery_store if gallery_loaded else None,
            )
            for face in detected_faces
        ]

        if gallery_loaded:
            return _build_similarity_response(
                model_id=runtime.model_id,
                faces=analyzed_faces,
                gallery=getattr(gallery_store, "summary", lambda: {})(),
            )

        return _build_embedding_response(
            model_id=runtime.model_id,
            faces=analyzed_faces,
        )

    def status(self) -> dict[str, object]:
        runtime_status = self._runtime_status()
        return {
            "state": self.state(),
            "mode": self.mode(),
            "ready": self.is_ready(),
            "models": runtime_status["models"],
            "gallery": runtime_status["gallery"],
            "load_error": runtime_status["load_error"],
            "assets": runtime_status["assets"],
            "gallery_details": runtime_status.get("gallery_details", {}),
            "cpu_only": runtime_status["cpu_only"],
        }

    def state(self) -> str:
        runtime_status = self._runtime_status()
        detector_state = self._model_state(runtime_status, "detector")
        embedder_state = self._model_state(runtime_status, "embedder")
        gallery_state = self._gallery_state(runtime_status)

        if detector_state == MODEL_STATE_ERROR:
            return "detector_error"
        if embedder_state == MODEL_STATE_ERROR:
            return "embedder_error"
        if gallery_state == "error":
            return "gallery_error"
        if detector_state == MODEL_STATE_MISSING:
            return "models_missing"
        if detector_state != MODEL_STATE_LOADED:
            return "engine_not_ready"
        if embedder_state == MODEL_STATE_LOADED and gallery_state == "loaded":
            return "ready"
        if embedder_state == MODEL_STATE_LOADED:
            return "embedding_only"
        if detector_state == MODEL_STATE_LOADED:
            return "detection_only"
        if embedder_state == MODEL_STATE_PRESENT_NOT_LOADED:
            return MODEL_STATE_PRESENT_NOT_LOADED
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
                "gallery": "missing",
                "load_error": None,
                "assets": {},
                "gallery_details": {},
                "cpu_only": True,
            }

        return runtime.status()

    @staticmethod
    def _model_state(runtime_status: dict[str, object], key: str) -> str:
        models = runtime_status.get("models")
        if isinstance(models, dict):
            value = models.get(key)
            if isinstance(value, str):
                return value
        return MODEL_STATE_MISSING

    @staticmethod
    def _gallery_state(runtime_status: dict[str, object]) -> str:
        value = runtime_status.get("gallery")
        if isinstance(value, str):
            return value
        return "missing"

    @staticmethod
    def _runtime_model_state(runtime: ModelRuntime, key: str) -> str:
        getter_name = f"{key}_state"
        getter = getattr(runtime, getter_name, None)
        if callable(getter):
            value = getter()
            if isinstance(value, str):
                return value
        return MODEL_STATE_MISSING


def get_engine(request: Request) -> FaceSimilarityEngine:
    return request.app.state.face_similarity_engine


def _analyze_face(
    *,
    face: DetectedFace,
    embedder: object,
    bgr_image: np.ndarray,
    top_k: int,
    gallery_store: GalleryStore | None,
) -> AnalyzedFace:
    embedding = _generate_embedding(embedder, face, bgr_image)
    top_matches: list[dict[str, object]] = []
    if embedding.generated and embedding.vector is not None and gallery_store is not None:
        matches = gallery_store.search(embedding.vector, top_k)
        top_matches = [match.to_public_dict() for match in matches]
    return AnalyzedFace(detection=face, embedding=embedding, top_matches=top_matches)


def _run_yunet_detection(
    detector: object,
    bgr_image: np.ndarray,
    width: int,
    height: int,
) -> list[DetectedFace]:
    if hasattr(detector, "setInputSize"):
        detector.setInputSize((width, height))

    detection_result = detector.detect(bgr_image)
    faces = _extract_faces_array(detection_result)
    if faces.size == 0:
        return []

    return [_format_face(row) for row in _reshape_face_rows(faces)]


def _generate_embedding(
    embedder: object,
    face: DetectedFace,
    bgr_image: np.ndarray,
) -> FaceEmbedding:
    try:
        aligned_face = _align_face(embedder, face, bgr_image)
        feature = _extract_feature(embedder, aligned_face)
        vector = np.asarray(feature, dtype=np.float32).reshape(-1)
        return FaceEmbedding(
            model=_EMBEDDING_MODEL_NAME,
            generated=True,
            returned=False,
            dimension=int(vector.size),
            vector=vector,
        )
    except Exception:  # pragma: no cover - exercised via failure fakes
        return FaceEmbedding(
            model=_EMBEDDING_MODEL_NAME,
            generated=False,
            returned=False,
            dimension=None,
            error="embedding_failed",
        )


def _align_face(embedder: object, face: DetectedFace, bgr_image: np.ndarray) -> np.ndarray:
    if hasattr(embedder, "alignCrop"):
        detection_row = face.raw_detection_row.reshape(1, -1)
        aligned_face = embedder.alignCrop(bgr_image, detection_row)
        return np.asarray(aligned_face)
    return np.asarray(bgr_image)


def _extract_feature(embedder: object, aligned_face: np.ndarray) -> object:
    if hasattr(embedder, "feature"):
        return embedder.feature(aligned_face)
    return aligned_face


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


def _format_face(face: np.ndarray) -> DetectedFace:
    flattened = np.asarray(face, dtype=np.float32).reshape(-1)
    box = tuple(float(value) for value in flattened[:4])
    detection_score = float(flattened[14]) if flattened.size >= 15 else 0.0
    landmarks = None
    if flattened.size >= 15:
        landmarks = FaceLandmarks(
            right_eye=_point_from_flattened(flattened, 4, 5),
            left_eye=_point_from_flattened(flattened, 6, 7),
            nose_tip=_point_from_flattened(flattened, 8, 9),
            right_mouth_corner=_point_from_flattened(flattened, 10, 11),
            left_mouth_corner=_point_from_flattened(flattened, 12, 13),
        )
    return DetectedFace(
        box=box,
        detection_score=detection_score,
        landmarks=landmarks,
        raw_detection_row=flattened.copy(),
    )


def _build_detection_response(
    *,
    model_id: str,
    faces: list[AnalyzedFace],
) -> dict[str, object]:
    disclaimer = (
        "Detection-only result. Similarity matching is not implemented yet."
        if faces
        else "No faces detected. Similarity matching is not implemented yet."
    )

    result = FaceAnalysisResult(
        object_name="face_similarity.detection_result",
        model=model_id,
        mode="detection_only",
        faces=faces,
        disclaimer=disclaimer,
    )
    return result.to_public_dict()


def _build_embedding_response(
    *,
    model_id: str,
    faces: list[AnalyzedFace],
) -> dict[str, object]:
    disclaimer = (
        "Embeddings were generated internally. CelebA similarity matching is not implemented yet."
        if faces
        else "No faces detected. CelebA similarity matching is not implemented yet."
    )

    result = FaceAnalysisResult(
        object_name="face_similarity.embedding_result",
        model=model_id,
        mode="embedding_only",
        faces=faces,
        disclaimer=disclaimer,
    )
    return result.to_public_dict()


def _build_similarity_response(
    *,
    model_id: str,
    faces: list[AnalyzedFace],
    gallery: dict[str, object],
) -> dict[str, object]:
    disclaimer = (
        "Similarity result only; not identity verification."
        if faces
        else "No faces detected. Similarity result only; not identity verification."
    )

    result = FaceAnalysisResult(
        object_name="face_similarity.result",
        model=model_id,
        mode="similarity",
        faces=faces,
        disclaimer=disclaimer,
        gallery=gallery,
    )
    return result.to_public_dict()


def _point_from_flattened(
    flattened: np.ndarray,
    x_index: int,
    y_index: int,
) -> tuple[float, float] | None:
    if flattened.size <= y_index:
        return None
    return float(flattened[x_index]), float(flattened[y_index])


def _point_to_list(point: tuple[float, float] | None) -> list[int] | None:
    if point is None:
        return None
    return [int(round(point[0])), int(round(point[1]))]
