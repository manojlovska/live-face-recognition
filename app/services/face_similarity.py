from fastapi import Request
from pydantic import BaseModel, Field

from app.api.errors import EngineNotReadyError
from app.services.image_input import DecodedImage


class FaceSimilarityRequest(BaseModel):
    image: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    return_face_boxes: bool = True


class FaceSimilarityEngine:
    def is_ready(self) -> bool:
        return False

    def analyze(self, request: FaceSimilarityRequest, image: DecodedImage) -> None:
        raise EngineNotReadyError


def get_engine(request: Request) -> FaceSimilarityEngine:
    return request.app.state.face_similarity_engine
