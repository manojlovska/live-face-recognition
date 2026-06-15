from fastapi import Request
from pydantic import BaseModel, Field

from app.api.errors import EngineNotReadyError
from app.services.image_input import DecodedImage
from app.services.model_runtime import ModelRuntime


class FaceSimilarityRequest(BaseModel):
    image: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    return_face_boxes: bool = True


class FaceSimilarityEngine:
    def __init__(self, model_runtime: ModelRuntime | None = None) -> None:
        self._model_runtime = model_runtime

    def is_ready(self) -> bool:
        return False

    def analyze(self, request: FaceSimilarityRequest, image: DecodedImage) -> None:
        raise EngineNotReadyError

    def status(self) -> dict[str, object]:
        runtime_status = self._runtime_status()
        return {
            "ready": self.is_ready(),
            "models": runtime_status["models"],
            "gallery": runtime_status["gallery"],
            "load_error": runtime_status["load_error"],
            "assets": runtime_status["assets"],
            "cpu_only": runtime_status["cpu_only"],
        }

    def _runtime_status(self) -> dict[str, object]:
        if self._model_runtime is None:
            return {
                "ready": False,
                "models": {
                    "detector": "missing",
                    "embedder": "missing",
                },
                "gallery": "not_loaded",
                "load_error": None,
                "assets": {},
                "cpu_only": True,
            }

        return self._model_runtime.status()


def get_engine(request: Request) -> FaceSimilarityEngine:
    return request.app.state.face_similarity_engine
