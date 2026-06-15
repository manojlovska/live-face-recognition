from fastapi import APIRouter, Depends, Request

from app.security import require_api_key
from app.services.face_similarity import FaceSimilarityRequest, get_engine
from app.services.image_input import decode_data_url_image

router = APIRouter(
    prefix="/v1/face",
    tags=["face-similarity"],
    dependencies=[Depends(require_api_key)],
)


@router.post("/similarity")
async def face_similarity(request: Request, body: FaceSimilarityRequest) -> dict[str, object]:
    settings = request.app.state.settings
    decoded_image = decode_data_url_image(body.image, settings.max_image_bytes)
    engine = get_engine(request)
    engine.analyze(body, decoded_image)
    return {}
