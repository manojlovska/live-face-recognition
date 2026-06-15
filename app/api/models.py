from fastapi import APIRouter, Depends, Request

from app.security import require_api_key

router = APIRouter(prefix="/v1", tags=["models"], dependencies=[Depends(require_api_key)])


@router.get("/models")
async def list_models(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    return {
        "object": "list",
        "data": [
            {
                "id": settings.model_id,
                "object": "model",
                "created": 0,
                "owned_by": "local",
            }
        ],
    }
