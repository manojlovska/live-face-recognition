from fastapi import APIRouter, Depends, Request

from app.security import require_api_key
from app.services.face_similarity import FaceSimilarityRequest, get_engine

router = APIRouter(
    prefix="/v1/face",
    tags=["face-similarity"],
    dependencies=[Depends(require_api_key)],
)


@router.post("/similarity")
async def face_similarity(request: Request, body: FaceSimilarityRequest) -> dict[str, object]:
    engine = get_engine(request)
    engine.analyze(body)
    return {}
