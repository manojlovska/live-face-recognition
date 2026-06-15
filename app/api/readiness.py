from fastapi import APIRouter, Request, status

router = APIRouter()


@router.get("/readyz", tags=["health"], status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
async def readyz(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    return {
        "status": "not_ready",
        "service": settings.app_name,
        "version": "0.0.0",
        "checks": {
            "api": "ok",
            "models": "not_loaded",
            "gallery": "not_loaded",
        },
    }
